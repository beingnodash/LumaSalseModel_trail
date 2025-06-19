import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from typing import Dict, Any, List, Tuple
import copy

class LumaEnhancedFinancialModel:
    """
    Luma增强版高校销售与收益分析模型
    
    重构支持三种基本商业模式：
    - 模式A: 高校付费 + 学生免费使用全部功能
    - 模式B: 高校付费 + 学生免费基础功能 + 学生付费高级功能  
    - 模式C: 高校免费 + 学生免费基础功能 + 学生付费高级功能
    
    核心特性：
    - 高校3年服务周期，一次性付费
    - 学生双重付费模式：按次付费 + 订阅付费
    - 灵活的收入分成机制
    - 详细的续约率建模
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """初始化增强版财务模型"""
        default_params = {
            # --- 基础业务参数 ---
            'total_half_years': 8,  # 总分析周期（4年，观察完整3年服务周期+续约）
            'new_clients_per_half_year': 5,  # 每半年新签约高校数
            'uni_service_period_years': 3,  # 高校服务周期（年）
            
            # --- 商业模式分布 ---
            'business_mode_distribution': {
                'mode_a': 0.3,  # 高校付费+学生全免费
                'mode_b': 0.4,  # 高校付费+学生分层付费
                'mode_c': 0.3   # 高校免费+学生分层付费
            },
            
            # --- 高校基础数据 ---
            'avg_students_per_uni': 10000,  # 平均每所高校学生数
            
            # --- 高校端定价策略 (3年服务周期) ---
            'uni_pricing': {
                'mode_a': {
                    'base_price': 600000,  # 模式A基础价格（3年）
                    'negotiation_range': (0.7, 1.3),  # 谈判价格范围
                    'price_elasticity': -0.2  # 价格弹性系数
                },
                'mode_b': {
                    'base_price': 400000,  # 模式B基础价格（3年）
                    'negotiation_range': (0.8, 1.2),
                    'price_elasticity': -0.15
                },
                'mode_c': {
                    'base_price': 0,  # 模式C免费
                    'negotiation_range': (1.0, 1.0),
                    'price_elasticity': 0
                }
            },
            
            # --- 高校续约率 (3年后) ---
            'uni_renewal_rates': {
                'mode_a': 0.85,
                'mode_b': 0.80,
                'mode_c': 0.75
            },
            
            # --- 学生付费转化率 ---
            'student_paid_conversion_rates': {
                'mode_a': 0.0,   # 模式A学生不付费
                'mode_b': 0.08,  # 模式B学生付费转化率
                'mode_c': 0.12   # 模式C学生付费转化率
            },
            
            # --- 学生付费方式分布 ---
            'student_payment_method_distribution': {
                'per_use': 0.4,      # 按次付费用户比例
                'subscription': 0.6   # 订阅付费用户比例
            },
            
            # --- 按次付费参数 ---
            'per_use_pricing': {
                'price_per_use': 8.0,  # 单次使用价格
                'avg_uses_per_half_year': 3,  # 平均半年使用次数
                'repurchase_rate': 0.7  # 复购率
            },
            
            # --- 订阅付费参数 ---
            'subscription_pricing': {
                'monthly_price': 15.0,  # 月度订阅价格
                
                # 套餐定价
                'package_pricing': {
                    '12_months': {'price': 150, 'discount_rate': 0.17},
                    '36_months': {'price': 400, 'discount_rate': 0.26},
                    '60_months': {'price': 600, 'discount_rate': 0.33}
                },
                
                # 套餐选择分布
                'package_distribution': {
                    'monthly': 0.4,
                    '12_months': 0.45,
                    '36_months': 0.12,
                    '60_months': 0.03
                },
                
                'subscription_renewal_rate': 0.75
            },
            
            # --- 学生付费分成比例 (Luma获得的比例) ---
            'luma_share_from_student_payment': {
                'mode_a': 0.0,   # 无学生付费
                'mode_b': 0.3,   # 模式B: Luma获得30%
                'mode_c': 0.5    # 模式C: Luma获得50%
            },
            
            # --- 价格谈判参数 ---
            'price_negotiation': {
                'default_multiplier': 1.0,  # 默认价格倍数
                'negotiation_std': 0.1      # 谈判价格标准差
            }
        }
        
        self.params = copy.deepcopy(default_params)
        if params:
            self._update_params(params)
        
        self._validate_params()
        
        self.results_df = None
        self.cohorts = []
    
    def _update_params(self, user_params: Dict[str, Any]):
        """递归更新参数"""
        def recursive_update(default_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in default_dict and isinstance(default_dict[key], dict):
                    recursive_update(default_dict[key], value)
                else:
                    default_dict[key] = copy.deepcopy(value)
        
        recursive_update(self.params, user_params)
    
    def _validate_params(self):
        """验证参数有效性"""
        p = self.params
        
        # 验证商业模式分布总和为1
        mode_sum = sum(p['business_mode_distribution'].values())
        if not np.isclose(mode_sum, 1.0):
            warnings.warn(f"商业模式分布总和为 {mode_sum}，应为1.0")
        
        # 验证学生付费方式分布总和为1
        payment_sum = sum(p['student_payment_method_distribution'].values())
        if not np.isclose(payment_sum, 1.0):
            warnings.warn(f"学生付费方式分布总和为 {payment_sum}，应为1.0")
        
        # 验证订阅套餐分布总和为1
        package_sum = sum(p['subscription_pricing']['package_distribution'].values())
        if not np.isclose(package_sum, 1.0):
            warnings.warn(f"订阅套餐分布总和为 {package_sum}，应为1.0")
        
        # 验证续约率在合理范围内
        for mode, rate in p['uni_renewal_rates'].items():
            if not (0 <= rate <= 1):
                warnings.warn(f"高校续约率 {mode}: {rate} 超出合理范围 [0,1]")
                p['uni_renewal_rates'][mode] = max(0, min(1, rate))
    
    def _calculate_university_revenue(self, mode: str, period: int, uni_count: int, 
                                    is_renewal: bool = False) -> float:
        """计算高校端收入"""
        if mode == 'mode_c':
            return 0.0  # 模式C高校免费
        
        base_price = self.params['uni_pricing'][mode]['base_price']
        
        if is_renewal:
            # 续约时应用续约率
            renewal_rate = self.params['uni_renewal_rates'][mode]
            effective_uni_count = uni_count * renewal_rate
        else:
            effective_uni_count = uni_count
        
        # 应用价格谈判
        negotiated_price = self._apply_price_negotiation(base_price, mode)
        
        return effective_uni_count * negotiated_price
    
    def _apply_price_negotiation(self, base_price: float, mode: str) -> float:
        """应用价格谈判逻辑"""
        if base_price == 0:
            return 0
        
        negotiation_range = self.params['uni_pricing'][mode]['negotiation_range']
        min_mult, max_mult = negotiation_range
        
        # 使用默认倍数加上随机扰动
        default_mult = self.params['price_negotiation']['default_multiplier']
        std = self.params['price_negotiation']['negotiation_std']
        
        # 确保在合理范围内
        negotiated_mult = np.clip(
            np.random.normal(default_mult, std), 
            min_mult, max_mult
        )
        
        return base_price * negotiated_mult
    
    def _calculate_student_revenue(self, mode: str, active_students: int, 
                                 period: int) -> Dict[str, float]:
        """计算学生端收入"""
        if mode == 'mode_a':
            return {
                'per_use_revenue': 0,
                'subscription_revenue': 0,
                'total_student_revenue': 0,
                'luma_share': 0,
                'uni_share': 0
            }
        
        # 计算付费学生数
        conversion_rate = self.params['student_paid_conversion_rates'][mode]
        paying_students = active_students * conversion_rate
        
        # 计算各种收入
        per_use_revenue = self._calculate_per_use_revenue(paying_students)
        subscription_revenue = self._calculate_subscription_revenue(paying_students, period)
        
        total_student_revenue = per_use_revenue + subscription_revenue
        
        # 计算分成
        luma_share_rate = self.params['luma_share_from_student_payment'][mode]
        luma_share = total_student_revenue * luma_share_rate
        uni_share = total_student_revenue * (1 - luma_share_rate)
        
        return {
            'per_use_revenue': per_use_revenue,
            'subscription_revenue': subscription_revenue,
            'total_student_revenue': total_student_revenue,
            'luma_share': luma_share,
            'uni_share': uni_share
        }
    
    def _calculate_per_use_revenue(self, paying_students: float) -> float:
        """计算按次付费收入"""
        per_use_ratio = self.params['student_payment_method_distribution']['per_use']
        per_use_students = paying_students * per_use_ratio
        
        price_per_use = self.params['per_use_pricing']['price_per_use']
        avg_uses = self.params['per_use_pricing']['avg_uses_per_half_year']
        
        return per_use_students * price_per_use * avg_uses
    
    def _calculate_subscription_revenue(self, paying_students: float, period: int) -> float:
        """计算订阅付费收入"""
        sub_ratio = self.params['student_payment_method_distribution']['subscription']
        sub_students = paying_students * sub_ratio
        
        package_dist = self.params['subscription_pricing']['package_distribution']
        package_pricing = self.params['subscription_pricing']['package_pricing']
        monthly_price = self.params['subscription_pricing']['monthly_price']
        
        total_revenue = 0
        
        # 月付用户 (半年收入)
        monthly_users = sub_students * package_dist['monthly']
        total_revenue += monthly_users * monthly_price * 6
        
        # 套餐用户收入计算
        for package, ratio in package_dist.items():
            if package != 'monthly':
                package_users = sub_students * ratio
                package_info = package_pricing[package]
                package_price = package_info['price']
                
                # 将套餐价格分摊到其有效期
                months = int(package.split('_')[0])
                half_year_revenue = (package_price / months) * 6
                total_revenue += package_users * half_year_revenue
        
        return total_revenue
    
    def _is_renewal_period(self, period: int, cohort_start_period: int) -> bool:
        """判断是否为续约期"""
        service_period_half_years = self.params['uni_service_period_years'] * 2
        periods_since_start = period - cohort_start_period
        return periods_since_start > 0 and periods_since_start % service_period_half_years == 0
    
    def _create_new_cohort(self, period: int) -> Dict[str, Any]:
        """创建新的客户群组"""
        new_clients = self.params['new_clients_per_half_year']
        mode_dist = self.params['business_mode_distribution']
        
        cohort = {
            'cohort_id': f'C_H{period + 1}',
            'created_period': period,
            'universities': {},
            'students': {},
            'revenue_history': []
        }
        
        # 按商业模式分配高校
        for mode, ratio in mode_dist.items():
            uni_count = int(new_clients * ratio)
            if uni_count > 0:
                cohort['universities'][mode] = {
                    'count': uni_count,
                    'active_count': uni_count,
                    'last_renewal_period': -1
                }
                
                # 初始化学生数据
                total_students = uni_count * self.params['avg_students_per_uni']
                conversion_rate = self.params['student_paid_conversion_rates'][mode]
                paying_students = total_students * conversion_rate
                
                cohort['students'][mode] = {
                    'total_students': total_students,
                    'paying_students': paying_students,
                    'active_paying_students': paying_students
                }
        
        return cohort
    
    def _update_cohort_renewals(self, cohort: Dict[str, Any], period: int):
        """更新群组续约状态"""
        for mode in cohort['universities'].keys():
            uni_data = cohort['universities'][mode]
            
            if self._is_renewal_period(period, cohort['created_period']):
                # 高校续约
                renewal_rate = self.params['uni_renewal_rates'][mode]
                uni_data['active_count'] = int(uni_data['active_count'] * renewal_rate)
                uni_data['last_renewal_period'] = period
                
                # 学生续约
                student_data = cohort['students'][mode]
                if mode != 'mode_a':  # 模式A学生不付费，无需续约
                    # 按次付费学生续约
                    repurchase_rate = self.params['per_use_pricing']['repurchase_rate']
                    # 订阅学生续约
                    sub_renewal_rate = self.params['subscription_pricing']['subscription_renewal_rate']
                    
                    # 简化处理：使用加权平均续约率
                    per_use_ratio = self.params['student_payment_method_distribution']['per_use']
                    sub_ratio = self.params['student_payment_method_distribution']['subscription']
                    
                    weighted_renewal_rate = (per_use_ratio * repurchase_rate + 
                                           sub_ratio * sub_renewal_rate)
                    
                    student_data['active_paying_students'] = (
                        student_data['active_paying_students'] * weighted_renewal_rate
                    )
    
    def run_model(self) -> pd.DataFrame:
        """运行增强版财务模型"""
        total_periods = self.params['total_half_years']
        results = []
        
        self.cohorts = []
        
        for period in range(total_periods):
            period_name = f"H{period + 1}"
            
            # 创建新群组
            new_cohort = self._create_new_cohort(period)
            self.cohorts.append(new_cohort)
            
            # 更新现有群组续约状态
            for cohort in self.cohorts:
                if cohort['created_period'] < period:
                    self._update_cohort_renewals(cohort, period)
            
            # 计算当期收入
            period_revenue = self._calculate_period_revenue(period)
            
            # 记录结果
            result_row = {
                'period': period + 1,
                'period_name': period_name,
                **period_revenue
            }
            results.append(result_row)
        
        self.results_df = pd.DataFrame(results)
        return self.results_df
    
    def _calculate_period_revenue(self, period: int) -> Dict[str, float]:
        """计算当期总收入"""
        total_uni_revenue_new = 0
        total_uni_revenue_renewal = 0
        total_student_per_use = 0
        total_student_subscription = 0
        total_luma_from_student = 0
        total_uni_from_student = 0
        total_active_unis = 0
        total_paying_students = 0
        
        for cohort in self.cohorts:
            cohort_revenue = {'uni_new': 0, 'uni_renewal': 0, 'student_detail': {}}
            
            for mode, uni_data in cohort['universities'].items():
                active_unis = uni_data['active_count']
                total_active_unis += active_unis
                
                if active_unis == 0:
                    continue
                
                # 高校收入计算
                if cohort['created_period'] == period:
                    # 新签约收入
                    uni_revenue = self._calculate_university_revenue(
                        mode, period, active_unis, is_renewal=False
                    )
                    total_uni_revenue_new += uni_revenue
                    cohort_revenue['uni_new'] += uni_revenue
                elif self._is_renewal_period(period, cohort['created_period']):
                    # 续约收入
                    uni_revenue = self._calculate_university_revenue(
                        mode, period, uni_data['count'], is_renewal=True
                    )
                    total_uni_revenue_renewal += uni_revenue
                    cohort_revenue['uni_renewal'] += uni_revenue
                
                # 学生收入计算
                if mode in cohort['students']:
                    student_data = cohort['students'][mode]
                    active_paying = student_data['active_paying_students']
                    total_paying_students += active_paying
                    
                    if active_paying > 0:
                        student_revenue = self._calculate_student_revenue(
                            mode, student_data['total_students'], period
                        )
                        
                        # 调整为实际活跃付费学生
                        adjustment_ratio = active_paying / student_data['paying_students']
                        for key in ['per_use_revenue', 'subscription_revenue', 
                                  'total_student_revenue', 'luma_share', 'uni_share']:
                            student_revenue[key] *= adjustment_ratio
                        
                        total_student_per_use += student_revenue['per_use_revenue']
                        total_student_subscription += student_revenue['subscription_revenue']
                        total_luma_from_student += student_revenue['luma_share']
                        total_uni_from_student += student_revenue['uni_share']
                        
                        cohort_revenue['student_detail'][mode] = student_revenue
            
            cohort['revenue_history'].append(cohort_revenue)
        
        # 汇总收入数据
        total_uni_revenue = total_uni_revenue_new + total_uni_revenue_renewal
        total_student_revenue = total_student_per_use + total_student_subscription
        total_luma_revenue = total_uni_revenue + total_luma_from_student
        
        return {
            'uni_revenue_new_signups': total_uni_revenue_new,
            'uni_revenue_renewals': total_uni_revenue_renewal,
            'uni_revenue_total': total_uni_revenue,
            
            'student_revenue_per_use': total_student_per_use,
            'student_revenue_subscription': total_student_subscription,
            'student_revenue_total': total_student_revenue,
            
            'luma_revenue_from_uni': total_uni_revenue,
            'luma_revenue_from_student_share': total_luma_from_student,
            'luma_revenue_total': total_luma_revenue,
            
            'uni_income_from_student_share': total_uni_from_student,
            
            'active_universities': total_active_unis,
            'total_paying_students': total_paying_students,
            'avg_revenue_per_uni': total_luma_revenue / max(1, total_active_unis),
            'avg_revenue_per_paying_student': total_luma_revenue / max(1, total_paying_students)
        }
    
    def get_business_summary(self) -> Dict[str, Any]:
        """获取业务摘要"""
        if self.results_df is None:
            raise ValueError("请先运行模型 run_model()")
        
        df = self.results_df
        
        return {
            'total_periods': len(df),
            'total_luma_revenue': df['luma_revenue_total'].sum(),
            'total_uni_revenue': df['uni_revenue_total'].sum(),
            'total_student_revenue': df['student_revenue_total'].sum(),
            'avg_luma_revenue_per_period': df['luma_revenue_total'].mean(),
            'peak_active_universities': df['active_universities'].max(),
            'peak_paying_students': df['total_paying_students'].max(),
            'revenue_growth_rate': self._calculate_growth_rate(df['luma_revenue_total']),
            'business_mode_distribution': self.params['business_mode_distribution']
        }
    
    def _calculate_growth_rate(self, revenue_series: pd.Series) -> float:
        """计算收入增长率"""
        if len(revenue_series) < 2:
            return 0.0
        
        first_half = revenue_series[:len(revenue_series)//2].mean()
        second_half = revenue_series[len(revenue_series)//2:].mean()
        
        if first_half == 0:
            return 0.0
        
        return (second_half - first_half) / first_half
    
    def plot_revenue_analysis(self, figsize: Tuple[int, int] = (15, 10)):
        """绘制收入分析图表"""
        if self.results_df is None:
            raise ValueError("请先运行模型 run_model()")
        
        df = self.results_df
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('Luma增强版财务模型 - 收入分析', fontsize=16, fontweight='bold')
        
        # 1. 总收入趋势
        axes[0, 0].plot(df['period'], df['luma_revenue_total'], 'b-', linewidth=2, label='Luma总收入')
        axes[0, 0].plot(df['period'], df['uni_revenue_total'], 'g--', linewidth=2, label='高校收入')
        axes[0, 0].plot(df['period'], df['student_revenue_total'], 'r:', linewidth=2, label='学生收入')
        axes[0, 0].set_title('收入趋势分析')
        axes[0, 0].set_xlabel('周期')
        axes[0, 0].set_ylabel('收入 (元)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Luma收入构成
        axes[0, 1].stackplot(df['period'], 
                           df['luma_revenue_from_uni'], 
                           df['luma_revenue_from_student_share'],
                           labels=['来自高校', '来自学生分成'],
                           alpha=0.7)
        axes[0, 1].set_title('Luma收入构成')
        axes[0, 1].set_xlabel('周期')
        axes[0, 1].set_ylabel('收入 (元)')
        axes[0, 1].legend()
        
        # 3. 客户数量趋势
        axes[1, 0].plot(df['period'], df['active_universities'], 'bo-', label='活跃高校数')
        ax_twin = axes[1, 0].twinx()
        ax_twin.plot(df['period'], df['total_paying_students'], 'ro-', label='付费学生数')
        axes[1, 0].set_title('客户数量趋势')
        axes[1, 0].set_xlabel('周期')
        axes[1, 0].set_ylabel('高校数量', color='b')
        ax_twin.set_ylabel('学生数量', color='r')
        axes[1, 0].legend(loc='upper left')
        ax_twin.legend(loc='upper right')
        
        # 4. 平均收入指标
        axes[1, 1].plot(df['period'], df['avg_revenue_per_uni'], 'g-', linewidth=2, label='每高校平均收入')
        axes[1, 1].plot(df['period'], df['avg_revenue_per_paying_student'], 'purple', linewidth=2, label='每付费学生平均收入')
        axes[1, 1].set_title('平均收入指标')
        axes[1, 1].set_xlabel('周期')
        axes[1, 1].set_ylabel('收入 (元)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        return fig