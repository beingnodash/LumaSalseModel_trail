"""
简化版商业模式分析页面
Simplified Business Model Analysis Page

特点：
1. 简化参数分类为7大类
2. 取消Type2的abc细分
3. 统一分成比例参数
4. 优化收入记账时间逻辑
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

from luma_sales_model.simplified_financial_model import LumaSimplifiedFinancialModel
from utils.simplified_parameter_ui import SimplifiedParameterUI

# 设置页面配置
st.set_page_config(
    page_title="简化版商业模式分析 - Luma高校销售与收益分析模型",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("⚡ 简化版商业模式分析")

# 添加详细的页面介绍
st.markdown("""
## 最新简化版商业模式架构

本页面采用全新简化的参数结构，使业务建模更加清晰和易用：

### 🎯 关键简化特性
- **统一商业模式**: 取消Type2的a/b/c细分，统一为模式B
- **清晰参数分类**: 7大类参数，逻辑清晰易懂
- **统一分成比例**: B/C模式共享同一个分成比例参数
- **优化记账逻辑**: 简化收入记账时间处理

### 📊 三种核心商业模式
- **🏫 模式A**: 高校付费 + 学生免费使用全部功能
- **🎓 模式B**: 高校付费 + 学生分层付费（统一分成比例）
- **💡 模式C**: 高校免费 + 学生分层付费（统一分成比例）

### 🔧 参数分类架构
1. **基础参数**: 模拟周期等全局参数
2. **价格参数**: 学生端和高校端的所有定价
3. **市场规模**: 新客户数量和学校规模
4. **市场分布**: 商业模式分布和付费转化率
5. **学生市场细分分布**: 付费方式和订阅期限选择
6. **续费率与复购率参数**: 各种续费和复购率
7. **分成比例**: 统一的Luma收入分成比例

### 💡 业务逻辑优化
- **收入记账**: 订阅收入按期限分摊，按次付费含复购当期折算
- **续约机制**: 高校3年续约，学生分别建模按次复购和订阅续费
- **分成统一**: B/C模式使用同一分成比例，符合实际业务逻辑
""", unsafe_allow_html=True)

# 初始化参数UI
param_ui = SimplifiedParameterUI()

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
    st.session_state.simplified_model_params = collected_params
    
    st.success("✅ 参数配置完成！请切换到「模型运行」标签页执行分析。")

with tab2:
    st.header("模型运行")
    
    if 'simplified_model_params' not in st.session_state:
        st.warning("⚠️ 请先在「参数配置」标签页设置参数。")
        st.stop()
    
    # 显示参数摘要
    with st.expander("📋 参数摘要", expanded=False):
        param_ui.display_parameter_summary(st.session_state.simplified_model_params)
    
    # 运行模型按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_model = st.button("⚡ 运行简化版财务模型", type="primary", use_container_width=True)
    
    if run_model:
        with st.spinner("正在运行简化版财务模型..."):
            try:
                # 创建模型实例
                model = LumaSimplifiedFinancialModel(st.session_state.simplified_model_params)
                
                # 运行模型
                results_df = model.run_model()
                
                # 保存结果
                st.session_state.simplified_model_results = results_df
                st.session_state.simplified_model_instance = model
                
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
                
                # 收入趋势图
                fig = px.line(results_df, x='period', 
                             y=['luma_revenue_total', 'uni_revenue_total', 'student_revenue_total'],
                             title="收入趋势总览",
                             labels={'value': '收入 (元)', 'period': '周期'})
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"模型运行出错: {str(e)}")
                st.exception(e)

with tab3:
    st.header("结果分析")
    
    if 'simplified_model_results' not in st.session_state:
        st.warning("⚠️ 请先在「模型运行」标签页运行模型。")
        st.stop()
    
    results_df = st.session_state.simplified_model_results
    model = st.session_state.simplified_model_instance
    
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
        
        # 统一分成比例
        sharing = business_summary['revenue_sharing']
        st.write("**统一学生分成比例**")
        st.write(f"Luma: {sharing['luma_share_from_student']:.1%}")
        st.write(f"高校: {1-sharing['luma_share_from_student']:.1%}")
    
    # 详细图表分析
    st.subheader("📈 详细收入分析")
    
    # 创建多维收入分析图表
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("收入趋势对比", "Luma收入构成", "学生收入分类", "关键业务指标"),
        specs=[[{"secondary_y": False}, {"type": "pie"}],
               [{"secondary_y": False}, {"secondary_y": True}]]
    )
    
    # 1. 收入趋势对比
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['luma_revenue_total'],
                  mode='lines+markers', name='Luma总收入', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['uni_revenue_total'],
                  mode='lines+markers', name='高校收入', line=dict(color='green')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['student_revenue_total'],
                  mode='lines+markers', name='学生收入', line=dict(color='red')),
        row=1, col=1
    )
    
    # 2. Luma收入构成饼图
    luma_revenue_sources = [
        '来自高校', '来自学生分成'
    ]
    luma_revenue_values = [
        results_df['luma_revenue_from_uni'].sum(),
        results_df['luma_revenue_from_student_share'].sum()
    ]
    
    fig.add_trace(
        go.Pie(labels=luma_revenue_sources, values=luma_revenue_values,
               name="Luma收入构成", hole=0.3),
        row=1, col=2
    )
    
    # 3. 学生收入分类
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['student_revenue_per_use'],
                  mode='lines', stackgroup='student', name='按次付费'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['student_revenue_subscription'],
                  mode='lines', stackgroup='student', name='订阅付费'),
        row=2, col=1
    )
    
    # 4. 关键业务指标（双轴）
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['active_universities'],
                  mode='lines+markers', name='活跃高校数', line=dict(color='navy')),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['total_paying_students'],
                  mode='lines+markers', name='付费学生数', line=dict(color='orange'), yaxis='y2'),
        row=2, col=2, secondary_y=True
    )
    
    fig.update_layout(height=800, title_text="简化版商业模式分析仪表板")
    st.plotly_chart(fig, use_container_width=True)
    
    # 详细数据表
    st.subheader("📊 详细财务数据")
    st.dataframe(results_df, use_container_width=True)
    
    # 下载数据
    csv = results_df.to_csv(index=False)
    st.download_button(
        label="📥 下载财务数据 (CSV)",
        data=csv,
        file_name=f"luma_simplified_financial_results.csv",
        mime="text/csv"
    )

with tab4:
    st.header("深度洞察")
    
    if 'simplified_model_results' not in st.session_state:
        st.warning("⚠️ 请先在「模型运行」标签页运行模型。")
        st.stop()
    
    results_df = st.session_state.simplified_model_results
    params = st.session_state.simplified_model_params
    
    # 商业模式影响分析
    st.subheader("🎯 商业模式影响分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("参数设置总览")
        
        # 显示关键参数设置
        dist = params['market_distribution']
        scale = params['market_scale']
        pricing = params['university_prices']
        sharing = params['revenue_sharing']
        
        # 创建参数对比表
        param_summary = pd.DataFrame({
            '参数类别': ['商业模式A占比', '商业模式B占比', '商业模式C占比',
                     'B/C学生转化率', '每半年新客户', '平均学校规模',
                     '模式A定价', '模式B定价', '统一分成比例(Luma)'],
            '参数值': [f"{dist['mode_a_ratio']:.1%}",
                     f"{dist['mode_b_ratio']:.1%}",
                     f"{dist['mode_c_ratio']:.1%}",
                     f"{dist['student_paid_conversion_rate_bc']:.1%}",
                     f"{scale['new_clients_per_half_year']} 所",
                     f"{scale['avg_students_per_uni']:,} 人",
                     f"¥{pricing['mode_a_price']:,.0f}",
                     f"¥{pricing['mode_b_price']:,.0f}",
                     f"{sharing['luma_share_from_student']:.1%}"]
        })
        
        st.dataframe(param_summary, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("收入结构分析")
        
        # 计算收入结构比例
        total_luma_revenue = results_df['luma_revenue_total'].sum()
        uni_revenue_from_luma = results_df['luma_revenue_from_uni'].sum()
        student_share_from_luma = results_df['luma_revenue_from_student_share'].sum()
        
        uni_ratio = uni_revenue_from_luma / total_luma_revenue if total_luma_revenue > 0 else 0
        student_ratio = student_share_from_luma / total_luma_revenue if total_luma_revenue > 0 else 0
        
        # 创建收入结构饼图
        revenue_structure = pd.DataFrame({
            '收入来源': ['高校付费', '学生分成'],
            '金额': [uni_revenue_from_luma, student_share_from_luma],
            '占比': [uni_ratio, student_ratio]
        })
        
        fig_structure = px.pie(revenue_structure, values='金额', names='收入来源',
                              title='Luma收入结构分布')
        st.plotly_chart(fig_structure, use_container_width=True)
        
        # 显示关键指标
        st.write("**关键收入指标**")
        st.write(f"• 高校付费占比: {uni_ratio:.1%}")
        st.write(f"• 学生分成占比: {student_ratio:.1%}")
        st.write(f"• 统一分成比例: {sharing['luma_share_from_student']:.1%}")
    
    # 业务策略建议
    st.subheader("💡 业务策略建议")
    
    # 基于收入结构提供建议
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**收入多元化程度**")
        if uni_ratio > 0.8:
            st.warning("🏫 收入主要依赖高校付费，建议：\n- 关注高校续约率提升\n- 考虑增加B/C模式比例")
        elif student_ratio > 0.6:
            st.info("🎓 学生分成贡献显著，建议：\n- 优化学生付费体验\n- 提升学生转化率")
        else:
            st.success("⚖️ 收入结构相对均衡，建议：\n- 保持当前模式分布\n- 持续优化各模式效率")
    
    with col2:
        st.write("**学生市场潜力**")
        conversion_rate = dist['student_paid_conversion_rate_bc']
        if conversion_rate < 0.05:
            st.warning("📈 学生转化率较低，建议：\n- 优化产品功能\n- 加强学生市场推广")
        elif conversion_rate > 0.15:
            st.success("🚀 学生转化率较高，建议：\n- 保持当前策略\n- 考虑提升定价")
        else:
            st.info("📊 学生转化率适中，建议：\n- 持续优化用户体验\n- 测试不同定价策略")
    
    with col3:
        st.write("**分成策略优化**")
        luma_share = sharing['luma_share_from_student']
        if luma_share < 0.3:
            st.info("🤝 Luma分成较低，有利于：\n- 吸引更多高校合作\n- 提升B/C模式接受度")
        elif luma_share > 0.6:
            st.warning("💰 Luma分成较高，需要：\n- 提供更多价值服务\n- 确保高校满意度")
        else:
            st.success("⚖️ 分成比例均衡，建议：\n- 保持当前策略\n- 根据市场反馈微调")
    
    # 参数敏感性分析
    st.subheader("📊 关键参数影响分析")
    
    # 简化的敏感性分析展示
    sensitivity_data = []
    
    # 分析学生转化率的影响
    base_student_revenue = results_df['student_revenue_total'].sum()
    conversion_impact = base_student_revenue * student_ratio  # 估算影响
    
    sensitivity_data.append({
        '参数': 'B/C学生转化率 +1%',
        '收入影响': conversion_impact * 0.1,  # 简化估算
        '影响百分比': '约 +10%学生收入'
    })
    
    # 分析分成比例的影响
    sharing_impact = student_share_from_luma * 0.1  # 分成比例变化10%的影响
    sensitivity_data.append({
        '参数': 'Luma分成比例 +5%',
        '收入影响': sharing_impact,
        '影响百分比': f'约 +{sharing_impact/total_luma_revenue:.1%}总收入'
    })
    
    # 分析新客户获取的影响
    uni_impact = uni_revenue_from_luma / scale['new_clients_per_half_year']  # 单客户价值
    sensitivity_data.append({
        '参数': '每半年新客户 +1所',
        '收入影响': uni_impact,
        '影响百分比': f'约 +{uni_impact/total_luma_revenue:.1%}总收入'
    })
    
    sensitivity_df = pd.DataFrame(sensitivity_data)
    st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)
    
    st.info("💡 **说明**: 以上敏感性分析为简化估算，实际影响可能因参数间相互作用而有所不同。建议通过调整参数重新运行模型来获得精确结果。")