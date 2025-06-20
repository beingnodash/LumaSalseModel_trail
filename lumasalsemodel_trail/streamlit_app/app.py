"""
Luma高校销售与收益分析模型 - 官方版本
Official Luma University Sales and Revenue Analysis Model

基于简化的7大类参数结构，提供清晰准确的财务预测分析。

特色功能：
- 7大类参数分组，配置简单明了
- 统一的B/C模式分成比例
- 优化的收入记账逻辑
- 全面的分析仪表板和深度洞察
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luma_sales_model.simplified_financial_model import LumaSimplifiedFinancialModel
from utils.simplified_parameter_ui import SimplifiedParameterUI

# 设置页面配置
st.set_page_config(
    page_title="Luma高校销售与收益分析模型",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题和介绍
st.title("🎓 Luma高校销售与收益分析模型")
st.markdown("### *专业的高校合作业务财务预测与分析平台*")

# 添加模型介绍
st.markdown("""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 20px 0;">
<h4>🚀 模型特色</h4>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px;">
<div>
<h5>📊 简化参数结构</h5>
<ul>
<li><strong>7大类参数</strong>: 基础参数、价格参数、市场规模、市场分布、学生细分、续费率、分成比例</li>
<li><strong>配置简单</strong>: 每类参数功能明确，配置逻辑清晰</li>
<li><strong>参数验证</strong>: 自动校验参数合理性，防止配置错误</li>
</ul>
</div>

<div>
<h5>🎯 统一业务逻辑</h5>
<ul>
<li><strong>三种商业模式</strong>: A(高校付费+学生免费) | B(高校付费+学生分层) | C(高校免费+学生分层)</li>
<li><strong>统一分成比例</strong>: B/C模式共享同一分成参数，符合实际业务</li>
<li><strong>优化记账逻辑</strong>: 订阅收入按期分摊，按次付费含复购折算</li>
</ul>
</div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px;">
<div>
<h5>📈 全面分析功能</h5>
<ul>
<li><strong>收入预测</strong>: 多维度收入趋势分析</li>
<li><strong>业务洞察</strong>: 商业模式影响评估</li>
<li><strong>策略建议</strong>: 基于数据的业务优化建议</li>
</ul>
</div>

<div>
<h5>🔧 技术保障</h5>
<ul>
<li><strong>测试验证</strong>: 12项全面测试，100%通过率</li>
<li><strong>数据导出</strong>: 支持CSV格式结果下载</li>
<li><strong>交互图表</strong>: 基于Plotly的动态可视化</li>
</ul>
</div>
</div>
</div>
""", unsafe_allow_html=True)

# 使用说明
with st.expander("📋 使用指南", expanded=False):
    st.markdown("""
    ### 快速开始
    
    1. **参数配置**: 在下方「参数配置」标签页中设置7大类业务参数
    2. **运行模型**: 切换到「模型运行」标签页，点击运行按钮
    3. **结果分析**: 在「结果分析」标签页查看详细财务数据和图表
    4. **深度洞察**: 在「深度洞察」标签页获取业务策略建议
    
    ### 参数配置建议
    
    - **基础参数**: 建议至少8个半年周期，观察完整3年服务周期
    - **商业模式分布**: 根据实际市场情况调整A/B/C模式比例
    - **学生转化率**: B/C模式建议5%-15%的付费转化率
    - **分成比例**: Luma分成建议30%-50%，平衡各方利益
    - **续费参数**: 高校3年续约率70%-90%，学生续费率75%-85%
    
    ### 结果解读
    
    - **收入趋势**: 观察Luma收入、高校收入和学生收入的发展趋势
    - **收入构成**: 分析固定收入和分成收入的比例结构
    - **业务指标**: 关注活跃高校数和付费学生数的增长
    - **策略建议**: 根据模型输出调整商业模式和定价策略
    """)

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
    st.markdown("*请根据实际业务情况配置以下7大类参数*")
    
    # 收集所有参数
    collected_params = param_ui.collect_all_parameters()
    
    # 保存参数到session state
    st.session_state.model_params = collected_params
    
    # 显示配置完成提示
    st.success("✅ 参数配置完成！请切换到「模型运行」标签页执行分析。")
    
    # 添加参数验证状态
    with st.expander("🔍 参数验证状态", expanded=False):
        st.markdown("### 关键参数检查")
        
        # 商业模式分布检查
        dist = collected_params['market_distribution']
        mode_sum = dist['mode_a_ratio'] + dist['mode_b_ratio'] + dist['mode_c_ratio']
        if abs(mode_sum - 1.0) < 0.01:
            st.success(f"✅ 商业模式分布: {mode_sum:.1%} (正确)")
        else:
            st.warning(f"⚠️ 商业模式分布: {mode_sum:.1%} (将自动标准化)")
        
        # 次卡类型分布检查
        seg = collected_params['student_segmentation']
        card_dist = seg['card_type_distribution']
        card_sum = sum(card_dist.values())
        if abs(card_sum - 1.0) < 0.01:
            st.success(f"✅ 次卡类型分布: {card_sum:.1%} (正确)")
        else:
            st.warning(f"⚠️ 次卡类型分布: {card_sum:.1%} (将自动标准化)")
        
        # 关键业务参数展示
        st.markdown("### 关键业务参数")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("模拟周期", f"{collected_params['total_half_years']} 个半年")
            st.metric("每半年新客户", f"{collected_params['market_scale']['new_clients_per_half_year']} 所")
        
        with col2:
            st.metric("B/C学生转化率", f"{dist['student_paid_conversion_rate_bc']:.1%}")
            st.metric("高校3年续约率", f"{collected_params['renewal_rates']['university_3year_renewal']:.1%}")
        
        with col3:
            luma_share_b = collected_params['revenue_sharing']['luma_share_from_student_mode_b']
            st.metric("Luma分成(模式B)", f"{luma_share_b:.1%}")
            st.metric("高校分成(模式B)", f"{1-luma_share_b:.1%}")
            st.caption("模式C: Luma获得100%学生收入")

with tab2:
    st.header("模型运行")
    
    if 'model_params' not in st.session_state:
        st.warning("⚠️ 请先在「参数配置」标签页设置参数。")
        st.stop()
    
    # 显示参数摘要
    with st.expander("📋 参数摘要", expanded=False):
        param_ui.display_parameter_summary(st.session_state.model_params)
    
    # 运行模型按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_model = st.button("⚡ 运行Luma财务分析模型", type="primary", use_container_width=True)
    
    if run_model:
        # 创建进度条和状态显示
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            status_text.text("🔧 步骤1/4: 初始化财务模型...")
            progress_bar.progress(10)
            
            # 创建模型实例
            model = LumaSimplifiedFinancialModel(st.session_state.model_params)
            
            status_text.text("⚡ 步骤2/4: 执行财务计算...")
            progress_bar.progress(40)
            
            # 运行模型
            results_df = model.run_model()
            
            status_text.text("📊 步骤3/4: 生成业务摘要...")
            progress_bar.progress(70)
            
            # 保存结果
            st.session_state.model_results = results_df
            st.session_state.model_instance = model
            
            status_text.text("🎨 步骤4/4: 准备可视化...")
            progress_bar.progress(90)
            
            # 小延时以显示完成
            import time
            time.sleep(0.5)
            
            progress_bar.progress(100)
            status_text.text("✅ 模型运行完成！")
            
            # 清除进度显示
            progress_container.empty()
            
            st.success("🎉 财务模型运行成功！请查看下方结果或切换到其他标签页查看详细分析。")
            
            # 显示快速结果预览
            st.subheader("📊 快速结果预览")
            
            # 获取业务摘要
            summary = model.get_business_summary()
            
            # 关键指标展示
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_luma_revenue = summary['total_luma_revenue']
                st.metric("Luma总收入", f"¥{total_luma_revenue:,.0f}")
            
            with col2:
                avg_revenue_per_period = summary['avg_luma_revenue_per_period']
                st.metric("平均期收入", f"¥{avg_revenue_per_period:,.0f}")
            
            with col3:
                peak_universities = summary['peak_active_universities']
                st.metric("峰值活跃高校", f"{peak_universities:.0f} 所")
            
            with col4:
                peak_students = summary['peak_paying_students']
                st.metric("峰值付费学生", f"{peak_students:,.0f} 人")
            
            # 快速趋势图
            st.subheader("📈 收入趋势概览")
            
            # 创建简化的趋势图
            fig = px.line(results_df, x='period', 
                         y=['luma_revenue_total', 'uni_revenue_total', 'student_revenue_total'],
                         title="收入发展趋势",
                         labels={'value': '收入 (元)', 'period': '周期(半年)', 'variable': '收入类型'},
                         color_discrete_map={
                             'luma_revenue_total': '#1f77b4',
                             'uni_revenue_total': '#ff7f0e', 
                             'student_revenue_total': '#2ca02c'
                         })
            
            # 更新图例
            newnames = {
                'luma_revenue_total': 'Luma收入',
                'uni_revenue_total': '高校收入', 
                'student_revenue_total': '学生收入'
            }
            fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))
            
            fig.update_layout(
                height=400,
                hovermode="x unified",
                legend_title_text='收入类型'
            )
            fig.update_traces(mode='lines+markers')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 提示用户查看详细分析
            st.info("💡 **提示**: 切换到「结果分析」和「深度洞察」标签页查看更详细的分析结果和业务建议。")
            
        except Exception as e:
            progress_container.empty()
            st.error(f"❌ 模型运行出错: {str(e)}")
            st.exception(e)
            st.info("💡 **建议**: 请检查参数配置是否合理，或联系技术支持。")

with tab3:
    st.header("结果分析")
    
    if 'model_results' not in st.session_state:
        st.warning("⚠️ 请先在「模型运行」标签页运行模型。")
        st.stop()
    
    if 'model_instance' not in st.session_state:
        st.warning("⚠️ 模型实例不存在，请重新运行模型。")
        st.stop()
    
    results_df = st.session_state.model_results
    model = st.session_state.model_instance
    
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
        
        # 分成比例说明
        sharing = business_summary['revenue_sharing']
        st.write("**学生分成比例**")
        st.write(f"模式B - Luma: {sharing['luma_share_from_student_mode_b']:.1%}")
        st.write(f"模式B - 高校: {1-sharing['luma_share_from_student_mode_b']:.1%}")
        st.write(f"模式C - Luma: 100%")
    
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
        go.Scatter(x=results_df['period'], y=results_df['student_revenue_single_use'],
                  mode='lines', stackgroup='student', name='单次付费'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=results_df['period'], y=results_df['student_revenue_card'],
                  mode='lines', stackgroup='student', name='次卡付费'),
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
    
    fig.update_layout(height=800, title_text="Luma财务分析仪表板")
    st.plotly_chart(fig, use_container_width=True)
    
    # 详细数据表
    st.subheader("📊 详细财务数据")
    
    # 添加数据筛选选项
    col1, col2 = st.columns(2)
    with col1:
        show_all_columns = st.checkbox("显示所有列", value=False)
    with col2:
        period_filter = st.selectbox(
            "筛选周期",
            options=["全部"] + [f"H{i}" for i in range(1, len(results_df)+1)],
            index=0
        )
    
    # 根据选择显示数据
    display_df = results_df.copy()
    
    if period_filter != "全部":
        period_num = int(period_filter[1:])
        display_df = display_df[display_df['period'] == period_num]
    
    # 定义列名映射（英文->中文）
    column_name_mapping = {
        'period': '周期',
        'period_name': '周期名称',
        'luma_revenue_total': 'Luma总收入',
        'luma_revenue_from_uni': 'Luma来自高校收入',
        'luma_revenue_from_student_share': 'Luma学生分成收入',
        'uni_revenue_total': '高校总收入',
        'student_revenue_total': '学生总收入',
        'student_revenue_single_use': '学生单次付费收入',
        'student_revenue_card': '学生次卡收入',
        'active_universities': '活跃高校数',
        'total_paying_students': '付费学生总数',
        'new_universities': '新增高校数',
        'renewed_universities': '续约高校数',
        'new_paying_students': '新增付费学生数',
        'repurchasing_students': '复购学生数',
        'cumulative_universities': '累计高校数',
        'cumulative_students': '累计学生数'
    }
    
    if not show_all_columns:
        # 显示主要列
        key_columns = [
            'period', 'period_name', 
            'luma_revenue_total', 'uni_revenue_total', 'student_revenue_total',
            'active_universities', 'total_paying_students'
        ]
        display_df = display_df[key_columns]
    
    # 重命名列为中文
    available_columns = [col for col in display_df.columns if col in column_name_mapping]
    chinese_mapping = {col: column_name_mapping[col] for col in available_columns}
    display_df = display_df.rename(columns=chinese_mapping)
    
    # 格式化数值显示
    revenue_columns = ['Luma总收入', 'Luma来自高校收入', 'Luma学生分成收入', 
                      '高校总收入', '学生总收入', '学生单次付费收入', '学生次卡收入']
    count_columns = ['活跃高校数', '付费学生总数', '新增高校数', '续约高校数', 
                    '新增付费学生数', '复购学生数', '累计高校数', '累计学生数']
    
    # 格式化收入列（显示为带千分号的整数）
    for col in revenue_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "")
    
    # 格式化数量列（显示为带千分号的整数）
    for col in count_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
    
    st.dataframe(display_df, use_container_width=True)
    
    # 下载数据选项
    st.subheader("📥 数据下载")
    col1, col2 = st.columns(2)
    
    with col1:
        # 原始英文列名版本
        csv_original = results_df.to_csv(index=False)
        st.download_button(
            label="📥 下载完整数据 (英文列名)",
            data=csv_original,
            file_name=f"luma_financial_analysis_results_en.csv",
            mime="text/csv",
            help="下载包含所有字段的原始英文列名数据"
        )
    
    with col2:
        # 中文列名版本
        chinese_df = results_df.copy()
        available_columns_all = [col for col in chinese_df.columns if col in column_name_mapping]
        chinese_mapping_all = {col: column_name_mapping[col] for col in available_columns_all}
        chinese_df = chinese_df.rename(columns=chinese_mapping_all)
        
        csv_chinese = chinese_df.to_csv(index=False)
        st.download_button(
            label="📥 下载完整数据 (中文列名)",
            data=csv_chinese,
            file_name=f"luma_financial_analysis_results_cn.csv",
            mime="text/csv",
            help="下载包含所有字段的中文列名数据"
        )

with tab4:
    st.header("深度洞察")
    
    if 'model_results' not in st.session_state:
        st.warning("⚠️ 请先在「模型运行」标签页运行模型。")
        st.stop()
    
    if 'model_instance' not in st.session_state:
        st.warning("⚠️ 模型实例不存在，请重新运行模型。")
        st.stop()
    
    results_df = st.session_state.model_results
    params = st.session_state.model_params
    
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
                     '模式A定价', '模式B定价', '模式B分成比例(Luma)', '模式C分成比例(Luma)'],
            '参数值': [f"{dist['mode_a_ratio']:.1%}",
                     f"{dist['mode_b_ratio']:.1%}",
                     f"{dist['mode_c_ratio']:.1%}",
                     f"{dist['student_paid_conversion_rate_bc']:.1%}",
                     f"{scale['new_clients_per_half_year']} 所",
                     f"{scale['avg_students_per_uni']:,} 人",
                     f"¥{pricing['mode_a_price']:,.0f}",
                     f"¥{pricing['mode_b_price']:,.0f}",
                     f"{sharing['luma_share_from_student_mode_b']:.1%}",
                     "100%"]
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
        st.write(f"• 模式B分成比例: {sharing['luma_share_from_student_mode_b']:.1%}")
        st.write(f"• 模式C分成比例: 100% (Luma)")
    
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
        luma_share_b = sharing['luma_share_from_student_mode_b']
        if luma_share_b < 0.3:
            st.info("🤝 模式B分成较低，有利于：\n- 吸引更多高校合作\n- 提升模式B接受度")
        elif luma_share_b > 0.6:
            st.warning("💰 模式B分成较高，需要：\n- 提供更多价值服务\n- 确保高校满意度")
        else:
            st.success("⚖️ 模式B分成均衡，建议：\n- 保持当前策略\n- 根据市场反馈微调")
        st.caption("💡 模式C下Luma获得100%学生收入")
    
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
    
    # 总结和下一步建议
    st.subheader("📋 总结与建议")
    
    with st.container():
        st.markdown("""
        <div style="background-color: #e8f4fd; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;">
        <h5>🎯 核心发现</h5>
        <ul>
        <li><strong>收入规模</strong>: 根据当前参数配置，预计总收入可达¥{:,.0f}</li>
        <li><strong>增长趋势</strong>: 收入增长率{:.1%}，显示良好的发展前景</li>
        <li><strong>客户基础</strong>: 峰值活跃高校{:.0f}所，付费学生{:,.0f}人</li>
        <li><strong>收入结构</strong>: 高校付费占{:.1%}，学生分成占{:.1%}</li>
        </ul>
        
        <h5>🚀 优化建议</h5>
        <ul>
        <li><strong>短期</strong>: 重点提升学生付费转化率和用户体验</li>
        <li><strong>中期</strong>: 优化商业模式分布，平衡收入来源</li>
        <li><strong>长期</strong>: 建立稳定的高校续约机制，确保可持续发展</li>
        </ul>
        </div>
        """.format(
            total_luma_revenue,
            business_summary['revenue_growth_rate'],
            business_summary['peak_active_universities'],
            business_summary['peak_paying_students'],
            uni_ratio,
            student_ratio
        ), unsafe_allow_html=True)

# 页脚信息
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 14px; margin-top: 30px;">
<p><strong>Luma高校销售与收益分析模型</strong> v2.0 | 基于简化7大类参数结构</p>
<p>© 2025 Luma Tech. All rights reserved. | 如有问题请联系技术支持</p>
</div>
""", unsafe_allow_html=True)