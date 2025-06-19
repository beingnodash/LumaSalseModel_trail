# Optimization algorithms and helper functions
import copy
import numpy as np
import pandas as pd
import sys
import os
import itertools # 确保导入 itertools
import time      # 确保导入 time
import warnings
from typing import Dict, Any, Tuple, Optional, Callable

try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer
    from skopt.utils import use_named_args
except ImportError:
    print("scikit-optimize 未安装。请运行 'pip install scikit-optimize' 来安装它。")
    # 可以选择抛出错误或设置一个标志，以便在UI中禁用此选项
    gp_minimize = None 
    Real = None
    Integer = None
    use_named_args = None

# 确保能够找到 luma_sales_model模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from luma_sales_model.financial_model import LumaFinancialModel

# 导入新的优化组件
try:
    from .constraint_handler import LumaConstraintHandler
    from .optimization_monitor import OptimizationMonitor, OptimizationCallback
except ImportError:
    # 如果导入失败，定义空的替代类
    class LumaConstraintHandler:
        def __init__(self, *args, **kwargs): pass
        def validate_and_repair_optimization_params(self, params): return params
    
    class OptimizationMonitor:
        def __init__(self, *args, **kwargs): pass
        def record_iteration(self, *args, **kwargs): pass
        def should_stop_early(self): return False
    
    class OptimizationCallback:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return False

def run_model_with_params(base_params: dict, params_to_update: dict, objective_metric: str) -> float:
    """
    使用一组新的参数运行LumaFinancialModel，并返回目标指标的值。

    Args:
        base_params (dict): 模型参数的基础字典。
        params_to_update (dict): 一个字典，键是参数名称（嵌套参数可用点分隔），
                                 值是新的参数值。
        objective_metric (str): 模型结果中要返回的指标名称。

    Returns:
        float: 目标指标的值，如果发生错误或未找到指标，则返回-float('inf')。
    """
    try:
        model_params = copy.deepcopy(base_params)

        # 更新参数，处理嵌套参数
        for param_key, param_value in params_to_update.items():
            keys = param_key.split('.')
            d = model_params
            for i, k in enumerate(keys[:-1]):
                if k not in d:
                    # 如果基础参数完整且param_key有效，则理想情况下不应发生这种情况。
                    # 为确保稳健性，如果路径不存在则创建它。
                    d[k] = {} 
                d = d[k]
            d[keys[-1]] = param_value
        
        # 初始化并运行模型
        model = LumaFinancialModel(params=model_params)
        results_df = model.run_model() # run_model 返回一个DataFrame

        # 检查DataFrame是否有效以及目标列是否存在
        if results_df is not None and not results_df.empty and objective_metric in results_df.columns:
            # 计算目标指标的总和，就像在 app.py 中一样
            metric_value = results_df[objective_metric].sum()
        else:
            # 如果DataFrame无效或列不存在，则返回一个非常小的值
            print(f"警告: 在模型输出的DataFrame中未找到目标指标 '{objective_metric}'。")
            metric_value = -float('inf')

        return float(metric_value)

    except Exception as e:
        print(f"使用参数运行模型时出错: {params_to_update}. 错误: {e}")
        import traceback
        traceback.print_exc()
        return -float('inf') # 发生错误时返回一个非常小的数字

# --- 网格搜索 ---
def grid_search_optimizer(base_params: dict, 
                          params_to_optimize_ranges: dict, 
                          objective_metric: str, 
                          points_per_dim: int,
                          progress_callback=None,
                          constraint_handler: Optional[LumaConstraintHandler] = None,
                          monitor: Optional[OptimizationMonitor] = None) -> tuple:
    """
    执行网格搜索以找到最大化目标指标的参数组合。

    Args:
        base_params (dict): 模型参数的基础字典。
        params_to_optimize_ranges (dict): 字典，键是参数名称，
                                          值是 (min_val, max_val) 元组。
        objective_metric (str): 要优化的目标指标名称。
        points_per_dim (int): 每个参数维度上要采样的点数。
        progress_callback (function, optional): 用于报告进度的回调函数。
                                                它应该接受一个浮点数 (0.0 到 1.0)。
        constraint_handler: 约束处理器
        monitor: 优化监控器

    Returns:
        tuple: (best_params, best_score, all_results_df)
               best_params (dict): 找到的最佳参数组合。
               best_score (float): 对应的最佳目标指标值。
               all_results_df (pd.DataFrame): 包含所有评估过的参数组合及其结果的DataFrame。
    """
    if not params_to_optimize_ranges:
        return {}, -float('inf'), pd.DataFrame()

    param_names = list(params_to_optimize_ranges.keys())
    
    # 为每个参数生成采样点
    param_value_grids = []
    for param_name in param_names:
        min_val, max_val = params_to_optimize_ranges[param_name]
        # 确保 max_val 大于 min_val，否则 np.linspace 行为可能不符合预期
        if max_val <= min_val:
            # 如果范围无效，则只使用 min_val 或设置一个小的默认范围
            # 这里我们只使用 min_val，或者您可以抛出错误/警告
            param_value_grids.append(np.array([min_val]))
            print(f"警告: 参数 '{param_name}' 的范围无效 [{min_val}, {max_val}]。仅使用最小值。")
        else:
            param_value_grids.append(np.linspace(min_val, max_val, points_per_dim))

    # 创建所有参数组合
    # itertools.product 会生成所有组合的迭代器
    param_combinations = list(itertools.product(*param_value_grids))
    total_combinations = len(param_combinations)
    
    print(f"网格搜索：总共 {total_combinations} 种参数组合需要评估。")

    best_score = -float('inf')
    best_params_combination = {}
    
    results_list = [] # 用于存储每次运行的结果

    # 初始化约束处理器和监控器
    if constraint_handler is None:
        constraint_handler = LumaConstraintHandler(params_to_optimize_ranges)
    
    if monitor is None:
        monitor = OptimizationMonitor(patience=max(5, total_combinations // 20))
    
    start_time = time.time()

    for i, current_combination_values in enumerate(param_combinations):
        params_to_update = dict(zip(param_names, current_combination_values))
        
        # 应用约束修复
        try:
            params_to_update = constraint_handler.validate_and_repair_optimization_params(params_to_update)
        except Exception as e:
            warnings.warn(f"约束修复失败: {str(e)}")
        
        current_score = run_model_with_params(base_params, params_to_update, objective_metric)
        
        # 更新监控器
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
        if monitor.should_stop_early():
            print(f"检测到早停条件，在第{i+1}次迭代停止")
            break
            
        if progress_callback:
            progress_callback((i + 1) / total_combinations)
        
        # 打印进度（可选，对于长时间运行的任务有帮助）
        if (i + 1) % max(1, total_combinations // 20) == 0 or (i + 1) == total_combinations : # 每5%或最后一次打印
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

    print(f"网格搜索完成。最佳参数: {best_params_combination}, 最佳 {objective_metric}: {best_score}")
    
    return best_params_combination, best_score, all_results_df

# --- 贝叶斯优化 ---
def bayesian_optimizer(base_params: dict,
                       params_to_optimize_ranges: dict,
                       objective_metric: str,
                       n_iterations: int,
                       n_initial_points: int,
                       exploitation_vs_exploration: float = 0.1, # skopt 中通常用 acq_func_kwargs={'xi': value}
                       progress_callback=None) -> tuple:
    """
    执行贝叶斯优化以找到最大化目标指标的参数组合。

    Args:
        base_params (dict): 模型参数的基础字典。
        params_to_optimize_ranges (dict): 字典，键是参数名称，
                                          值是 (min_val, max_val) 元组。
        objective_metric (str): 要优化的目标指标名称。
        n_iterations (int): 贝叶斯优化的总迭代次数 (包括初始点)。
        n_initial_points (int): 初始随机探索的点数。
        exploitation_vs_exploration (float): 控制探索与利用的平衡，对应 'xi' 参数。
                                            较小的值 (如 0.01) 倾向于利用，较大的值倾向于探索。
        progress_callback (function, optional): 用于报告进度的回调函数。

    Returns:
        tuple: (best_params, best_score, all_results_df)
               best_params (dict): 找到的最佳参数组合。
               best_score (float): 对应的最佳目标指标值。
               all_results_df (pd.DataFrame): 包含所有评估过的参数组合及其结果的DataFrame。
    """
    if gp_minimize is None: # 检查 skopt 是否成功导入
        raise ImportError("scikit-optimize 库未找到或导入失败。请确保已正确安装。")

    if not params_to_optimize_ranges:
        return {}, -float('inf'), pd.DataFrame()

    param_names = list(params_to_optimize_ranges.keys())
    
    # 定义搜索空间 (skopt.space)
    search_space = []
    for param_name in param_names:
        min_val, max_val = params_to_optimize_ranges[param_name]
        # 根据参数名称或类型判断是 Real 还是 Integer
        # 这里简单处理：如果步长是1或者值看起来像整数，则认为是Integer
        # 更好的方法是让用户在UI中指定参数类型
        if isinstance(min_val, int) and isinstance(max_val, int) and \
           (param_name == "new_clients_per_half_year" or (max_val - min_val < 20 and points_per_dim > (max_val - min_val +1))): # 启发式判断
            search_space.append(Integer(min_val, max_val, name=param_name))
        else:
            search_space.append(Real(min_val, max_val, name=param_name))

    results_list = [] # 用于存储所有评估结果
    iteration_count = 0 # 手动计数器

    # 定义目标函数 (skopt 需要一个最小化的函数，所以我们对目标指标取反)
    @use_named_args(search_space)
    def objective_function(**params_as_kwargs):
        nonlocal iteration_count # 允许修改外部作用域的 iteration_count
        iteration_count += 1

        # params_as_kwargs 是一个字典，键是参数名，值是skopt建议的值
        current_score = run_model_with_params(base_params, params_as_kwargs, objective_metric)
        
        # 存储结果
        result_entry = {**params_as_kwargs, objective_metric: current_score}
        results_list.append(result_entry)
        
        if progress_callback:
            # n_iterations 是总调用次数，包括 n_initial_points
            progress_callback(iteration_count / n_iterations, f"贝叶斯优化: {iteration_count}/{n_iterations}")
            
        # gp_minimize 默认是最小化，所以返回负的目标值
        return -current_score 

    print(f"开始贝叶斯优化：总迭代 {n_iterations} 次, 初始点 {n_initial_points} 次。")
    
    # 执行优化
    # xi 参数用于平衡探索和利用 (对应采集函数 EI 的 xi)
    # xi 默认是 0.01 (倾向于利用)，值越大越倾向于探索
    # 注意：旧版本的 scikit-optimize 可能不支持 acq_func_kwargs，因此直接传递 xi 参数
    result = gp_minimize(
        func=objective_function,
        dimensions=search_space,
        n_calls=n_iterations,
        n_initial_points=n_initial_points,
        acq_func="EI",  # Expected Improvement,常用的采集函数
        xi=exploitation_vs_exploration, # 直接传递 xi 参数以兼容旧版本
        random_state=0 # 为了结果可复现
    )

    best_params_combination = dict(zip(param_names, result.x))
    best_score_negative = result.fun # 这是最小化的负值
    best_score_positive = -best_score_negative # 转回原始的最大化值

    all_results_df = pd.DataFrame(results_list)
    # 按目标指标降序排序
    if not all_results_df.empty and objective_metric in all_results_df.columns:
         all_results_df = all_results_df.sort_values(by=objective_metric, ascending=False).reset_index(drop=True)
    
    print(f"贝叶斯优化完成。最佳参数: {best_params_combination}, 最佳 {objective_metric}: {best_score_positive}")

    return best_params_combination, best_score_positive, all_results_df

# --- 遗传算法 ---
def genetic_algorithm_optimizer(base_params: dict,
                              params_to_optimize_ranges: dict,
                              objective_metric: str,
                              population_size: int,
                              n_generations: int,
                              mutation_rate: float,
                              crossover_prob: float = 0.7, # 交叉概率
                              progress_callback=None) -> tuple:
    """
    使用遗传算法 (DEAP) 执行优化。

    Args:
        base_params (dict): 模型参数的基础字典。
        params_to_optimize_ranges (dict): 优化的参数及其范围。
        objective_metric (str): 优化的目标指标。
        population_size (int): 种群大小。
        n_generations (int): 迭代代数。
        mutation_rate (float): 变异率。
        crossover_prob (float): 交叉概率。
        progress_callback (function, optional): 进度回调函数。

    Returns:
        tuple: (best_params, best_score, all_results_df)
    """
    try:
        import random
        from deap import base, creator, tools
    except ImportError:
        raise ImportError("DEAP 库未找到或导入失败。请确保已正确安装 (pip install deap)。")

    if not params_to_optimize_ranges:
        return {}, -float('inf'), pd.DataFrame()

    param_names = list(params_to_optimize_ranges.keys())
    bounds = [params_to_optimize_ranges[name] for name in param_names]

    # --- DEAP 设置 ---
    # 1. 定义问题：最大化单目标适应度
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    # 2. 定义个体：一个个体是一个列表，带有我们刚定义的适应度
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    # 3. 定义如何生成个体的基因（属性）
    # 对于每个参数，我们创建一个在指定范围内均匀分布的随机浮点数生成器
    for i, param_name in enumerate(param_names):
        min_val, max_val = bounds[i]
        toolbox.register(f"attr_{i}", random.uniform, min_val, max_val)

    # 4. 定义如何创建个体和种群
    # 个体由每个基因生成器创建一个基因组成
    attrs = tuple(toolbox.__getattribute__(f'attr_{i}') for i in range(len(param_names)))
    toolbox.register("individual", tools.initCycle, creator.Individual, attrs)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # 5. 定义遗传算子
    def evaluate(individual):
        params_to_update = dict(zip(param_names, individual))
        score = run_model_with_params(base_params, params_to_update, objective_metric)
        return (score,) # DEAP期望返回一个元组

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxBlend, alpha=0.5) # 模拟二进制交叉
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.2, indpb=0.2) # 高斯变异
    toolbox.register("select", tools.selTournament, tournsize=3) # 锦标赛选择

    # --- 运行算法 ---
    pop = toolbox.population(n=population_size)
    hof = tools.HallOfFame(1) # 名人堂，只存储最佳个体
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    results_list = []

    # 初始种群评估
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
        results_list.append({**dict(zip(param_names, ind)), objective_metric: fit[0]})

    if progress_callback:
        progress_callback(0, f"遗传算法: 第 0 代")

    for gen in range(1, n_generations + 1):
        # 选择下一代个体
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))

        # 应用交叉
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < crossover_prob:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        # 应用变异
        for mutant in offspring:
            if random.random() < mutation_rate:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        
        # 评估无效的个体 (那些被交叉或变异的)
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            results_list.append({**dict(zip(param_names, ind)), objective_metric: fit[0]})

        # 种群更新
        pop[:] = offspring
        hof.update(pop)
        
        if progress_callback:
            progress_callback(gen / n_generations, f"遗传算法: 第 {gen}/{n_generations} 代 | 最佳: {hof[0].fitness.values[0]:.4f}")

    # --- 结果处理 ---
    best_ind = hof[0]
    best_params_combination = dict(zip(param_names, best_ind))
    best_score = best_ind.fitness.values[0]
    
    all_results_df = pd.DataFrame(results_list)
    if not all_results_df.empty and objective_metric in all_results_df.columns:
        all_results_df = all_results_df.sort_values(by=objective_metric, ascending=False).reset_index(drop=True)

    print(f"遗传算法完成。最佳参数: {best_params_combination}, 最佳 {objective_metric}: {best_score}")

    return best_params_combination, best_score, all_results_df