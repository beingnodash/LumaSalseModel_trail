# 优化过程监控系统
import numpy as np
import pandas as pd
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from collections import deque
import warnings

class OptimizationMonitor:
    """
    优化过程监控系统，提供实时监控、收敛检测、早停决策等功能。
    
    主要功能：
    1. 记录优化过程中的关键指标
    2. 检测收敛和停滞
    3. 提供早停建议
    4. 生成优化诊断报告
    5. 可视化优化过程
    """
    
    def __init__(self, patience: int = 10, min_improvement: float = 1e-4):
        """
        初始化监控器
        
        Args:
            patience: 早停耐心值，连续多少次无改进后建议停止
            min_improvement: 最小改进幅度，低于此值认为无改进
        """
        self.patience = patience
        self.min_improvement = min_improvement
        
        # 监控数据
        self.history = {
            'iteration': [],
            'best_score': [],
            'current_score': [],
            'improvement': [],
            'time_elapsed': [],
            'diversity': [],  # 种群多样性（适用于遗传算法）
            'exploration_rate': []  # 探索率（适用于贝叶斯优化）
        }
        
        # 状态跟踪
        self.start_time = None
        self.best_score_so_far = -float('inf')
        self.no_improvement_count = 0
        self.convergence_detected = False
        self.early_stop_suggested = False
        
        # 诊断信息
        self.diagnostics = {
            'convergence_rate': 0.0,
            'exploration_coverage': 0.0,
            'efficiency_score': 0.0,
            'recommendations': []
        }
    
    def start_monitoring(self):
        """开始监控"""
        self.start_time = time.time()
        self.reset_history()
    
    def reset_history(self):
        """重置监控历史"""
        for key in self.history:
            self.history[key] = []
        self.best_score_so_far = -float('inf')
        self.no_improvement_count = 0
        self.convergence_detected = False
        self.early_stop_suggested = False
    
    def record_iteration(self, iteration: int, current_score: float, 
                        best_score: float, **kwargs):
        """
        记录一次迭代的结果
        
        Args:
            iteration: 迭代次数
            current_score: 当前评估得分
            best_score: 到目前为止的最佳得分
            **kwargs: 其他监控指标（如diversity, exploration_rate等）
        """
        if self.start_time is None:
            self.start_monitoring()
        
        time_elapsed = time.time() - self.start_time
        
        # 计算改进幅度
        improvement = best_score - self.best_score_so_far if self.best_score_so_far != -float('inf') else 0
        
        # 记录数据
        self.history['iteration'].append(iteration)
        self.history['current_score'].append(current_score)
        self.history['best_score'].append(best_score)
        self.history['improvement'].append(improvement)
        self.history['time_elapsed'].append(time_elapsed)
        
        # 记录额外指标
        self.history['diversity'].append(kwargs.get('diversity', 0.0))
        self.history['exploration_rate'].append(kwargs.get('exploration_rate', 0.0))
        
        # 更新状态
        if improvement > self.min_improvement:
            self.no_improvement_count = 0
            self.best_score_so_far = best_score
        else:
            self.no_improvement_count += 1
        
        # 检测收敛和早停
        self._check_convergence()
        self._check_early_stop()
    
    def _check_convergence(self):
        """检测收敛"""
        if len(self.history['best_score']) < 5:
            return
        
        # 检查最近几次迭代的改进幅度
        recent_improvements = self.history['improvement'][-5:]
        avg_improvement = np.mean(recent_improvements)
        
        if avg_improvement < self.min_improvement:
            self.convergence_detected = True
    
    def _check_early_stop(self):
        """检查是否应该早停"""
        if self.no_improvement_count >= self.patience:
            self.early_stop_suggested = True
    
    def should_stop_early(self) -> bool:
        """判断是否应该早停"""
        return self.early_stop_suggested
    
    def get_convergence_status(self) -> Dict[str, Any]:
        """获取收敛状态"""
        return {
            'converged': self.convergence_detected,
            'early_stop_suggested': self.early_stop_suggested,
            'no_improvement_count': self.no_improvement_count,
            'best_score': self.best_score_so_far,
            'iterations_completed': len(self.history['iteration'])
        }
    
    def calculate_convergence_rate(self) -> float:
        """计算收敛速度"""
        if len(self.history['best_score']) < 2:
            return 0.0
        
        scores = np.array(self.history['best_score'])
        iterations = np.array(self.history['iteration'])
        
        # 计算改进的斜率
        if len(scores) > 1:
            # 使用线性回归计算趋势
            coeffs = np.polyfit(iterations, scores, 1)
            convergence_rate = coeffs[0]  # 斜率
        else:
            convergence_rate = 0.0
        
        return max(0.0, convergence_rate)
    
    def calculate_exploration_coverage(self, search_space_bounds: Optional[Dict] = None) -> float:
        """
        计算探索覆盖率（需要额外的搜索点信息）
        
        Args:
            search_space_bounds: 搜索空间边界
            
        Returns:
            探索覆盖率 [0, 1]
        """
        # 这是一个简化版本，实际实现需要搜索点的坐标信息
        if not self.history['exploration_rate']:
            return 0.5  # 默认值
        
        # 基于探索率的平均值来估算
        avg_exploration_rate = np.mean(self.history['exploration_rate'])
        return min(1.0, avg_exploration_rate)
    
    def calculate_efficiency_score(self) -> float:
        """
        计算优化效率得分
        
        Returns:
            效率得分 [0, 1]，越高表示效率越好
        """
        if len(self.history['best_score']) < 2:
            return 0.0
        
        # 基于改进速度和时间消耗计算效率
        total_improvement = self.best_score_so_far - self.history['best_score'][0]
        total_time = self.history['time_elapsed'][-1] if self.history['time_elapsed'] else 1.0
        total_iterations = len(self.history['iteration'])
        
        # 归一化效率指标
        time_efficiency = min(1.0, 1.0 / (total_time / total_iterations + 1e-6))
        improvement_efficiency = min(1.0, total_improvement / (total_iterations + 1e-6))
        
        return 0.6 * improvement_efficiency + 0.4 * time_efficiency
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if len(self.history['best_score']) < 5:
            return ["需要更多迭代数据才能提供建议"]
        
        # 基于收敛状态的建议
        if self.convergence_detected:
            recommendations.append("检测到收敛，建议考虑停止优化或调整算法参数")
        
        if self.early_stop_suggested:
            recommendations.append(f"连续{self.no_improvement_count}次无改进，建议早停")
        
        # 基于效率的建议
        efficiency = self.calculate_efficiency_score()
        if efficiency < 0.3:
            recommendations.append("优化效率较低，建议：1)增加种群大小 2)调整学习率 3)换用其他算法")
        elif efficiency > 0.8:
            recommendations.append("优化效率很高，当前设置良好")
        
        # 基于探索率的建议
        if self.history['exploration_rate']:
            avg_exploration = np.mean(self.history['exploration_rate'][-5:])
            if avg_exploration < 0.1:
                recommendations.append("探索率过低，可能陷入局部最优，建议增加探索（如增大变异率）")
            elif avg_exploration > 0.8:
                recommendations.append("探索率过高，可能影响收敛，建议增加利用（如降低变异率）")
        
        # 基于改进趋势的建议
        recent_improvements = self.history['improvement'][-5:]
        if all(imp <= 0 for imp in recent_improvements):
            recommendations.append("最近几次迭代无改进，建议重启或更换算法")
        
        return recommendations if recommendations else ["优化过程正常，继续执行"]
    
    def update_diagnostics(self):
        """更新诊断信息"""
        self.diagnostics['convergence_rate'] = self.calculate_convergence_rate()
        self.diagnostics['exploration_coverage'] = self.calculate_exploration_coverage()
        self.diagnostics['efficiency_score'] = self.calculate_efficiency_score()
        self.diagnostics['recommendations'] = self.generate_recommendations()
    
    def generate_diagnostic_report(self) -> str:
        """生成诊断报告"""
        self.update_diagnostics()
        
        if not self.history['iteration']:
            return "无监控数据，无法生成诊断报告"
        
        report = f"""
# 优化过程诊断报告

## 基本统计
- 总迭代次数: {len(self.history['iteration'])}
- 当前最佳得分: {self.best_score_so_far:.6f}
- 总用时: {self.history['time_elapsed'][-1]:.2f} 秒
- 平均每次迭代用时: {np.mean(np.diff([0] + self.history['time_elapsed'])):.3f} 秒

## 收敛状态
- 收敛检测: {'是' if self.convergence_detected else '否'}
- 连续无改进次数: {self.no_improvement_count}
- 早停建议: {'是' if self.early_stop_suggested else '否'}

## 性能指标
- 收敛速度: {self.diagnostics['convergence_rate']:.6f}
- 探索覆盖率: {self.diagnostics['exploration_coverage']:.2%}
- 效率得分: {self.diagnostics['efficiency_score']:.2%}

## 优化建议
"""
        for i, rec in enumerate(self.diagnostics['recommendations'], 1):
            report += f"{i}. {rec}\n"
        
        return report
    
    def create_convergence_plot(self) -> go.Figure:
        """创建收敛过程图表"""
        if not self.history['iteration']:
            # 返回空图表
            fig = go.Figure()
            fig.add_annotation(text="暂无数据", x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = go.Figure()
        
        # 添加最佳得分曲线
        fig.add_trace(go.Scatter(
            x=self.history['iteration'],
            y=self.history['best_score'],
            mode='lines+markers',
            name='最佳得分',
            line=dict(color='blue', width=2)
        ))
        
        # 添加当前得分曲线
        fig.add_trace(go.Scatter(
            x=self.history['iteration'],
            y=self.history['current_score'],
            mode='markers',
            name='当前得分',
            marker=dict(color='lightblue', size=4, opacity=0.6)
        ))
        
        fig.update_layout(
            title='优化收敛过程',
            xaxis_title='迭代次数',
            yaxis_title='目标函数值',
            hovermode='x unified'
        )
        
        return fig
    
    def create_improvement_plot(self) -> go.Figure:
        """创建改进幅度图表"""
        if len(self.history['improvement']) < 2:
            fig = go.Figure()
            fig.add_annotation(text="需要更多数据", x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=self.history['iteration'][1:],  # 第一次迭代没有改进数据
            y=self.history['improvement'][1:],
            name='改进幅度',
            marker_color=['green' if imp > 0 else 'red' for imp in self.history['improvement'][1:]]
        ))
        
        fig.update_layout(
            title='每次迭代的改进幅度',
            xaxis_title='迭代次数',
            yaxis_title='改进幅度',
            showlegend=False
        )
        
        return fig
    
    def create_efficiency_plot(self) -> go.Figure:
        """创建效率分析图表"""
        if not self.history['time_elapsed']:
            fig = go.Figure()
            fig.add_annotation(text="暂无时间数据", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # 计算累积效率
        cumulative_improvement = np.cumsum([0] + self.history['improvement'])
        time_per_iteration = np.diff([0] + self.history['time_elapsed'])
        efficiency_ratio = []
        
        for i in range(len(cumulative_improvement)):
            if i == 0:
                efficiency_ratio.append(0)
            else:
                total_time = self.history['time_elapsed'][i-1]
                efficiency = cumulative_improvement[i] / (total_time + 1e-6)
                efficiency_ratio.append(efficiency)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=self.history['iteration'],
            y=efficiency_ratio,
            mode='lines+markers',
            name='效率比率',
            line=dict(color='orange', width=2)
        ))
        
        fig.update_layout(
            title='优化效率趋势',
            xaxis_title='迭代次数',
            yaxis_title='效率比率 (改进量/时间)',
            hovermode='x unified'
        )
        
        return fig

class OptimizationCallback:
    """
    优化回调类，用于在优化算法中集成监控功能
    """
    
    def __init__(self, monitor: OptimizationMonitor, 
                 progress_callback: Optional[Callable] = None):
        self.monitor = monitor
        self.progress_callback = progress_callback
        self.iteration_count = 0
    
    def __call__(self, current_score: float, best_score: float, **kwargs):
        """
        回调函数，在每次迭代时调用
        
        Args:
            current_score: 当前评估得分
            best_score: 最佳得分
            **kwargs: 其他监控指标
        """
        self.iteration_count += 1
        
        # 记录到监控器
        self.monitor.record_iteration(
            self.iteration_count, current_score, best_score, **kwargs
        )
        
        # 调用进度回调
        if self.progress_callback:
            progress = kwargs.get('progress', self.iteration_count / kwargs.get('total_iterations', 100))
            status_text = f"迭代 {self.iteration_count} | 最佳: {best_score:.4f}"
            
            if self.monitor.should_stop_early():
                status_text += " | 建议早停"
            
            self.progress_callback(progress, status_text)
        
        # 返回是否应该早停
        return self.monitor.should_stop_early()