"""
增强版敏感性分析页面
Enhanced Sensitivity Analysis Page

基于简化版7大类参数结构的高级敏感性分析功能：
- 单参数敏感性分析
- 多参数敏感性分析  
- 参数重要性排序
- 业务洞察生成
- 交互式可视化
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
from utils.enhanced_sensitivity_analysis import EnhancedSensitivityAnalyzer
from utils.sensitivity_parameter_ui import SensitivityParameterUI

# 设置页面配置
st.set_page_config(
    page_title="增强版敏感性分析 - Luma高校销售与收益分析模型",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("🔍 增强版敏感性分析")
st.markdown("### *基于简化版7大类参数结构的高级敏感性分析*")

# 功能介绍
st.markdown("""
<div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
<h4>🚀 增强版特色功能</h4>

<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 15px;">
<div>
<h5>📊 智能参数分析</h5>
<ul>
<li><strong>7大类参数支持</strong>: 完整覆盖简化版参数结构</li>
<li><strong>自定义测试范围</strong>: 灵活设置参数变化区间</li>
<li><strong>批量参数分析</strong>: 同时分析多个参数影响</li>
</ul>
</div>

<div>
<h5>🎯 深度业务洞察</h5>
<ul>
<li><strong>参数重要性排序</strong>: 识别关键影响因子</li>
<li><strong>相关性分析</strong>: 发现参数间关联关系</li>
<li><strong>业务策略建议</strong>: 基于数据的决策支持</li>
</ul>
</div>

<div>
<h5>📈 高级可视化</h5>
<ul>
<li><strong>交互式图表</strong>: Plotly动态可视化</li>
<li><strong>多维度展示</strong>: 参数-结果关系分析</li>
<li><strong>结果导出</strong>: 支持CSV数据下载</li>
</ul>
</div>
</div>
</div>
""", unsafe_allow_html=True)

# 使用说明
with st.expander("📋 使用指南", expanded=False):
    st.markdown("""
    ### 🎯 敏感性分析的价值
    
    敏感性分析帮助您理解：
    - **哪些参数对业务结果影响最大**
    - **参数变化的风险和机会**
    - **如何优化参数配置以最大化收益**
    - **业务模式的稳健性和脆弱性**
    
    ### 📊 三种分析类型
    
    1. **单参数敏感性分析**
       - 分析单个参数变化对结果的影响
       - 适合深入了解关键参数的作用机制
       - 生成详细的参数-结果关系图
    
    2. **多参数敏感性分析**
       - 同时分析多个参数的影响效果
       - 适合对比不同参数的相对重要性
       - 识别参数间的相互作用
    
    3. **参数重要性排序**
       - 识别对结果影响最大的关键参数
       - 提供参数优化的优先级指导
       - 生成基于数据的业务策略建议
    
    ### 🔧 操作步骤
    
    1. **选择分析类型**: 根据需求选择单参数、多参数或重要性分析
    2. **配置参数**: 选择要分析的参数和测试范围
    3. **选择指标**: 选择要观察的业务结果指标
    4. **运行分析**: 点击运行按钮开始分析
    5. **查看结果**: 分析图表、数据表和业务建议
    """)

# 检查基础参数
if 'model_params' not in st.session_state or not st.session_state.model_params:
    st.error("""
    ❌ **缺少基础参数配置**
    
    请先在主页面配置并运行模型，然后再进行敏感性分析。
    
    💡 **如何操作**:
    1. 返回主页面
    2. 在「参数配置」标签页设置7大类参数
    3. 在「模型运行」标签页运行模型
    4. 再回到此页面进行敏感性分析
    """)
    st.stop()

# 初始化UI组件
try:
    param_ui = SensitivityParameterUI(st.session_state.model_params)
except Exception as e:
    st.error(f"初始化参数UI失败: {str(e)}")
    st.stop()

# 显示当前基础参数
with st.expander("📋 当前基础参数配置", expanded=False):
    st.markdown("*这些是您在主页面设置的基础参数，敏感性分析将基于这些参数进行*")
    
    # 格式化显示基础参数
    base_params = st.session_state.model_params
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 业务配置")
        st.write(f"**模拟周期**: {base_params['total_half_years']} 个半年")
        st.write(f"**每半年新客户**: {base_params['market_scale']['new_clients_per_half_year']} 所")
        st.write(f"**平均学校规模**: {base_params['market_scale']['avg_students_per_uni']:,} 人")
        
        dist = base_params['market_distribution']
        st.write(f"**商业模式分布**: A({dist['mode_a_ratio']:.1%}) | B({dist['mode_b_ratio']:.1%}) | C({dist['mode_c_ratio']:.1%})")
    
    with col2:
        st.subheader("💰 关键参数")
        prices = base_params['university_prices']
        st.write(f"**模式A定价**: ¥{prices['mode_a_price']:,.0f}")
        st.write(f"**模式B定价**: ¥{prices['mode_b_price']:,.0f}")
        
        sharing = base_params['revenue_sharing']
        st.write(f"**模式B Luma分成**: {sharing['luma_share_from_student_mode_b']:.1%}")
        st.write(f"**模式C Luma分成**: 100%")
        
        renewal = base_params['renewal_rates']
        st.write(f"**高校续约率**: {renewal['university_3year_renewal']:.1%}")

# 主要分析区域
st.markdown("---")

# 第一步：选择分析类型
analysis_type = param_ui.render_analysis_type_selection()

st.markdown("---")

# 初始化变量
param_key = None
test_values = []
param_configs = {}

# 第二步：根据分析类型配置参数
if analysis_type == "single":
    # 单参数分析
    param_key, test_values, use_custom = param_ui.render_single_parameter_controls()
    param_configs = {param_key: {'values': test_values}} if test_values else {}
    
elif analysis_type == "multi":
    # 多参数分析
    param_configs = param_ui.render_multi_parameter_controls()
    
elif analysis_type == "importance":
    # 重要性分析 - 使用预设的关键参数
    st.subheader("📊 参数重要性分析设置")
    st.markdown("""
    **参数重要性分析**将自动选择7大类参数中的关键参数进行分析，
    识别对业务结果影响最大的参数，并提供优化建议。
    """)
    
    # 预设重要参数
    key_params = [
        'new_clients_per_half_year',
        'student_paid_conversion_rate_bc', 
        'university_3year_renewal',
        'luma_share_from_student_mode_b',
        'mode_a_price',
        'single_use_ratio',
        'price_single_use',
        'price_5_times_card'
    ]
    
    param_configs = {}
    for param in key_params:
        if param in param_ui.parameter_definitions:
            param_configs[param] = {'values': None}  # 使用默认值
    
    st.success(f"✅ 已选择 {len(param_configs)} 个关键参数进行重要性分析")

# 第三步：选择输出指标
st.markdown("---")
output_metrics = param_ui.render_output_metrics_selection(analysis_type)

# 第四步：分析设置
st.markdown("---")
analysis_settings = param_ui.render_analysis_settings()

# 第五步：显示配置摘要
if param_configs and output_metrics:
    st.markdown("---")
    param_ui.display_parameter_summary(
        analysis_type=analysis_type,
        param_key=param_key,
        test_values=test_values if analysis_type == "single" else None,
        param_configs=param_configs,
        output_metrics=output_metrics,
        analysis_settings=analysis_settings
    )

# 第六步：运行分析
st.markdown("---")
st.subheader("⚡ 运行敏感性分析")

# 检查配置完整性
has_params = bool(param_configs)
has_metrics = bool(output_metrics)
can_run = has_params and has_metrics

if not can_run:
    if not has_params:
        st.warning("⚠️ 请先配置要分析的参数")
    if not has_metrics:
        st.warning("⚠️ 请先选择要观察的输出指标")

# 运行按钮
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_analysis = st.button(
        "🚀 开始敏感性分析",
        disabled=not can_run,
        type="primary",
        use_container_width=True
    )

# 运行分析
if run_analysis and can_run:
    # 创建分析器
    analyzer = EnhancedSensitivityAnalyzer(st.session_state.model_params)
    
    # 进度显示
    if analysis_settings.get('show_progress', True):
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
    
    try:
        if analysis_settings.get('show_progress', True):
            status_text.text("🔧 步骤1/4: 初始化分析器...")
            progress_bar.progress(10)
        
        # 运行分析
        if analysis_type == "single":
            if analysis_settings.get('show_progress', True):
                status_text.text("⚡ 步骤2/4: 运行单参数敏感性分析...")
                progress_bar.progress(30)
            
            results_df = analyzer.run_single_parameter_analysis(
                param_key=param_key,
                model_class=LumaSimplifiedFinancialModel,
                test_values=test_values,
                output_metrics=output_metrics
            )
            
            # 保存结果
            st.session_state.sensitivity_results = {param_key: results_df}
            st.session_state.sensitivity_type = "single"
            st.session_state.sensitivity_param = param_key
            
        elif analysis_type == "multi":
            if analysis_settings.get('show_progress', True):
                status_text.text("⚡ 步骤2/4: 运行多参数敏感性分析...")
                progress_bar.progress(30)
            
            results = analyzer.run_multi_parameter_analysis(
                param_configs=param_configs,
                model_class=LumaSimplifiedFinancialModel,
                output_metrics=output_metrics
            )
            
            # 保存结果
            st.session_state.sensitivity_results = results
            st.session_state.sensitivity_type = "multi"
            
        elif analysis_type == "importance":
            if analysis_settings.get('show_progress', True):
                status_text.text("⚡ 步骤2/4: 运行参数重要性分析...")
                progress_bar.progress(30)
            
            results = analyzer.run_multi_parameter_analysis(
                param_configs=param_configs,
                model_class=LumaSimplifiedFinancialModel,
                output_metrics=output_metrics
            )
            
            # 计算重要性
            if analysis_settings.get('show_progress', True):
                status_text.text("📊 步骤3/4: 计算参数重要性...")
                progress_bar.progress(60)
            
            importance_df = analyzer.calculate_parameter_importance(
                results=results,
                target_metric=output_metrics[0]  # 使用第一个指标作为目标
            )
            
            # 保存结果
            st.session_state.sensitivity_results = results
            st.session_state.sensitivity_importance = importance_df
            st.session_state.sensitivity_type = "importance"
        
        if analysis_settings.get('show_progress', True):
            status_text.text("🎨 步骤4/4: 准备可视化...")
            progress_bar.progress(90)
            
            # 完成
            progress_bar.progress(100)
            status_text.text("✅ 敏感性分析完成！")
            
            # 清除进度显示
            progress_container.empty()
        
        st.success("🎉 敏感性分析运行成功！请查看下方结果。")
        
    except Exception as e:
        if analysis_settings.get('show_progress', True):
            progress_container.empty()
        st.error(f"❌ 敏感性分析出错: {str(e)}")
        st.exception(e)

# 显示分析结果
if 'sensitivity_results' in st.session_state and st.session_state.sensitivity_results is not None:
    st.markdown("---")
    st.header("📊 敏感性分析结果")
    
    results = st.session_state.sensitivity_results
    analysis_type = st.session_state.get('sensitivity_type', 'single')
    
    if analysis_type == "single":
        # 单参数分析结果
        param_key = st.session_state.get('sensitivity_param')
        if param_key and param_key in results:
            results_df = results[param_key]
            param_def = param_ui.parameter_definitions[param_key]
            
            st.subheader(f"📈 {param_def['name']} 敏感性分析")
            st.markdown(f"*{param_def['description']}*")
            
            # 创建可视化
            if analysis_settings.get('detailed_charts', True):
                for metric in output_metrics:
                    if metric in results_df.columns:
                        # 创建图表
                        fig = px.line(
                            results_df,
                            x=param_key,
                            y=metric,
                            markers=True,
                            title=f"{param_def['name']} vs {metric}",
                            labels={
                                param_key: f"{param_def['name']} ({param_def['unit']})",
                                metric: metric
                            }
                        )
                        
                        fig.update_layout(
                            height=400,
                            hovermode="x unified"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 简单的结果解读
                        min_val = results_df[metric].min()
                        max_val = results_df[metric].max()
                        change_pct = ((max_val - min_val) / min_val * 100) if min_val > 0 else 0
                        
                        if change_pct > 10:
                            impact_level = "显著影响"
                            color = "🔴"
                        elif change_pct > 5:
                            impact_level = "中等影响"
                            color = "🟡"
                        else:
                            impact_level = "较小影响"
                            color = "🟢"
                        
                        st.info(f"{color} **影响评估**: {param_def['name']}的变化对{metric}有{impact_level}，变化幅度约{change_pct:.1f}%")
            
            # 显示数据表
            st.subheader("📋 详细数据")
            st.dataframe(results_df, use_container_width=True)
            
            # 导出功能
            if analysis_settings.get('export_results', True):
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 下载分析结果 (CSV)",
                    data=csv,
                    file_name=f"sensitivity_analysis_{param_key}.csv",
                    mime="text/csv"
                )
    
    elif analysis_type == "multi":
        # 多参数分析结果
        st.subheader("📊 多参数对比分析")
        
        # 创建对比图表
        if analysis_settings.get('detailed_charts', True):
            for metric in output_metrics:
                # 创建子图
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=[f"{param_ui.parameter_definitions[param]['name']}" 
                                  for param in list(results.keys())[:4]],
                    vertical_spacing=0.12
                )
                
                row_col_positions = [(1,1), (1,2), (2,1), (2,2)]
                
                for i, (param_key, result_df) in enumerate(list(results.items())[:4]):
                    if metric in result_df.columns:
                        row, col = row_col_positions[i]
                        
                        fig.add_trace(
                            go.Scatter(
                                x=result_df[param_key],
                                y=result_df[metric],
                                mode='lines+markers',
                                name=param_ui.parameter_definitions[param_key]['name'],
                                showlegend=False
                            ),
                            row=row, col=col
                        )
                
                fig.update_layout(
                    height=600,
                    title_text=f"多参数对{metric}的影响对比"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # 显示各参数结果摘要
        st.subheader("📋 参数影响摘要")
        
        summary_data = []
        target_metric = output_metrics[0]  # 使用第一个指标
        
        for param_key, result_df in results.items():
            if target_metric in result_df.columns and len(result_df) > 1:
                param_def = param_ui.parameter_definitions[param_key]
                values = result_df[target_metric]
                
                min_val = values.min()
                max_val = values.max()
                change_rate = (max_val - min_val) / min_val if min_val > 0 else 0
                
                summary_data.append({
                    '参数名称': param_def['name'],
                    '参数类别': param_def['category'],
                    '影响幅度': f"{change_rate:.1%}",
                    '最小值': f"{min_val:,.0f}",
                    '最大值': f"{max_val:,.0f}",
                    '平均值': f"{values.mean():,.0f}"
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    elif analysis_type == "importance":
        # 重要性分析结果
        importance_df = st.session_state.get('sensitivity_importance')
        
        if importance_df is not None and len(importance_df) > 0:
            st.subheader("🏆 参数重要性排序")
            
            # 重要性排序图表
            if analysis_settings.get('detailed_charts', True):
                fig = px.bar(
                    importance_df.head(8),
                    x='重要性得分',
                    y='参数',
                    orientation='h',
                    color='重要性得分',
                    title="参数重要性排序 (前8名)",
                    color_continuous_scale='viridis'
                )
                
                fig.update_layout(
                    height=500,
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # 显示重要性数据表
            st.subheader("📊 详细重要性分析")
            
            # 格式化显示
            display_df = importance_df.copy()
            display_df['影响幅度'] = display_df['变化幅度'].apply(lambda x: f"{x:.1%}")
            display_df['变异系数'] = display_df['变异系数'].apply(lambda x: f"{x:.3f}")
            display_df['相关系数'] = display_df['相关系数'].apply(lambda x: f"{x:.3f}")
            display_df['重要性得分'] = display_df['重要性得分'].apply(lambda x: f"{x:.4f}")
            
            # 选择显示列
            display_columns = ['参数', '参数类别', '重要性得分', '影响幅度', '相关系数']
            st.dataframe(display_df[display_columns], use_container_width=True, hide_index=True)
            
            # 生成业务洞察
            if analysis_settings.get('generate_insights', True):
                st.subheader("💡 业务洞察与建议")
                
                analyzer = EnhancedSensitivityAnalyzer(st.session_state.model_params)
                insights = analyzer.generate_business_insights(
                    importance_df=importance_df,
                    target_metric=output_metrics[0]
                )
                
                for insight in insights:
                    st.markdown(insight)
            
            # 导出功能
            if analysis_settings.get('export_results', True):
                csv = importance_df.to_csv(index=False)
                st.download_button(
                    label="📥 下载重要性分析结果 (CSV)",
                    data=csv,
                    file_name="parameter_importance_analysis.csv",
                    mime="text/csv"
                )
    
    # 通用业务建议
    st.subheader("🎯 通用优化建议")
    st.markdown("""
    <div style="background-color: #f0f9ff; padding: 20px; border-radius: 10px; border-left: 5px solid #0ea5e9;">
    <h5>📈 基于敏感性分析的业务优化建议</h5>
    <ul>
    <li><strong>优先优化高影响参数</strong>: 重点关注敏感性最高的参数，小幅改善可能带来显著收益</li>
    <li><strong>风险管理</strong>: 对于负相关的重要参数，建立监控机制防止不利变化</li>
    <li><strong>A/B测试</strong>: 对关键参数进行小范围测试，验证敏感性分析的预测</li>
    <li><strong>组合优化</strong>: 考虑多个参数的联合优化，而非单独调整</li>
    <li><strong>定期回顾</strong>: 随着业务发展，定期重新进行敏感性分析更新策略</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 14px;">
<p><strong>增强版敏感性分析</strong> | 基于简化版7大类参数结构 | © 2025 Luma Tech</p>
</div>
""", unsafe_allow_html=True)