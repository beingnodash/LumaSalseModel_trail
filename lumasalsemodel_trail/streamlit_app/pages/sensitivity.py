"""
敏感性分析页面 - 提供交互式敏感性分析功能
"""
import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import copy

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from luma_sales_model.financial_model import LumaFinancialModel
from streamlit_app.utils.parameter_ui import render_sensitivity_analysis_controls
from streamlit_app.utils.plot_utils import plot_sensitivity_analysis

# 设置页面配置
st.set_page_config(
    page_title="敏感性分析 - Luma高校销售与收益分析模型",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("参数敏感性分析")
# 添加详细的页面介绍和敏感性分析概念解释
st.markdown("""
## 什么是敏感性分析？

<div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin-bottom: 15px">
<p>敏感性分析是一种评估模型参数变化对结果影响程度的方法。通过系统性地改变某个参数的值，同时保持其他参数不变，我们可以观察并量化这种变化对关键输出指标的影响。</p>

<p>在商业决策中，敏感性分析可以帮助您：</p>
<ul>
  <li>识别对结果影响最大的关键参数</li>
  <li>评估业务策略在不同条件下的稳健性</li>
  <li>了解参数变化的风险和机会</li>
  <li>为战略决策提供数据支持</li>
</ul>
</div>

### 使用说明

1. 选择您想要分析的参数（例如：高校续约率、学生付费转化率等）
2. 设置该参数的测试值范围（最小值、最大值和测试点数量）
3. 选择您关注的输出指标（如总收入、高校基金等）
4. 点击"运行敏感性分析"按钮
5. 查看结果图表和数据表，分析参数变化对结果的影响
""", unsafe_allow_html=True)

# 添加视觉分隔符
st.markdown("<hr style='margin: 15px 0px; border: 1px solid #f0f2f6;'>", unsafe_allow_html=True)

# 初始化会话状态
if 'model_params' not in st.session_state:
    st.session_state.model_params = {}
if 'sensitivity_results' not in st.session_state:
    st.session_state.sensitivity_results = None

# 检查是否有模型参数
if not st.session_state.model_params:
    st.warning("请先在主页设置并运行模型，然后再进行敏感性分析。")
    st.stop()

# 显示当前模型参数
with st.expander("当前模型参数（点击展开）"):
    st.markdown("""
    <small>这些是您在主页设置并运行的模型参数，敏感性分析将基于这些基准参数进行。</small>
    """, unsafe_allow_html=True)
    st.json(st.session_state.model_params)

# 敏感性分析控件
st.header("设置敏感性分析参数")
st.markdown("""
<small>在此部分，您可以选择要分析的参数及其测试范围。系统将在保持其他参数不变的情况下，测试所选参数在指定范围内的不同值对结果的影响。</small>
""", unsafe_allow_html=True)

# 选择要分析的参数和测试值
with st.container():
    st.subheader("第1步：选择分析参数和测试范围")
    param_to_analyze, test_values = render_sensitivity_analysis_controls()

# 选择要跟踪的输出指标
with st.container():
    st.subheader("第2步：选择要观察的输出指标")
    st.markdown("""
    <small>选择您想要观察的模型输出指标。这些指标将显示在结果图表和数据表中，帮助您理解参数变化的影响。</small>
    """, unsafe_allow_html=True)
    
    output_metrics = st.multiselect(
        "输出指标",
        options=["Luma_Revenue_Total", "Uni_Fund_Total", "Luma_Fixed_Fee_New", "Luma_Student_Share_New", "Luma_Student_Share_Renewed"],
        default=["Luma_Revenue_Total"],
        help="""可选的输出指标说明：
        - Luma_Revenue_Total：Luma公司总收入
        - Uni_Fund_Total：高校基金总额
        - Luma_Fixed_Fee_New：来自新签约的固定接入费
        - Luma_Student_Share_New：来自新签约高校学生的付费分成
        - Luma_Student_Share_Renewed：来自续约高校学生的付费分成"""
    )

# 运行敏感性分析按钮
st.subheader("第3步：运行分析")
st.markdown("""
<small>点击下方按钮开始敏感性分析。系统将为所选参数的每个测试值运行模型，并收集所选输出指标的结果。</small>
""", unsafe_allow_html=True)

run_col1, run_col2 = st.columns([1, 3])
with run_col1:
    run_button = st.button("🚀 运行敏感性分析", use_container_width=True)

with run_col2:
    if not output_metrics:
        st.warning("⚠️ 请至少选择一个输出指标后再运行分析")

if run_button:
    if not output_metrics:
        st.error("❌ 无法运行分析：请至少选择一个输出指标")
    else:
        # 创建进度条和状态显示区域
        st.markdown("### 分析进度")
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            # 准备参数
            params_to_vary = {param_to_analyze: test_values}
            
            # 获取当前模型参数的副本
            base_params = copy.deepcopy(st.session_state.model_params)
            
            status_text.text("⏳ 步骤 1/4: 初始化模型...")
            progress_bar.progress(10)
            
            # 创建模型实例
            model = LumaFinancialModel(params=base_params)
            
            status_text.text("⏳ 步骤 2/4: 运行敏感性分析...")
            progress_bar.progress(30)
            
            # 运行敏感性分析
            sensitivity_results = model.run_sensitivity_analysis(
                params_to_vary=params_to_vary,
                output_metrics=output_metrics
            )
            
            status_text.text("⏳ 步骤 3/4: 处理结果数据...")
            progress_bar.progress(70)
            
            # 保存结果到会话状态
            st.session_state.sensitivity_results = sensitivity_results
            
            status_text.text("⏳ 步骤 4/4: 准备可视化...")
            progress_bar.progress(90)
            
            # 完成
            progress_bar.progress(100)
            status_text.markdown("✅ **敏感性分析完成！** 请查看下方结果。")
            
        except Exception as e:
            st.error(f"❌ 敏感性分析出错: {str(e)}")
            st.info("💡 提示：请检查参数设置是否合理，或尝试缩小测试范围。")

# 显示敏感性分析结果
if st.session_state.sensitivity_results is not None:
    sensitivity_df = st.session_state.sensitivity_results
    
    st.markdown("<hr style='margin: 30px 0px; border: 1px solid #f0f2f6;'>", unsafe_allow_html=True)
    st.header("敏感性分析结果与解读")
    
    # 添加结果解释
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin-bottom: 20px">
    <p>下方展示了参数变化对所选输出指标的影响。图表中的斜率越陡，表示该参数对结果的影响越显著。</p>
    
    <p>如何解读结果：</p>
    <ul>
      <li><strong>上升曲线</strong>：参数值增加会导致输出指标增加（正相关）</li>
      <li><strong>下降曲线</strong>：参数值增加会导致输出指标减少（负相关）</li>
      <li><strong>平缓曲线</strong>：参数对输出指标影响较小</li>
      <li><strong>陡峰曲线</strong>：参数对输出指标影响较大</li>
      <li><strong>非线性曲线</strong>：参数与输出指标之间存在复杂关系</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 为每个输出指标绘制敏感性分析图
    st.subheader("参数影响可视化")
    for metric in output_metrics:
        if metric in sensitivity_df.columns:
            # 添加指标解释
            metric_explanations = {
                "Luma_Revenue_Total": "Luma公司总收入（包括固定费用和学生付费分成）",
                "Uni_Fund_Total": "高校基金总额（高校从学生付费中获得的分成）",
                "Luma_Fixed_Fee_New": "来自新签约高校的固定接入费收入",
                "Luma_Student_Share_New": "来自新签约高校学生的付费分成收入",
                "Luma_Student_Share_Renewed": "来自续约高校学生的付费分成收入"
            }
            
            st.markdown(f"#### {metric} 的敏感性分析")
            st.markdown(f"<small>**指标说明**: {metric_explanations.get(metric, '未提供说明')}</small>", unsafe_allow_html=True)
            
            # 绘制图表
            plot_sensitivity_analysis(sensitivity_df, param_to_analyze, metric)
            
            # 添加简单的结果解读
            min_value = sensitivity_df[metric].min()
            max_value = sensitivity_df[metric].max()
            change_pct = ((max_value - min_value) / min_value * 100) if min_value > 0 else 0
            
            st.markdown(f"""
            <div style="margin: 10px 0 20px 0">
            <small>
            <strong>结果解读:</strong> 在测试范围内，{param_to_analyze}的变化导致{metric}从{min_value:.2f}变化到{max_value:.2f}，
            变化幅度约为{change_pct:.1f}%。{' 这表明该参数对此指标有显著影响。' if change_pct > 10 else ' 这表明该参数对此指标影响相对较小。'}
            </small>
            </div>
            """, unsafe_allow_html=True)
    
    # 显示结果表格
    st.subheader("详细数据表")
    st.markdown("<small>下表显示了所有测试值及其对应的输出指标结果。您可以排序、筛选和下载这些数据。</small>", unsafe_allow_html=True)
    st.dataframe(sensitivity_df, use_container_width=True)
    
    # 提供下载结果的选项
    csv = sensitivity_df.to_csv(index=False)
    st.download_button(
        label="📊 下载敏感性分析结果 (CSV)",
        data=csv,
        file_name="sensitivity_analysis_results.csv",
        mime="text/csv",
        help="将分析结果下载为CSV文件，可在Excel等软件中进一步分析"
    )
    
    # 添加业务建议
    st.subheader("业务决策参考")
    st.markdown("""
    <div style="background-color: #e6f3ff; padding: 15px; border-radius: 5px; margin: 20px 0">
    <p>基于敏感性分析结果，您可以考虑以下业务决策方向：</p>
    <ul>
      <li>关注对收入影响最大的参数，优先考虑改善这些因素</li>
      <li>评估不同参数组合的最佳收益点</li>
      <li>制定针对性的风险管理策略，应对参数波动带来的不确定性</li>
      <li>将分析结果与实际业务数据对比，验证模型准确性</li>
    </ul>
    <p>建议：定期进行敏感性分析，随着业务发展调整关键参数，持续优化商业模式。</p>
    </div>
    """, unsafe_allow_html=True)
