import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from typing import Dict, Any, List
import copy

class LumaFinancialModel:
    """
    Luma高校销售与收益分析模型 (Luma University Sales & Revenue Analysis Model)

    该模型用于模拟和预测Luma公司在高校业务中的销售收入和相关财务指标。
    核心功能包括：
    - 基于可配置参数进行多周期（半年）的财务预测。
    - 支持多种高校合作模式，每种模式有不同的收费结构和分成比例。
    - 模拟新客户签约过程。
    - 实现客户群组（Cohorts）跟踪，模拟高校和学生的年度续约行为。
    - 输出详细的收入构成（新签、续约、固定费用、学生付费分成等）。
    - 提供结果的可视化图表。

    使用方法：
    1. 实例化模型: `model = LumaFinancialModel(custom_params)` (custom_params可选)
    2. 运行模型: `results_df = model.run_model()`
    3. 查看结果: `print(results_df)` 或 `results_df.to_csv('results.csv')`
    4. 生成图表: `model.plot_results()`
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        初始化模型参数。

        参数可以作为字典传入。如果未提供 `params` 或某些参数缺失，
        将使用类中定义的 `default_params`。

        Args:
            params (Dict[str, Any], optional): 用户自定义参数字典.
                                               键为参数名, 值为参数值.
                                               Defaults to None.
        """
        default_params = {
            # --- 模拟周期与客户增长 ---
            'total_half_years': 4,  # 总共分析多少个半年周期 (例如: 4个半年 = 2年)
            'new_clients_per_half_year': 5,  # 每个半年计划新签约高校总数
            
            # --- 高校合作模式分布 (各模式占比，总和应为1) ---
            # 键: 模式名称 (str), 值: 该模式占比 (float)
            'mode_distribution': {
                'Type1': 0.2, 
                'Type2a': 0.0,
                'Type2b': 0.0, 
                'Type2c': 0.2,
                'Type3': 0.6  
            },

            # --- 高校与学生基础数据 ---
            'avg_students_per_uni': 10000, # 平均每所签约高校学生总人数
            'student_total_paid_cr': 0.05, # 学生总付费转化率 (在校总学生中，转化为付费用户的比例)

            # --- 学生付费行为细分 (在已付费用户中) ---
            'share_paid_user_per_use_only': 0.5, # 选择按次付费功能的用户比例
            'share_paid_user_membership': 0.5, # 选择购买会员的用户比例
            'avg_per_use_features_half_year': 2, # 平均每个【按次付费】学生半年内使用单次功能总次数

            # --- 定价策略 ---
            'price_per_feature_use': 7.9,  # 单次功能使用价格
            'price_annual_member': 29.0,   # 年度会员价格
            'price_3year_member': 69.0,    # 三年期会员价格
            'price_5year_member': 99.0,    # 五年期会员价格

            # --- 会员购买类型分布 (在购买会员的用户中，占比总和应为1) ---
            # 键: 会员类型 (str), 值: 该类型购买比例 (float)
            'member_purchase_shares': {
                'Annual': 0.9, 
                '3Year': 0.1,  
                '5Year': 0.0   
            },

            # --- 各合作模式固定收费 (一次性，新签时收取) ---
            'type1_access_fee': 200000.0, # 模式1接入费
            # 模式2各子类型接入费
            # 键: 子类型 (str, e.g., 'a', 'b', 'c'), 值: 接入费 (float)
            'type2_access_fees': {      
                'a': 200000.0,
                'b': 150000.0,
                'c': 100000.0
            },

            # --- 各合作模式Luma学生付费分成比例 (从学生付费流水中Luma获得的部分) ---
            # 键: 子类型 (str, e.g., 'a', 'b', 'c'), 值: Luma分成比例 (float)
            'type2_luma_share_from_student': {
                'a': 0.5, 
                'b': 0.6, 
                'c': 0.7  
            },
            
            # --- 学生付费模型选择 ---
            # 'type1': 基于高校平均学生数和总体转化率计算付费用户基数
            # 'type2': (未来扩展) 可能基于更细致的学生分群或行为模式
            'student_fee_model': 'type1',

            # --- 年度续约率 (应用于每年结束，即每2个半年周期后) ---
            'renewal_rate_uni': 0.80,     # 高校客户年度续约率
            'renewal_rate_student': 0.70  # 学生用户年度留存/续约率 (针对已付费学生群体)
        }
        # 深拷贝默认参数以确保每个实例有独立的参数副本
        self.params = copy.deepcopy(default_params)
        if params:
            # 用户传入的参数会覆盖默认参数，同样使用深拷贝处理嵌套结构
            for key, value in params.items():
                if isinstance(value, dict) and key in self.params and isinstance(self.params[key], dict):
                    # 对于字典，进行递归更新式的深拷贝
                    self.params[key].update(copy.deepcopy(value))
                elif isinstance(value, list) and key in self.params and isinstance(self.params[key], list):
                    # 对于列表，直接替换为深拷贝副本
                    self.params[key] = copy.deepcopy(value)
                else:
                    # 其他类型直接赋值（如果是可变类型如自定义对象，也应考虑深拷贝）
                    self.params[key] = copy.deepcopy(value) if isinstance(value, (dict, list)) else value

        self._validate_params() # 执行参数校验

        self.results_df = None # 用于存储模型运行结果的DataFrame
        self.cohorts = []      # 用于存储每个客户群组的详细信息

    def _validate_params(self):
        """
        校验关键模型参数的合理性与一致性.

        主要检查:
        - 概率和比例参数是否在 [0, 1] 区间内.
        - 分布型参数(如模式分布, 付费行为分布)的各项之和是否为1.
        - 数值型参数(如周期数, 费用, 价格)是否为非负.
        - 特定枚举型参数(如学生付费模型)是否为有效值.

        对于不符合约束的参数, 此方法会发出警告 (warnings.warn),
        并在某些情况下尝试将参数重置为合理的边界值(例如, 将超出[0,1]的比例修正到0或1).
        对于总和不为1的分布, 仅发出警告, 不进行自动修正.
        """
        p = self.params

        # 校验学生付费模型参数
        valid_student_fee_models = ['type1'] # 未来可以扩展, e.g., ['type1', 'type2']
        if p.get('student_fee_model') not in valid_student_fee_models:
            warnings.warn(
                f"参数 'student_fee_model' 的值 ('{p.get('student_fee_model')}') 不是有效选项 "
                f"({valid_student_fee_models})。已重置为 '{valid_student_fee_models[0]}'."
            )
            p['student_fee_model'] = valid_student_fee_models[0]

        # 校验概率/比例参数 (应在0到1之间)
        ratio_params = [
            'student_total_paid_cr', 'share_paid_user_per_use_only', 'share_paid_user_membership',
            'renewal_rate_uni', 'renewal_rate_student'
        ]
        for rp_key in ratio_params:
            if not (0 <= p[rp_key] <= 1):
                warnings.warn(f"参数 '{rp_key}' 的值 ({p[rp_key]}) 超出合理范围 [0, 1]. 已重置为边界值。")
                p[rp_key] = max(0, min(1, p[rp_key]))
        
        # 校验模式分布总和
        if not np.isclose(sum(p['mode_distribution'].values()), 1.0):
            warnings.warn(f"参数 'mode_distribution' 各模式占比之和 ({sum(p['mode_distribution'].values())}) 不为1。请检查配置。")
        
        # 校验付费用户行为细分比例总和
        if not np.isclose(p['share_paid_user_per_use_only'] + p['share_paid_user_membership'], 1.0):
            warnings.warn("参数 'share_paid_user_per_use_only' 和 'share_paid_user_membership' 之和不为1。请检查配置。")

        # 校验会员购买类型分布总和
        if not np.isclose(sum(p['member_purchase_shares'].values()), 1.0):
            warnings.warn(f"参数 'member_purchase_shares' 各类型占比之和 ({sum(p['member_purchase_shares'].values())}) 不为1。请检查配置。")

        # 校验数值型参数非负性
        non_negative_params = [
            'total_half_years', 'new_clients_per_half_year', 'avg_students_per_uni',
            'avg_per_use_features_half_year', 'price_per_feature_use', 'price_annual_member',
            'price_3year_member', 'price_5year_member', 'type1_access_fee'
        ]
        for nnp_key in non_negative_params:
            if p[nnp_key] < 0:
                warnings.warn(f"参数 '{nnp_key}' 的值 ({p[nnp_key]}) 为负。已重置为0。")
                p[nnp_key] = 0
        
        for fee_key in p['type2_access_fees']:
            if p['type2_access_fees'][fee_key] < 0:
                param_display_name = f"type2_access_fees['{fee_key}']"
                warnings.warn(f"参数 '{param_display_name}' 的值 ({p['type2_access_fees'][fee_key]}) 为负。已重置为0。")
                p['type2_access_fees'][fee_key] = 0

        for share_key in p['type2_luma_share_from_student']:
            if not (0 <= p['type2_luma_share_from_student'][share_key] <= 1):
                param_display_name = f"type2_luma_share_from_student['{share_key}']"
                warnings.warn(f"参数 '{param_display_name}' 的值 ({p['type2_luma_share_from_student'][share_key]}) 超出合理范围 [0, 1]. 已重置为边界值。")
                p['type2_luma_share_from_student'][share_key] = max(0, min(1, p['type2_luma_share_from_student'][share_key]))

    def _calculate_avg_student_revenue(self) -> float:
        """
        计算平均每个[付费学生]在单个半年周期内产生的"总收入流水".
        
        此计算基于学生选择不同付费方式(按次付费, 会员)的比例及其对应价格.
        多年期会员费在此被平均分摊到每个半年周期进行计算. 例如, 年度会员费会被除以2,
        三年期会员费(覆盖6个半年)会被除以6再乘以1(代表当前半年), 以此类推,
        但在当前简化模型中, 所有会员费均直接除以其覆盖的半年数来得到单半年的等效收入贡献.
        更准确地说, 是将会员的总价值在其有效期内的每个半年平均分摊.

        Returns:
            float: 平均每个付费学生半年贡献的总收入流水.
        """
        p = self.params

        # 1. 计算按次付费用户的半年收入贡献
        # = 平均使用次数 * 单次价格
        revenue_per_use_user_half_year = (
            p['avg_per_use_features_half_year'] * p['price_per_feature_use']
        )

        # 2. 计算会员用户的半年收入贡献
        # 会员收入需要将其年费/多年期费用折算到半年周期
        # 例如，年度会员价/2，三年会员价/6，五年会员价/10 (因为模型按半年计算)
        # 当前简化处理：所有会员价格直接除以其覆盖的半年数
        # (Annual=2个半年, 3Year=6个半年, 5Year=10个半年)
        
        # 年度会员的半年等效收入
        member_annual_rev_hy = p['price_annual_member'] / 2  
        # 三年会员的半年等效收入
        member_3year_rev_hy = p['price_3year_member'] / (3 * 2) 
        # 五年会员的半年等效收入
        member_5year_rev_hy = p['price_5year_member'] / (5 * 2) 

        # 根据各类型会员购买比例，计算会员用户的平均半年收入
        revenue_per_member_user_half_year = (
            p['member_purchase_shares']['Annual'] * member_annual_rev_hy +
            p['member_purchase_shares']['3Year'] * member_3year_rev_hy +
            p['member_purchase_shares']['5Year'] * member_5year_rev_hy
        )

        # 3. 加权平均得到每个付费学生的总平均半年收入
        avg_total_revenue_per_paid_student_half_year = (
            p['share_paid_user_per_use_only'] * revenue_per_use_user_half_year +
            p['share_paid_user_membership'] * revenue_per_member_user_half_year
        )
        
        return avg_total_revenue_per_paid_student_half_year

    def _calculate_uni_revenue_streams_new_signup(self, uni_type: str) -> Dict[str, float]:
        """
        计算[新签约]的单所高校, 在首个半年周期内产生的各项收入流细分.

        这包括该高校贡献的一次性固定接入费(如果模式有)以及首期学生付费带来的收入.

        Args:
            uni_type (str): 高校的合作模式类型 (例如 'Type1', 'Type2a', 'Type3').

        Returns:
            Dict[str, float]: 包含Luma固定费用, Luma学生付费分成, 高校基金的字典.
                              例如: {'luma_fixed_fee': X, 'luma_student_share': Y, 'uni_fund': Z}
        
        Raises:
            ValueError: 如果传入未知的 `uni_type`.
        """
        p = self.params
        
        # 1. 计算该高校初始付费学生带来的总学生付费流水
        #    - 平均每付费学生收入 * 该校初始付费学生数
        #    - 该校初始付费学生数 = 平均学生总数 * 学生总付费转化率
        avg_revenue_per_paying_student = self._calculate_avg_student_revenue()
        initial_paying_students_per_uni = p['avg_students_per_uni'] * p['student_total_paid_cr']
        total_student_revenue_stream_per_uni = initial_paying_students_per_uni * avg_revenue_per_paying_student

        # 初始化各收入项
        luma_revenue_from_fixed_fee = 0.0
        luma_revenue_from_student_share = 0.0
        uni_fund = 0.0 # 高校从学生付费中获得的部分

        try:
            if uni_type == 'Type1':
                # 模式1: Luma收取固定接入费。学生付费流水全部归属高校。
                luma_revenue_from_fixed_fee = self._get_nested_param(p, 'type1_access_fee')
                luma_revenue_from_student_share = 0.0  # Luma不参与学生付费分成
                uni_fund = total_student_revenue_stream_per_uni # 学生付费流水归高校
            elif uni_type.startswith('Type2'):
                # 模式2 (a,b,c): Luma收取固定接入费，并按比例从学生付费中分成
                option = uni_type[-1] # 'a', 'b', or 'c'
                # _get_nested_param will raise KeyError if path is invalid
                luma_revenue_from_fixed_fee = self._get_nested_param(p, f'type2_access_fees.{option}')
                luma_share_rate = self._get_nested_param(p, f'type2_luma_share_from_student.{option}')
                
                luma_revenue_from_student_share = total_student_revenue_stream_per_uni * luma_share_rate
                uni_fund = total_student_revenue_stream_per_uni * (1 - luma_share_rate)
            elif uni_type == 'Type3':
                # 模式3: Luma不收取固定费用，但从学生付费中获得100%分成
                luma_revenue_from_fixed_fee = 0.0 # Luma无固定费用
                luma_revenue_from_student_share = total_student_revenue_stream_per_uni # Luma获得全部学生付费
                uni_fund = 0.0 # 高校无学生付费分成
            else:
                raise ValueError(f"未知的高校合作模式: {uni_type}")
        except KeyError as e:
            # Re-raise as ValueError to indicate bad configuration for the given uni_type
            raise ValueError(f"配置错误: 高校类型 '{uni_type}' 的参数缺失或路径无效. 详细: {e}") from e

        return {
            'luma_fixed_fee': luma_revenue_from_fixed_fee,
            'luma_student_share': luma_revenue_from_student_share,
            'uni_fund': uni_fund
        }
    
    def _calculate_ongoing_student_revenue_for_cohort_uni(self, uni_type: str, current_paying_students_this_uni: float) -> Dict[str, float]:
        """
        计算[已存续群组中的单所高校]因学生付费(不含固定费用)带来的Luma收入和高校基金.

        此方法用于计算老客户在续约期内, 其现有付费学生群体持续贡献的收入.
        不包含任何一次性的固定费用, 因为这些通常只在新签约时发生.

        Args:
            uni_type (str): 高校的合作模式类型.
            current_paying_students_this_uni (float): 该高校当前周期的活跃付费学生数.
                                                     (可能因学生续约率而少于初始值)

        Returns:
            Dict[str, float]: 包含Luma学生付费分成和高校基金的字典.
                              例如: {'luma_student_share': Y, 'uni_fund': Z}
            
        Raises:
            ValueError: 如果传入未知的 `uni_type` 或无效的Type2子模式.
        """
        p = self.params
        avg_revenue_per_paying_student = self._calculate_avg_student_revenue()
            
        # 1. 计算该高校当前付费学生带来的总学生付费流水
        total_student_revenue_stream_this_uni = current_paying_students_this_uni * avg_revenue_per_paying_student
            
        luma_student_share = 0.0
        uni_fund = 0.0

        # 2. 根据高校合作模式，分配学生付费流水 (续约期通常无新的固定费用)
        try:
            if uni_type == 'Type1':
                # 模式1: Luma不参与学生付费分成。学生付费流水全部归属高校。
                luma_student_share = 0.0  # Luma无学生付费分成
                uni_fund = total_student_revenue_stream_this_uni # 学生付费流水归高校
            elif uni_type.startswith('Type2'):
                # 模式2 (a,b,c): Luma按比例从学生付费中分成
                option = uni_type[-1] # 'a', 'b', or 'c'
                # _get_nested_param will raise KeyError if path is invalid
                luma_share_rate = self._get_nested_param(p, f'type2_luma_share_from_student.{option}')
                
                luma_student_share = total_student_revenue_stream_this_uni * luma_share_rate
                uni_fund = total_student_revenue_stream_this_uni * (1 - luma_share_rate)
            elif uni_type == 'Type3':
                # 模式3: Luma从学生付费中获得100%分成
                luma_student_share = total_student_revenue_stream_this_uni # Luma获得全部学生付费
                uni_fund = 0.0 # 高校无学生付费分成
            else:
                raise ValueError(f"未知的高校合作模式: {uni_type}")
        except KeyError as e:
            # Re-raise as ValueError to indicate bad configuration for the given uni_type
            raise ValueError(f"配置错误: 高校类型 '{uni_type}' 的参数缺失或路径无效. 详细: {e}") from e

        return {
            'luma_student_share': luma_student_share,
            'uni_fund': uni_fund
        }

    def run_model(self) -> pd.DataFrame:
        """
        运行财务模型, 模拟多个半年周期的收入情况.

        核心逻辑包括:
        1. 迭代每个半年周期.
        2. 处理现有客户群组的续约(高校层面和学生层面).
        3. 计算续约群组贡献的持续收入(主要来自学生付费).
        4. 处理新签约的高校, 创建新群组, 并计算其首期收入.
        5. 汇总每个周期的各项收入指标.
        6. 将结果存储在Pandas DataFrame中.

        此方法会更新实例的 `self.results_df` 和 `self.cohorts` 属性.

        Args:
            None: 此方法直接使用实例初始化时配置的参数 (self.params).
        # 全局初始付费学生数，用于新群组创建 (避免重复计算)
        """
        p = self.params # Define p for convenience
        avg_students_per_uni = self._get_nested_param(p, 'avg_students_per_uni')
        student_total_paid_cr = self._get_nested_param(p, 'student_total_paid_cr')
        initial_paying_students_per_uni_global = avg_students_per_uni * student_total_paid_cr
        
        new_clients_per_half_year = self._get_nested_param(p, 'new_clients_per_half_year') # Fetch this parameter
        total_half_years = self._get_nested_param(p, 'total_half_years')
        mode_distribution = self._get_nested_param(p, 'mode_distribution')
        if not isinstance(mode_distribution, dict):
            raise ValueError("参数 'mode_distribution' 必须是一个字典.")

        renewal_rate_uni = self._get_nested_param(p, 'renewal_rate_uni')
        renewal_rate_student = self._get_nested_param(p, 'renewal_rate_student')

        # --- 按周期迭代 --- 
        period_summary_data = [] # Initialize list to store period summaries
        for current_period_idx in range(total_half_years):
            period_name = f"H{current_period_idx + 1}" # 例如 H1, H2, ...
            
            # 初始化本周期各项收入指标的累加器
            current_period_summary = {
                'Period': period_name,
                'Luma_Fixed_Fee_New': 0.0, 
                'Luma_Student_Share_New': 0.0, 
                'Luma_Student_Share_Renewed': 0.0,
                'Uni_Fund_New_Total': 0.0, 
                'Uni_Fund_Renewed_Total': 0.0,
                'Luma_Revenue_Total': 0.0, 
                'Uni_Fund_Total': 0.0
            }
            # 为每种高校类型初始化新签和续约的详细收入与基金字段
            for ut in mode_distribution.keys():
                current_period_summary[f'Luma_Revenue_{ut}_New'] = 0.0
                current_period_summary[f'Luma_Revenue_{ut}_Renewed'] = 0.0
                current_period_summary[f'Uni_Fund_{ut}_New'] = 0.0
                current_period_summary[f'Uni_Fund_{ut}_Renewed'] = 0.0

            # === 1. 处理现有客户群组的续约和收入贡献 ===
            active_cohorts_for_next_period_calculation = [] # 存储本周期结束后仍然活跃的群组
            for cohort in self.cohorts: # 遍历上周期结束时存在的所有群组
                if not cohort['is_active']: 
                    continue # 跳过已标记为不活跃的群组

                # 计算群组年龄（单位：半年）
                age_in_half_years = current_period_idx - cohort['start_period_idx']
                
                # 应用【年度】续约率 (仅在每个【年度】结束时，即群组年龄为2, 4, 6...个半年时)
                if age_in_half_years > 0 and age_in_half_years % 2 == 0:
                    # a. 高校层面续约
                    cohort['num_unis'] = round(cohort['num_unis'] * renewal_rate_uni)
                    if cohort['num_unis'] == 0:
                        cohort['is_active'] = False # 如果高校全部流失，群组不再活跃
                        continue # 不再计算此群组本期收入，也不加入下一轮活跃列表
                    
                    # b. 学生层面续约/留存 (针对群组内每所高校的付费学生数)
                    cohort['current_paying_students_per_uni'] *= renewal_rate_student

                # 如果群组内仍有活跃高校，则计算其在本周期的【续约学生付费】收入
                if cohort['num_unis'] > 0:
                    revenue_from_this_cohort_unis = self._calculate_ongoing_student_revenue_for_cohort_uni(
                        cohort['uni_type'], 
                        cohort['current_paying_students_per_uni']
                    )
                    
                    # 累加到本周期总的续约收入中
                    luma_student_share_from_this_cohort = revenue_from_this_cohort_unis['luma_student_share'] * cohort['num_unis']
                    uni_fund_from_this_cohort = revenue_from_this_cohort_unis['uni_fund'] * cohort['num_unis']
                    
                    current_period_summary[f'Luma_Revenue_{cohort["uni_type"]}_Renewed'] += luma_student_share_from_this_cohort
                    current_period_summary[f'Uni_Fund_{cohort["uni_type"]}_Renewed'] += uni_fund_from_this_cohort
                    current_period_summary['Luma_Student_Share_Renewed'] += luma_student_share_from_this_cohort
                    current_period_summary['Uni_Fund_Renewed_Total'] += uni_fund_from_this_cohort
                
                # 如果群组在本周期结束后依然活跃，则将其加入列表，供下一周期计算
                if cohort['is_active']:
                    active_cohorts_for_next_period_calculation.append(cohort)
            
            self.cohorts = active_cohorts_for_next_period_calculation # 更新活跃群组列表

            # === 2. 处理本周期【新签约】的客户 ===
            for uni_type, share_of_new_clients in mode_distribution.items():
                num_new_unis_of_this_type = round(new_clients_per_half_year * share_of_new_clients)
                if num_new_unis_of_this_type == 0: 
                    continue # 如果此类型本期无新签约，则跳过

                # 创建新的客户群组条目
                new_cohort_entry = {
                    'start_period_idx': current_period_idx, # 签约的起始周期
                    'uni_type': uni_type,                   # 高校合作模式
                    'num_unis': num_new_unis_of_this_type,  # 该群组中此类型高校数量
                    'initial_paying_students_per_uni': initial_paying_students_per_uni_global, # 初始付费学生数/校
                    'current_paying_students_per_uni': initial_paying_students_per_uni_global, # 当前付费学生数/校 (初始与上面相同)
                    'is_active': True # 新群组默认为活跃
                }
                self.cohorts.append(new_cohort_entry) # 将新群组加入总列表

                # 计算这些新签约高校的首期收入 (固定费用 + 首期学生付费)
                revenue_streams_for_new_signup = self._calculate_uni_revenue_streams_new_signup(uni_type)
                
                luma_fixed_fee_from_new_cohort = revenue_streams_for_new_signup['luma_fixed_fee'] * num_new_unis_of_this_type
                luma_student_share_from_new_cohort = revenue_streams_for_new_signup['luma_student_share'] * num_new_unis_of_this_type
                uni_fund_from_new_cohort = revenue_streams_for_new_signup['uni_fund'] * num_new_unis_of_this_type

                # 累加到本周期总的新签收入中
                current_period_summary[f'Luma_Revenue_{uni_type}_New'] += (luma_fixed_fee_from_new_cohort + luma_student_share_from_new_cohort)
                current_period_summary[f'Uni_Fund_{uni_type}_New'] += uni_fund_from_new_cohort
                current_period_summary['Luma_Fixed_Fee_New'] += luma_fixed_fee_from_new_cohort
                current_period_summary['Luma_Student_Share_New'] += luma_student_share_from_new_cohort
                current_period_summary['Uni_Fund_New_Total'] += uni_fund_from_new_cohort

            # === 3. 汇总本周期各项总收入 ===
            current_period_summary['Luma_Revenue_Total'] = (
                current_period_summary['Luma_Fixed_Fee_New'] + 
                current_period_summary['Luma_Student_Share_New'] + 
                current_period_summary['Luma_Student_Share_Renewed']
            )
            current_period_summary['Uni_Fund_Total'] = (
                current_period_summary['Uni_Fund_New_Total'] + 
                current_period_summary['Uni_Fund_Renewed_Total']
            )
            
            period_summary_data.append(current_period_summary) # 将本周期结果加入列表

        # --- 模型运行结束，构建并返回结果DataFrame ---
        # 定义DataFrame的列顺序，确保输出的一致性和可读性
        column_order = ['Period']
        detailed_cols_template = ['Luma_Revenue_{}_New', 'Luma_Revenue_{}_Renewed', 'Uni_Fund_{}_New', 'Uni_Fund_{}_Renewed']
        for ut_key in mode_distribution.keys(): # 使用参数中的key确保顺序
            for col_template_str in detailed_cols_template:
                column_order.append(col_template_str.format(ut_key))
        column_order.extend([
            'Luma_Fixed_Fee_New', 'Luma_Student_Share_New', 'Luma_Student_Share_Renewed',
            'Uni_Fund_New_Total', 'Uni_Fund_Renewed_Total',
            'Luma_Revenue_Total', 'Uni_Fund_Total'
        ])

        self.results_df = pd.DataFrame(period_summary_data)
        # 使用reindex确保所有定义的列都存在 (即使某些周期数据为0)，并填充NaN为0，然后设置Period为索引
        self.results_df = self.results_df.reindex(columns=column_order).fillna(0).set_index('Period')
        
        print("模型运行完成（含续约逻辑）。结果已存储在 'results_df' 属性中。")
        return self.results_df
    
    def plot_results(self, output_dir: str = "outputs"):
        """Plots the results of the financial model.

        Args:
            output_dir (str, optional): Directory to save plots. Defaults to "outputs".

        Returns:
            None.
        """
        if self.results_df is None:
            print("错误: 模型结果 (results_df) 不存在。请先调用 run_model() 。")
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")

        # 尝试设置中文字体以优化图表显示 (如果失败则忽略)
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体 (适用于Windows)
            # 对于macOS, 可尝试: plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
            # 对于Linux, 可尝试: plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
        except Exception as e:
            warnings.warn(f"设置中文字体失败，图表中的中文可能无法正确显示。请确保已安装SimHei或其他中文字体。错误: {e}")

        # --- 1. Luma总收入趋势图 ---
        plt.figure(figsize=(12, 7))
        self.results_df['Luma_Revenue_Total'].plot(kind='line', marker='o', linewidth=2, markersize=8)
        plt.title('Luma总收入趋势 (按半年周期)', fontsize=16)
        plt.xlabel('周期 (半年)', fontsize=12)
        plt.ylabel('收入 (元)', fontsize=12)
        plt.xticks(rotation=0, fontsize=10)
        plt.yticks(fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout() # 自动调整子图参数，使之填充整个图像区域
        plot_path_total_revenue = os.path.join(output_dir, 'luma_total_revenue_trend.png')
        try:
            plt.savefig(plot_path_total_revenue)
            print(f"Luma总收入趋势图已保存到: {plot_path_total_revenue}")
        except Exception as e:
            print(f"保存Luma总收入趋势图失败: {e}")
        # plt.show() # 可选: 如果希望在脚本运行时直接显示图表，取消此行注释
        plt.close() # 关闭图形，释放内存

        # --- 2. Luma收入构成图 (新签 vs. 续约) ---
        revenue_components_to_plot = [
            'Luma_Fixed_Fee_New',        # 新签带来的固定费用
            'Luma_Student_Share_New',    # 新签带来的学生付费分成
            'Luma_Student_Share_Renewed' # 续约带来的学生付费分成
        ]
        # 从results_df中提取绘图所需数据，并确保所有列存在 (如果某周期无数据则为0)
        plot_data_revenue_breakdown = self.results_df.reindex(columns=revenue_components_to_plot, fill_value=0)

        plt.figure(figsize=(12, 7))
        plot_data_revenue_breakdown.plot(kind='bar', stacked=True, width=0.8)
        plt.title('Luma收入构成: 新签 vs. 续约 (按半年周期)', fontsize=16)
        plt.xlabel('周期 (半年)', fontsize=12)
        plt.ylabel('收入 (元)', fontsize=12)
        plt.xticks(rotation=45, ha='right', fontsize=10) # 旋转X轴标签以便阅读
        plt.yticks(fontsize=10)
        plt.legend(
            title='收入类型',
            labels=['新签-固定费', '新签-学生付费', '续约-学生付费'], 
            fontsize=10, 
            title_fontsize=11
        )
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plot_path_revenue_breakdown = os.path.join(output_dir, 'luma_revenue_breakdown.png')
        try:
            plt.savefig(plot_path_revenue_breakdown)
            print(f"Luma收入构成图已保存到: {plot_path_revenue_breakdown}")
        except Exception as e:
            print(f"保存Luma收入构成图失败: {e}")
        # plt.show() # 可选: 直接显示图表
        plt.close() # 关闭图形
        
        print("图表生成完成。")
    def _get_nested_param(self, params_dict: Dict[str, Any], param_path: str) -> Any:
        """
        根据点分隔的路径字符串从参数字典中获取值.

        Args:
            params_dict (Dict[str, Any]): 要从中获取值的参数字典.
            param_path (str): 点分隔的参数路径 (例如 'group.subgroup.param').

        Returns:
            Any: 路径对应的值.

        Raises:
            KeyError: 如果路径在字典中无效.
        """
        keys = param_path.split('.')
        val = params_dict
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                # 可以选择抛出错误或返回None/默认值
                raise KeyError(f"参数路径 '{param_path}' 在字典中未找到 '{key}' 部分。")
        return val
    
    def _set_nested_param(self, params_dict: Dict[str, Any], param_path: str, value: Any):
        """
        根据点分隔的路径字符串在参数字典中设置值.

        如果路径中的中间字典不存在, 此方法会创建它们.

        Args:
            params_dict (Dict[str, Any]): 要在其中设置值的参数字典.
            param_path (str): 点分隔的参数路径 (例如 'group.subgroup.param').
            value (Any): 要设置的值.

        Raises:
            ValueError: 如果参数路径为空.
            TypeError: 如果路径中的某个中间键已存在但其值不是字典.
        """
        keys = param_path.split('.')
        d = params_dict
        for key in keys[:-1]: # 遍历到倒数第二个键
            if key in d:
                if not isinstance(d[key], dict):
                    raise TypeError(f"参数路径 '{param_path}' 中的 '{key}' 部分已存在但不是一个字典，无法设置嵌套值。")
                # else: d[key] is a dict, proceed
            else: # key not in d
                d[key] = {}
            d = d[key]
        if keys:
            d[keys[-1]] = value
        else:
            # param_path 为空的情况，不常见，可以抛出错误
            raise ValueError("参数路径不能为空。")
    
    def run_sensitivity_analysis(self, 
                                params_to_vary: Dict[str, List[Any]], 
                                output_metrics: List[str],
                                aggregate_output: bool = True) -> pd.DataFrame:
        """
        运行敏感性分析, 评估一个或多个参数变化对指定输出指标的影响.

        采用"一次改变一个参数"(OAT)的方法.

        Args:
            params_to_vary (Dict[str, List[Any]]): 
                字典, 键为参数名称 (字符串, 支持点符号访问嵌套参数, 如 'type2_access_fees.a'),
                值为该参数要测试的值列表.
            output_metrics (List[str]): 
                列表, 包含希望从 run_model() 的结果DataFrame中追踪的列名.
                例如 ['Luma_Revenue_Total', 'Uni_Fund_Total'].
            aggregate_output (bool, optional): 
                如果为 True (默认), 则对于每个输出指标, 只取其在模拟期末的最终值.
                如果为 False, 则会尝试返回每个参数组合下完整的 run_model() 输出中
                指定指标的整个时间序列(这可能导致结果DataFrame非常大, 需谨慎).
                当前主要支持 True 的情况. Defaults to True.

        Returns:
            pd.DataFrame: 一个包含敏感性分析结果的DataFrame.
                            列包括 'Parameter_Tested', 'Test_Value', 以及 output_metrics 中的各项.
        
        Raises:
            ValueError: 如果 output_metrics 为空, 或者 params_to_vary 格式不正确.
            KeyError: 如果 params_to_vary 中的参数路径无效, 或 output_metrics 中的指标在模型结果中找不到.
        """
        if not output_metrics:
            raise ValueError("output_metrics 列表不能为空。")
        if not params_to_vary or not isinstance(params_to_vary, dict):
            raise ValueError("params_to_vary 必须是一个非空字典。")

        results_list = []
        base_params = copy.deepcopy(self.params) # 获取当前模型的基础参数副本

        for param_name, test_values in params_to_vary.items():
            if not isinstance(test_values, list):
                warnings.warn(f"参数 '{param_name}' 的测试值不是列表，已跳过。")
                continue
            
            print(f"""---
正在分析参数: {param_name}
测试值: {test_values}
---""")

            for value in test_values:
                current_run_params = copy.deepcopy(base_params)
                try:
                    self._set_nested_param(current_run_params, param_name, value)
                except (KeyError, ValueError) as e:
                    warnings.warn(f"为参数 '{param_name}' 设置值 '{value}' 时出错: {e}。跳过此测试点。")
                    continue
                
                # 创建一个临时模型实例并使用修改后的参数运行
                # 注意：这里我们假设LumaFinancialModel的构造函数能正确处理传入的完整参数集
                # 并且run_model()会使用实例自身的params
                temp_model_instance = LumaFinancialModel(params=current_run_params)
                try:
                    model_output_df = temp_model_instance.run_model()
                except Exception as e:
                    warnings.warn(f"参数 '{param_name}' = {value} 时模型运行失败: {e}。跳过此测试点。")
                    continue

                if model_output_df is None or model_output_df.empty:
                    warnings.warn(f"参数 '{param_name}' = {value} 时模型未产生有效输出。跳过此测试点。")
                    continue

                result_row = {'Parameter_Tested': param_name, 'Test_Value': value}
                for metric in output_metrics:
                    if metric not in model_output_df.columns:
                        warnings.warn(f"输出指标 '{metric}' 在模型结果中未找到。跳过此指标。")
                        result_row[metric] = np.nan
                        continue
                    
                    if aggregate_output:
                        # 取最后一个周期的值
                        result_row[metric] = model_output_df[metric].iloc[-1] if not model_output_df[metric].empty else np.nan
                    else: # This means aggregate_output is False
                        # 返回整个序列 (可能需要后续处理或调整DataFrame结构)
                        # 为简化，当前版本若 aggregate_output=False，也只取最后一个值，提示用户此行为
                        warnings.warn(f"aggregate_output=False 暂未完全支持返回完整序列，仍取指标 '{metric}' 的最终值。")
                        result_row[metric] = model_output_df[metric].iloc[-1] if not model_output_df[metric].empty else np.nan
                
                results_list.append(result_row)
        
        if not results_list:
            print("敏感性分析未产生任何结果。请检查参数和模型运行情况。")
            return pd.DataFrame()
            
        sensitivity_df = pd.DataFrame(results_list)
        print("敏感性分析完成。")
        return sensitivity_df
