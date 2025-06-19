# 鲁棒性分析系统
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Callable
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
from scipy import stats
from dataclasses import dataclass
import copy

from .optimization import run_model_with_params

@dataclass
class RobustnessResult:
    """鲁棒性分析结果数据类"""
    base_performance: float
    mean_performance: float
    std_performance: float
    worst_case: float
    best_case: float
    confidence_interval_95: Tuple[float, float]
    risk_level: str
    sensitivity_metrics: Dict[str, float]
    scenario_analysis: pd.DataFrame

class RobustnessAnalyzer:
    """
    鲁棒性分析器
    
    评估优化解在参数不确定性和外部扰动下的表现稳定性。
    通过Monte Carlo模拟、敏感性分析和情景分析等方法，
    量化解的可靠性和风险水平。
    
    主要功能：
    1. Monte Carlo鲁棒性测试
    2. 参数敏感性风险评估
    3. 极端情景分析
    4. 不确定性传播分析
    5. 风险等级评估
    """
    
    def __init__(self, base_params: Dict[str, Any], objective_metric: str):
        """
        初始化鲁棒性分析器
        
        Args:
            base_params: 基础模型参数
            objective_metric: 目标评估指标
        """
        self.base_params = base_params
        self.objective_metric = objective_metric
        
        # 分析设置
        self.monte_carlo_samples = 1000
        self.confidence_level = 0.95
        
        # 风险等级阈值
        self.risk_thresholds = {
            'low': 0.05,      # 标准差/均值 < 5%
            'medium': 0.15,   # 5% <= 标准差/均值 < 15%
            'high': 0.30,     # 15% <= 标准差/均值 < 30%
            'extreme': 1.0    # 标准差/均值 >= 30%
        }
    
    def analyze_robustness(self, 
                          best_params: Dict[str, Any],
                          uncertainty_ranges: Optional[Dict[str, float]] = None,
                          scenario_params: Optional[List[Dict[str, Any]]] = None,
                          progress_callback: Optional[Callable] = None) -> RobustnessResult:
        """
        综合鲁棒性分析
        
        Args:
            best_params: 最优参数组合
            uncertainty_ranges: 参数不确定性范围 (参数名 -> 相对变化范围)
            scenario_params: 特定情景参数列表
            progress_callback: 进度回调函数
            
        Returns:
            鲁棒性分析结果
        """
        if progress_callback:
            progress_callback(0.0, "开始鲁棒性分析...")
        
        # 1. 计算基准性能
        base_performance = self._evaluate_base_performance(best_params)
        
        if progress_callback:
            progress_callback(0.1, "基准性能计算完成")
        
        # 2. 设置默认不确定性范围
        if uncertainty_ranges is None:
            uncertainty_ranges = self._generate_default_uncertainty_ranges(best_params)
        
        # 3. Monte Carlo模拟
        if progress_callback:
            progress_callback(0.2, "进行Monte Carlo模拟...")
        
        mc_results = self._monte_carlo_simulation(
            best_params, uncertainty_ranges, progress_callback
        )
        
        # 4. 敏感性分析
        if progress_callback:
            progress_callback(0.6, "进行敏感性分析...")
        
        sensitivity_metrics = self._sensitivity_analysis(
            best_params, uncertainty_ranges
        )
        
        # 5. 情景分析
        if progress_callback:
            progress_callback(0.8, "进行情景分析...")
        
        scenario_analysis = self._scenario_analysis(
            best_params, scenario_params
        )
        
        # 6. 计算统计指标
        mean_perf = np.mean(mc_results)
        std_perf = np.std(mc_results)
        worst_case = np.min(mc_results)
        best_case = np.max(mc_results)
        
        # 7. 计算置信区间
        alpha = 1 - self.confidence_level
        ci_lower = np.percentile(mc_results, (alpha/2) * 100)
        ci_upper = np.percentile(mc_results, (1 - alpha/2) * 100)
        
        # 8. 评估风险等级
        risk_level = self._assess_risk_level(mean_perf, std_perf, base_performance)
        
        if progress_callback:
            progress_callback(1.0, "鲁棒性分析完成")
        
        return RobustnessResult(
            base_performance=base_performance,
            mean_performance=mean_perf,
            std_performance=std_perf,
            worst_case=worst_case,
            best_case=best_case,
            confidence_interval_95=(ci_lower, ci_upper),
            risk_level=risk_level,
            sensitivity_metrics=sensitivity_metrics,
            scenario_analysis=scenario_analysis
        )
    
    def _evaluate_base_performance(self, best_params: Dict[str, Any]) -> float:
        """评估基准性能"""
        try:
            return run_model_with_params(
                self.base_params, best_params, self.objective_metric
            )
        except Exception as e:
            warnings.warn(f"基准性能评估失败: {str(e)}")
            return 0.0
    
    def _generate_default_uncertainty_ranges(self, best_params: Dict[str, Any]) -> Dict[str, float]:
        """生成默认不确定性范围"""
        uncertainty_ranges = {}
        
        for param_name in best_params.keys():
            if "price" in param_name.lower() or "fee" in param_name.lower():
                # 价格参数：±20%不确定性
                uncertainty_ranges[param_name] = 0.20
            elif "rate" in param_name.lower() or "share" in param_name.lower():
                # 比例参数：±10%不确定性
                uncertainty_ranges[param_name] = 0.10
            elif "per_half_year" in param_name.lower() or "clients" in param_name.lower():
                # 数量参数：±25%不确定性
                uncertainty_ranges[param_name] = 0.25
            else:
                # 其他参数：±15%不确定性
                uncertainty_ranges[param_name] = 0.15
        
        return uncertainty_ranges
    
    def _monte_carlo_simulation(self, 
                               best_params: Dict[str, Any],
                               uncertainty_ranges: Dict[str, float],
                               progress_callback: Optional[Callable] = None) -> np.ndarray:
        """Monte Carlo模拟"""
        results = []
        
        for i in range(self.monte_carlo_samples):
            # 生成扰动参数
            perturbed_params = self._generate_perturbed_params(
                best_params, uncertainty_ranges
            )
            
            # 评估性能
            try:
                performance = run_model_with_params(
                    self.base_params, perturbed_params, self.objective_metric
                )
                results.append(performance)
            except Exception as e:
                # 如果评估失败，使用一个很低的值
                results.append(-1e6)
            
            # 更新进度
            if progress_callback and i % (self.monte_carlo_samples // 10) == 0:
                progress = 0.2 + 0.4 * (i / self.monte_carlo_samples)
                progress_callback(progress, f"Monte Carlo: {i+1}/{self.monte_carlo_samples}")
        
        return np.array(results)
    
    def _generate_perturbed_params(self, 
                                  best_params: Dict[str, Any],
                                  uncertainty_ranges: Dict[str, float]) -> Dict[str, Any]:
        """生成扰动参数"""
        perturbed_params = copy.deepcopy(best_params)
        
        for param_name, uncertainty in uncertainty_ranges.items():
            if param_name in perturbed_params:
                original_value = perturbed_params[param_name]
                
                if isinstance(original_value, (int, float)):
                    # 正态分布扰动
                    std_dev = abs(original_value) * uncertainty
                    noise = np.random.normal(0, std_dev)
                    new_value = original_value + noise
                    
                    # 确保参数在合理范围内
                    if "rate" in param_name.lower() or "share" in param_name.lower():
                        new_value = max(0.01, min(0.99, new_value))
                    elif "price" in param_name.lower() or "fee" in param_name.lower():
                        new_value = max(0.1, new_value)
                    elif "per_half_year" in param_name.lower():
                        new_value = max(1, int(new_value))
                    
                    perturbed_params[param_name] = new_value
        
        return perturbed_params
    
    def _sensitivity_analysis(self, 
                             best_params: Dict[str, Any],
                             uncertainty_ranges: Dict[str, float]) -> Dict[str, float]:
        """敏感性分析"""
        sensitivity_metrics = {}
        
        base_performance = self._evaluate_base_performance(best_params)
        
        for param_name, uncertainty in uncertainty_ranges.items():
            if param_name in best_params:
                original_value = best_params[param_name]
                
                if isinstance(original_value, (int, float)):
                    # 计算参数变化对结果的影响
                    perturbation = abs(original_value) * uncertainty
                    
                    # 正向扰动
                    test_params_pos = copy.deepcopy(best_params)
                    test_params_pos[param_name] = original_value + perturbation
                    
                    # 负向扰动
                    test_params_neg = copy.deepcopy(best_params)
                    test_params_neg[param_name] = original_value - perturbation
                    
                    try:
                        perf_pos = run_model_with_params(
                            self.base_params, test_params_pos, self.objective_metric
                        )
                        perf_neg = run_model_with_params(
                            self.base_params, test_params_neg, self.objective_metric
                        )
                        
                        # 计算敏感性指标（弹性）
                        avg_perf_change = abs((perf_pos - base_performance) + (perf_neg - base_performance)) / 2
                        param_change_rate = uncertainty
                        
                        if param_change_rate > 0:
                            sensitivity = (avg_perf_change / base_performance) / param_change_rate
                        else:
                            sensitivity = 0.0
                        
                        sensitivity_metrics[param_name] = abs(sensitivity)
                        
                    except Exception as e:
                        sensitivity_metrics[param_name] = 0.0
        
        return sensitivity_metrics
    
    def _scenario_analysis(self, 
                          best_params: Dict[str, Any],
                          scenario_params: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """情景分析"""
        if scenario_params is None:
            scenario_params = self._generate_default_scenarios(best_params)
        
        scenario_results = []
        
        for i, scenario in enumerate(scenario_params):
            # 合并基础参数和情景参数
            test_params = copy.deepcopy(best_params)
            test_params.update(scenario)
            
            try:
                performance = run_model_with_params(
                    self.base_params, test_params, self.objective_metric
                )
                
                scenario_results.append({
                    'scenario_id': i,
                    'scenario_name': scenario.get('name', f'场景{i+1}'),
                    'performance': performance,
                    **scenario
                })
            except Exception as e:
                scenario_results.append({
                    'scenario_id': i,
                    'scenario_name': scenario.get('name', f'场景{i+1}'),
                    'performance': -1e6,
                    **scenario
                })
        
        return pd.DataFrame(scenario_results)
    
    def _generate_default_scenarios(self, best_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成默认情景"""
        scenarios = []
        
        # 乐观情景
        optimistic = {'name': '乐观情景'}
        for param_name in best_params.keys():
            if "rate" in param_name.lower() and "renewal" in param_name.lower():
                optimistic[param_name] = min(0.95, best_params[param_name] * 1.2)
            elif "per_half_year" in param_name.lower() and "clients" in param_name.lower():
                optimistic[param_name] = int(best_params[param_name] * 1.5)
        scenarios.append(optimistic)
        
        # 悲观情景
        pessimistic = {'name': '悲观情景'}
        for param_name in best_params.keys():
            if "rate" in param_name.lower() and "renewal" in param_name.lower():
                pessimistic[param_name] = max(0.1, best_params[param_name] * 0.7)
            elif "per_half_year" in param_name.lower() and "clients" in param_name.lower():
                pessimistic[param_name] = max(1, int(best_params[param_name] * 0.6))
        scenarios.append(pessimistic)
        
        # 市场波动情景
        market_volatility = {'name': '市场波动情景'}
        for param_name in best_params.keys():
            if "price" in param_name.lower():
                market_volatility[param_name] = best_params[param_name] * 0.8
        scenarios.append(market_volatility)
        
        return scenarios
    
    def _assess_risk_level(self, mean_perf: float, std_perf: float, base_perf: float) -> str:
        """评估风险等级"""
        if mean_perf <= 0:
            return 'extreme'
        
        # 计算变异系数
        cv = std_perf / mean_perf
        
        # 计算性能下降风险
        performance_drop = max(0, (base_perf - mean_perf) / base_perf)
        
        # 综合评估
        risk_score = cv + performance_drop
        
        if risk_score < self.risk_thresholds['low']:
            return 'low'
        elif risk_score < self.risk_thresholds['medium']:
            return 'medium'
        elif risk_score < self.risk_thresholds['high']:
            return 'high'
        else:
            return 'extreme'
    
    def create_robustness_plots(self, 
                               mc_results: np.ndarray,
                               base_performance: float,
                               sensitivity_metrics: Dict[str, float]) -> Dict[str, go.Figure]:
        """创建鲁棒性分析图表"""
        plots = {}
        
        # 1. 性能分布直方图
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=mc_results,
            nbinsx=50,
            name='性能分布',
            opacity=0.7
        ))
        
        # 添加基准性能线
        fig_dist.add_vline(
            x=base_performance,
            line_dash="dash",
            line_color="red",
            annotation_text="基准性能"
        )
        
        fig_dist.update_layout(
            title='Monte Carlo模拟性能分布',
            xaxis_title='目标函数值',
            yaxis_title='频次'
        )
        plots['distribution'] = fig_dist
        
        # 2. 敏感性雷达图
        if sensitivity_metrics:
            param_names = list(sensitivity_metrics.keys())
            sensitivity_values = list(sensitivity_metrics.values())
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=sensitivity_values,
                theta=param_names,
                fill='toself',
                name='参数敏感性'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(sensitivity_values) if sensitivity_values else 1]
                    )),
                title='参数敏感性分析'
            )
            plots['sensitivity'] = fig_radar
        
        # 3. 性能时间序列（Monte Carlo收敛）
        cumulative_mean = np.cumsum(mc_results) / np.arange(1, len(mc_results) + 1)
        
        fig_convergence = go.Figure()
        fig_convergence.add_trace(go.Scatter(
            x=list(range(len(cumulative_mean))),
            y=cumulative_mean,
            mode='lines',
            name='累积均值'
        ))
        
        fig_convergence.add_hline(
            y=base_performance,
            line_dash="dash",
            line_color="red",
            annotation_text="基准性能"
        )
        
        fig_convergence.update_layout(
            title='Monte Carlo收敛分析',
            xaxis_title='模拟次数',
            yaxis_title='累积平均性能'
        )
        plots['convergence'] = fig_convergence
        
        return plots
    
    def generate_robustness_report(self, result: RobustnessResult) -> str:
        """生成鲁棒性分析报告"""
        report = f"""
# 鲁棒性分析报告

## 总体评估
- **风险等级**: {result.risk_level.upper()}
- **基准性能**: {result.base_performance:.6f}
- **预期性能**: {result.mean_performance:.6f} (±{result.std_performance:.6f})
- **性能变异系数**: {(result.std_performance/result.mean_performance)*100:.2f}%

## 性能统计
- **最好情况**: {result.best_case:.6f}
- **最坏情况**: {result.worst_case:.6f}
- **95%置信区间**: [{result.confidence_interval_95[0]:.6f}, {result.confidence_interval_95[1]:.6f}]
- **下跌风险**: {max(0, (result.base_performance - result.worst_case)/result.base_performance)*100:.2f}%

## 参数敏感性排序
"""
        
        # 按敏感性排序
        sorted_sensitivity = sorted(
            result.sensitivity_metrics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for i, (param, sensitivity) in enumerate(sorted_sensitivity[:10], 1):
            report += f"{i}. {param}: {sensitivity:.4f}\n"
        
        report += f"""
## 情景分析结果
"""
        
        if not result.scenario_analysis.empty:
            for _, scenario in result.scenario_analysis.iterrows():
                perf_change = ((scenario['performance'] - result.base_performance) / 
                              result.base_performance * 100)
                report += f"- **{scenario['scenario_name']}**: {scenario['performance']:.6f} "
                report += f"({perf_change:+.2f}%)\n"
        
        report += f"""
## 风险建议

"""
        
        if result.risk_level == 'low':
            report += "- 解的鲁棒性很好，在参数不确定性下表现稳定\n"
            report += "- 可以放心采用此优化结果\n"
        elif result.risk_level == 'medium':
            report += "- 解的鲁棒性中等，需要关注关键参数的变化\n"
            report += "- 建议对敏感性最高的参数进行更精确的估计\n"
            report += "- 考虑建立监控机制跟踪关键指标\n"
        elif result.risk_level == 'high':
            report += "- 解的鲁棒性较差，存在较大的性能波动风险\n"
            report += "- 强烈建议重新优化或寻找更鲁棒的解\n"
            report += "- 需要建立风险管控措施\n"
        else:  # extreme
            report += "- 解的鲁棒性极差，不建议在实际中使用\n"
            report += "- 建议重新定义优化问题或约束条件\n"
            report += "- 考虑多目标优化，同时优化性能和鲁棒性\n"
        
        return report