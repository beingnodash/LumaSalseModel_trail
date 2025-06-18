"""
可视化页面 - 提供丰富的数据可视化功能
"""
import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from streamlit_app.utils.plot_utils import (
    plot_revenue_trend, 
    plot_revenue_breakdown, 
    plot_mode_distribution,
    plot_luma_vs_uni_fund,
    plot_new_vs_renewed
)

# 设置页面配置
st.set_page_config(
    page_title="数据可视化 - Luma高校销售与收益分析模型",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("数据可视化")
st.markdown("""
本页面提供了丰富的数据可视化功能，帮助您更直观地理解模型结果。您可以查看各种图表，分析收入趋势、结构分布等关键指标。
""")

# 初始化会话状态
if 'model_results' not in st.session_state:
    st.session_state.model_results = None

# 检查是否有模型结果
if st.session_state.model_results is None:
    st.warning("请先在主页设置并运行模型，然后再查看可视化结果。")
    st.stop()

# 获取模型结果
results_df = st.session_state.model_results

# 创建可视化选项
visualization_options = {
    "收入趋势图": "revenue_trend",
    "收入构成图": "revenue_breakdown",
    "合作模式分布": "mode_distribution",
    "Luma与高校基金对比": "luma_vs_uni",
    "新签与续约对比": "new_vs_renewed",
    "自定义图表": "custom"
}

# 选择可视化类型
selected_viz = st.selectbox(
    "选择可视化类型",
    list(visualization_options.keys())
)

# 根据选择显示不同的可视化
viz_type = visualization_options[selected_viz]

if viz_type == "revenue_trend":
    plot_revenue_trend(results_df)
    
    # 添加额外的趋势分析
    st.subheader("趋势分析")
    
    # 计算增长率
    growth_rates = results_df['Luma_Revenue_Total'].pct_change() * 100
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "平均半年增长率", 
            f"{growth_rates.mean():.2f}%",
            delta=f"{growth_rates.iloc[-1]:.2f}%" if len(growth_rates) > 1 else None
        )
    
    with col2:
        total_periods = len(results_df)
        total_growth = ((results_df['Luma_Revenue_Total'].iloc[-1] / results_df['Luma_Revenue_Total'].iloc[0]) - 1) * 100 if total_periods > 1 else 0
        st.metric(
            f"总增长率 ({total_periods} 个半年)",
            f"{total_growth:.2f}%"
        )
    
    # 显示增长率趋势
    if len(growth_rates) > 1:
        st.subheader("半年增长率趋势")
        growth_df = pd.DataFrame({'增长率 (%)': growth_rates}).dropna()
        st.bar_chart(growth_df)

elif viz_type == "revenue_breakdown":
    plot_revenue_breakdown(results_df)
    
    # 添加收入构成分析
    st.subheader("收入构成分析")
    
    # 计算各部分收入占比
    total_fixed_fee = results_df['Luma_Fixed_Fee_New'].sum()
    total_student_new = results_df['Luma_Student_Share_New'].sum()
    total_student_renewed = results_df['Luma_Student_Share_Renewed'].sum()
    total_revenue = total_fixed_fee + total_student_new + total_student_renewed
    
    # 显示占比
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "固定费占比",
            f"{(total_fixed_fee / total_revenue * 100):.2f}%"
        )
    
    with col2:
        st.metric(
            "新签学生付费占比",
            f"{(total_student_new / total_revenue * 100):.2f}%"
        )
    
    with col3:
        st.metric(
            "续约学生付费占比",
            f"{(total_student_renewed / total_revenue * 100):.2f}%"
        )
    
    # 显示饼图
    pie_data = pd.DataFrame({
        '收入类型': ['固定接入费', '新签学生付费', '续约学生付费'],
        '金额': [total_fixed_fee, total_student_new, total_student_renewed]
    })
    
    fig = px.pie(
        pie_data,
        values='金额',
        names='收入类型',
        title='Luma收入构成占比'
    )
    
    st.plotly_chart(fig, use_container_width=True)

elif viz_type == "mode_distribution":
    plot_mode_distribution(results_df)
    
    # 添加模式分布分析
    st.subheader("合作模式分析")
    
    # 提取各模式的收入数据
    mode_data = {}
    for mode in ['Type1', 'Type2a', 'Type2b', 'Type2c', 'Type3']:
        new_col = f'Luma_Revenue_{mode}_New'
        renewed_col = f'Luma_Revenue_{mode}_Renewed'
        
        if new_col in results_df.columns and renewed_col in results_df.columns:
            mode_data[f'{mode}'] = results_df[new_col].sum() + results_df[renewed_col].sum()
    
    if mode_data:
        # 显示各模式收入及占比
        mode_df = pd.DataFrame({
            '合作模式': list(mode_data.keys()),
            '总收入': list(mode_data.values())
        })
        
        mode_df['占比 (%)'] = mode_df['总收入'] / mode_df['总收入'].sum() * 100
        mode_df = mode_df.sort_values('总收入', ascending=False)
        
        st.dataframe(mode_df)

elif viz_type == "luma_vs_uni":
    plot_luma_vs_uni_fund(results_df)
    
    # 添加额外分析
    st.subheader("Luma与高校收益分析")
    
    # 计算总收益和比例
    total_luma = results_df['Luma_Revenue_Total'].sum()
    total_uni = results_df['Uni_Fund_Total'].sum()
    total_ecosystem = total_luma + total_uni
    
    # 显示生态系统总收益分配
    st.markdown(f"""
    ### 生态系统总收益分配
    - **总生态系统收益**: {total_ecosystem:.2f} 元
    - **Luma收益占比**: {(total_luma / total_ecosystem * 100):.2f}%
    - **高校基金占比**: {(total_uni / total_ecosystem * 100):.2f}%
    """)
    
    # 显示饼图
    eco_data = pd.DataFrame({
        '收益主体': ['Luma', '高校基金'],
        '金额': [total_luma, total_uni]
    })
    
    fig = px.pie(
        eco_data,
        values='金额',
        names='收益主体',
        title='生态系统收益分配'
    )
    
    st.plotly_chart(fig, use_container_width=True)

elif viz_type == "new_vs_renewed":
    plot_new_vs_renewed(results_df)
    
    # 添加新签与续约分析
    st.subheader("新签与续约趋势分析")
    
    # 准备数据
    new_revenue = results_df['Luma_Fixed_Fee_New'] + results_df['Luma_Student_Share_New']
    renewed_revenue = results_df['Luma_Student_Share_Renewed']
    
    # 计算新签与续约的比例变化
    ratio_df = pd.DataFrame({
        '新签收入': new_revenue,
        '续约收入': renewed_revenue,
        '新签占比 (%)': new_revenue / (new_revenue + renewed_revenue) * 100,
        '续约占比 (%)': renewed_revenue / (new_revenue + renewed_revenue) * 100
    })
    
    # 显示比例变化趋势
    st.subheader("新签与续约收入占比变化")
    
    fig = px.line(
        ratio_df,
        y=['新签占比 (%)', '续约占比 (%)'],
        markers=True,
        title='新签与续约收入占比变化趋势'
    )
    
    fig.update_layout(
        xaxis_title='周期 (半年)',
        yaxis_title='占比 (%)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

elif viz_type == "custom":
    st.subheader("自定义图表")
    
    # 选择要显示的指标
    available_metrics = results_df.columns.tolist()
    
    selected_metrics = st.multiselect(
        "选择要显示的指标",
        available_metrics,
        default=['Luma_Revenue_Total', 'Uni_Fund_Total']
    )
    
    if selected_metrics:
        # 选择图表类型
        chart_type = st.selectbox(
            "选择图表类型",
            ["折线图", "柱状图", "面积图", "散点图"]
        )
        
        # 显示选定的图表
        st.subheader(f"自定义{chart_type}")
        
        if chart_type == "折线图":
            st.line_chart(results_df[selected_metrics])
        elif chart_type == "柱状图":
            st.bar_chart(results_df[selected_metrics])
        elif chart_type == "面积图":
            fig = px.area(results_df[selected_metrics])
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "散点图":
            if len(selected_metrics) >= 2:
                fig = px.scatter(
                    results_df.reset_index(),
                    x=selected_metrics[0],
                    y=selected_metrics[1],
                    size=selected_metrics[1] if len(selected_metrics) > 2 else None,
                    hover_name="Period"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("散点图需要至少选择两个指标")
    else:
        st.info("请选择至少一个指标来创建图表")

# 提供下载结果的选项
st.markdown("---")
st.subheader("下载数据")

csv = results_df.to_csv()
st.download_button(
    label="下载模型结果数据 (CSV)",
    data=csv,
    file_name="model_results.csv",
    mime="text/csv",
)
