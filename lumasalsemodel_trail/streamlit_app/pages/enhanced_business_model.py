"""
增强版商业模式分析页面
Enhanced Business Model Analysis Page

支持新的三种商业模式：
- 模式A: 高校付费 + 学生免费使用全部功能
- 模式B: 高校付费 + 学生免费基础功能 + 学生付费高级功能
- 模式C: 高校免费 + 学生免费基础功能 + 学生付费高级功能
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from luma_sales_model.enhanced_financial_model import LumaEnhancedFinancialModel
from utils.enhanced_parameter_ui import EnhancedParameterUI

# 设置页面配置
st.set_page_config(
    page_title="增强版商业模式分析 - Luma高校销售与收益分析模型",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("🚀 增强版商业模式分析")

# 添加详细的页面介绍
st.markdown("""
## 全新商业模式架构

本页面支持Luma的三种核心商业模式，为不同的市场策略提供灵活的财务建模：

### 📊 三种商业模式
- **🏫 模式A**: 高校付费 + 学生免费使用全部功能
- **🎓 模式B**: 高校付费 + 学生免费基础功能 + 学生付费高级功能  
- **💡 模式C**: 高校免费 + 学生免费基础功能 + 学生付费高级功能

### 🔄 核心业务特性
- **高校3年服务周期**: 一次性付费，3年后续约
- **双重学生付费模式**: 按次付费 + 订阅付费
- **灵活收入分成**: 根据商业模式调整Luma与高校的分成比例
- **精细化续约建模**: 高校续约、学生复购、订阅续费分别建模

### 📈 分析能力
- **多周期财务预测**: 支持长期业务发展分析
- **收入构成分解**: 详细的收入来源分析
- **客户生命周期**: 完整的客户群组追踪
- **业务指标监控**: 关键KPI指标实时监控
""", unsafe_allow_html=True)

# 初始化参数UI
param_ui = EnhancedParameterUI()

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 参数配置", 
    "📊 模型运行", 
    "📈 结果分析",
    "🔍 深度洞察"
])

with tab1:
    st.header("参数配置")
    
    # 收集所有参数
    collected_params = param_ui.collect_all_parameters()
    
    # 保存参数到session state
    st.session_state.enhanced_model_params = collected_params
    
    st.success("✅ 参数配置完成！请切换到「模型运行」标签页执行分析。")

with tab2:
    st.header("模型运行")
    
    if 'enhanced_model_params' not in st.session_state:
        st.warning("⚠️ 请先在「参数配置」标签页设置参数。")
        st.stop()
    
    # 显示参数摘要
    with st.expander("📋 参数摘要", expanded=False):
        param_ui.display_parameter_summary(st.session_state.enhanced_model_params)
    
    # 运行模型按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_model = st.button("🚀 运行增强版财务模型", type="primary", use_container_width=True)
    
    if run_model:
        with st.spinner("正在运行增强版财务模型..."):
            try:
                # 创建模型实例
                model = LumaEnhancedFinancialModel(st.session_state.enhanced_model_params)
                
                # 运行模型
                results_df = model.run_model()
                
                # 保存结果
                st.session_state.enhanced_model_results = results_df
                st.session_state.enhanced_model_instance = model
                
                st.success("✅ 模型运行完成！")
                
                # 显示基础结果预览
                st.subheader("📊 结果预览")
                
                # 关键指标
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_luma_revenue = results_df['luma_revenue_total'].sum()
                    st.metric("Luma总收入", f"¥{total_luma_revenue:,.0f}")
                
                with col2:
                    avg_revenue_per_period = results_df['luma_revenue_total'].mean()
                    st.metric("平均期收入", f"¥{avg_revenue_per_period:,.0f}")
                
                with col3:
                    max_active_unis = results_df['active_universities'].max()
                    st.metric("峰值活跃高校", f"{max_active_unis:.0f} 所")
                
                with col4:
                    max_paying_students = results_df['total_paying_students'].max()
                    st.metric("峰值付费学生", f"{max_paying_students:,.0f} 人")
                
                # 简化收入趋势图
                fig = px.line(results_df, x='period', y=['luma_revenue_total', 'uni_revenue_total', 'student_revenue_total'],
                             title="收入趋势总览",
                             labels={'value': '收入 (元)', 'period': '周期'})
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"模型运行出错: {str(e)}")
                st.exception(e)

with tab3:
    st.header("结果分析")
    
    if 'enhanced_model_results' not in st.session_state:
        st.warning("⚠️ 请先在「模型运行」标签页运行模型。")
        st.stop()
    
    results_df = st.session_state.enhanced_model_results
    model = st.session_state.enhanced_model_instance
    
    # 业务摘要
    st.subheader("🎯 业务摘要")
    business_summary = model.get_business_summary()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总分析周期", f"{business_summary['total_periods']} 个半年")
        st.metric("Luma总收入", f"¥{business_summary['total_luma_revenue']:,.0f}")
        st.metric("高校总收入", f"¥{business_summary['total_uni_revenue']:,.0f}")
    
    with col2:
        st.metric("学生总收入", f"¥{business_summary['total_student_revenue']:,.0f}")
        st.metric("平均期收入", f"¥{business_summary['avg_luma_revenue_per_period']:,.0f}")
        st.metric("收入增长率", f"{business_summary['revenue_growth_rate']:.1%}")
    
    with col3:
        st.metric("峰值活跃高校", f"{business_summary['peak_active_universities']:.0f} 所")
        st.metric("峰值付费学生", f"{business_summary['peak_paying_students']:,.0f} 人")
        
        # 商业模式分布
        mode_dist = business_summary['business_mode_distribution']
        st.write("**商业模式分布**")
        st.write(f"模式A: {mode_dist['mode_a']:.1%}")
        st.write(f"模式B: {mode_dist['mode_b']:.1%}")
        st.write(f"模式C: {mode_dist['mode_c']:.1%}")
    
    # 详细数据表
    st.subheader("📊 详细财务数据")
    st.dataframe(results_df, use_container_width=True)
    
    # 下载数据
    csv = results_df.to_csv(index=False)
    st.download_button(
        label="📥 下载财务数据 (CSV)",
        data=csv,
        file_name=f"luma_enhanced_financial_results.csv",
        mime="text/csv"
    )

with tab4:
    st.header("深度洞察")
    
    if 'enhanced_model_results' not in st.session_state:
        st.warning("⚠️ 请先在「模型运行」标签页运行模型。")
        st.stop()
    
    results_df = st.session_state.enhanced_model_results
    
    # 创建高级可视化
    st.subheader("🔍 高级可视化分析")
    
    # 1. 收入构成堆叠图
    fig1 = make_subplots(rows=2, cols=2,
                        subplot_titles=("Luma收入构成", "学生收入类型分布", 
                                      "客户数量趋势", "平均收入指标"),
                        specs=[[{"secondary_y": False}, {"secondary_y": False}],
                               [{"secondary_y": True}, {"secondary_y": False}]])
    
    # Luma收入构成堆叠图
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['luma_revenue_from_uni'],
                  mode='lines', stackgroup='luma', name='来自高校'),
        row=1, col=1
    )
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['luma_revenue_from_student_share'],
                  mode='lines', stackgroup='luma', name='来自学生分成'),
        row=1, col=1
    )
    
    # 学生收入类型分布
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['student_revenue_per_use'],
                  mode='lines', stackgroup='student', name='按次付费'),
        row=1, col=2
    )
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['student_revenue_subscription'],
                  mode='lines', stackgroup='student', name='订阅付费'),
        row=1, col=2
    )
    
    # 客户数量趋势（双轴）
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['active_universities'],
                  mode='lines+markers', name='活跃高校数', line=dict(color='blue')),
        row=2, col=1
    )
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['total_paying_students'],
                  mode='lines+markers', name='付费学生数', line=dict(color='red'), yaxis='y2'),
        row=2, col=1, secondary_y=True
    )
    
    # 平均收入指标
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['avg_revenue_per_uni'],
                  mode='lines+markers', name='每高校平均收入'),
        row=2, col=2
    )
    fig1.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['avg_revenue_per_paying_student'],
                  mode='lines+markers', name='每付费学生平均收入'),
        row=2, col=2
    )
    
    fig1.update_layout(height=800, title_text="深度业务分析仪表板")
    st.plotly_chart(fig1, use_container_width=True)
    
    # 2. 商业模式对比分析
    st.subheader("🎯 商业模式影响分析")
    
    params = st.session_state.enhanced_model_params
    
    # 创建对比分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("收入分成比例影响")
        
        # 计算各模式的理论收入分成
        mode_analysis = []
        for mode in ['mode_a', 'mode_b', 'mode_c']:
            luma_share = params['luma_share_from_student_payment'][mode]
            uni_price = params['uni_pricing'][mode]['base_price']
            conversion = params['student_paid_conversion_rates'][mode]
            
            mode_analysis.append({
                'mode': mode,
                'luma_student_share': luma_share,
                'uni_student_share': 1 - luma_share,
                'uni_price': uni_price,
                'student_conversion': conversion
            })
        
        mode_df = pd.DataFrame(mode_analysis)
        mode_df['mode_label'] = ['模式A', '模式B', '模式C']
        
        # 分成比例饼图
        fig2 = make_subplots(rows=1, cols=3, 
                            specs=[[{'type':'domain'}, {'type':'domain'}, {'type':'domain'}]],
                            subplot_titles=('模式A分成', '模式B分成', '模式C分成'))
        
        for i, (_, row) in enumerate(mode_df.iterrows()):
            if row['student_conversion'] > 0:  # 只显示有学生付费的模式
                fig2.add_trace(go.Pie(
                    labels=['Luma分成', '高校分成'],
                    values=[row['luma_student_share'], row['uni_student_share']],
                    name=f"模式{row['mode'][-1].upper()}"
                ), 1, i+1)
            else:
                fig2.add_trace(go.Pie(
                    labels=['无学生付费'],
                    values=[1],
                    name=f"模式{row['mode'][-1].upper()}"
                ), 1, i+1)
        
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        st.subheader("关键业务指标")
        
        # 显示关键指标对比
        metrics_data = []
        for _, row in mode_df.iterrows():
            metrics_data.append([
                row['mode_label'],
                f"¥{row['uni_price']:,}",
                f"{row['student_conversion']:.1%}",
                f"{row['luma_student_share']:.1%}",
                f"{row['uni_student_share']:.1%}"
            ])
        
        metrics_df = pd.DataFrame(metrics_data, columns=[
            '商业模式', '高校费用', '学生转化率', 'Luma学生分成', '高校学生分成'
        ])
        
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
        
        # 策略建议
        st.subheader("💡 策略建议")
        
        total_luma_revenue = results_df['luma_revenue_total'].sum()
        uni_revenue_ratio = results_df['luma_revenue_from_uni'].sum() / total_luma_revenue
        student_revenue_ratio = results_df['luma_revenue_from_student_share'].sum() / total_luma_revenue
        
        st.write("**收入结构分析**")
        st.write(f"• 高校收入占比: {uni_revenue_ratio:.1%}")
        st.write(f"• 学生分成占比: {student_revenue_ratio:.1%}")
        
        if uni_revenue_ratio > 0.7:
            st.info("🏫 当前模式以高校付费为主，建议关注高校续约率的提升")
        elif student_revenue_ratio > 0.4:
            st.info("🎓 学生付费贡献显著，建议优化学生付费体验和转化率")
        else:
            st.info("⚖️ 收入结构较为均衡，建议继续保持多元化策略")
    
    # 3. 敏感性分析
    st.subheader("📊 敏感性分析")
    
    # 参数敏感性分析（简化版）
    sensitivity_params = [
        'student_paid_conversion_rates',
        'uni_renewal_rates', 
        'per_use_pricing',
        'subscription_pricing'
    ]
    
    st.write("**关键参数影响分析**")
    
    current_revenue = results_df['luma_revenue_total'].sum()
    
    # 模拟参数变化对收入的影响
    sensitivity_results = []
    
    # 学生转化率 +/- 20%
    for delta in [-0.2, -0.1, 0.1, 0.2]:
        modified_params = params.copy()
        for mode in ['mode_b', 'mode_c']:
            original_rate = params['student_paid_conversion_rates'][mode]
            modified_params['student_paid_conversion_rates'][mode] = max(0, original_rate * (1 + delta))
        
        # 简化计算影响（实际应重新运行模型）
        estimated_impact = delta * student_revenue_ratio * current_revenue
        sensitivity_results.append({
            'parameter': f"学生转化率 {delta:+.0%}",
            'impact_amount': estimated_impact,
            'impact_percent': estimated_impact / current_revenue
        })
    
    # 续约率 +/- 10%
    for delta in [-0.1, -0.05, 0.05, 0.1]:
        estimated_impact = delta * uni_revenue_ratio * current_revenue * 0.5  # 简化估算
        sensitivity_results.append({
            'parameter': f"高校续约率 {delta:+.0%}",
            'impact_amount': estimated_impact,
            'impact_percent': estimated_impact / current_revenue
        })
    
    sensitivity_df = pd.DataFrame(sensitivity_results)
    sensitivity_df = sensitivity_df.sort_values('impact_amount', key=abs, ascending=False)
    
    # 敏感性分析图表
    fig3 = px.bar(sensitivity_df, x='parameter', y='impact_percent',
                  title="参数变化对总收入的影响",
                  labels={'impact_percent': '收入影响(%)', 'parameter': '参数变化'})
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)
    
    st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)