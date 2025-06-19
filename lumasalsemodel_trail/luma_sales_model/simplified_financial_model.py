import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from typing import Dict, Any, List, Tuple
import copy

class LumaSimplifiedFinancialModel:
    """
    Luma简化版高校销售与收益分析模型
    
    根据简化的参数结构重新设计：
    - 取消Type2的abc细分，统一为模式B
    - 简化参数分类为7大类
    - 优化收入记账时间逻辑
    - 统一分成比例参数
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """初始化简化版财务模型"""
        default_params = {
            # 基础参数
            'total_half_years': 8,
            
            # 价格参数
            'student_prices': {
                'price_per_use': 8.0,
                'price_1year_member': 150.0,
                'price_3year_member': 400.0,
                'price_5year_member': 600.0
            },
            'university_prices': {
                'mode_a_price': 600000.0,
                'mode_b_price': 400000.0,
                'mode_c_price': 0.0
            },
            
            # 市场规模
            'market_scale': {
                'new_clients_per_half_year': 5,
                'avg_students_per_uni': 10000
            },
            
            # 市场分布
            'market_distribution': {
                'mode_a_ratio': 0.3,
                'mode_b_ratio': 0.4,
                'mode_c_ratio': 0.3,
                'student_paid_conversion_rate_bc': 0.1
            },
            
            # 学生市场细分分布
            'student_segmentation': {
                'per_use_ratio': 0.4,
                'subscription_period_distribution': {
                    '1year': 0.6,
                    '3year': 0.3,
                    '5year': 0.1
                }
            },
            
            # 续费率与复购率参数
            'renewal_rates': {
                'university_3year_renewal': 0.8,
                'student_per_use_repurchase': 0.7,
                'student_subscription_renewal': 0.75
            },
            
            # 分成比例
            'revenue_sharing': {
                'luma_share_from_student': 0.4
            },
            
            # 内部计算参数
            'uni_service_period_years': 3  # 高校服务周期固定3年
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
        dist = p['market_distribution']
        mode_sum = dist['mode_a_ratio'] + dist['mode_b_ratio'] + dist['mode_c_ratio']
        if not np.isclose(mode_sum, 1.0):
            warnings.warn(f"商业模式分布总和为 {mode_sum}，应为1.0")
        
        # 验证订阅期限分布总和为1
        sub_dist = p['student_segmentation']['subscription_period_distribution']
        sub_sum = sum(sub_dist.values())
        if not np.isclose(sub_sum, 1.0):
            warnings.warn(f"订阅期限分布总和为 {sub_sum}，应为1.0")
    
    def _calculate_university_revenue(self, mode: str, uni_count: int, period: int, 
                                    cohort_start_period: int) -> float:
        """计算高校端收入"""
        if mode == 'mode_c':
            return 0.0  # 模式C高校免费
        
        # 判断是否为续约期（3年后）
        service_period_half_years = self.params['uni_service_period_years'] * 2
        periods_since_start = period - cohort_start_period
        
        is_renewal_period = (periods_since_start > 0 and 
                           periods_since_start % service_period_half_years == 0)
        
        if cohort_start_period == period:
            # 新签约
            if mode == 'mode_a':
                return uni_count * self.params['university_prices']['mode_a_price']
            elif mode == 'mode_b':
                return uni_count * self.params['university_prices']['mode_b_price']
        elif is_renewal_period:
            # 续约期
            renewal_rate = self.params['renewal_rates']['university_3year_renewal']
            if mode == 'mode_a':
                return uni_count * renewal_rate * self.params['university_prices']['mode_a_price']
            elif mode == 'mode_b':
                return uni_count * renewal_rate * self.params['university_prices']['mode_b_price']
        
        return 0.0
    
    def _calculate_student_revenue(self, mode: str, total_students: int, 
                                 active_paying_students: int, period: int) -> Dict[str, float]:
        """计算学生端收入"""
        if mode == 'mode_a':
            # 模式A学生全免费
            return {
                'per_use_revenue': 0,
                'subscription_revenue': 0,
                'total_student_revenue': 0,
                'luma_share': 0,
                'uni_share': 0
            }
        
        if active_paying_students <= 0:
            return {
                'per_use_revenue': 0,
                'subscription_revenue': 0,
                'total_student_revenue': 0,
                'luma_share': 0,
                'uni_share': 0
            }
        
        # 计算按次付费收入（包含复购率的当期折算）
        per_use_revenue = self._calculate_per_use_revenue(active_paying_students)
        
        # 计算订阅付费收入（考虑收入记账时间）
        subscription_revenue = self._calculate_subscription_revenue(active_paying_students, period)
        
        total_student_revenue = per_use_revenue + subscription_revenue
        
        # 计算分成
        luma_share_rate = self.params['revenue_sharing']['luma_share_from_student']
        luma_share = total_student_revenue * luma_share_rate
        uni_share = total_student_revenue * (1 - luma_share_rate)
        
        return {
            'per_use_revenue': per_use_revenue,
            'subscription_revenue': subscription_revenue,
            'total_student_revenue': total_student_revenue,
            'luma_share': luma_share,
            'uni_share': uni_share
        }
    
    def _calculate_per_use_revenue(self, active_paying_students: float) -> float:
        """计算按次付费收入（包含复购率的当期折算）"""
        segmentation = self.params['student_segmentation']
        per_use_ratio = segmentation['per_use_ratio']
        per_use_students = active_paying_students * per_use_ratio
        
        # 单次价格
        price_per_use = self.params['student_prices']['price_per_use']
        
        # 基础使用次数（假设每半年3次）
        base_uses_per_half_year = 3
        
        # 考虑复购率的总使用次数（简化为当期折算）
        repurchase_rate = self.params['renewal_rates']['student_per_use_repurchase']
        effective_uses = base_uses_per_half_year * (1 + repurchase_rate)
        
        return per_use_students * price_per_use * effective_uses
    
    def _calculate_subscription_revenue(self, active_paying_students: float, period: int) -> float:
        """计算订阅付费收入（考虑收入记账时间）"""
        segmentation = self.params['student_segmentation']
        subscription_ratio = 1 - segmentation['per_use_ratio']
        subscription_students = active_paying_students * subscription_ratio
        
        if subscription_students <= 0:
            return 0
        
        period_dist = segmentation['subscription_period_distribution']
        student_prices = self.params['student_prices']
        
        total_revenue = 0
        
        # 1年订阅用户
        students_1year = subscription_students * period_dist['1year']
        # 1年订阅按半年分摊收入
        revenue_1year_per_half_year = student_prices['price_1year_member'] / 2
        total_revenue += students_1year * revenue_1year_per_half_year
        
        # 3年订阅用户  
        students_3year = subscription_students * period_dist['3year']
        # 3年订阅按半年分摊收入
        revenue_3year_per_half_year = student_prices['price_3year_member'] / 6
        total_revenue += students_3year * revenue_3year_per_half_year
        
        # 5年订阅用户
        students_5year = subscription_students * period_dist['5year']
        # 5年订阅按半年分摊收入
        revenue_5year_per_half_year = student_prices['price_5year_member'] / 10
        total_revenue += students_5year * revenue_5year_per_half_year
        
        return total_revenue
    
    def _create_new_cohort(self, period: int) -> Dict[str, Any]:
        """创建新的客户群组"""
        new_clients = self.params['market_scale']['new_clients_per_half_year']
        distribution = self.params['market_distribution']
        
        cohort = {
            'cohort_id': f'C_H{period + 1}',
            'created_period': period,
            'universities': {},
            'students': {},
            'revenue_history': []
        }
        
        # 按商业模式分配高校
        for mode_key in ['mode_a', 'mode_b', 'mode_c']:
            ratio_key = f'{mode_key}_ratio'
            uni_count = int(new_clients * distribution[ratio_key])
            
            if uni_count > 0:
                cohort['universities'][mode_key] = {
                    'count': uni_count,
                    'active_count': uni_count
                }
                
                # 初始化学生数据
                total_students = uni_count * self.params['market_scale']['avg_students_per_uni']
                
                if mode_key == 'mode_a':
                    # 模式A学生不付费
                    paying_students = 0
                else:
                    # 模式B/C使用统一的转化率
                    conversion_rate = distribution['student_paid_conversion_rate_bc']
                    paying_students = total_students * conversion_rate
                
                cohort['students'][mode_key] = {
                    'total_students': total_students,
                    'paying_students': paying_students,
                    'active_paying_students': paying_students
                }
        
        return cohort
    
    def _update_cohort_renewals(self, cohort: Dict[str, Any], period: int):
        """更新群组续约状态"""
        service_period_half_years = self.params['uni_service_period_years'] * 2
        periods_since_start = period - cohort['created_period']
        
        # 检查是否为续约期
        is_renewal_period = (periods_since_start > 0 and 
                           periods_since_start % service_period_half_years == 0)
        
        if is_renewal_period:
            # 高校续约
            uni_renewal_rate = self.params['renewal_rates']['university_3year_renewal']
            
            for mode_key in cohort['universities'].keys():
                uni_data = cohort['universities'][mode_key]
                uni_data['active_count'] = int(uni_data['active_count'] * uni_renewal_rate)
        
        # 学生续费（每期都有可能）
        for mode_key in cohort['students'].keys():
            if mode_key == 'mode_a':
                continue  # 模式A学生不付费
            
            student_data = cohort['students'][mode_key]
            if student_data['active_paying_students'] > 0:
                # 使用订阅续费率作为学生整体留存率
                renewal_rate = self.params['renewal_rates']['student_subscription_renewal']
                student_data['active_paying_students'] *= renewal_rate
    
    def run_model(self) -> pd.DataFrame:
        """运行简化版财务模型"""
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
        # 初始化收入项
        uni_revenue_new = 0
        uni_revenue_renewal = 0
        student_per_use_revenue = 0
        student_subscription_revenue = 0
        luma_student_share = 0
        uni_student_share = 0
        
        # 统计指标
        total_active_unis = 0
        total_paying_students = 0
        
        for cohort in self.cohorts:
            for mode_key, uni_data in cohort['universities'].items():
                active_unis = uni_data['active_count']
                total_active_unis += active_unis
                
                if active_unis == 0:
                    continue
                
                # 计算高校收入
                uni_revenue = self._calculate_university_revenue(
                    mode_key, uni_data['count'], period, cohort['created_period']
                )
                
                if cohort['created_period'] == period:
                    uni_revenue_new += uni_revenue
                else:
                    uni_revenue_renewal += uni_revenue
                
                # 计算学生收入
                if mode_key in cohort['students']:
                    student_data = cohort['students'][mode_key]
                    active_paying = student_data['active_paying_students']
                    total_paying_students += active_paying
                    
                    student_revenue = self._calculate_student_revenue(
                        mode_key, student_data['total_students'], active_paying, period
                    )
                    
                    # 调整为实际活跃高校的学生
                    if uni_data['count'] > 0:
                        adjustment_ratio = active_unis / uni_data['count']
                        for key in ['per_use_revenue', 'subscription_revenue', 
                                  'total_student_revenue', 'luma_share', 'uni_share']:
                            student_revenue[key] *= adjustment_ratio
                    
                    student_per_use_revenue += student_revenue['per_use_revenue']
                    student_subscription_revenue += student_revenue['subscription_revenue']
                    luma_student_share += student_revenue['luma_share']
                    uni_student_share += student_revenue['uni_share']
        
        # 汇总数据
        total_uni_revenue = uni_revenue_new + uni_revenue_renewal
        total_student_revenue = student_per_use_revenue + student_subscription_revenue
        total_luma_revenue = total_uni_revenue + luma_student_share
        
        return {
            # 高校收入
            'uni_revenue_new_signups': uni_revenue_new,
            'uni_revenue_renewals': uni_revenue_renewal,
            'uni_revenue_total': total_uni_revenue,
            
            # 学生收入
            'student_revenue_per_use': student_per_use_revenue,
            'student_revenue_subscription': student_subscription_revenue,
            'student_revenue_total': total_student_revenue,
            
            # Luma收入
            'luma_revenue_from_uni': total_uni_revenue,
            'luma_revenue_from_student_share': luma_student_share,
            'luma_revenue_total': total_luma_revenue,
            
            # 高校收入
            'uni_income_from_student_share': uni_student_share,
            
            # 业务指标
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
            'market_distribution': self.params['market_distribution'],
            'revenue_sharing': self.params['revenue_sharing']
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
        fig.suptitle('Luma简化版财务模型 - 收入分析', fontsize=16, fontweight='bold')
        
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
        
        # 4. 学生收入构成
        axes[1, 1].stackplot(df['period'],
                           df['student_revenue_per_use'],
                           df['student_revenue_subscription'],
                           labels=['按次付费', '订阅付费'],
                           alpha=0.7)
        axes[1, 1].set_title('学生收入构成')
        axes[1, 1].set_xlabel('周期')
        axes[1, 1].set_ylabel('收入 (元)')
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.show()
        
        return fig