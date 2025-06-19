"""
增强版可视化工具
Enhanced Plot Utilities

为简化版财务模型和敏感性分析设计的高级可视化功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional, Any
import seaborn as sns
import matplotlib.pyplot as plt

class EnhancedPlotUtils:
    """增强版绘图工具类"""
    
    @staticmethod
    def plot_sensitivity_analysis(results_df: pd.DataFrame, param_key: str, metric: str,
                                 param_name: str = None, metric_name: str = None) -> go.Figure:
        """
        绘制敏感性分析图表
        
        Args:
            results_df: 敏感性分析结果数据
            param_key: 参数键
            metric: 指标键
            param_name: 参数显示名称
            metric_name: 指标显示名称
            
        Returns:
            plotly图表对象
        """
        if param_key not in results_df.columns or metric not in results_df.columns:
            st.error(f"数据中缺少必要的列: {param_key} 或 {metric}")
            return go.Figure()
        
        # 设置默认名称
        if param_name is None:
            param_name = param_key
        if metric_name is None:
            metric_name = metric
        
        # 创建基础线图
        fig = px.line(
            results_df,
            x=param_key,
            y=metric,
            markers=True,
            title=f"{param_name} vs {metric_name}",
            labels={
                param_key: param_name,
                metric: metric_name
            }
        )
        
        # 添加数据点标注
        fig.update_traces(
            mode='lines+markers',
            marker=dict(size=8),
            line=dict(width=3)
        )
        
        # 更新布局
        fig.update_layout(
            height=400,
            hovermode="x unified",
            title_x=0.5,
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )
        )
        
        # 添加当前值标记线（如果存在基准值）
        current_val = results_df[param_key].iloc[len(results_df)//2]  # 取中间值作为基准
        fig.add_vline(
            x=current_val,
            line_dash="dash",
            line_color="red",
            annotation_text="基准值",
            annotation_position="top"
        )
        
        return fig
    
    @staticmethod
    def plot_multi_parameter_comparison(results: Dict[str, pd.DataFrame], metric: str,
                                      param_definitions: Dict[str, Dict] = None) -> go.Figure:
        """
        绘制多参数对比图表
        
        Args:
            results: 多参数分析结果
            metric: 目标指标
            param_definitions: 参数定义字典
            
        Returns:
            plotly图表对象
        """
        # 创建子图
        n_params = len(results)
        if n_params == 0:
            return go.Figure()
        
        # 计算子图布局
        cols = min(2, n_params)
        rows = (n_params + cols - 1) // cols
        
        subplot_titles = []
        for param_key in results.keys():
            if param_definitions and param_key in param_definitions:
                title = param_definitions[param_key]['name']
            else:
                title = param_key
            subplot_titles.append(title)
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )
        
        # 添加每个参数的线图
        colors = px.colors.qualitative.Set1
        
        for i, (param_key, result_df) in enumerate(results.items()):
            if metric not in result_df.columns:
                continue
            
            row = i // cols + 1
            col = i % cols + 1
            color = colors[i % len(colors)]
            
            fig.add_trace(
                go.Scatter(
                    x=result_df[param_key],
                    y=result_df[metric],
                    mode='lines+markers',
                    name=param_key,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                    showlegend=False
                ),
                row=row, col=col
            )
        
        # 更新布局
        fig.update_layout(
            height=300 * rows,
            title_text=f"多参数对{metric}的影响对比",
            title_x=0.5
        )
        
        # 更新子图轴
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
    
    @staticmethod
    def plot_parameter_importance(importance_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """
        绘制参数重要性排序图表
        
        Args:
            importance_df: 参数重要性数据
            top_n: 显示前N个参数
            
        Returns:
            plotly图表对象
        """
        if len(importance_df) == 0:
            return go.Figure()
        
        # 取前N个参数
        top_params = importance_df.head(top_n)
        
        # 创建水平条形图
        fig = px.bar(
            top_params,
            x='重要性得分',
            y='参数',
            orientation='h',
            color='重要性得分',
            title=f"参数重要性排序 (前{min(top_n, len(top_params))}名)",
            color_continuous_scale='viridis',
            text='重要性得分'
        )
        
        # 格式化文本
        fig.update_traces(
            texttemplate='%{text:.4f}',
            textposition="outside"
        )
        
        # 更新布局
        fig.update_layout(
            height=max(400, len(top_params) * 40),
            yaxis={'categoryorder': 'total ascending'},
            title_x=0.5,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def plot_correlation_heatmap(results: Dict[str, pd.DataFrame], metrics: List[str],
                                param_definitions: Dict[str, Dict] = None) -> go.Figure:
        """
        绘制参数-指标相关性热力图
        
        Args:
            results: 多参数分析结果
            metrics: 指标列表
            param_definitions: 参数定义字典
            
        Returns:
            plotly图表对象
        """
        # 构建相关性矩阵
        correlation_data = []
        param_names = []
        
        for param_key, result_df in results.items():
            if param_definitions and param_key in param_definitions:
                param_name = param_definitions[param_key]['name']
            else:
                param_name = param_key
            param_names.append(param_name)
            
            correlations = []
            for metric in metrics:
                if metric in result_df.columns and param_key in result_df.columns:
                    corr = np.corrcoef(result_df[param_key], result_df[metric])[0, 1]
                    correlations.append(corr if not np.isnan(corr) else 0)
                else:
                    correlations.append(0)
            correlation_data.append(correlations)
        
        if not correlation_data:
            return go.Figure()
        
        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=correlation_data,
            x=metrics,
            y=param_names,
            colorscale='RdBu',
            zmid=0,
            text=[[f"{val:.3f}" for val in row] for row in correlation_data],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        # 更新布局
        fig.update_layout(
            title="参数-指标相关性分析",
            title_x=0.5,
            height=max(400, len(param_names) * 40),
            xaxis_title="业务指标",
            yaxis_title="分析参数"
        )
        
        return fig
    
    @staticmethod
    def plot_revenue_trend_enhanced(results_df: pd.DataFrame, 
                                  show_breakdown: bool = True) -> go.Figure:
        """
        绘制增强版收入趋势图
        
        Args:
            results_df: 模型结果数据
            show_breakdown: 是否显示收入分解
            
        Returns:
            plotly图表对象
        """
        if show_breakdown:
            # 创建堆叠面积图
            fig = go.Figure()
            
            # 添加各收入来源
            revenue_sources = [
                ('luma_revenue_from_uni', 'Luma高校收入', '#1f77b4'),
                ('luma_revenue_from_student_share', 'Luma学生分成', '#ff7f0e'),
                ('uni_income_from_student_share', '高校学生分成', '#2ca02c')
            ]
            
            for column, name, color in revenue_sources:
                if column in results_df.columns:
                    fig.add_trace(go.Scatter(
                        x=results_df['period'],
                        y=results_df[column],
                        mode='lines',
                        stackgroup='one',
                        name=name,
                        line=dict(color=color),
                        hovertemplate=f"<b>{name}</b><br>" +
                                    "周期: %{x}<br>" +
                                    "收入: ¥%{y:,.0f}<extra></extra>"
                    ))
            
            title = "收入构成趋势分析"
        else:
            # 创建简单线图
            fig = px.line(
                results_df,
                x='period',
                y=['luma_revenue_total', 'uni_revenue_total', 'student_revenue_total'],
                title="收入趋势总览",
                labels={'value': '收入 (元)', 'period': '周期(半年)', 'variable': '收入类型'}
            )
            
            # 更新图例
            newnames = {
                'luma_revenue_total': 'Luma总收入',
                'uni_revenue_total': '高校收入',
                'student_revenue_total': '学生收入'
            }
            fig.for_each_trace(lambda t: t.update(name=newnames.get(t.name, t.name)))
            title = "收入趋势总览"
        
        # 更新布局
        fig.update_layout(
            title=title,
            title_x=0.5,
            height=500,
            hovermode="x unified",
            xaxis_title="周期(半年)",
            yaxis_title="收入 (元)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    @staticmethod
    def plot_business_metrics_dashboard(results_df: pd.DataFrame) -> go.Figure:
        """
        绘制业务指标仪表板
        
        Args:
            results_df: 模型结果数据
            
        Returns:
            plotly图表对象
        """
        # 创建2x2子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("收入趋势", "客户数量", "平均收入指标", "增长率分析"),
            specs=[[{"secondary_y": False}, {"secondary_y": True}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. 收入趋势
        fig.add_trace(
            go.Scatter(
                x=results_df['period'],
                y=results_df['luma_revenue_total'],
                mode='lines+markers',
                name='Luma总收入',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        # 2. 客户数量（双轴）
        fig.add_trace(
            go.Scatter(
                x=results_df['period'],
                y=results_df['active_universities'],
                mode='lines+markers',
                name='活跃高校数',
                line=dict(color='green')
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=results_df['period'],
                y=results_df['total_paying_students'],
                mode='lines+markers',
                name='付费学生数',
                line=dict(color='orange'),
                yaxis='y2'
            ),
            row=1, col=2, secondary_y=True
        )
        
        # 3. 平均收入指标
        if 'avg_revenue_per_uni' in results_df.columns:
            fig.add_trace(
                go.Bar(
                    x=results_df['period'],
                    y=results_df['avg_revenue_per_uni'],
                    name='平均每校收入',
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
        
        # 4. 增长率分析
        if len(results_df) > 1:
            growth_rates = results_df['luma_revenue_total'].pct_change() * 100
            fig.add_trace(
                go.Scatter(
                    x=results_df['period'][1:],
                    y=growth_rates[1:],
                    mode='lines+markers',
                    name='收入增长率',
                    line=dict(color='red')
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            height=800,
            title_text="业务指标综合仪表板",
            title_x=0.5,
            showlegend=True
        )
        
        # 设置y轴标题
        fig.update_yaxes(title_text="收入 (元)", row=1, col=1)
        fig.update_yaxes(title_text="高校数量", row=1, col=2)
        fig.update_yaxes(title_text="学生数量", row=1, col=2, secondary_y=True)
        fig.update_yaxes(title_text="平均收入 (元)", row=2, col=1)
        fig.update_yaxes(title_text="增长率 (%)", row=2, col=2)
        
        # 设置x轴标题
        fig.update_xaxes(title_text="周期(半年)", row=2, col=1)
        fig.update_xaxes(title_text="周期(半年)", row=2, col=2)
        
        return fig
    
    @staticmethod
    def plot_scenario_comparison(scenarios: Dict[str, pd.DataFrame], 
                               metric: str = 'luma_revenue_total') -> go.Figure:
        """
        绘制不同情景对比图
        
        Args:
            scenarios: 不同情景的结果数据
            metric: 对比指标
            
        Returns:
            plotly图表对象
        """
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        
        for i, (scenario_name, results_df) in enumerate(scenarios.items()):
            if metric in results_df.columns:
                color = colors[i % len(colors)]
                
                fig.add_trace(go.Scatter(
                    x=results_df['period'],
                    y=results_df[metric],
                    mode='lines+markers',
                    name=scenario_name,
                    line=dict(color=color, width=3),
                    marker=dict(size=8)
                ))
        
        # 更新布局
        fig.update_layout(
            title=f"不同情景下的{metric}对比",
            title_x=0.5,
            height=500,
            hovermode="x unified",
            xaxis_title="周期(半年)",
            yaxis_title=metric,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig