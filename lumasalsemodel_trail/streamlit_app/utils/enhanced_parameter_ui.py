"""
增强版参数UI模块
Enhanced Parameter UI Module

为新的三种商业模式提供参数配置界面：
- 模式A: 高校付费 + 学生免费使用全部功能
- 模式B: 高校付费 + 学生免费基础功能 + 学生付费高级功能
- 模式C: 高校免费 + 学生免费基础功能 + 学生付费高级功能
"""

import streamlit as st
from typing import Dict, Any, Tuple
import numpy as np

class EnhancedParameterUI:
    """增强版参数配置UI"""
    
    def __init__(self):
        self.default_params = self._get_default_params()
    
    def _get_default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        return {
            # 基础业务参数
            'total_half_years': 8,
            'new_clients_per_half_year': 5,
            'uni_service_period_years': 3,
            'avg_students_per_uni': 10000,
            
            # 商业模式分布
            'business_mode_distribution': {
                'mode_a': 0.3,
                'mode_b': 0.4,
                'mode_c': 0.3
            },
            
            # 高校定价
            'uni_pricing': {
                'mode_a': {'base_price': 600000, 'negotiation_range': (0.7, 1.3)},
                'mode_b': {'base_price': 400000, 'negotiation_range': (0.8, 1.2)},
                'mode_c': {'base_price': 0, 'negotiation_range': (1.0, 1.0)}
            },
            
            # 续约率
            'uni_renewal_rates': {'mode_a': 0.85, 'mode_b': 0.80, 'mode_c': 0.75},
            
            # 学生付费转化率
            'student_paid_conversion_rates': {'mode_a': 0.0, 'mode_b': 0.08, 'mode_c': 0.12},
            
            # 学生付费方式分布
            'student_payment_method_distribution': {'per_use': 0.4, 'subscription': 0.6},
            
            # 按次付费参数
            'per_use_pricing': {
                'price_per_use': 8.0,
                'avg_uses_per_half_year': 3,
                'repurchase_rate': 0.7
            },
            
            # 订阅付费参数
            'subscription_pricing': {
                'monthly_price': 15.0,
                'package_pricing': {
                    '12_months': {'price': 150, 'discount_rate': 0.17},
                    '36_months': {'price': 400, 'discount_rate': 0.26},
                    '60_months': {'price': 600, 'discount_rate': 0.33}
                },
                'package_distribution': {
                    'monthly': 0.4,
                    '12_months': 0.45,
                    '36_months': 0.12,
                    '60_months': 0.03
                },
                'subscription_renewal_rate': 0.75
            },
            
            # 收入分成
            'luma_share_from_student_payment': {'mode_a': 0.0, 'mode_b': 0.3, 'mode_c': 0.5}
        }
    
    def render_business_config_section(self) -> Dict[str, Any]:
        """渲染基础业务配置部分"""
        st.header("📊 基础业务配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            total_half_years = st.slider(
                "总分析周期（半年）",
                min_value=4, max_value=16, 
                value=self.default_params['total_half_years'],
                help="建议至少8个半年以观察完整的3年服务周期和续约情况"
            )
            
            new_clients_per_half_year = st.slider(
                "每半年新签约高校数",
                min_value=1, max_value=20,
                value=self.default_params['new_clients_per_half_year']
            )
            
            uni_service_period_years = st.selectbox(
                "高校服务周期（年）",
                options=[1, 2, 3, 4, 5],
                index=2,  # 默认3年
                help="高校一次性付费的服务周期长度"
            )
        
        with col2:
            avg_students_per_uni = st.number_input(
                "平均每所高校学生数",
                min_value=1000, max_value=50000,
                value=self.default_params['avg_students_per_uni'],
                step=1000
            )
        
        return {
            'total_half_years': total_half_years,
            'new_clients_per_half_year': new_clients_per_half_year,
            'uni_service_period_years': uni_service_period_years,
            'avg_students_per_uni': avg_students_per_uni
        }
    
    def render_business_mode_section(self) -> Dict[str, Any]:
        """渲染商业模式配置部分"""
        st.header("🎯 商业模式配置")
        
        st.markdown("""
        **三种基本商业模式说明**：
        - **模式A**: 高校付费 + 学生免费使用全部功能
        - **模式B**: 高校付费 + 学生免费基础功能 + 学生付费高级功能
        - **模式C**: 高校免费 + 学生免费基础功能 + 学生付费高级功能
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mode_a_ratio = st.slider(
                "模式A占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['business_mode_distribution']['mode_a'],
                step=0.05,
                help="高校付费，学生全免费"
            )
        
        with col2:
            mode_b_ratio = st.slider(
                "模式B占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['business_mode_distribution']['mode_b'],
                step=0.05,
                help="高校付费，学生分层付费"
            )
        
        with col3:
            mode_c_ratio = st.slider(
                "模式C占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['business_mode_distribution']['mode_c'],
                step=0.05,
                help="高校免费，学生分层付费"
            )
        
        # 自动标准化比例
        total_ratio = mode_a_ratio + mode_b_ratio + mode_c_ratio
        if total_ratio > 0:
            mode_a_ratio /= total_ratio
            mode_b_ratio /= total_ratio
            mode_c_ratio /= total_ratio
        
        if abs(total_ratio - 1.0) > 0.01:
            st.warning(f"商业模式占比总和为 {total_ratio:.2f}，已自动标准化为1.0")
        
        return {
            'business_mode_distribution': {
                'mode_a': mode_a_ratio,
                'mode_b': mode_b_ratio,
                'mode_c': mode_c_ratio
            }
        }
    
    def render_university_pricing_section(self) -> Dict[str, Any]:
        """渲染高校定价配置部分"""
        st.header("🏫 高校端定价策略")
        
        st.markdown("**3年服务周期一次性付费价格**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("模式A定价")
            mode_a_price = st.number_input(
                "基础价格（元）",
                min_value=0, max_value=2000000,
                value=self.default_params['uni_pricing']['mode_a']['base_price'],
                step=50000,
                key="mode_a_price",
                help="模式A：高校付费+学生全免费"
            )
            
            mode_a_renewal_rate = st.slider(
                "续约率",
                min_value=0.0, max_value=1.0,
                value=self.default_params['uni_renewal_rates']['mode_a'],
                step=0.05,
                key="mode_a_renewal"
            )
        
        with col2:
            st.subheader("模式B定价")
            mode_b_price = st.number_input(
                "基础价格（元）",
                min_value=0, max_value=2000000,
                value=self.default_params['uni_pricing']['mode_b']['base_price'],
                step=50000,
                key="mode_b_price",
                help="模式B：高校付费+学生分层付费"
            )
            
            mode_b_renewal_rate = st.slider(
                "续约率",
                min_value=0.0, max_value=1.0,
                value=self.default_params['uni_renewal_rates']['mode_b'],
                step=0.05,
                key="mode_b_renewal"
            )
        
        with col3:
            st.subheader("模式C定价")
            st.markdown("**免费模式**")
            mode_c_price = 0  # 固定为0
            
            mode_c_renewal_rate = st.slider(
                "续约率",
                min_value=0.0, max_value=1.0,
                value=self.default_params['uni_renewal_rates']['mode_c'],
                step=0.05,
                key="mode_c_renewal",
                help="模式C虽然免费，但仍可能因服务质量等因素流失"
            )
        
        # 价格谈判范围配置
        st.subheader("价格谈判配置")
        col1, col2 = st.columns(2)
        
        with col1:
            price_negotiation_std = st.slider(
                "价格谈判标准差",
                min_value=0.0, max_value=0.3,
                value=0.1,
                step=0.01,
                help="价格谈判的随机波动程度"
            )
        
        with col2:
            default_multiplier = st.slider(
                "默认价格倍数",
                min_value=0.5, max_value=1.5,
                value=1.0,
                step=0.05,
                help="相对于基础价格的默认倍数"
            )
        
        return {
            'uni_pricing': {
                'mode_a': {
                    'base_price': mode_a_price,
                    'negotiation_range': (0.7, 1.3),
                    'price_elasticity': -0.2
                },
                'mode_b': {
                    'base_price': mode_b_price,
                    'negotiation_range': (0.8, 1.2),
                    'price_elasticity': -0.15
                },
                'mode_c': {
                    'base_price': mode_c_price,
                    'negotiation_range': (1.0, 1.0),
                    'price_elasticity': 0
                }
            },
            'uni_renewal_rates': {
                'mode_a': mode_a_renewal_rate,
                'mode_b': mode_b_renewal_rate,
                'mode_c': mode_c_renewal_rate
            },
            'price_negotiation': {
                'default_multiplier': default_multiplier,
                'negotiation_std': price_negotiation_std
            }
        }
    
    def render_student_payment_section(self) -> Dict[str, Any]:
        """渲染学生付费配置部分"""
        st.header("🎓 学生端付费策略")
        
        # 学生付费转化率
        st.subheader("学生付费转化率")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mode_a_conversion = 0.0  # 固定为0
            st.metric("模式A转化率", "0%", help="模式A学生全免费")
        
        with col2:
            mode_b_conversion = st.slider(
                "模式B转化率",
                min_value=0.0, max_value=0.5,
                value=self.default_params['student_paid_conversion_rates']['mode_b'],
                step=0.01,
                format="%.2f",
                help="模式B学生付费转化率"
            )
        
        with col3:
            mode_c_conversion = st.slider(
                "模式C转化率",
                min_value=0.0, max_value=0.5,
                value=self.default_params['student_paid_conversion_rates']['mode_c'],
                step=0.01,
                format="%.2f",
                help="模式C学生付费转化率（通常更高）"
            )
        
        # 付费方式分布
        st.subheader("学生付费方式分布")
        col1, col2 = st.columns(2)
        
        with col1:
            per_use_ratio = st.slider(
                "按次付费用户比例",
                min_value=0.0, max_value=1.0,
                value=self.default_params['student_payment_method_distribution']['per_use'],
                step=0.05
            )
        
        with col2:
            subscription_ratio = 1.0 - per_use_ratio
            st.metric("订阅付费用户比例", f"{subscription_ratio:.1%}")
        
        # 按次付费参数
        st.subheader("按次付费参数")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            price_per_use = st.number_input(
                "单次使用价格（元）",
                min_value=1.0, max_value=50.0,
                value=self.default_params['per_use_pricing']['price_per_use'],
                step=0.5
            )
        
        with col2:
            avg_uses_per_half_year = st.number_input(
                "半年平均使用次数",
                min_value=1, max_value=20,
                value=self.default_params['per_use_pricing']['avg_uses_per_half_year'],
                step=1
            )
        
        with col3:
            repurchase_rate = st.slider(
                "复购率",
                min_value=0.0, max_value=1.0,
                value=self.default_params['per_use_pricing']['repurchase_rate'],
                step=0.05
            )
        
        # 订阅付费参数
        st.subheader("订阅付费参数")
        
        monthly_price = st.number_input(
            "月度订阅价格（元）",
            min_value=5.0, max_value=100.0,
            value=self.default_params['subscription_pricing']['monthly_price'],
            step=1.0
        )
        
        # 套餐配置
        st.subheader("订阅套餐配置")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            package_12_price = st.number_input(
                "12个月套餐价格",
                min_value=50, max_value=500,
                value=self.default_params['subscription_pricing']['package_pricing']['12_months']['price'],
                step=10,
                key="package_12"
            )
            package_12_discount = (1 - package_12_price / (monthly_price * 12)) if monthly_price > 0 else 0
            st.metric("折扣率", f"{package_12_discount:.1%}")
        
        with col2:
            package_36_price = st.number_input(
                "36个月套餐价格",
                min_value=100, max_value=1500,
                value=self.default_params['subscription_pricing']['package_pricing']['36_months']['price'],
                step=20,
                key="package_36"
            )
            package_36_discount = (1 - package_36_price / (monthly_price * 36)) if monthly_price > 0 else 0
            st.metric("折扣率", f"{package_36_discount:.1%}")
        
        with col3:
            package_60_price = st.number_input(
                "60个月套餐价格",
                min_value=200, max_value=2000,
                value=self.default_params['subscription_pricing']['package_pricing']['60_months']['price'],
                step=50,
                key="package_60"
            )
            package_60_discount = (1 - package_60_price / (monthly_price * 60)) if monthly_price > 0 else 0
            st.metric("折扣率", f"{package_60_discount:.1%}")
        
        # 套餐分布
        st.subheader("套餐选择分布")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            monthly_dist = st.slider(
                "月付用户比例",
                min_value=0.0, max_value=1.0,
                value=self.default_params['subscription_pricing']['package_distribution']['monthly'],
                step=0.05,
                key="monthly_dist"
            )
        
        with col2:
            package_12_dist = st.slider(
                "12月套餐比例",
                min_value=0.0, max_value=1.0,
                value=self.default_params['subscription_pricing']['package_distribution']['12_months'],
                step=0.05,
                key="12_dist"
            )
        
        with col3:
            package_36_dist = st.slider(
                "36月套餐比例",
                min_value=0.0, max_value=1.0,
                value=self.default_params['subscription_pricing']['package_distribution']['36_months'],
                step=0.05,
                key="36_dist"
            )
        
        with col4:
            remaining_dist = max(0, 1.0 - monthly_dist - package_12_dist - package_36_dist)
            package_60_dist = remaining_dist
            st.metric("60月套餐比例", f"{package_60_dist:.1%}")
        
        # 自动标准化分布
        total_dist = monthly_dist + package_12_dist + package_36_dist + package_60_dist
        if total_dist > 0:
            monthly_dist /= total_dist
            package_12_dist /= total_dist
            package_36_dist /= total_dist
            package_60_dist /= total_dist
        
        # 续费率
        subscription_renewal_rate = st.slider(
            "订阅续费率",
            min_value=0.0, max_value=1.0,
            value=self.default_params['subscription_pricing']['subscription_renewal_rate'],
            step=0.05
        )
        
        return {
            'student_paid_conversion_rates': {
                'mode_a': mode_a_conversion,
                'mode_b': mode_b_conversion,
                'mode_c': mode_c_conversion
            },
            'student_payment_method_distribution': {
                'per_use': per_use_ratio,
                'subscription': subscription_ratio
            },
            'per_use_pricing': {
                'price_per_use': price_per_use,
                'avg_uses_per_half_year': avg_uses_per_half_year,
                'repurchase_rate': repurchase_rate
            },
            'subscription_pricing': {
                'monthly_price': monthly_price,
                'package_pricing': {
                    '12_months': {'price': package_12_price, 'discount_rate': package_12_discount},
                    '36_months': {'price': package_36_price, 'discount_rate': package_36_discount},
                    '60_months': {'price': package_60_price, 'discount_rate': package_60_discount}
                },
                'package_distribution': {
                    'monthly': monthly_dist,
                    '12_months': package_12_dist,
                    '36_months': package_36_dist,
                    '60_months': package_60_dist
                },
                'subscription_renewal_rate': subscription_renewal_rate
            }
        }
    
    def render_revenue_sharing_section(self) -> Dict[str, Any]:
        """渲染收入分成配置部分"""
        st.header("💰 收入分成策略")
        
        st.markdown("""
        **收入分成说明**：
        - **模式A**: 无学生付费，无分成
        - **模式B**: 学生付费与高校分成（Luma获得部分比例）
        - **模式C**: 学生付费与高校分成（Luma获得更高比例以补偿高校免费）
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mode_a_share = 0.0  # 固定为0
            st.metric("模式A - Luma分成比例", "0%", help="无学生付费")
        
        with col2:
            mode_b_share = st.slider(
                "模式B - Luma分成比例",
                min_value=0.0, max_value=1.0,
                value=self.default_params['luma_share_from_student_payment']['mode_b'],
                step=0.05,
                format="%.1%",
                help="从学生付费中Luma获得的比例"
            )
        
        with col3:
            mode_c_share = st.slider(
                "模式C - Luma分成比例",
                min_value=0.0, max_value=1.0,
                value=self.default_params['luma_share_from_student_payment']['mode_c'],
                step=0.05,
                format="%.1%",
                help="补偿高校免费，Luma通常获得更高分成"
            )
        
        # 显示高校分成比例
        st.subheader("高校分成比例")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("模式A - 高校分成", "0%", help="无学生付费")
        
        with col2:
            uni_b_share = 1.0 - mode_b_share
            st.metric("模式B - 高校分成", f"{uni_b_share:.1%}")
        
        with col3:
            uni_c_share = 1.0 - mode_c_share
            st.metric("模式C - 高校分成", f"{uni_c_share:.1%}")
        
        return {
            'luma_share_from_student_payment': {
                'mode_a': mode_a_share,
                'mode_b': mode_b_share,
                'mode_c': mode_c_share
            }
        }
    
    def collect_all_parameters(self) -> Dict[str, Any]:
        """收集所有参数"""
        params = {}
        
        # 基础业务配置
        business_config = self.render_business_config_section()
        params.update(business_config)
        
        st.divider()
        
        # 商业模式配置
        mode_config = self.render_business_mode_section()
        params.update(mode_config)
        
        st.divider()
        
        # 高校定价配置
        uni_pricing_config = self.render_university_pricing_section()
        params.update(uni_pricing_config)
        
        st.divider()
        
        # 学生付费配置
        student_config = self.render_student_payment_section()
        params.update(student_config)
        
        st.divider()
        
        # 收入分成配置
        revenue_sharing_config = self.render_revenue_sharing_section()
        params.update(revenue_sharing_config)
        
        return params
    
    def display_parameter_summary(self, params: Dict[str, Any]):
        """显示参数摘要"""
        st.header("📋 参数配置摘要")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("业务基础")
            st.write(f"分析周期: {params['total_half_years']} 个半年")
            st.write(f"每半年新客户: {params['new_clients_per_half_year']} 所高校")
            st.write(f"服务周期: {params['uni_service_period_years']} 年")
            st.write(f"平均学生数: {params['avg_students_per_uni']:,} 人/高校")
            
            st.subheader("商业模式分布")
            mode_dist = params['business_mode_distribution']
            st.write(f"模式A: {mode_dist['mode_a']:.1%}")
            st.write(f"模式B: {mode_dist['mode_b']:.1%}")
            st.write(f"模式C: {mode_dist['mode_c']:.1%}")
        
        with col2:
            st.subheader("高校定价")
            uni_pricing = params['uni_pricing']
            st.write(f"模式A: ¥{uni_pricing['mode_a']['base_price']:,}")
            st.write(f"模式B: ¥{uni_pricing['mode_b']['base_price']:,}")
            st.write(f"模式C: 免费")
            
            st.subheader("学生付费")
            conversion = params['student_paid_conversion_rates']
            st.write(f"模式A转化率: {conversion['mode_a']:.1%}")
            st.write(f"模式B转化率: {conversion['mode_b']:.1%}")
            st.write(f"模式C转化率: {conversion['mode_c']:.1%}")
            
            per_use = params['per_use_pricing']
            st.write(f"按次付费: ¥{per_use['price_per_use']}/次")
            
            sub = params['subscription_pricing']
            st.write(f"月订阅: ¥{sub['monthly_price']}/月")
        
        return params