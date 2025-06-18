"""
参数UI组件模块 - 提供Streamlit参数输入界面的组件
"""
import streamlit as st
import numpy as np
from typing import Dict, Any, Tuple, List

def render_basic_parameters() -> Dict[str, Any]:
    """
    渲染基础参数输入控件并返回参数值
    
    Returns:
        Dict[str, Any]: 包含基础参数的字典
    """
    st.sidebar.subheader("基础参数")
    total_half_years = st.sidebar.slider("模拟周期数（半年）", 2, 10, 4)
    new_clients_per_half_year = st.sidebar.slider("每半年新签约客户数", 1, 20, 5)
    
    return {
        'total_half_years': total_half_years,
        'new_clients_per_half_year': new_clients_per_half_year
    }

def render_mode_distribution() -> Tuple[Dict[str, float], float]:
    """
    渲染合作模式分布输入控件并返回分布值
    
    Returns:
        Tuple[Dict[str, float], float]: 包含模式分布的字典和分布总和
    """
    st.sidebar.subheader("合作模式分布")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        type1_share = st.number_input("Type1占比", 0.0, 1.0, 0.2, format="%.2f")
        type2a_share = st.number_input("Type2a占比", 0.0, 1.0, 0.0, format="%.2f")
        type2b_share = st.number_input("Type2b占比", 0.0, 1.0, 0.0, format="%.2f")
    
    with col2:
        type2c_share = st.number_input("Type2c占比", 0.0, 1.0, 0.2, format="%.2f")
        type3_share = st.number_input("Type3占比", 0.0, 1.0, 0.6, format="%.2f")
    
    mode_distribution = {
        'Type1': type1_share,
        'Type2a': type2a_share,
        'Type2b': type2b_share,
        'Type2c': type2c_share,
        'Type3': type3_share
    }
    
    mode_sum = sum(mode_distribution.values())
    
    return mode_distribution, mode_sum

def render_renewal_parameters() -> Dict[str, float]:
    """
    渲染续约率参数输入控件并返回参数值
    
    Returns:
        Dict[str, float]: 包含续约率参数的字典
    """
    st.sidebar.subheader("续约率参数")
    renewal_rate_uni = st.sidebar.slider("高校年度续约率", 0.0, 1.0, 0.8, format="%.2f")
    renewal_rate_student = st.sidebar.slider("学生年度续约率", 0.0, 1.0, 0.7, format="%.2f")
    
    return {
        'renewal_rate_uni': renewal_rate_uni,
        'renewal_rate_student': renewal_rate_student
    }

def render_advanced_parameters() -> Dict[str, Any]:
    """
    渲染高级参数输入控件并返回参数值
    
    Returns:
        Dict[str, Any]: 包含高级参数的字典
    """
    with st.sidebar.expander("高级参数设置"):
        avg_students_per_uni = st.number_input("平均学生数/校", 1000, 50000, 10000)
        student_total_paid_cr = st.slider("学生付费转化率", 0.0, 0.2, 0.05, format="%.3f")
        
        st.subheader("学生付费用户分布")
        share_paid_user_per_use_only = st.slider("单次付费用户占比", 0.0, 1.0, 0.3, format="%.2f")
        share_paid_user_membership = st.slider("会员付费用户占比", 0.0, 1.0, 0.7, format="%.2f")
        
        paid_user_sum = share_paid_user_per_use_only + share_paid_user_membership
        if not np.isclose(paid_user_sum, 1.0):
            st.warning(f"付费用户分布总和为 {paid_user_sum:.2f}，应为 1.0")
    
    return {
        'avg_students_per_uni': avg_students_per_uni,
        'student_total_paid_cr': student_total_paid_cr,
        'share_paid_user_per_use_only': share_paid_user_per_use_only,
        'share_paid_user_membership': share_paid_user_membership
    }

def render_fee_parameters() -> Dict[str, Dict[str, float]]:
    """
    渲染费用参数输入控件并返回参数值
    
    Returns:
        Dict[str, Dict[str, float]]: 包含费用参数的嵌套字典
    """
    with st.sidebar.expander("费用参数设置"):
        st.subheader("固定接入费")
        type1_access_fee = st.number_input("Type1接入费", 0.0, 100000.0, 20000.0, format="%.2f")
        type2_access_fee_a = st.number_input("Type2a接入费", 0.0, 100000.0, 0.0, format="%.2f")
        type2_access_fee_b = st.number_input("Type2b接入费", 0.0, 100000.0, 0.0, format="%.2f")
        type2_access_fee_c = st.number_input("Type2c接入费", 0.0, 100000.0, 30000.0, format="%.2f")
        type3_access_fee = st.number_input("Type3接入费", 0.0, 100000.0, 50000.0, format="%.2f")
        
        st.subheader("学生付费分成比例")
        type1_luma_share = st.slider("Type1 Luma分成", 0.0, 1.0, 0.3, format="%.2f")
        type2_luma_share_a = st.slider("Type2a Luma分成", 0.0, 1.0, 0.0, format="%.2f")
        type2_luma_share_b = st.slider("Type2b Luma分成", 0.0, 1.0, 0.0, format="%.2f")
        type2_luma_share_c = st.slider("Type2c Luma分成", 0.0, 1.0, 0.4, format="%.2f")
        type3_luma_share = st.slider("Type3 Luma分成", 0.0, 1.0, 0.5, format="%.2f")
    
    return {
        'type1_access_fee': type1_access_fee,
        'type2_access_fees': {
            'a': type2_access_fee_a,
            'b': type2_access_fee_b,
            'c': type2_access_fee_c
        },
        'type3_access_fee': type3_access_fee,
        'type1_luma_share_from_student': type1_luma_share,
        'type2_luma_share_from_student': {
            'a': type2_luma_share_a,
            'b': type2_luma_share_b,
            'c': type2_luma_share_c
        },
        'type3_luma_share_from_student': type3_luma_share
    }

def render_student_fee_parameters() -> Dict[str, Any]:
    """
    渲染学生付费参数输入控件并返回参数值
    
    Returns:
        Dict[str, Any]: 包含学生付费参数的字典
    """
    with st.sidebar.expander("学生付费参数"):
        st.subheader("学生付费模式")
        student_fee_model = st.selectbox(
            "付费模式",
            ["type1"],
            index=0
        )
        
        st.subheader("单次付费价格")
        per_use_fee = st.number_input("单次付费价格", 0.0, 1000.0, 50.0, format="%.2f")
        
        st.subheader("会员付费价格")
        membership_fee_half_year = st.number_input("半年会员价格", 0.0, 1000.0, 100.0, format="%.2f")
        
        st.subheader("使用频率")
        avg_uses_per_half_year_per_use_only = st.slider("单次付费用户平均使用次数/半年", 1, 20, 3)
        avg_uses_per_half_year_membership = st.slider("会员用户平均使用次数/半年", 1, 50, 10)
    
    return {
        'student_fee_model': student_fee_model,
        'per_use_fee': per_use_fee,
        'membership_fee_half_year': membership_fee_half_year,
        'avg_uses_per_half_year_per_use_only': avg_uses_per_half_year_per_use_only,
        'avg_uses_per_half_year_membership': avg_uses_per_half_year_membership
    }

def collect_all_parameters() -> Dict[str, Any]:
    """
    收集所有参数输入并返回完整的参数字典
    
    Returns:
        Dict[str, Any]: 包含所有模型参数的字典
    """
    # 基础参数
    params = render_basic_parameters()
    
    # 模式分布
    mode_distribution, mode_sum = render_mode_distribution()
    params['mode_distribution'] = mode_distribution
    
    # 显示模式分布总和警告
    if not np.isclose(mode_sum, 1.0):
        st.sidebar.warning(f"模式分布总和为 {mode_sum:.2f}，应为 1.0")
    
    # 续约率参数
    renewal_params = render_renewal_parameters()
    params.update(renewal_params)
    
    # 高级参数
    advanced_params = render_advanced_parameters()
    params.update(advanced_params)
    
    # 费用参数
    fee_params = render_fee_parameters()
    params.update(fee_params)
    
    # 学生付费参数
    student_fee_params = render_student_fee_parameters()
    params.update(student_fee_params)
    
    return params

def render_parameter_presets() -> Dict[str, Any]:
    """
    渲染参数预设选择控件并返回选定的预设参数
    
    Returns:
        Dict[str, Any]: 选定的预设参数，如果未选择预设则返回None
    """
    st.sidebar.subheader("参数预设")
    
    presets = {
        "默认设置": None,
        "高增长情景": {
            'new_clients_per_half_year': 10,
            'renewal_rate_uni': 0.9,
            'renewal_rate_student': 0.8,
            'student_total_paid_cr': 0.08
        },
        "低增长情景": {
            'new_clients_per_half_year': 3,
            'renewal_rate_uni': 0.7,
            'renewal_rate_student': 0.6,
            'student_total_paid_cr': 0.03
        }
    }
    
    selected_preset = st.sidebar.selectbox("选择预设", list(presets.keys()))
    
    return presets[selected_preset]

def render_sensitivity_analysis_controls() -> Tuple[str, List[float]]:
    """
    渲染敏感性分析控件并返回分析参数
    
    Returns:
        Tuple[str, List[float]]: 选定的参数名称和测试值列表
    """
    st.subheader("选择要分析的参数")
    param_to_analyze = st.selectbox(
        "参数",
        [
            "new_clients_per_half_year", 
            "renewal_rate_uni", 
            "renewal_rate_student",
            "student_total_paid_cr",
            "type1_luma_share_from_student",
            "type2_luma_share_from_student.c",
            "type3_luma_share_from_student"
        ]
    )
    
    # 根据参数类型设置合适的范围和步长
    min_val, max_val, steps = 0, 0, 0
    if param_to_analyze == "new_clients_per_half_year":
        min_val, max_val, steps = 1, 10, 10
    elif "renewal_rate" in param_to_analyze:
        min_val, max_val, steps = 0.5, 1.0, 6
    elif "student_total_paid_cr" == param_to_analyze:
        min_val, max_val, steps = 0.01, 0.1, 10
    elif "luma_share" in param_to_analyze:
        min_val, max_val, steps = 0.1, 0.7, 7
    
    test_values = np.linspace(min_val, max_val, steps).tolist()
    test_values = [round(val, 3) for val in test_values]
    
    st.write(f"测试值: {test_values}")
    
    return param_to_analyze, test_values
