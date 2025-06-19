"""
简化参数UI模块
Simplified Parameter UI Module

根据业务需求重新整理的参数分类：
1. 基础参数：模拟周期等全局参数
2. 价格参数：学生端和高校端的所有定价
3. 市场规模：新客户数量和学校规模
4. 市场分布：商业模式分布和付费转化率
5. 学生市场细分分布：付费方式选择和订阅期限选择
6. 续费率与复购率参数：各种续费和复购率
7. 分成比例：Luma的收入分成比例
"""

import streamlit as st
from typing import Dict, Any, Tuple
import numpy as np

class SimplifiedParameterUI:
    """简化参数配置UI"""
    
    def __init__(self):
        self.default_params = self._get_default_params()
    
    def _get_default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        return {
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
                'mode_a_price': 600000.0,  # 3年服务周期
                'mode_b_price': 400000.0,  # 3年服务周期
                'mode_c_price': 0.0        # 免费
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
                'student_paid_conversion_rate_bc': 0.1  # B/C模式的学生付费转化率
            },
            
            # 学生市场细分分布
            'student_segmentation': {
                'per_use_ratio': 0.4,                    # 选择按次付费的比例
                'subscription_period_distribution': {     # 在订阅用户中的期限分布
                    '1year': 0.6,
                    '3year': 0.3,
                    '5year': 0.1
                }
            },
            
            # 续费率与复购率参数
            'renewal_rates': {
                'university_3year_renewal': 0.8,         # 高校3年续约率
                'student_per_use_repurchase': 0.7,       # 学生按次付费复购率
                'student_subscription_renewal': 0.75     # 学生订阅续费率
            },
            
            # 分成比例
            'revenue_sharing': {
                'luma_share_from_student': 0.4           # B/C模式下Luma的分成比例
            }
        }
    
    def render_basic_parameters(self) -> Dict[str, Any]:
        """渲染基础参数"""
        st.header("📊 基础参数")
        st.markdown("*全局性的模拟参数*")
        
        total_half_years = st.slider(
            "模拟周期数（半年）",
            min_value=4, max_value=16,
            value=self.default_params['total_half_years'],
            help="设置模拟的半年周期数量。建议至少8个半年以观察完整的3年服务周期和续约情况。"
        )
        
        return {'total_half_years': total_half_years}
    
    def render_pricing_parameters(self) -> Dict[str, Any]:
        """渲染价格参数"""
        st.header("💰 价格参数")
        st.markdown("*学生端和高校端的所有定价策略*")
        
        # 学生端价格
        st.subheader("🎓 学生端价格")
        col1, col2 = st.columns(2)
        
        with col1:
            price_per_use = st.number_input(
                "单次付费价格（元）",
                min_value=1.0, max_value=50.0,
                value=self.default_params['student_prices']['price_per_use'],
                step=0.5,
                help="学生按次使用功能的价格"
            )
            
            price_1year_member = st.number_input(
                "1年订阅价格（元）",
                min_value=50.0, max_value=500.0,
                value=self.default_params['student_prices']['price_1year_member'],
                step=10.0,
                help="学生1年订阅会员的价格"
            )
        
        with col2:
            price_3year_member = st.number_input(
                "3年订阅价格（元）",
                min_value=100.0, max_value=1500.0,
                value=self.default_params['student_prices']['price_3year_member'],
                step=50.0,
                help="学生3年订阅会员的价格"
            )
            
            price_5year_member = st.number_input(
                "5年订阅价格（元）",
                min_value=200.0, max_value=2000.0,
                value=self.default_params['student_prices']['price_5year_member'],
                step=50.0,
                help="学生5年订阅会员的价格"
            )
        
        # 高校端价格
        st.subheader("🏫 高校端价格（3年服务周期）")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mode_a_price = st.number_input(
                "模式A价格（元）",
                min_value=0.0, max_value=2000000.0,
                value=self.default_params['university_prices']['mode_a_price'],
                step=50000.0,
                help="模式A：高校付费 + 学生免费使用全部功能"
            )
        
        with col2:
            mode_b_price = st.number_input(
                "模式B价格（元）",
                min_value=0.0, max_value=2000000.0,
                value=self.default_params['university_prices']['mode_b_price'],
                step=50000.0,
                help="模式B：高校付费 + 学生分层付费"
            )
        
        with col3:
            st.metric("模式C价格", "免费", help="模式C：高校免费 + 学生分层付费")
        
        return {
            'student_prices': {
                'price_per_use': price_per_use,
                'price_1year_member': price_1year_member,
                'price_3year_member': price_3year_member,
                'price_5year_member': price_5year_member
            },
            'university_prices': {
                'mode_a_price': mode_a_price,
                'mode_b_price': mode_b_price,
                'mode_c_price': 0.0
            }
        }
    
    def render_market_scale_parameters(self) -> Dict[str, Any]:
        """渲染市场规模参数"""
        st.header("📈 市场规模")
        st.markdown("*客户获取速度和学校规模设定*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_clients_per_half_year = st.number_input(
                "每半年新签约高校数",
                min_value=1, max_value=50,
                value=self.default_params['market_scale']['new_clients_per_half_year'],
                step=1,
                help="每半年新获取的高校客户数量，决定业务增长速度"
            )
        
        with col2:
            avg_students_per_uni = st.number_input(
                "平均每校学生数",
                min_value=1000, max_value=50000,
                value=self.default_params['market_scale']['avg_students_per_uni'],
                step=1000,
                help="每所高校的平均学生数量，影响潜在付费用户基数"
            )
        
        return {
            'market_scale': {
                'new_clients_per_half_year': new_clients_per_half_year,
                'avg_students_per_uni': avg_students_per_uni
            }
        }
    
    def render_market_distribution_parameters(self) -> Dict[str, Any]:
        """渲染市场分布参数"""
        st.header("🎯 市场分布")
        st.markdown("*商业模式分布和付费转化率*")
        
        # 商业模式分布
        st.subheader("商业模式分布")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mode_a_ratio = st.slider(
                "模式A占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['market_distribution']['mode_a_ratio'],
                step=0.05,
                help="高校付费 + 学生免费使用全部功能"
            )
        
        with col2:
            mode_b_ratio = st.slider(
                "模式B占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['market_distribution']['mode_b_ratio'],
                step=0.05,
                help="高校付费 + 学生分层付费"
            )
        
        with col3:
            mode_c_ratio = st.slider(
                "模式C占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['market_distribution']['mode_c_ratio'],
                step=0.05,
                help="高校免费 + 学生分层付费"
            )
        
        # 自动标准化比例
        total_ratio = mode_a_ratio + mode_b_ratio + mode_c_ratio
        if total_ratio > 0:
            mode_a_ratio /= total_ratio
            mode_b_ratio /= total_ratio
            mode_c_ratio /= total_ratio
        
        if abs(total_ratio - 1.0) > 0.01:
            st.warning(f"商业模式占比总和为 {total_ratio:.2f}，已自动标准化为1.0")
        
        # B/C模式学生付费转化率
        st.subheader("学生付费转化率（仅B/C模式）")
        student_paid_conversion_rate_bc = st.slider(
            "B/C模式学生付费转化率",
            min_value=0.0, max_value=0.5,
            value=self.default_params['market_distribution']['student_paid_conversion_rate_bc'],
            step=0.01,
            format="%.2f",
            help="在B/C模式下，学生转化为付费用户的比例。模式A学生全免费，转化率为0。"
        )
        
        return {
            'market_distribution': {
                'mode_a_ratio': mode_a_ratio,
                'mode_b_ratio': mode_b_ratio,
                'mode_c_ratio': mode_c_ratio,
                'student_paid_conversion_rate_bc': student_paid_conversion_rate_bc
            }
        }
    
    def render_student_segmentation_parameters(self) -> Dict[str, Any]:
        """渲染学生市场细分分布参数"""
        st.header("👥 学生市场细分分布")
        st.markdown("*付费学生的付费方式和订阅期限选择*")
        
        # 付费方式分布
        st.subheader("付费方式选择")
        per_use_ratio = st.slider(
            "选择按次付费的学生比例",
            min_value=0.0, max_value=1.0,
            value=self.default_params['student_segmentation']['per_use_ratio'],
            step=0.05,
            help="付费学生中选择按次付费的比例，其余选择订阅付费"
        )
        
        subscription_ratio = 1.0 - per_use_ratio
        st.info(f"选择订阅付费的学生比例: {subscription_ratio:.1%}")
        
        # 订阅期限分布
        st.subheader("订阅期限选择（在订阅用户中）")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            subscription_1year = st.slider(
                "1年订阅占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['student_segmentation']['subscription_period_distribution']['1year'],
                step=0.05,
                key="sub_1year"
            )
        
        with col2:
            subscription_3year = st.slider(
                "3年订阅占比",
                min_value=0.0, max_value=1.0,
                value=self.default_params['student_segmentation']['subscription_period_distribution']['3year'],
                step=0.05,
                key="sub_3year"
            )
        
        with col3:
            remaining_ratio = max(0, 1.0 - subscription_1year - subscription_3year)
            subscription_5year = remaining_ratio
            st.metric("5年订阅占比", f"{subscription_5year:.1%}")
        
        # 自动标准化订阅期限分布
        total_sub_ratio = subscription_1year + subscription_3year + subscription_5year
        if total_sub_ratio > 0:
            subscription_1year /= total_sub_ratio
            subscription_3year /= total_sub_ratio
            subscription_5year /= total_sub_ratio
        
        return {
            'student_segmentation': {
                'per_use_ratio': per_use_ratio,
                'subscription_period_distribution': {
                    '1year': subscription_1year,
                    '3year': subscription_3year,
                    '5year': subscription_5year
                }
            }
        }
    
    def render_renewal_parameters(self) -> Dict[str, Any]:
        """渲染续费率与复购率参数"""
        st.header("🔄 续费率与复购率参数")
        st.markdown("*客户和学生的留存与续费行为*")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            university_3year_renewal = st.slider(
                "高校3年续约率",
                min_value=0.0, max_value=1.0,
                value=self.default_params['renewal_rates']['university_3year_renewal'],
                step=0.05,
                help="高校客户3年服务期到期后的续约概率"
            )
        
        with col2:
            student_per_use_repurchase = st.slider(
                "按次付费复购率",
                min_value=0.0, max_value=1.0,
                value=self.default_params['renewal_rates']['student_per_use_repurchase'],
                step=0.05,
                help="选择按次付费的学生继续付费的概率（简化为当期折算）"
            )
        
        with col3:
            student_subscription_renewal = st.slider(
                "订阅续费率",
                min_value=0.0, max_value=1.0,
                value=self.default_params['renewal_rates']['student_subscription_renewal'],
                step=0.05,
                help="学生订阅到期后的续费概率"
            )
        
        return {
            'renewal_rates': {
                'university_3year_renewal': university_3year_renewal,
                'student_per_use_repurchase': student_per_use_repurchase,
                'student_subscription_renewal': student_subscription_renewal
            }
        }
    
    def render_revenue_sharing_parameters(self) -> Dict[str, Any]:
        """渲染分成比例参数"""
        st.header("💼 分成比例")
        st.markdown("*B/C模式下的收入分成设定*")
        
        luma_share_from_student = st.slider(
            "Luma学生付费分成比例",
            min_value=0.0, max_value=1.0,
            value=self.default_params['revenue_sharing']['luma_share_from_student'],
            step=0.05,
            format="%.2f",
            help="B/C模式下，Luma从学生付费中获得的比例"
        )
        
        university_share = 1.0 - luma_share_from_student
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Luma分成比例", f"{luma_share_from_student:.1%}")
        with col2:
            st.metric("高校分成比例", f"{university_share:.1%}")
        
        return {
            'revenue_sharing': {
                'luma_share_from_student': luma_share_from_student
            }
        }
    
    def collect_all_parameters(self) -> Dict[str, Any]:
        """收集所有参数"""
        params = {}
        
        # 基础参数
        basic_params = self.render_basic_parameters()
        params.update(basic_params)
        
        st.divider()
        
        # 价格参数
        pricing_params = self.render_pricing_parameters()
        params.update(pricing_params)
        
        st.divider()
        
        # 市场规模
        market_scale_params = self.render_market_scale_parameters()
        params.update(market_scale_params)
        
        st.divider()
        
        # 市场分布
        market_distribution_params = self.render_market_distribution_parameters()
        params.update(market_distribution_params)
        
        st.divider()
        
        # 学生市场细分分布
        segmentation_params = self.render_student_segmentation_parameters()
        params.update(segmentation_params)
        
        st.divider()
        
        # 续费率与复购率参数
        renewal_params = self.render_renewal_parameters()
        params.update(renewal_params)
        
        st.divider()
        
        # 分成比例
        revenue_sharing_params = self.render_revenue_sharing_parameters()
        params.update(revenue_sharing_params)
        
        return params
    
    def display_parameter_summary(self, params: Dict[str, Any]):
        """显示参数配置摘要"""
        st.header("📋 参数配置摘要")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("基础设置")
            st.write(f"**模拟周期**: {params['total_half_years']} 个半年")
            st.write(f"**每半年新客户**: {params['market_scale']['new_clients_per_half_year']} 所高校")
            st.write(f"**平均学校规模**: {params['market_scale']['avg_students_per_uni']:,} 人")
            
            st.subheader("商业模式分布")
            dist = params['market_distribution']
            st.write(f"**模式A**: {dist['mode_a_ratio']:.1%}")
            st.write(f"**模式B**: {dist['mode_b_ratio']:.1%}")
            st.write(f"**模式C**: {dist['mode_c_ratio']:.1%}")
            st.write(f"**B/C付费转化率**: {dist['student_paid_conversion_rate_bc']:.1%}")
            
            st.subheader("学生市场细分")
            seg = params['student_segmentation']
            st.write(f"**按次付费**: {seg['per_use_ratio']:.1%}")
            st.write(f"**订阅付费**: {1-seg['per_use_ratio']:.1%}")
            sub_dist = seg['subscription_period_distribution']
            st.write(f"  - 1年: {sub_dist['1year']:.1%}")
            st.write(f"  - 3年: {sub_dist['3year']:.1%}")
            st.write(f"  - 5年: {sub_dist['5year']:.1%}")
        
        with col2:
            st.subheader("价格设定")
            st_prices = params['student_prices']
            st.write(f"**学生单次**: ¥{st_prices['price_per_use']}")
            st.write(f"**学生1年订阅**: ¥{st_prices['price_1year_member']}")
            st.write(f"**学生3年订阅**: ¥{st_prices['price_3year_member']}")
            st.write(f"**学生5年订阅**: ¥{st_prices['price_5year_member']}")
            
            uni_prices = params['university_prices']
            st.write(f"**高校模式A**: ¥{uni_prices['mode_a_price']:,.0f}")
            st.write(f"**高校模式B**: ¥{uni_prices['mode_b_price']:,.0f}")
            st.write(f"**高校模式C**: 免费")
            
            st.subheader("续费与分成")
            renewal = params['renewal_rates']
            st.write(f"**高校3年续约率**: {renewal['university_3year_renewal']:.1%}")
            st.write(f"**按次付费复购率**: {renewal['student_per_use_repurchase']:.1%}")
            st.write(f"**订阅续费率**: {renewal['student_subscription_renewal']:.1%}")
            
            sharing = params['revenue_sharing']
            st.write(f"**Luma学生分成**: {sharing['luma_share_from_student']:.1%}")
            st.write(f"**高校学生分成**: {1-sharing['luma_share_from_student']:.1%}")
        
        return params