"""
策略优化页面 - 自动寻找最优参数组合以最大化收入
"""
import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import copy
import time
from typing import Dict, Any, List, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from luma_sales_model.financial_model import LumaFinancialModel
from utils.optimization import grid_search_optimizer, bayesian_optimizer, genetic_algorithm_optimizer
from utils.localization import get_param_display_name

# 设置页面配置
st.set_page_config(
    page_title="策略优化 - Luma高校销售与收益分析模型",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("策略优化与收入最大化")

# 添加详细的页面介绍
st.markdown("""
## 什么是策略优化？

<div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin-bottom: 15px">
<p>策略优化是一种通过系统性探索参数空间，寻找能够最大化目标指标（如总收入）的参数组合的方法。与敏感性分析不同，策略优化同时调整多个参数，以找到全局最优或近似最优解。</p>

<p>在商业决策中，策略优化可以帮助您：</p>
<ul>
  <li>发现能够最大化收入或利润的最佳参数组合</li>
  <li>在多个业务目标之间找到平衡点</li>
  <li>识别非直观的参数交互作用，发现创新策略</li>
  <li>量化不同业务决策的潜在收益</li>
</ul>
</div>

### 使用说明

1. 选择要优化的参数及其取值范围
2. 设置优化目标（如最大化Luma总收入）
3. 选择优化算法及其参数
4. 点击"开始优化"按钮
5. 查看优化结果，获取最佳参数组合和业务洞见
""", unsafe_allow_html=True)

# 添加视觉分隔符
st.markdown("<hr style='margin: 15px 0px; border: 1px solid #f0f2f6;'>", unsafe_allow_html=True)

# 初始化会话状态
if 'model_params' not in st.session_state:
    st.session_state.model_params = {}
if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = None

# 检查是否有模型参数
if not st.session_state.model_params:
    st.warning("请先在主页设置并运行模型，然后再进行策略优化。")
    st.stop()

# 显示当前模型参数
with st.expander("当前模型参数（点击展开）"):
    st.markdown("""
    <small>这些是您在主页设置并运行的模型参数，策略优化将基于这些基准参数进行。</small>
    """, unsafe_allow_html=True)
    st.json(st.session_state.model_params)

# 参数优化设置
st.header("设置优化参数")
st.markdown("""
<small>在此部分，您可以选择要优化的参数及其取值范围。系统将在这些范围内搜索最优参数组合。</small>
""", unsafe_allow_html=True)

# 创建两列布局
col1, col2 = st.columns(2)

# 第一列：参数选择
with col1:
    st.subheader("第1步：选择要优化的参数")
    
    # 定义可优化的参数组
    parameter_groups = {
        "价格参数": [
            "price_per_feature_use",
            "price_annual_member",
            "price_3year_member",
            "price_5year_member",
            "type1_access_fee",
            "type2_access_fees.a",
            "type2_access_fees.b",
            "type2_access_fees.c",
        ],
        "分成比例参数": [
            "type2_luma_share_from_student.a",
            "type2_luma_share_from_student.b",
            "type2_luma_share_from_student.c",
        ],
        "市场参数": [
            "new_clients_per_half_year",
            "student_total_paid_cr",
            "share_paid_user_per_use_only",
            "share_paid_user_membership",
        ],
        "续约参数": [
            "renewal_rate_uni",
            "renewal_rate_student",
        ]
    }
    
    # 创建参数选择界面
    selected_params = {}
    for group_name, params in parameter_groups.items():
        with st.expander(f"{group_name}"):
            for param in params:
                selected = st.checkbox(f"优化 {param}", value=False)
                if selected:
                    selected_params[param] = True
    
    # 如果没有选择任何参数，显示警告
    if not selected_params:
        st.warning("请至少选择一个要优化的参数")

# 第二列：参数范围设置
with col2:
    st.subheader("第2步：设置参数范围")
    
    # 为选中的参数设置范围
    param_ranges = {}
    for param in selected_params:
        st.markdown(f"##### {param} 的取值范围")
        
        # 根据参数类型设置合适的默认范围和步长
        if param == "new_clients_per_half_year":
            min_val = st.number_input(f"{param} 最小值", value=1, min_value=1, step=1)
            max_val = st.number_input(f"{param} 最大值", value=20, min_value=2, step=1)
        elif "price" in param or "fee" in param:
            # 价格参数
            current_value = 100  # 默认值
            # 尝试从当前参数中获取实际值
            try:
                if "." in param:  # 嵌套参数
                    parts = param.split(".")
                    if len(parts) == 2 and parts[0] in st.session_state.model_params and parts[1] in st.session_state.model_params[parts[0]]:
                        current_value = st.session_state.model_params[parts[0]][parts[1]]
                else:  # 顶层参数
                    if param in st.session_state.model_params:
                        current_value = st.session_state.model_params[param]
            except:
                pass
            
            min_val = st.number_input(f"{param} 最小值", value=max(0.0, current_value * 0.5), min_value=0.0, step=0.1)
            max_val = st.number_input(f"{param} 最大值", value=current_value * 1.5, min_value=min_val + 0.1, step=0.1)
        elif "share" in param or "rate" in param:
            # 比例参数
            min_val = st.number_input(f"{param} 最小值", value=0.1, min_value=0.0, max_value=1.0, step=0.05)
            max_val = st.number_input(f"{param} 最大值", value=0.9, min_value=min_val, max_value=1.0, step=0.05)
        else:
            # 其他参数
            min_val = st.number_input(f"{param} 最小值", value=0.0, step=0.1)
            max_val = st.number_input(f"{param} 最大值", value=1.0, step=0.1)
        
        param_ranges[param] = (min_val, max_val)
        st.markdown("---")

# 优化目标设置
st.header("设置优化目标")
st.markdown("""
<small>选择您想要最大化的指标。系统将寻找使该指标最大化的参数组合。</small>
""", unsafe_allow_html=True)

objective_metric = st.selectbox(
    "优化目标",
    options=[
        "Luma_Revenue_Total",  # Luma总收入
        "Luma_Fixed_Fee_New",  # 新签约固定费用
        "Luma_Student_Share_New",  # 新签约学生分成
        "Luma_Student_Share_Renewed",  # 续约学生分成
    ],
    index=0,
    help="选择要最大化的指标。通常选择Luma_Revenue_Total（总收入）作为优化目标。"
)

# 优化算法设置
st.header("优化算法设置")
st.markdown("""
<small>选择用于寻找最优参数组合的算法及其设置。不同算法适用于不同类型的优化问题。</small>
""", unsafe_allow_html=True)

optimization_method = st.selectbox(
    "优化算法",
    options=[
        "网格搜索 (Grid Search)",
        "贝叶斯优化 (Bayesian Optimization)",
        "遗传算法 (Genetic Algorithm)",
    ],
    index=0,
    help="""不同算法的特点：
    - 网格搜索：系统地探索所有参数组合，适合参数较少的情况
    - 贝叶斯优化：智能地选择下一组要评估的参数，适合计算成本高的函数优化
    - 遗传算法：模拟自然选择过程，适合复杂的多维参数空间"""
)

# 根据所选算法显示相应的设置选项
if optimization_method == "网格搜索 (Grid Search)":
    points_per_dim = st.slider("每个维度的采样点数", min_value=3, max_value=10, value=5, 
                              help="每个参数取值范围内的采样点数量。点数越多，搜索越精细，但计算量也越大。")
    
    # 计算并显示总评估次数
    if selected_params:
        total_evaluations = points_per_dim ** len(selected_params)
        if total_evaluations > 10000:
            st.warning(f"警告：当前设置将产生约 {total_evaluations:,} 次模型评估，这可能需要很长时间。建议减少参数数量或降低每个维度的采样点数。")
        else:
            st.info(f"当前设置将产生约 {total_evaluations:,} 次模型评估。")

elif optimization_method == "贝叶斯优化 (Bayesian Optimization)":
    n_iterations = st.slider("迭代次数", min_value=10, max_value=100, value=30, 
                           help="贝叶斯优化的迭代次数。迭代次数越多，找到更好解的可能性越大，但计算时间也越长。")
    n_initial_points = st.slider("初始随机点数", min_value=5, max_value=20, value=10, 
                               help="优化开始前随机采样的点数。这些点用于构建初始代理模型。")
    exploitation_vs_exploration = st.slider("探索与利用平衡", min_value=0.0, max_value=1.0, value=0.1, step=0.05, 
                                         help="值越低，算法越倾向于在已知的高收益区域附近搜索；值越高，算法越倾向于探索未知区域。")

elif optimization_method == "遗传算法 (Genetic Algorithm)":
    population_size = st.slider("种群大小", min_value=10, max_value=100, value=30, 
                              help="每一代中个体的数量。种群越大，覆盖的搜索空间越广，但计算成本也越高。")
    n_generations = st.slider("迭代代数", min_value=5, max_value=50, value=20, 
                           help="遗传算法运行的代数。代数越多，找到更好解的可能性越大，但计算时间也越长。")
    mutation_rate = st.slider("变异率", min_value=0.01, max_value=0.5, value=0.1, step=0.01, 
                           help="控制基因变异的概率。变异率过低可能导致早熟收敛，过高可能破坏良好的解。")

# 运行优化按钮
st.header("运行优化")
st.markdown("""
<small>点击下方按钮开始优化过程。系统将搜索参数空间，寻找能够最大化所选指标的参数组合。</small>
""", unsafe_allow_html=True)

run_col1, run_col2 = st.columns([1, 3])
with run_col1:
    run_button = st.button("🚀 开始优化", use_container_width=True)

with run_col2:
    if not selected_params:
        st.warning("⚠️ 请至少选择一个要优化的参数后再运行优化")
    elif len(selected_params) > 5 and optimization_method == "网格搜索 (Grid Search)":
        st.warning("⚠️ 网格搜索不建议用于5个以上的参数，可能会导致计算时间过长。请考虑减少参数数量或选择其他优化算法。")
# ... (紧接上一段代码) ...

if run_button and selected_params:
    st.session_state.optimization_results = None # 清除旧结果
    
    # 准备基础参数 (从主页获取)
    base_model_params = st.session_state.get('model_params', {})
    if not base_model_params:
        st.error("错误：无法从主页获取模型参数。请先在主页运行模型。")
        st.stop()

    st.info(f"开始使用 '{optimization_method}' 方法进行优化，目标指标：'{objective_metric}'...")
    
    progress_bar = st.progress(0)
    status_text = st.empty() # 用于显示更详细的状态

    def update_progress(value, text=""):
        progress_bar.progress(value)
        if text:
            status_text.text(text)

    if optimization_method == "网格搜索 (Grid Search)":
        status_text.text("正在准备网格搜索...")
        
        # 确保 param_ranges 只包含选中的参数
        current_param_ranges = {k: v for k, v in param_ranges.items() if k in selected_params}

        if not current_param_ranges:
            st.error("错误：没有为选定的优化参数设置范围。")
        else:
            try:
                best_params, best_score, all_results_df = grid_search_optimizer(
                    base_params=base_model_params,
                    params_to_optimize_ranges=current_param_ranges,
                    objective_metric=objective_metric,
                    points_per_dim=points_per_dim, # 'points_per_dim' 是之前定义的slider
                    progress_callback=lambda p: update_progress(p, f"网格搜索进度: {p*100:.1f}%")
                )
                st.session_state.optimization_results = {
                    "method": "网格搜索",
                    "best_params": best_params,
                    "best_score": best_score,
                    "all_results": all_results_df,
                    "objective_metric": objective_metric
                }
                status_text.success(f"网格搜索完成！最佳 {objective_metric}: {best_score:.4f}")
            except Exception as e:
                st.error(f"网格搜索过程中发生错误: {e}")
                import traceback
                st.error(traceback.format_exc())


    elif optimization_method == "贝叶斯优化 (Bayesian Optimization)":
        status_text.text("正在准备贝叶斯优化...")
        
        # 确保 param_ranges 只包含选中的参数
        current_param_ranges = {k: v for k, v in param_ranges.items() if k in selected_params}

        if not current_param_ranges:
            st.error("错误：没有为选定的优化参数设置范围。")
        else:
            try:
                best_params, best_score, all_results_df = bayesian_optimizer(
                    base_params=base_model_params,
                    params_to_optimize_ranges=current_param_ranges,
                    objective_metric=objective_metric,
                    n_iterations=n_iterations,
                    n_initial_points=n_initial_points,
                    exploitation_vs_exploration=exploitation_vs_exploration,
                    progress_callback=lambda p, txt="": update_progress(p, txt or f"贝叶斯优化进度: {p*100:.1f}%")
                )
                st.session_state.optimization_results = {
                    "method": "贝叶斯优化",
                    "best_params": best_params,
                    "best_score": best_score,
                    "all_results": all_results_df,
                    "objective_metric": objective_metric
                }
                status_text.success(f"贝叶斯优化完成！最佳 {objective_metric}: {best_score:.4f}")
            except Exception as e:
                st.error(f"贝叶斯优化过程中发生错误: {e}")
                import traceback
                st.error(traceback.format_exc())


    elif optimization_method == "遗传算法 (Genetic Algorithm)":
        status_text.text("正在准备遗传算法...")
        
        current_param_ranges = {k: v for k, v in param_ranges.items() if k in selected_params}

        if not current_param_ranges:
            st.error("错误：没有为选定的优化参数设置范围。")
        else:
            try:
                best_params, best_score, all_results_df = genetic_algorithm_optimizer(
                    base_params=base_model_params,
                    params_to_optimize_ranges=current_param_ranges,
                    objective_metric=objective_metric,
                    population_size=population_size,
                    n_generations=n_generations,
                    mutation_rate=mutation_rate,
                    progress_callback=lambda p, txt="": update_progress(p, txt or f"遗传算法进度: {p*100:.1f}%")
                )
                st.session_state.optimization_results = {
                    "method": "遗传算法",
                    "best_params": best_params,
                    "best_score": best_score,
                    "all_results": all_results_df,
                    "objective_metric": objective_metric
                }
                status_text.success(f"遗传算法完成！最佳 {objective_metric}: {best_score:.4f}")
            except Exception as e:
                st.error(f"遗传算法过程中发生错误: {e}")
                import traceback
                st.error(traceback.format_exc())
        
    progress_bar.progress(1.0) # 确保进度条在结束时为100%

elif run_button and not selected_params:
    # 这个警告已由之前的代码处理，但保留以防万一
    st.warning("⚠️ 请至少选择一个要优化的参数后再运行优化")


# 结果展示部分（在此处或之后添加）
st.markdown("---") # 分隔线
st.header("优化结果")

if st.session_state.get('optimization_results'):
    results = st.session_state.optimization_results
    st.subheader(f"使用 '{results['method']}' 的优化结果")
    
    st.metric(label=f"最佳 {results['objective_metric']}", value=f"{results['best_score']:.4f}")
    
    st.markdown("##### 最佳参数组合:")
    # 将最佳参数格式化为更易读的形式
    best_params_df = pd.DataFrame(list(results['best_params'].items()), columns=['参数', '值'])
    st.table(best_params_df)

    # --- Explanation of Best Parameter Combination ---
    objective_metric_key = results['objective_metric']
    objective_metric_display_name = get_param_display_name(objective_metric_key)
    optimization_method_name = results['method']
    best_score_formatted = f"{results['best_score']:.4f}"

    best_params_dict = results['best_params']
    param_examples = []
    # Limit the number of examples to avoid a very long string, e.g., first 3
    for i, (p_key, p_value) in enumerate(best_params_dict.items()):
        if i < 3: # Show up to 3 examples
            p_display_name = get_param_display_name(p_key)
            if isinstance(p_value, float):
                # Show as int if it's a whole number, else format to 2 decimal places
                p_value_formatted = f"{int(p_value)}" if p_value == int(p_value) else f"{p_value:.2f}"
            else:
                p_value_formatted = str(p_value)
            param_examples.append(f"“{p_display_name}”为“{p_value_formatted}”")
        else:
            param_examples.append("等")
            break
    
    param_examples_str = "，".join(param_examples)
    if not best_params_dict: 
        param_examples_str = "这些参数的特定组合"

    explanation_text = f"""
    <div style="background-color: #eef7ff; border-left: 6px solid #1e90ff; padding: 15px; margin-top: 20px; margin-bottom: 15px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
    <p style="font-size: 1.15em; font-weight: bold; color: #0056b3; margin-bottom: 10px;">📊 表格解读：最佳参数组合的含义</p>
    <p style="font-size: 1.0em; line-height: 1.6;">上方的“最佳参数组合”表格，清晰地列出了在您设定的参数搜索范围、并以“<strong>{objective_metric_display_name}</strong>”为核心优化目标的前提下，通过精密的 <strong>{optimization_method_name}</strong> 算法运算后，所找到的一组实现了最优效果的参数数值。</p>
    <p style="font-size: 1.0em; line-height: 1.6;">具体而言，这意味着当模型中的各项可调整参数（例如：{param_examples_str}）被精确地设置为表格中所示的这些特定值时，系统预测您的关键优化指标“<strong>{objective_metric_display_name}</strong>”能够达到所显示的最佳结果，即：<strong>{best_score_formatted}</strong>。</p>
    <p style="font-size: 1.0em; line-height: 1.6;">此结果为您提供了基于数据的决策支持。依据当前模型的分析与预测，采纳这一参数组合，将最有可能帮助您实现所追求的“<strong>{objective_metric_display_name}</strong>”的最大化（或您选定的其他优化方向）。请注意，这仍是基于模型和已提供数据的预测，实际业务成果可能受到模型外其他复杂因素的影响。</p>
    </div>
    """
    st.markdown(explanation_text, unsafe_allow_html=True)
    # --- End of Explanation ---

    if results.get('all_results') is not None and not results['all_results'].empty:
        st.markdown("##### 所有评估结果:")
        st.dataframe(results['all_results'])
        
        # 可选：添加下载按钮
        csv = results['all_results'].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下载所有结果 (CSV)",
            data=csv,
            file_name=f"{results['method']}_optimization_results.csv",
            mime='text/csv',
        )
    else:
        st.info("没有详细的评估结果可供展示。")
        
else:
    st.info("尚未运行优化，或优化未产生结果。请在上方配置并开始优化。")

