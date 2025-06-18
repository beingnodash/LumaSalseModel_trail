# streamlit_app/utils/localization.py

PARAM_NAME_MAP = {
    # 预测周期配置
    'total_half_years': '总分析周期数（半年）',
    'single_period_length_months': '单个分析周期时长（月）',

    # 签约目标与模式分布
    'new_clients_per_half_year': '每半年新签约高校数',
    'mode_distribution_Type1': '模式1签约比例',
    'mode_distribution_Type2a': '模式2a签约比例',
    'mode_distribution_Type2b': '模式2b签约比例',
    'mode_distribution_Type2c': '模式2c签约比例',
    'mode_distribution_Type3': '模式3签约比例',

    # 高校与学生规模
    'avg_students_per_uni': '平均每高校学生数',

    # 学生付费行为
    'student_total_paid_cr': '学生总付费转化率',
    'share_paid_user_per_use_only': '付费用户中单次功能比例',
    'share_paid_user_membership': '付费用户中会员比例',
    'avg_per_use_features_half_year': '每付费学生半年单次功能使用次数',
    'member_purchase_shares_Annual': '年费会员购买比例',
    'member_purchase_shares_3Year': '3年会员购买比例',
    'member_purchase_shares_5Year': '5年会员购买比例',

    # 定价与分成
    'price_per_feature_use': '单次功能价格',
    'price_annual_member': '年费会员价格',
    'price_3year_member': '3年会员价格',
    'price_5year_member': '5年会员价格',
    'type1_access_fee': '模式1高校使用费',
    'type2_access_fees_a': '模式2a高校使用费',
    'type2_access_fees_b': '模式2b高校使用费',
    'type2_access_fees_c': '模式2c高校使用费',
    'type2_luma_share_from_student_a': '模式2a Luma学生付费分成',
    'type2_luma_share_from_student_b': '模式2b Luma学生付费分成',
    'type2_luma_share_from_student_c': '模式2c Luma学生付费分成',

    # 客户留存/续约
    'renewal_rate_uni': '高校客户年度续约率',
    'renewal_rate_student': '学生付费用户年度续约率',
    
    # 优化算法特定参数
    'grid_search_steps': '网格搜索步数',
    'bayesian_n_iter': '贝叶斯优化迭代次数',
    'bayesian_init_points': '贝叶斯优化初始点数',
    'bayesian_xi': '贝叶斯优化探索-利用平衡因子',
    'ga_population_size': '遗传算法种群大小',
    'ga_n_generations': '遗传算法迭代代数',
    'ga_mutation_rate': '遗传算法变异率',
    'ga_crossover_prob': '遗传算法交叉概率',

    # 目标指标
    'Luma_Revenue_Total_Sum': 'Luma总收入',
    'Uni_Fund_Total_Sum': '高校基金总额',
    # ... 更多指标可以按需添加
}

# 反向映射，用于从中文名查找英文名 (如果需要)
PARAM_NAME_MAP_REVERSE = {v: k for k, v in PARAM_NAME_MAP.items()}

def get_param_display_name(param_key: str) -> str:
    """获取参数的中文显示名称，如果未找到则返回原始key。"""
    return PARAM_NAME_MAP.get(param_key, param_key)

def get_param_internal_name(param_display_name: str) -> str:
    """获取参数的内部英文名称，如果未找到则返回原始显示名称。"""
    return PARAM_NAME_MAP_REVERSE.get(param_display_name, param_display_name)
