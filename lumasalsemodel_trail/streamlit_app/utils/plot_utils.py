"""
可视化辅助函数模块 - 提供Streamlit中展示模型结果的可视化功能
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional, Any

def set_chinese_font():
    """
    设置matplotlib中文字体支持
    """
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体 (适用于Windows)
        plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
    except Exception as e:
        st.warning(f"设置中文字体失败，图表中的中文可能无法正确显示。请确保已安装SimHei或其他中文字体。")

def plot_revenue_trend(results_df: pd.DataFrame) -> None:
    """
    绘制Luma总收入趋势图
    
    Args:
        results_df (pd.DataFrame): 模型结果DataFrame
    """
    st.subheader("Luma总收入趋势")
    
    # 使用Plotly创建交互式图表
    fig = px.line(
        results_df.reset_index(), 
        x='Period', 
        y='Luma_Revenue_Total',
        markers=True,
        labels={'Period': '周期 (半年)', 'Luma_Revenue_Total': '收入 (元)'},
        title='Luma总收入趋势 (按半年周期)'
    )
    
    fig.update_layout(
        xaxis_title='周期 (半年)',
        yaxis_title='收入 (元)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_revenue_breakdown(results_df: pd.DataFrame) -> None:
    """
    绘制Luma收入构成图 (新签 vs. 续约)
    
    Args:
        results_df (pd.DataFrame): 模型结果DataFrame
    """
    st.subheader("Luma收入构成: 新签 vs. 续约")
    
    # 准备数据
    plot_data = pd.DataFrame({
        '新签-固定费': results_df['Luma_Fixed_Fee_New'],
        '新签-学生付费': results_df['Luma_Student_Share_New'],
        '续约-学生付费': results_df['Luma_Student_Share_Renewed']
    })
    
    # 使用Plotly创建交互式堆叠柱状图
    fig = go.Figure()
    
    for column in plot_data.columns:
        fig.add_trace(go.Bar(
            x=results_df.index,
            y=plot_data[column],
            name=column
        ))
    
    fig.update_layout(
        title='Luma收入构成: 新签 vs. 续约 (按半年周期)',
        xaxis_title='周期 (半年)',
        yaxis_title='收入 (元)',
        barmode='stack',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_mode_distribution(results_df: pd.DataFrame) -> None:
    """
    绘制各合作模式收入分布图
    
    Args:
        results_df (pd.DataFrame): 模型结果DataFrame
    """
    st.subheader("各合作模式收入分布")
    
    # 提取各模式的收入数据
    mode_data = {}
    for mode in ['Type1', 'Type2a', 'Type2b', 'Type2c', 'Type3']:
        new_col = f'Luma_Revenue_{mode}_New'
        renewed_col = f'Luma_Revenue_{mode}_Renewed'
        
        if new_col in results_df.columns and renewed_col in results_df.columns:
            mode_data[f'{mode}'] = results_df[new_col] + results_df[renewed_col]
    
    if mode_data:
        mode_df = pd.DataFrame(mode_data)
        
        # 计算总收入
        total_by_mode = mode_df.sum()
        
        # 创建饼图
        fig = px.pie(
            values=total_by_mode.values,
            names=total_by_mode.index,
            title='各合作模式总收入占比'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 创建趋势图
        fig2 = px.line(
            mode_df,
            markers=True,
            labels={'value': '收入 (元)', 'variable': '合作模式'},
            title='各合作模式收入趋势'
        )
        
        fig2.update_layout(
            xaxis_title='周期 (半年)',
            yaxis_title='收入 (元)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig2, use_container_width=True)

def plot_luma_vs_uni_fund(results_df: pd.DataFrame) -> None:
    """
    绘制Luma收入与高校基金对比图
    
    Args:
        results_df (pd.DataFrame): 模型结果DataFrame
    """
    st.subheader("Luma收入与高校基金对比")
    
    # 准备数据
    comparison_data = pd.DataFrame({
        'Luma收入': results_df['Luma_Revenue_Total'],
        '高校基金': results_df['Uni_Fund_Total']
    })
    
    # 创建柱状图
    fig = go.Figure()
    
    for column in comparison_data.columns:
        fig.add_trace(go.Bar(
            x=results_df.index,
            y=comparison_data[column],
            name=column
        ))
    
    fig.update_layout(
        title='Luma收入与高校基金对比 (按半年周期)',
        xaxis_title='周期 (半年)',
        yaxis_title='金额 (元)',
        barmode='group',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 计算总额
    total_luma = comparison_data['Luma收入'].sum()
    total_uni = comparison_data['高校基金'].sum()
    
    # 显示总额对比
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Luma总收入", f"{total_luma:.2f} 元")
    with col2:
        st.metric("高校基金总额", f"{total_uni:.2f} 元")

def plot_new_vs_renewed(results_df: pd.DataFrame) -> None:
    """
    绘制新签与续约收入对比图
    
    Args:
        results_df (pd.DataFrame): 模型结果DataFrame
    """
    st.subheader("新签与续约收入对比")
    
    # 准备数据
    new_revenue = results_df['Luma_Fixed_Fee_New'] + results_df['Luma_Student_Share_New']
    renewed_revenue = results_df['Luma_Student_Share_Renewed']
    
    comparison_data = pd.DataFrame({
        '新签收入': new_revenue,
        '续约收入': renewed_revenue
    })
    
    # 创建面积图
    fig = px.area(
        comparison_data,
        labels={'value': '收入 (元)', 'variable': '收入类型'},
        title='新签与续约收入趋势'
    )
    
    fig.update_layout(
        xaxis_title='周期 (半年)',
        yaxis_title='收入 (元)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 计算总额和占比
    total_new = new_revenue.sum()
    total_renewed = renewed_revenue.sum()
    total = total_new + total_renewed
    
    # 显示总额和占比
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("新签收入总额", f"{total_new:.2f} 元")
    with col2:
        st.metric("续约收入总额", f"{total_renewed:.2f} 元")
    with col3:
        st.metric("新签收入占比", f"{(total_new/total*100):.1f}%")

def plot_sensitivity_analysis(sensitivity_df: pd.DataFrame, param_name: str, output_metric: str) -> None:
    """
    绘制敏感性分析结果图
    
    Args:
        sensitivity_df (pd.DataFrame): 敏感性分析结果DataFrame
        param_name (str): 参数名称
        output_metric (str): 输出指标名称
    """
    if sensitivity_df is None or sensitivity_df.empty:
        st.warning("没有可用的敏感性分析结果")
        return
    
    st.subheader(f"参数敏感性分析: {param_name}")
    
    # 确保数据按参数值排序
    sensitivity_df = sensitivity_df.sort_values('Test_Value')
    
    # 创建线图
    fig = px.line(
        sensitivity_df,
        x='Test_Value',
        y=output_metric,
        markers=True,
        labels={
            'Test_Value': f'{param_name} 值',
            output_metric: f'{output_metric} 值'
        },
        title=f'{param_name} 对 {output_metric} 的影响'
    )
    
    fig.update_layout(
        xaxis_title=f'{param_name} 值',
        yaxis_title=f'{output_metric} 值',
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 计算敏感性指标
    baseline = sensitivity_df.iloc[0][output_metric]
    changes = []
    
    for i, row in sensitivity_df.iterrows():
        param_change = (row['Test_Value'] - sensitivity_df.iloc[0]['Test_Value']) / sensitivity_df.iloc[0]['Test_Value'] if sensitivity_df.iloc[0]['Test_Value'] != 0 else float('inf')
        output_change = (row[output_metric] - baseline) / baseline if baseline != 0 else float('inf')
        
        if param_change != 0:
            elasticity = output_change / param_change
        else:
            elasticity = 0
            
        changes.append({
            'Parameter_Value': row['Test_Value'],
            'Output_Value': row[output_metric],
            'Parameter_Change': f"{param_change:.2%}",
            'Output_Change': f"{output_change:.2%}",
            'Elasticity': elasticity
        })
    
    changes_df = pd.DataFrame(changes)
    st.dataframe(changes_df)
    
    # 弹性分析
    st.subheader("参数弹性分析")
    st.markdown("""
    **参数弹性** 表示输出指标对参数变化的敏感程度。弹性值越高，表示参数变化对结果的影响越大。
    
    - 弹性 > 1: 高敏感度，参数变化会导致更大比例的输出变化
    - 弹性 = 1: 等比敏感度，参数变化导致相同比例的输出变化
    - 弹性 < 1: 低敏感度，参数变化导致较小比例的输出变化
    """)

def plot_dual_parameter_sensitivity(results: List[Dict[str, Any]], param1: str, param2: str, output_metric: str) -> None:
    """
    绘制双参数敏感性分析热力图
    
    Args:
        results (List[Dict[str, Any]]): 敏感性分析结果列表
        param1 (str): 第一个参数名称
        param2 (str): 第二个参数名称
        output_metric (str): 输出指标名称
    """
    st.subheader(f"双参数敏感性分析: {param1} 和 {param2}")
    
    if not results:
        st.warning("没有可用的双参数敏感性分析结果")
        return
    
    # 提取唯一的参数值
    param1_values = sorted(list(set([r[param1] for r in results])))
    param2_values = sorted(list(set([r[param2] for r in results])))
    
    # 创建热力图数据
    heatmap_data = np.zeros((len(param1_values), len(param2_values)))
    
    for r in results:
        i = param1_values.index(r[param1])
        j = param2_values.index(r[param2])
        heatmap_data[i, j] = r[output_metric]
    
    # 创建热力图
    fig = px.imshow(
        heatmap_data,
        x=param2_values,
        y=param1_values,
        labels={
            'x': param2,
            'y': param1,
            'color': output_metric
        },
        title=f'{param1} 和 {param2} 对 {output_metric} 的影响'
    )
    
    fig.update_layout(
        xaxis_title=param2,
        yaxis_title=param1
    )
    
    st.plotly_chart(fig, use_container_width=True)
