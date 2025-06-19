"""
增强版策略优化页面 - 集成所有改进功能
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
from utils.algorithm_selector import AlgorithmSelector
from utils.constraint_handler import LumaConstraintHandler
from utils.optimization_monitor import OptimizationMonitor
from utils.ensemble_optimizer import EnsembleOptimizer
from utils.robustness_analyzer import RobustnessAnalyzer
from utils.realistic_constraints import RealisticConstraintHandler
from utils.optimization import grid_search_optimizer, bayesian_optimizer, genetic_algorithm_optimizer
from utils.enhanced_optimization import (
    enhanced_grid_search_optimizer, 
    enhanced_bayesian_optimizer, 
    enhanced_genetic_algorithm_optimizer
)

# 设置页面配置
st.set_page_config(
    page_title="增强版策略优化 - Luma高校销售与收益分析模型",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("🚀 增强版策略优化系统")

# 添加详细的页面介绍
st.markdown("""
## 全新增强功能

本页面集成了最新的优化增强功能，提供更智能、更可靠的策略优化体验：

### 🧠 智能算法选择
- 基于问题特性自动推荐最适合的优化算法
- 提供详细的选择理由和注意事项
- 智能参数建议

### 🔒 约束处理系统
- 自动约束检查和修复
- 确保业务逻辑的合理性
- 支持复杂参数关系约束

### 📊 实时优化监控
- 收敛性实时检测
- 智能早停建议
- 详细的诊断报告

### 🎯 多算法集成
- 并行运行多种算法
- 智能结果融合
- 性能对比分析

### 🛡️ 鲁棒性分析
- Monte Carlo稳定性测试
- 参数敏感性评估
- 风险等级评估

### 🎯 现实约束优化 (新功能!)
- **解决"极值寻找"问题**: 避免所有参数都取最大值的不现实结果
- **价格弹性建模**: 价格上涨时自动调整需求和转化率
- **竞争因素考虑**: 高分成比例会影响高校接受度和续约率
- **市场容量限制**: 过高的获客目标会面临递增的边际成本
- **真正的策略优化**: 在现实约束下寻找最优平衡点
""", unsafe_allow_html=True)

# 初始化会话状态
if 'model_params' not in st.session_state:
    st.session_state.model_params = {}
if 'enhanced_optimization_results' not in st.session_state:
    st.session_state.enhanced_optimization_results = None

# 检查是否有模型参数
if not st.session_state.model_params:
    st.warning("请先在主页设置并运行模型，然后再进行策略优化。")
    st.stop()

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 智能优化配置", 
    "📊 优化监控与诊断", 
    "🔍 鲁棒性分析",
    "📈 结果对比分析"
])

with tab1:
    st.header("智能优化配置")
    
    # 算法选择指导
    st.subheader("1. 智能算法选择")
    
    # 参数选择（简化版）
    st.markdown("**选择要优化的参数**")
    
    # 预定义的常用参数组合（更新为新的参数结构）
    parameter_presets = {
        "价格优化": [
            "student_prices.price_per_use",
            "student_prices.price_1year_member", 
            "student_prices.price_3year_member",
            "student_prices.price_5year_member"
        ],
        "分成策略": [
            "revenue_sharing.luma_share_from_student"
        ],
        "市场策略": [
            "market_scale.new_clients_per_half_year",
            "market_distribution.student_paid_conversion_rate_bc",
            "renewal_rates.university_3year_renewal"
        ],
        "综合策略": [
            "student_prices.price_1year_member",
            "market_scale.new_clients_per_half_year", 
            "revenue_sharing.luma_share_from_student",
            "renewal_rates.university_3year_renewal"
        ],
        "高校定价策略": [
            "university_prices.mode_a_price",
            "university_prices.mode_b_price",
            "market_distribution.mode_a_ratio",
            "market_distribution.mode_b_ratio"
        ]
    }
    
    preset_choice = st.selectbox("选择参数预设", list(parameter_presets.keys()))
    selected_params = parameter_presets[preset_choice]
    
    # 显示选中的参数
    st.write(f"已选择参数: {', '.join(selected_params)}")
    
    # 自动生成参数范围（适配新参数结构）
    param_ranges = {}
    for param in selected_params:
        st.markdown(f"##### {param}")
        
        # 根据参数类型设置合理的默认范围
        if "price_per_use" in param:
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"{param} 最小值", value=3.0, min_value=0.1, step=0.5, key=f"{param}_min")
            with col2:
                max_val = st.number_input(f"{param} 最大值", value=15.0, min_value=min_val + 0.1, step=0.5, key=f"{param}_max")
        elif "price_1year_member" in param:
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"{param} 最小值", value=100.0, min_value=50.0, step=10.0, key=f"{param}_min")
            with col2:
                max_val = st.number_input(f"{param} 最大值", value=300.0, min_value=min_val + 10.0, step=10.0, key=f"{param}_max")
        elif "price_3year_member" in param:
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"{param} 最小值", value=250.0, min_value=100.0, step=25.0, key=f"{param}_min")
            with col2:
                max_val = st.number_input(f"{param} 最大值", value=600.0, min_value=min_val + 25.0, step=25.0, key=f"{param}_max")
        elif "price_5year_member" in param:
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"{param} 最小值", value=400.0, min_value=200.0, step=50.0, key=f"{param}_min")
            with col2:
                max_val = st.number_input(f"{param} 最大值", value=800.0, min_value=min_val + 50.0, step=50.0, key=f"{param}_max")
        elif "mode_a_price" in param or "mode_b_price" in param:
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"{param} 最小值", value=200000.0, min_value=0.0, step=50000.0, key=f"{param}_min")
            with col2:
                max_val = st.number_input(f"{param} 最大值", value=1000000.0, min_value=min_val + 50000.0, step=50000.0, key=f"{param}_max")
        elif "share" in param or "rate" in param or "ratio" in param:
            col1, col2 = st.columns(2)
            with col1:
                if "ratio" in param:
                    min_val = st.number_input(f"{param} 最小值", value=0.1, min_value=0.0, max_value=1.0, step=0.05, key=f"{param}_min")
                else:
                    min_val = st.number_input(f"{param} 最小值", value=0.1, min_value=0.0, max_value=1.0, step=0.05, key=f"{param}_min")
            with col2:
                if "ratio" in param:
                    max_val = st.number_input(f"{param} 最大值", value=0.8, min_value=min_val, max_value=1.0, step=0.05, key=f"{param}_max")
                else:
                    max_val = st.number_input(f"{param} 最大值", value=0.9, min_value=min_val, max_value=1.0, step=0.05, key=f"{param}_max")
        elif "new_clients_per_half_year" in param:
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"{param} 最小值", value=1, step=1, key=f"{param}_min")
            with col2:
                max_val = st.number_input(f"{param} 最大值", value=15, min_value=min_val, step=1, key=f"{param}_max")
        else:
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"{param} 最小值", value=1, step=1, key=f"{param}_min")
            with col2:
                max_val = st.number_input(f"{param} 最大值", value=20, min_value=min_val, step=1, key=f"{param}_max")
        
        param_ranges[param] = (min_val, max_val)
    
    # 算法选择指导
    if param_ranges:
        st.subheader("2. 算法推荐")
        
        # 评估预算设置
        budget = st.slider("评估预算", min_value=50, max_value=500, value=200, step=25,
                          help="总的模型评估次数。预算越高，搜索越精确，但时间越长。")
        
        # 获取算法推荐
        algorithm_selector = AlgorithmSelector()
        recommendations = algorithm_selector.recommend_algorithm(param_ranges, budget)
        
        # 显示推荐结果
        for i, rec in enumerate(recommendations[:3], 1):
            with st.expander(f"{i}. {rec['name']} - {rec['suitability']} (得分: {rec['score']:.2f})"):
                st.markdown("**推荐理由:**")
                for reason in rec['reasons']:
                    st.write(f"• {reason}")
                
                if rec['warnings']:
                    st.markdown("**注意事项:**")
                    for warning in rec['warnings']:
                        st.warning(warning)
                
                st.markdown("**建议参数:**")
                for param, value in rec['suggested_params'].items():
                    st.write(f"• {param}: {value}")
    
    # 优化策略选择
    st.subheader("3. 优化策略")
    
    optimization_strategy = st.radio(
        "选择优化策略",
        [
            "智能单算法优化 (推荐)",
            "多算法集成优化 (最佳结果)",
            "自定义算法配置"
        ],
        help="智能单算法使用推荐的最佳算法；多算法集成并行运行多种算法并融合结果"
    )
    
    # 高级设置
    with st.expander("高级设置"):
        enable_constraints = st.checkbox("启用智能约束处理", value=True,
                                       help="自动检查和修复参数约束，确保解的可行性")
        
        enable_monitoring = st.checkbox("启用实时监控", value=True,
                                      help="监控优化过程，提供早停建议和诊断信息")
        
        enable_robustness = st.checkbox("启用鲁棒性分析", value=False,
                                      help="分析最优解的稳定性和风险（增加计算时间）")
        
        enable_realistic_constraints = st.checkbox("启用现实约束 🔥", value=True,
                                                 help="考虑价格弹性、竞争因素等现实约束，避免不切实际的极值解")
        
        if enable_realistic_constraints:
            penalty_weight = st.slider(
                "现实约束强度", 
                min_value=0.0, max_value=1.0, value=0.1, step=0.05,
                help="约束强度越高，越倾向于选择现实可行的参数组合"
            )

with tab2:
    st.header("优化监控与诊断")
    
    if st.session_state.enhanced_optimization_results:
        results = st.session_state.enhanced_optimization_results
        
        # 显示基本优化信息
        st.subheader("📊 优化过程总览")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("使用算法", results.get('algorithm', '未知'))
        with col2:
            if 'execution_time' in results:
                st.metric("执行时间", f"{results['execution_time']:.1f}秒")
            elif 'individual_results' in results:
                total_time = sum(r.execution_time for r in results['individual_results'].values())
                st.metric("总执行时间", f"{total_time:.1f}秒")
        with col3:
            if 'individual_results' in results:
                st.metric("算法数量", len(results['individual_results']))
            else:
                st.metric("评估次数", len(results.get('all_results', [])))
        
        # 显示监控图表
        monitor = results.get('monitor')
        if monitor and hasattr(monitor, 'history') and monitor.history.get('iteration'):
            st.subheader("📈 收敛过程监控")
            
            # 创建收敛图表
            try:
                convergence_plot = monitor.create_convergence_plot()
                st.plotly_chart(convergence_plot, use_container_width=True)
                
                # 显示诊断报告
                st.subheader("🔍 优化诊断报告")
                diagnostic_report = monitor.generate_diagnostic_report()
                st.text(diagnostic_report)
            except Exception as e:
                st.warning(f"监控图表生成失败: {str(e)}")
        else:
            st.info("📋 监控数据不可用（可能是多算法集成模式，监控信息分散在各算法中）")
            
            # 如果是集成优化，显示各算法的基本信息
            if 'individual_results' in results:
                st.subheader("🔄 各算法执行情况")
                algo_info = []
                for algo_name, result in results['individual_results'].items():
                    algo_info.append({
                        "算法": algo_name,
                        "最佳得分": f"{result.best_score:.2f}",
                        "执行时间": f"{result.execution_time:.1f}s",
                        "迭代次数": result.iterations_used,
                        "是否收敛": "是" if result.convergence_info.get('converged', False) else "否"
                    })
                
                algo_df = pd.DataFrame(algo_info)
                st.dataframe(algo_df, use_container_width=True, hide_index=True)
        
        # 显示约束验证结果
        st.subheader("✅ 约束验证结果")
        constraint_violations = results.get('constraint_violations', [])
        if constraint_violations:
            st.warning("⚠️ 发现约束违反:")
            for violation in constraint_violations:
                st.write(f"• {violation}")
        else:
            st.success("✅ 所有约束均满足，参数组合完全可行")
        
        # 显示参数合理性分析
        if results.get('best_params'):
            st.subheader("📋 参数合理性分析")
            
            reasonable_ranges = {
                'student_prices.price_per_use': (3, 15, "按次使用价格"),
                'student_prices.price_1year_member': (100, 300, "一年订阅价格"),
                'student_prices.price_3year_member': (250, 600, "三年订阅价格"), 
                'student_prices.price_5year_member': (400, 800, "五年订阅价格"),
                'university_prices.mode_a_price': (200000, 1000000, "高校模式A价格"),
                'university_prices.mode_b_price': (200000, 1000000, "高校模式B价格"),
                'revenue_sharing.luma_share_from_student': (0.2, 0.8, "学生付费分成比例"),
                'renewal_rates.university_3year_renewal': (0.5, 0.95, "高校续约率"),
                'renewal_rates.student_per_use_repurchase': (0.3, 0.9, "按次付费复购率"),
                'renewal_rates.student_subscription_renewal': (0.6, 0.9, "订阅续费率"),
                'market_scale.new_clients_per_half_year': (1, 15, "半年新客户数"),
                'market_scale.avg_students_per_uni': (5000, 30000, "平均学校规模"),
                'market_distribution.student_paid_conversion_rate_bc': (0.05, 0.3, "B/C模式学生付费转化率"),
                'market_distribution.mode_a_ratio': (0.1, 0.7, "模式A占比"),
                'market_distribution.mode_b_ratio': (0.1, 0.7, "模式B占比"),
                'market_distribution.mode_c_ratio': (0.1, 0.7, "模式C占比")
            }
            
            analysis_results = []
            for param, value in results['best_params'].items():
                if param in reasonable_ranges:
                    min_val, max_val, display_name = reasonable_ranges[param]
                    if isinstance(value, (int, float)):
                        if min_val <= value <= max_val:
                            status = "✅ 合理"
                        elif value < min_val:
                            status = "⚠️ 偏低"
                        else:
                            status = "⚠️ 偏高"
                        
                        analysis_results.append({
                            "参数": display_name,
                            "最优值": f"{value:.2f}" if isinstance(value, float) else str(value),
                            "合理范围": f"{min_val}-{max_val}",
                            "评估": status
                        })
            
            if analysis_results:
                analysis_df = pd.DataFrame(analysis_results)
                st.dataframe(analysis_df, use_container_width=True, hide_index=True)
    
    else:
        st.info("请先运行优化以查看监控信息")

with tab3:
    st.header("鲁棒性分析")
    
    if st.session_state.enhanced_optimization_results:
        results = st.session_state.enhanced_optimization_results
        
        # 鲁棒性分析配置
        st.subheader("鲁棒性分析配置")
        
        uncertainty_level = st.slider(
            "参数不确定性水平", 
            min_value=0.05, max_value=0.30, value=0.15, step=0.05,
            help="参数值的相对变化范围，用于Monte Carlo模拟"
        )
        
        if st.button("运行鲁棒性分析", type="primary"):
            with st.spinner("正在进行鲁棒性分析..."):
                # 初始化鲁棒性分析器
                robustness_analyzer = RobustnessAnalyzer(
                    st.session_state.model_params,
                    results.get('objective_metric', 'luma_revenue_total')
                )
                
                # 生成不确定性范围
                uncertainty_ranges = {}
                for param in results['best_params'].keys():
                    uncertainty_ranges[param] = uncertainty_level
                
                # 运行分析
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(progress, text=""):
                    progress_bar.progress(progress)
                    status_text.text(text)
                
                robustness_result = robustness_analyzer.analyze_robustness(
                    results['best_params'],
                    uncertainty_ranges,
                    progress_callback=progress_callback
                )
                
                # 显示结果
                st.subheader("鲁棒性分析结果")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("风险等级", robustness_result.risk_level.upper())
                with col2:
                    st.metric("预期性能", f"{robustness_result.mean_performance:.4f}")
                with col3:
                    cv = robustness_result.std_performance / robustness_result.mean_performance
                    st.metric("变异系数", f"{cv:.2%}")
                
                # 生成报告
                robustness_report = robustness_analyzer.generate_robustness_report(robustness_result)
                st.markdown(robustness_report)
                
                # 存储结果
                st.session_state.robustness_result = robustness_result
    
    else:
        st.info("请先运行优化以进行鲁棒性分析")

with tab4:
    st.header("结果对比分析")
    
    if st.session_state.enhanced_optimization_results:
        results = st.session_state.enhanced_optimization_results
        
        # 如果是集成优化结果，显示算法对比
        if hasattr(results, 'individual_results'):
            st.subheader("算法性能对比")
            
            comparison_report = results.generate_comparison_report()
            st.markdown(comparison_report)
        
        # 显示最佳参数
        st.subheader("最优参数组合")
        best_params_df = pd.DataFrame([
            {"参数": k, "最优值": v} 
            for k, v in results['best_params'].items()
        ])
        st.table(best_params_df)
        
        # 性能提升分析
        if 'base_performance' in results:
            st.subheader("性能提升分析")
            improvement = ((results['best_score'] - results['base_performance']) / 
                          results['base_performance'] * 100)
            st.metric(
                "性能提升", 
                f"{improvement:+.2f}%",
                delta=f"{results['best_score'] - results['base_performance']:.4f}"
            )
    
    else:
        st.info("请先运行优化以查看结果对比")

# 运行优化按钮（放在主区域底部）
st.markdown("---")
st.header("🚀 运行增强优化")

col1, col2 = st.columns([1, 3])

with col1:
    run_enhanced_button = st.button(
        "运行增强优化", 
        type="primary",
        use_container_width=True,
        disabled=not param_ranges
    )

with col2:
    if not param_ranges:
        st.warning("请先配置优化参数")
    else:
        total_params = len(param_ranges)
        estimated_time = budget * 0.1  # 估算时间（秒）
        st.info(f"将优化 {total_params} 个参数，预计耗时 {estimated_time:.0f} 秒")

# 执行优化
if run_enhanced_button and param_ranges:
    st.session_state.enhanced_optimization_results = None
    
    with st.spinner("正在运行增强版策略优化..."):
        try:
            # 创建进度显示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(progress, text=""):
                progress_bar.progress(min(progress, 1.0))
                status_text.text(text)
            
            # 根据选择的策略运行优化
            if optimization_strategy == "智能单算法优化 (推荐)":
                # 使用推荐的最佳算法
                best_algorithm = recommendations[0]
                algorithm_name = best_algorithm['algorithm']
                
                # 初始化组件
                constraint_handler = LumaConstraintHandler(param_ranges) if enable_constraints else None
                monitor = OptimizationMonitor() if enable_monitoring else None
                realistic_handler = RealisticConstraintHandler() if enable_realistic_constraints else None
                
                # 根据是否启用现实约束选择优化函数
                if enable_realistic_constraints:
                    # 使用增强版优化函数
                    penalty_wt = penalty_weight
                    
                    if algorithm_name == 'grid_search':
                        best_params, best_score, all_results = enhanced_grid_search_optimizer(
                            st.session_state.model_params,
                            param_ranges,
                            'luma_revenue_total',
                            best_algorithm['suggested_params'].get('points_per_dim', 5),
                            progress_callback,
                            constraint_handler,
                            monitor,
                            realistic_handler,
                            penalty_wt
                        )
                    elif algorithm_name == 'bayesian_optimization':
                        best_params, best_score, all_results = enhanced_bayesian_optimizer(
                            st.session_state.model_params,
                            param_ranges,
                            'luma_revenue_total',
                            best_algorithm['suggested_params'].get('n_iterations', 50),
                            best_algorithm['suggested_params'].get('n_initial_points', 10),
                            best_algorithm['suggested_params'].get('exploitation_vs_exploration', 0.1),
                            progress_callback,
                            realistic_handler,
                            penalty_wt
                        )
                    elif algorithm_name == 'genetic_algorithm':
                        best_params, best_score, all_results = enhanced_genetic_algorithm_optimizer(
                            st.session_state.model_params,
                            param_ranges,
                            'luma_revenue_total',
                            best_algorithm['suggested_params'].get('population_size', 30),
                            best_algorithm['suggested_params'].get('n_generations', 20),
                            best_algorithm['suggested_params'].get('mutation_rate', 0.1),
                            0.7,
                            progress_callback,
                            realistic_handler,
                            penalty_wt
                        )
                else:
                    # 使用原始优化函数
                    if algorithm_name == 'grid_search':
                        best_params, best_score, all_results = grid_search_optimizer(
                            st.session_state.model_params,
                            param_ranges,
                            'luma_revenue_total',
                            best_algorithm['suggested_params'].get('points_per_dim', 5),
                            progress_callback,
                            constraint_handler,
                            monitor
                        )
                    elif algorithm_name == 'bayesian_optimization':
                        best_params, best_score, all_results = bayesian_optimizer(
                            st.session_state.model_params,
                            param_ranges,
                            'luma_revenue_total',
                            best_algorithm['suggested_params'].get('n_iterations', 50),
                            best_algorithm['suggested_params'].get('n_initial_points', 10),
                            best_algorithm['suggested_params'].get('exploitation_vs_exploration', 0.1),
                            progress_callback
                        )
                    elif algorithm_name == 'genetic_algorithm':
                        best_params, best_score, all_results = genetic_algorithm_optimizer(
                            st.session_state.model_params,
                            param_ranges,
                            'luma_revenue_total',
                            best_algorithm['suggested_params'].get('population_size', 30),
                            best_algorithm['suggested_params'].get('n_generations', 20),
                            best_algorithm['suggested_params'].get('mutation_rate', 0.1),
                            0.7,
                            progress_callback
                        )
                
                # 存储结果
                result = {
                    'algorithm': algorithm_name,
                    'best_params': best_params,
                    'best_score': best_score,
                    'all_results': all_results,
                    'objective_metric': 'luma_revenue_total',
                    'monitor': monitor if enable_monitoring else None
                }
                
            elif optimization_strategy == "多算法集成优化 (最佳结果)":
                # 使用集成优化器
                ensemble_optimizer = EnsembleOptimizer(
                    st.session_state.model_params,
                    'luma_revenue_total'
                )
                
                result = ensemble_optimizer.optimize(
                    param_ranges,
                    budget,
                    'auto',
                    True,  # 并行执行
                    progress_callback
                )
                
                # 转换为字典格式
                ensemble_result_dict = {
                    'algorithm': result.algorithm,
                    'best_params': result.best_params,
                    'best_score': result.best_score,
                    'execution_time': result.execution_time,
                    'individual_results': ensemble_optimizer.individual_results,
                    'objective_metric': 'luma_revenue_total'
                }
                
                # 添加生成对比报告的方法
                ensemble_result_dict['generate_comparison_report'] = lambda: ensemble_optimizer.generate_comparison_report()
                
                result = ensemble_result_dict
            
            # 验证约束
            if enable_constraints:
                constraint_handler = LumaConstraintHandler(param_ranges)
                is_valid, violations = constraint_handler.validate_params(result['best_params'])
                result['constraint_violations'] = violations if not is_valid else []
            
            # 现实约束分析
            if enable_realistic_constraints:
                realistic_handler = RealisticConstraintHandler()
                result['realistic_constraint_report'] = realistic_handler.generate_constraint_report(result['best_params'])
                result['penalty_score'] = realistic_handler.calculate_penalty_score(result['best_params'])
            
            st.session_state.enhanced_optimization_results = result
            
            # 显示完成信息
            progress_bar.progress(1.0)
            status_text.success(f"优化完成！最佳得分: {result['best_score']:.6f}")
            
            # 立即显示核心结果 - 最优参数组合
            st.success("🎉 增强版策略优化完成！")
            
            # 显示最佳得分
            st.metric("🎯 最佳优化得分", f"{result['best_score']:.2f}", 
                     delta=f"算法: {result.get('algorithm', '集成优化')}")
            
            # 立即显示最优参数组合 - 这是用户最关心的
            st.subheader("🔧 最优参数组合")
            st.info("💡 以下参数组合在当前设置下能实现最佳收益，建议直接应用到业务策略中：")
            
            # 创建更友好的参数展示
            best_params_display = []
            for param, value in result['best_params'].items():
                # 美化参数名显示
                param_display = param.replace('_', ' ').replace('.', ' → ').title()
                if isinstance(value, float):
                    if 0 <= value <= 1 and 'rate' in param.lower() or 'share' in param.lower():
                        value_display = f"{value:.1%}"  # 百分比显示
                    else:
                        value_display = f"{value:.2f}"
                else:
                    value_display = str(value)
                
                best_params_display.append({
                    "参数名": param_display,
                    "最优值": value_display,
                    "原始参数": param
                })
            
            best_params_df = pd.DataFrame(best_params_display)
            st.dataframe(best_params_df[['参数名', '最优值']], use_container_width=True, hide_index=True)
            
            # 添加业务策略建议
            st.subheader("💼 业务策略建议")
            strategy_recommendations = []
            
            for param, value in result['best_params'].items():
                if 'price_1year_member' in param and isinstance(value, (int, float)):
                    if value > 200:
                        strategy_recommendations.append(f"🔸 **1年订阅定价**: {value:.0f}元属于高价策略，建议强化产品价值宣传，突出高级功能")
                    elif value < 150:
                        strategy_recommendations.append(f"🔸 **1年订阅定价**: {value:.0f}元属于低价策略，建议通过价格优势快速获取市场份额")
                    else:
                        strategy_recommendations.append(f"🔸 **1年订阅定价**: {value:.0f}元定价适中，平衡了市场接受度和盈利能力")
                
                elif 'price_per_use' in param and isinstance(value, (int, float)):
                    if value > 10:
                        strategy_recommendations.append(f"🔸 **按次使用定价**: {value:.1f}元较高，适合高价值功能，建议强调单次使用的便利性")
                    elif value < 5:
                        strategy_recommendations.append(f"🔸 **按次使用定价**: {value:.1f}元较低，有利于吸引尝试用户，建议引导转化为订阅")
                
                elif 'luma_share_from_student' in param and isinstance(value, (int, float)):
                    if value > 0.6:
                        strategy_recommendations.append(f"🔸 **学生分成策略**: {value:.1%}的高分成比例，建议为高校提供更多增值服务以维持合作")
                    elif value < 0.4:
                        strategy_recommendations.append(f"🔸 **学生分成策略**: {value:.1%}的低分成比例，有利于高校接受度，可考虑适度提升")
                
                elif 'mode_a_price' in param and isinstance(value, (int, float)):
                    if value > 800000:
                        strategy_recommendations.append(f"🔸 **模式A定价**: {value:,.0f}元的高价策略，需要提供全面的服务保障和ROI证明")
                    elif value < 400000:
                        strategy_recommendations.append(f"🔸 **模式A定价**: {value:,.0f}元的亲民定价，有利于快速市场渗透")
                
                elif 'new_clients_per_half_year' in param and isinstance(value, (int, float)):
                    if value > 8:
                        strategy_recommendations.append(f"🔸 **市场拓展**: 每半年{value:.0f}家新客户的目标较高，建议加大销售投入和渠道建设")
                    elif value < 4:
                        strategy_recommendations.append(f"🔸 **市场拓展**: 每半年{value:.0f}家新客户目标保守，可将资源更多投入现有客户维护")
                
                elif 'student_paid_conversion_rate_bc' in param and isinstance(value, (int, float)):
                    if value > 0.15:
                        strategy_recommendations.append(f"🔸 **付费转化**: {value:.1%}的转化率较高，说明产品价值获得认可，可考虑适度提价")
                    elif value < 0.08:
                        strategy_recommendations.append(f"🔸 **付费转化**: {value:.1%}的转化率偏低，建议优化产品体验和降低付费门槛")
            
            if strategy_recommendations:
                for rec in strategy_recommendations:
                    st.markdown(rec)
            else:
                st.info("💡 根据当前优化的参数类型，暂无特定的业务策略建议")
            
            # 显示现实约束分析
            if 'realistic_constraint_report' in result:
                st.subheader("🔍 现实约束分析")
                
                penalty_score = result.get('penalty_score', 0)
                if penalty_score == 0:
                    st.success("✅ 参数组合完全符合市场现实，无风险")
                elif penalty_score < 50:
                    st.info("🟡 参数组合基本合理，存在轻微的现实性问题")
                elif penalty_score < 200:
                    st.warning("🟠 参数组合存在一定的现实风险，建议谨慎实施")
                else:
                    st.error("🔴 参数组合严重偏离市场现实，强烈建议调整")
                
                st.metric("现实约束得分", f"{penalty_score:.1f}", 
                         delta="分数越低越好" if penalty_score > 0 else "理想状态")
                
                # 显示详细的约束报告
                with st.expander("查看详细的现实约束分析报告"):
                    st.markdown(result['realistic_constraint_report'])
            
            # 如果是集成优化，显示使用的算法信息
            if 'individual_results' in result:
                st.info(f"📊 本次优化使用了 {len(result['individual_results'])} 种算法，结果已自动融合")
            
            # 添加下载功能
            st.subheader("📥 导出结果")
            
            # 创建CSV下载内容
            export_data = []
            export_data.append(["优化结果总结", ""])
            export_data.append(["最佳得分", f"{result['best_score']:.2f}"])
            export_data.append(["使用算法", result.get('algorithm', '集成优化')])
            export_data.append(["", ""])
            export_data.append(["最优参数组合", ""])
            
            for param, value in result['best_params'].items():
                param_display = param.replace('_', ' ').replace('.', ' → ').title()
                if isinstance(value, float):
                    if 0 <= value <= 1 and ('rate' in param.lower() or 'share' in param.lower()):
                        value_display = f"{value:.1%}"
                    else:
                        value_display = f"{value:.2f}"
                else:
                    value_display = str(value)
                export_data.append([param_display, value_display])
            
            if strategy_recommendations:
                export_data.append(["", ""])
                export_data.append(["业务策略建议", ""])
                for rec in strategy_recommendations:
                    clean_rec = rec.replace("🔸 **", "").replace("**:", ":").replace("**", "")
                    export_data.append([clean_rec, ""])
            
            # 转换为DataFrame
            export_df = pd.DataFrame(export_data, columns=["项目", "值"])
            
            # 创建CSV下载
            csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📊 下载优化报告 (CSV)",
                    data=csv_data,
                    file_name=f"luma_optimization_report_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime='text/csv'
                )
            
            with col2:
                # 创建策略实施清单
                checklist_content = f"""# Luma策略优化实施清单

## 优化结果概览
- 最佳得分: {result['best_score']:.2f}
- 算法: {result.get('algorithm', '集成优化')}

## 参数调整清单
"""
                for param, value in result['best_params'].items():
                    param_display = param.replace('_', ' ').replace('.', ' → ').title()
                    if isinstance(value, float):
                        if 0 <= value <= 1 and ('rate' in param.lower() or 'share' in param.lower()):
                            value_display = f"{value:.1%}"
                        else:
                            value_display = f"{value:.2f}"
                    else:
                        value_display = str(value)
                    checklist_content += f"- [ ] {param_display}: 调整为 {value_display}\n"

                if strategy_recommendations:
                    checklist_content += "\n## 业务策略建议\n"
                    for rec in strategy_recommendations:
                        clean_rec = rec.replace("🔸 **", "").replace("**:", ":").replace("**", "")
                        checklist_content += f"- [ ] {clean_rec}\n"

                checklist_content += f"""
## 实施注意事项
- [ ] 在实施前进行小规模测试
- [ ] 监控关键指标变化
- [ ] 记录实施效果以便后续优化
- [ ] 定期回顾和调整策略

## 生成时间
{time.strftime('%Y年%m月%d日 %H:%M:%S')}
"""
                
                st.download_button(
                    label="📋 下载实施清单 (MD)",
                    data=checklist_content,
                    file_name=f"luma_strategy_checklist_{time.strftime('%Y%m%d_%H%M%S')}.md",
                    mime='text/markdown'
                )
            
            # 显示详细信息提示
            st.markdown("---")
            st.markdown("📋 **查看更多详细信息：**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if enable_monitoring:
                    st.write("→ 📊 优化监控与诊断")
            with col2:
                if enable_robustness:
                    st.write("→ 🔍 鲁棒性分析")
            with col3:
                if 'individual_results' in result:
                    st.write("→ 📈 结果对比分析")
            
        except Exception as e:
            st.error(f"优化过程中发生错误: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

# 页脚
st.markdown("---")
st.markdown("© 2025 Luma高校销售与收益分析模型 - 增强版策略优化系统 | Powered by Advanced AI Optimization")