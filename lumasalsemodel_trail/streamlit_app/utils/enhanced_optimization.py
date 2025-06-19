# 增强版优化函数 - 集成现实约束
import copy
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, Callable

from .optimization import run_model_with_params
from .realistic_constraints import RealisticConstraintHandler

def run_model_with_realistic_constraints(base_params: Dict[str, Any], 
                                       params_to_update: Dict[str, Any], 
                                       objective_metric: str,
                                       constraint_handler: Optional[RealisticConstraintHandler] = None,
                                       penalty_weight: float = 0.1) -> float:
    """
    使用现实约束的模型评估函数
    
    Args:
        base_params: 基础模型参数
        params_to_update: 要更新的参数
        objective_metric: 目标指标
        constraint_handler: 现实约束处理器
        penalty_weight: 惩罚权重
        
    Returns:
        考虑现实约束后的目标函数值
    """
    if constraint_handler is None:
        constraint_handler = RealisticConstraintHandler()
    
    try:
        # 1. 应用现实约束修正参数
        constrained_params = constraint_handler.apply_realistic_constraints(params_to_update)
        
        # 2. 使用修正后的参数运行模型
        model_params = copy.deepcopy(base_params)
        
        # 更新参数，处理嵌套参数
        for param_key, param_value in constrained_params.items():
            keys = param_key.split('.')
            d = model_params
            for i, k in enumerate(keys[:-1]):
                if k not in d:
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = param_value
        
        # 3. 运行模型获得基础得分
        from luma_sales_model.financial_model import LumaFinancialModel
        model = LumaFinancialModel(params=model_params)
        results_df = model.run_model()
        
        if results_df is not None and not results_df.empty and objective_metric in results_df.columns:
            base_score = results_df[objective_metric].sum()
        else:
            base_score = -float('inf')
        
        # 4. 计算现实约束惩罚
        penalty_score = constraint_handler.calculate_penalty_score(params_to_update)
        
        # 5. 返回调整后的得分
        final_score = base_score - penalty_weight * penalty_score
        
        return float(final_score)
        
    except Exception as e:
        print(f"现实约束模型评估出错: {str(e)}")
        return -float('inf')

def enhanced_grid_search_optimizer(base_params: dict, 
                                 params_to_optimize_ranges: dict, 
                                 objective_metric: str, 
                                 points_per_dim: int,
                                 progress_callback=None,
                                 constraint_handler=None,
                                 monitor=None,
                                 realistic_constraint_handler=None,
                                 penalty_weight: float = 0.1) -> tuple:
    """
    增强版网格搜索，集成现实约束
    """
    import itertools
    import time
    import warnings
    
    if not params_to_optimize_ranges:
        return {}, -float('inf'), pd.DataFrame()

    param_names = list(params_to_optimize_ranges.keys())
    
    # 为每个参数生成采样点
    param_value_grids = []
    for param_name in param_names:
        min_val, max_val = params_to_optimize_ranges[param_name]
        if max_val <= min_val:
            param_value_grids.append(np.array([min_val]))
            print(f"警告: 参数 '{param_name}' 的范围无效 [{min_val}, {max_val}]。仅使用最小值。")
        else:
            param_value_grids.append(np.linspace(min_val, max_val, points_per_dim))

    # 创建所有参数组合
    param_combinations = list(itertools.product(*param_value_grids))
    total_combinations = len(param_combinations)
    
    print(f"增强网格搜索：总共 {total_combinations} 种参数组合需要评估。")

    best_score = -float('inf')
    best_params_combination = {}
    
    results_list = []

    # 初始化现实约束处理器
    if realistic_constraint_handler is None:
        realistic_constraint_handler = RealisticConstraintHandler()
    
    start_time = time.time()

    for i, current_combination_values in enumerate(param_combinations):
        params_to_update = dict(zip(param_names, current_combination_values))
        
        # 使用现实约束的评估函数
        current_score = run_model_with_realistic_constraints(
            base_params, params_to_update, objective_metric,
            realistic_constraint_handler, penalty_weight
        )
        
        # 更新监控器
        if monitor:
            monitor.record_iteration(
                iteration=i+1,
                current_score=current_score,
                best_score=max(best_score, current_score),
                exploration_rate=1.0 - (i / total_combinations)
            )
        
        results_list.append({**params_to_update, objective_metric: current_score})

        if current_score > best_score:
            best_score = current_score
            best_params_combination = params_to_update
        
        # 检查早停
        if monitor and monitor.should_stop_early():
            print(f"检测到早停条件，在第{i+1}次迭代停止")
            break
            
        if progress_callback:
            progress_callback((i + 1) / total_combinations)
        
        # 打印进度
        if (i + 1) % max(1, total_combinations // 20) == 0 or (i + 1) == total_combinations:
            elapsed_time = time.time() - start_time
            avg_time_per_combo = elapsed_time / (i + 1)
            remaining_combos = total_combinations - (i + 1)
            estimated_time_remaining = remaining_combos * avg_time_per_combo
            print(f"进度: {i+1}/{total_combinations} ({((i+1)/total_combinations)*100:.2f}%) | "
                  f"当前最佳 {objective_metric}: {best_score:.2f} | "
                  f"预计剩余时间: {estimated_time_remaining:.2f} 秒")

    all_results_df = pd.DataFrame(results_list)
    # 按目标指标降序排序
    if not all_results_df.empty and objective_metric in all_results_df.columns:
        all_results_df = all_results_df.sort_values(by=objective_metric, ascending=False).reset_index(drop=True)

    print(f"增强网格搜索完成。最佳参数: {best_params_combination}, 最佳 {objective_metric}: {best_score}")
    
    return best_params_combination, best_score, all_results_df

def enhanced_bayesian_optimizer(base_params: dict,
                               params_to_optimize_ranges: dict,
                               objective_metric: str,
                               n_iterations: int,
                               n_initial_points: int,
                               exploitation_vs_exploration: float = 0.1,
                               progress_callback=None,
                               realistic_constraint_handler=None,
                               penalty_weight: float = 0.1) -> tuple:
    """
    增强版贝叶斯优化，集成现实约束
    """
    try:
        from skopt import gp_minimize
        from skopt.space import Real, Integer
        from skopt.utils import use_named_args
    except ImportError:
        raise ImportError("scikit-optimize 库未找到或导入失败。")

    if not params_to_optimize_ranges:
        return {}, -float('inf'), pd.DataFrame()

    param_names = list(params_to_optimize_ranges.keys())
    
    # 定义搜索空间
    search_space = []
    for param_name in param_names:
        min_val, max_val = params_to_optimize_ranges[param_name]
        # 简单的类型判断
        if isinstance(min_val, int) and isinstance(max_val, int) and \
           ("per_half_year" in param_name or "clients" in param_name):
            search_space.append(Integer(min_val, max_val, name=param_name))
        else:
            search_space.append(Real(min_val, max_val, name=param_name))

    results_list = []
    iteration_count = 0
    
    # 初始化现实约束处理器
    if realistic_constraint_handler is None:
        realistic_constraint_handler = RealisticConstraintHandler()

    # 定义目标函数
    @use_named_args(search_space)
    def objective_function(**params_as_kwargs):
        nonlocal iteration_count
        iteration_count += 1

        # 使用现实约束的评估函数
        current_score = run_model_with_realistic_constraints(
            base_params, params_as_kwargs, objective_metric,
            realistic_constraint_handler, penalty_weight
        )
        
        # 存储结果
        result_entry = {**params_as_kwargs, objective_metric: current_score}
        results_list.append(result_entry)
        
        if progress_callback:
            progress_callback(iteration_count / n_iterations, f"贝叶斯优化: {iteration_count}/{n_iterations}")
            
        # 返回负值用于最小化
        return -current_score 

    print(f"开始增强贝叶斯优化：总迭代 {n_iterations} 次, 初始点 {n_initial_points} 次。")
    
    # 执行优化
    result = gp_minimize(
        func=objective_function,
        dimensions=search_space,
        n_calls=n_iterations,
        n_initial_points=n_initial_points,
        acq_func="EI",
        xi=exploitation_vs_exploration,
        random_state=0
    )

    best_params_combination = dict(zip(param_names, result.x))
    best_score_positive = -result.fun

    all_results_df = pd.DataFrame(results_list)
    if not all_results_df.empty and objective_metric in all_results_df.columns:
         all_results_df = all_results_df.sort_values(by=objective_metric, ascending=False).reset_index(drop=True)
    
    print(f"增强贝叶斯优化完成。最佳参数: {best_params_combination}, 最佳 {objective_metric}: {best_score_positive}")

    return best_params_combination, best_score_positive, all_results_df

def enhanced_genetic_algorithm_optimizer(base_params: dict,
                                        params_to_optimize_ranges: dict,
                                        objective_metric: str,
                                        population_size: int,
                                        n_generations: int,
                                        mutation_rate: float,
                                        crossover_prob: float = 0.7,
                                        progress_callback=None,
                                        realistic_constraint_handler=None,
                                        penalty_weight: float = 0.1) -> tuple:
    """
    增强版遗传算法，集成现实约束
    """
    try:
        import random
        from deap import base, creator, tools
    except ImportError:
        raise ImportError("DEAP 库未找到或导入失败。")

    if not params_to_optimize_ranges:
        return {}, -float('inf'), pd.DataFrame()

    param_names = list(params_to_optimize_ranges.keys())
    bounds = [params_to_optimize_ranges[name] for name in param_names]
    
    # 初始化现实约束处理器
    if realistic_constraint_handler is None:
        realistic_constraint_handler = RealisticConstraintHandler()

    # DEAP 设置
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    # 定义基因生成器
    for i, param_name in enumerate(param_names):
        min_val, max_val = bounds[i]
        toolbox.register(f"attr_{i}", random.uniform, min_val, max_val)

    # 定义个体和种群
    attrs = tuple(toolbox.__getattribute__(f'attr_{i}') for i in range(len(param_names)))
    toolbox.register("individual", tools.initCycle, creator.Individual, attrs)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # 定义遗传算子
    def evaluate(individual):
        params_to_update = dict(zip(param_names, individual))
        score = run_model_with_realistic_constraints(
            base_params, params_to_update, objective_metric,
            realistic_constraint_handler, penalty_weight
        )
        return (score,)

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2)
    toolbox.register("select", tools.selTournament, tournsize=3)

    # 运行算法
    pop = toolbox.population(n=population_size)
    hof = tools.HallOfFame(1)

    results_list = []

    # 初始种群评估
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
        results_list.append({**dict(zip(param_names, ind)), objective_metric: fit[0]})

    if progress_callback:
        progress_callback(0, f"遗传算法: 第 0 代")

    for gen in range(1, n_generations + 1):
        # 选择下一代
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))

        # 交叉
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < crossover_prob:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        # 变异
        for mutant in offspring:
            if random.random() < mutation_rate:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        
        # 评估新个体
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            results_list.append({**dict(zip(param_names, ind)), objective_metric: fit[0]})

        # 更新种群
        pop[:] = offspring
        hof.update(pop)
        
        if progress_callback:
            progress_callback(gen / n_generations, f"遗传算法: 第 {gen}/{n_generations} 代 | 最佳: {hof[0].fitness.values[0]:.4f}")

    # 结果处理
    best_ind = hof[0]
    best_params_combination = dict(zip(param_names, best_ind))
    best_score = best_ind.fitness.values[0]
    
    all_results_df = pd.DataFrame(results_list)
    if not all_results_df.empty and objective_metric in all_results_df.columns:
        all_results_df = all_results_df.sort_values(by=objective_metric, ascending=False).reset_index(drop=True)

    print(f"增强遗传算法完成。最佳参数: {best_params_combination}, 最佳 {objective_metric}: {best_score}")

    return best_params_combination, best_score, all_results_df