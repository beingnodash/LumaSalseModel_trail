# 多算法集成优化系统
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Callable
import concurrent.futures
import time
import copy
from dataclasses import dataclass

# 导入我们的优化模块
from .optimization import grid_search_optimizer, bayesian_optimizer, genetic_algorithm_optimizer
from .algorithm_selector import AlgorithmSelector
from .constraint_handler import LumaConstraintHandler
from .optimization_monitor import OptimizationMonitor, OptimizationCallback

@dataclass
class OptimizationResult:
    """优化结果数据类"""
    algorithm: str
    best_params: Dict[str, Any]
    best_score: float
    execution_time: float
    iterations_used: int
    convergence_info: Dict[str, Any]
    all_evaluations: Optional[pd.DataFrame] = None

class EnsembleOptimizer:
    """
    多算法集成优化器
    
    该系统结合多种优化算法的优势，通过智能的预算分配和结果融合策略，
    提供更稳健和高效的优化解决方案。
    
    主要特性：
    1. 自动算法选择和预算分配
    2. 并行算法执行
    3. 智能结果融合
    4. 性能对比分析
    5. 自适应策略调整
    """
    
    def __init__(self, base_params: Dict[str, Any], objective_metric: str):
        """
        初始化集成优化器
        
        Args:
            base_params: 基础模型参数
            objective_metric: 优化目标指标
        """
        self.base_params = base_params
        self.objective_metric = objective_metric
        
        # 初始化组件
        self.algorithm_selector = AlgorithmSelector()
        self.constraint_handler = LumaConstraintHandler()
        
        # 优化结果存储
        self.individual_results: Dict[str, OptimizationResult] = {}
        self.ensemble_result: Optional[OptimizationResult] = None
        
        # 配置信息
        self.available_algorithms = {
            'grid_search': self._run_grid_search,
            'bayesian_optimization': self._run_bayesian_optimization,
            'genetic_algorithm': self._run_genetic_algorithm
        }
    
    def optimize(self, 
                param_ranges: Dict[str, Tuple[float, float]],
                total_budget: int = 200,
                ensemble_strategy: str = 'auto',
                parallel_execution: bool = True,
                progress_callback: Optional[Callable] = None) -> OptimizationResult:
        """
        执行集成优化
        
        Args:
            param_ranges: 参数搜索范围
            total_budget: 总评估预算
            ensemble_strategy: 集成策略 ('auto', 'equal', 'weighted', 'sequential')
            parallel_execution: 是否并行执行
            progress_callback: 进度回调函数
            
        Returns:
            集成优化结果
        """
        if progress_callback:
            progress_callback(0.0, "开始集成优化...")
        
        # 1. 分析问题特性并选择算法
        algorithm_recommendations = self.algorithm_selector.recommend_algorithm(
            param_ranges, total_budget
        )
        
        # 2. 根据策略分配预算
        budget_allocation = self._allocate_budget(
            algorithm_recommendations, total_budget, ensemble_strategy
        )
        
        if progress_callback:
            progress_callback(0.1, f"预算分配完成，将使用{len(budget_allocation)}种算法")
        
        # 3. 执行优化算法
        if parallel_execution and len(budget_allocation) > 1:
            self._run_algorithms_parallel(
                param_ranges, budget_allocation, progress_callback
            )
        else:
            self._run_algorithms_sequential(
                param_ranges, budget_allocation, progress_callback
            )
        
        if progress_callback:
            progress_callback(0.9, "融合优化结果...")
        
        # 4. 融合结果
        self.ensemble_result = self._merge_results()
        
        if progress_callback:
            progress_callback(1.0, "集成优化完成")
        
        return self.ensemble_result
    
    def _allocate_budget(self, 
                        algorithm_recommendations: List[Dict],
                        total_budget: int,
                        strategy: str) -> Dict[str, int]:
        """
        分配算法预算
        
        Args:
            algorithm_recommendations: 算法推荐结果
            total_budget: 总预算
            strategy: 分配策略
            
        Returns:
            算法预算分配字典
        """
        if strategy == 'auto':
            return self._auto_allocate_budget(algorithm_recommendations, total_budget)
        elif strategy == 'equal':
            return self._equal_allocate_budget(algorithm_recommendations, total_budget)
        elif strategy == 'weighted':
            return self._weighted_allocate_budget(algorithm_recommendations, total_budget)
        elif strategy == 'sequential':
            return self._sequential_allocate_budget(algorithm_recommendations, total_budget)
        else:
            raise ValueError(f"未知的预算分配策略: {strategy}")
    
    def _auto_allocate_budget(self, recommendations: List[Dict], total_budget: int) -> Dict[str, int]:
        """自动预算分配策略"""
        allocation = {}
        
        # 获取前3个推荐算法
        top_algorithms = recommendations[:3]
        
        if len(top_algorithms) == 1:
            # 只有一个算法适合，分配全部预算
            allocation[top_algorithms[0]['algorithm']] = total_budget
        elif len(top_algorithms) == 2:
            # 两个算法，按得分比例分配
            scores = [algo['score'] for algo in top_algorithms]
            total_score = sum(scores)
            for i, algo in enumerate(top_algorithms):
                weight = scores[i] / total_score
                allocation[algo['algorithm']] = max(20, int(total_budget * weight))
        else:
            # 三个算法，主要预算给最佳算法，其余平分
            best_algo = top_algorithms[0]
            allocation[best_algo['algorithm']] = int(total_budget * 0.6)
            
            remaining_budget = total_budget - allocation[best_algo['algorithm']]
            for algo in top_algorithms[1:3]:
                allocation[algo['algorithm']] = remaining_budget // 2
        
        return allocation
    
    def _equal_allocate_budget(self, recommendations: List[Dict], total_budget: int) -> Dict[str, int]:
        """等量预算分配策略"""
        suitable_algorithms = [algo for algo in recommendations if algo['score'] > 0.4]
        num_algorithms = min(3, len(suitable_algorithms))
        
        if num_algorithms == 0:
            # 如果没有合适的算法，选择得分最高的
            num_algorithms = 1
            suitable_algorithms = recommendations[:1]
        
        budget_per_algo = total_budget // num_algorithms
        
        allocation = {}
        for algo in suitable_algorithms[:num_algorithms]:
            allocation[algo['algorithm']] = budget_per_algo
        
        return allocation
    
    def _weighted_allocate_budget(self, recommendations: List[Dict], total_budget: int) -> Dict[str, int]:
        """加权预算分配策略"""
        suitable_algorithms = [algo for algo in recommendations if algo['score'] > 0.3]
        
        if not suitable_algorithms:
            suitable_algorithms = recommendations[:1]
        
        # 按得分加权分配
        scores = [algo['score'] for algo in suitable_algorithms]
        total_score = sum(scores)
        
        allocation = {}
        for i, algo in enumerate(suitable_algorithms):
            weight = scores[i] / total_score
            budget = max(15, int(total_budget * weight))
            allocation[algo['algorithm']] = budget
        
        return allocation
    
    def _sequential_allocate_budget(self, recommendations: List[Dict], total_budget: int) -> Dict[str, int]:
        """顺序预算分配策略（适合预算较少的情况）"""
        # 只选择最佳算法
        best_algorithm = recommendations[0]['algorithm']
        return {best_algorithm: total_budget}
    
    def _run_algorithms_parallel(self, 
                               param_ranges: Dict[str, Tuple[float, float]],
                               budget_allocation: Dict[str, int],
                               progress_callback: Optional[Callable]):
        """并行执行算法"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(budget_allocation)) as executor:
            # 提交所有算法任务
            future_to_algorithm = {}
            for algorithm, budget in budget_allocation.items():
                if algorithm in self.available_algorithms:
                    future = executor.submit(
                        self._run_single_algorithm,
                        algorithm, param_ranges, budget, progress_callback
                    )
                    future_to_algorithm[future] = algorithm
            
            # 收集结果
            completed = 0
            total_algorithms = len(budget_allocation)
            
            for future in concurrent.futures.as_completed(future_to_algorithm):
                algorithm = future_to_algorithm[future]
                try:
                    result = future.result()
                    self.individual_results[algorithm] = result
                    completed += 1
                    
                    if progress_callback:
                        progress = 0.1 + 0.8 * (completed / total_algorithms)
                        progress_callback(progress, f"算法 {algorithm} 完成")
                        
                except Exception as e:
                    print(f"算法 {algorithm} 执行失败: {str(e)}")
    
    def _run_algorithms_sequential(self,
                                 param_ranges: Dict[str, Tuple[float, float]],
                                 budget_allocation: Dict[str, int],
                                 progress_callback: Optional[Callable]):
        """顺序执行算法"""
        completed = 0
        total_algorithms = len(budget_allocation)
        
        for algorithm, budget in budget_allocation.items():
            if algorithm in self.available_algorithms:
                try:
                    if progress_callback:
                        progress = 0.1 + 0.8 * (completed / total_algorithms)
                        progress_callback(progress, f"正在运行 {algorithm}")
                    
                    result = self._run_single_algorithm(
                        algorithm, param_ranges, budget, progress_callback
                    )
                    self.individual_results[algorithm] = result
                    completed += 1
                    
                except Exception as e:
                    print(f"算法 {algorithm} 执行失败: {str(e)}")
    
    def _run_single_algorithm(self,
                            algorithm: str,
                            param_ranges: Dict[str, Tuple[float, float]],
                            budget: int,
                            progress_callback: Optional[Callable]) -> OptimizationResult:
        """运行单个算法"""
        start_time = time.time()
        
        # 创建监控器
        monitor = OptimizationMonitor(patience=max(5, budget // 10))
        monitor.start_monitoring()
        
        # 执行算法
        algorithm_func = self.available_algorithms[algorithm]
        best_params, best_score, all_results = algorithm_func(
            param_ranges, budget, monitor
        )
        
        execution_time = time.time() - start_time
        
        # 应用约束修复
        if best_params:
            best_params = self.constraint_handler.validate_and_repair_optimization_params(
                best_params
            )
        
        return OptimizationResult(
            algorithm=algorithm,
            best_params=best_params,
            best_score=best_score,
            execution_time=execution_time,
            iterations_used=len(all_results) if all_results is not None else budget,
            convergence_info=monitor.get_convergence_status(),
            all_evaluations=all_results
        )
    
    def _run_grid_search(self, param_ranges: Dict[str, Tuple[float, float]], 
                        budget: int, monitor: OptimizationMonitor) -> Tuple:
        """运行网格搜索"""
        num_params = len(param_ranges)
        points_per_dim = max(2, int(budget ** (1/num_params)))
        points_per_dim = min(points_per_dim, 10)  # 限制最大值
        
        def progress_callback(progress):
            monitor.record_iteration(
                int(progress * budget), 0, monitor.best_score_so_far,
                exploration_rate=1.0 - progress
            )
        
        return grid_search_optimizer(
            self.base_params, param_ranges, self.objective_metric,
            points_per_dim, progress_callback
        )
    
    def _run_bayesian_optimization(self, param_ranges: Dict[str, Tuple[float, float]], 
                                 budget: int, monitor: OptimizationMonitor) -> Tuple:
        """运行贝叶斯优化"""
        n_iterations = min(budget, 100)
        n_initial_points = min(n_iterations // 3, 20)
        
        def progress_callback(progress, text=""):
            iteration = int(progress * n_iterations)
            exploration_rate = max(0.1, 1.0 - progress)
            monitor.record_iteration(
                iteration, 0, monitor.best_score_so_far,
                exploration_rate=exploration_rate
            )
        
        return bayesian_optimizer(
            self.base_params, param_ranges, self.objective_metric,
            n_iterations, n_initial_points, 0.1, progress_callback
        )
    
    def _run_genetic_algorithm(self, param_ranges: Dict[str, Tuple[float, float]], 
                             budget: int, monitor: OptimizationMonitor) -> Tuple:
        """运行遗传算法"""
        population_size = min(50, max(20, budget // 10))
        n_generations = budget // population_size
        
        def progress_callback(progress, text=""):
            generation = int(progress * n_generations)
            # 遗传算法的多样性随代数递减
            diversity = max(0.1, 1.0 - progress * 0.8)
            monitor.record_iteration(
                generation, 0, monitor.best_score_so_far,
                diversity=diversity
            )
        
        return genetic_algorithm_optimizer(
            self.base_params, param_ranges, self.objective_metric,
            population_size, n_generations, 0.1, 0.7, progress_callback
        )
    
    def _merge_results(self) -> OptimizationResult:
        """融合多个算法的结果"""
        if not self.individual_results:
            raise ValueError("没有算法结果可供融合")
        
        # 1. 找到最佳结果
        best_result = max(
            self.individual_results.values(),
            key=lambda r: r.best_score
        )
        
        # 2. 计算加权平均参数（可选）
        ensemble_params = self._calculate_ensemble_params()
        
        # 3. 如果加权平均参数更好，使用它；否则使用最佳单一结果
        from .optimization import run_model_with_params
        
        try:
            ensemble_score = run_model_with_params(
                self.base_params, ensemble_params, self.objective_metric
            )
            
            if ensemble_score > best_result.best_score:
                final_params = ensemble_params
                final_score = ensemble_score
                source = "集成加权平均"
            else:
                final_params = best_result.best_params
                final_score = best_result.best_score
                source = f"最佳单一算法({best_result.algorithm})"
        except:
            # 如果加权平均失败，使用最佳单一结果
            final_params = best_result.best_params
            final_score = best_result.best_score
            source = f"最佳单一算法({best_result.algorithm})"
        
        # 4. 计算总执行时间和迭代数
        total_time = sum(r.execution_time for r in self.individual_results.values())
        total_iterations = sum(r.iterations_used for r in self.individual_results.values())
        
        return OptimizationResult(
            algorithm=f"集成优化({source})",
            best_params=final_params,
            best_score=final_score,
            execution_time=total_time,
            iterations_used=total_iterations,
            convergence_info=self._get_ensemble_convergence_info()
        )
    
    def _calculate_ensemble_params(self) -> Dict[str, Any]:
        """计算集成参数（加权平均）"""
        if not self.individual_results:
            return {}
        
        # 权重基于算法性能
        weights = {}
        total_weight = 0
        
        for algo, result in self.individual_results.items():
            # 权重基于得分和收敛状态
            weight = result.best_score
            if result.convergence_info.get('converged', False):
                weight *= 1.2  # 已收敛的结果权重更高
            
            weights[algo] = weight
            total_weight += weight
        
        # 归一化权重
        for algo in weights:
            weights[algo] /= total_weight
        
        # 计算加权平均参数
        ensemble_params = {}
        
        # 获取所有参数的键
        all_param_keys = set()
        for result in self.individual_results.values():
            all_param_keys.update(result.best_params.keys())
        
        # 对每个参数计算加权平均
        for param_key in all_param_keys:
            weighted_sum = 0
            weight_sum = 0
            
            for algo, result in self.individual_results.items():
                if param_key in result.best_params:
                    value = result.best_params[param_key]
                    if isinstance(value, (int, float)):
                        weighted_sum += value * weights[algo]
                        weight_sum += weights[algo]
            
            if weight_sum > 0:
                ensemble_params[param_key] = weighted_sum / weight_sum
        
        return ensemble_params
    
    def _get_ensemble_convergence_info(self) -> Dict[str, Any]:
        """获取集成收敛信息"""
        converged_count = sum(
            1 for r in self.individual_results.values()
            if r.convergence_info.get('converged', False)
        )
        
        avg_score = np.mean([r.best_score for r in self.individual_results.values()])
        std_score = np.std([r.best_score for r in self.individual_results.values()])
        
        return {
            'algorithms_used': list(self.individual_results.keys()),
            'converged_algorithms': converged_count,
            'total_algorithms': len(self.individual_results),
            'score_consistency': 1.0 - (std_score / (avg_score + 1e-6)),
            'ensemble_confidence': converged_count / len(self.individual_results)
        }
    
    def generate_comparison_report(self) -> str:
        """生成算法比较报告"""
        if not self.individual_results:
            return "没有算法结果可供比较"
        
        report = "# 多算法优化比较报告\n\n"
        
        # 创建比较表格
        comparison_data = []
        for algo, result in self.individual_results.items():
            comparison_data.append({
                '算法': algo,
                '最佳得分': f"{result.best_score:.6f}",
                '执行时间(秒)': f"{result.execution_time:.2f}",
                '使用迭代数': result.iterations_used,
                '是否收敛': '是' if result.convergence_info.get('converged', False) else '否'
            })
        
        # 按得分排序
        comparison_data.sort(key=lambda x: float(x['最佳得分']), reverse=True)
        
        report += "## 算法性能比较\n\n"
        report += "| 算法 | 最佳得分 | 执行时间(秒) | 使用迭代数 | 是否收敛 |\n"
        report += "|------|----------|--------------|------------|----------|\n"
        
        for data in comparison_data:
            report += f"| {data['算法']} | {data['最佳得分']} | {data['执行时间(秒)']} | {data['使用迭代数']} | {data['是否收敛']} |\n"
        
        if self.ensemble_result:
            report += f"\n## 集成优化结果\n\n"
            report += f"- **最终算法**: {self.ensemble_result.algorithm}\n"
            report += f"- **最佳得分**: {self.ensemble_result.best_score:.6f}\n"
            report += f"- **总执行时间**: {self.ensemble_result.execution_time:.2f} 秒\n"
            report += f"- **总迭代数**: {self.ensemble_result.iterations_used}\n"
            
            convergence_info = self.ensemble_result.convergence_info
            report += f"- **收敛置信度**: {convergence_info.get('ensemble_confidence', 0):.2%}\n"
            report += f"- **结果一致性**: {convergence_info.get('score_consistency', 0):.2%}\n"
        
        return report