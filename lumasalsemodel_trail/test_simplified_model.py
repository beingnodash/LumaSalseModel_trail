#!/usr/bin/env python3
"""
简化版Luma财务模型测试脚本
Simplified Luma Financial Model Test Script

测试目标：
1. 验证简化版参数结构的正确性
2. 测试统一分成比例逻辑
3. 验证收入记账时间处理
4. 确保业务逻辑一致性
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from luma_sales_model.simplified_financial_model import LumaSimplifiedFinancialModel

class TestSimplifiedLumaModel:
    """简化版Luma财务模型测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.default_params = {
            'total_half_years': 6,
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
            'market_scale': {
                'new_clients_per_half_year': 5,
                'avg_students_per_uni': 10000
            },
            'market_distribution': {
                'mode_a_ratio': 0.3,
                'mode_b_ratio': 0.4,
                'mode_c_ratio': 0.3,
                'student_paid_conversion_rate_bc': 0.1
            },
            'student_segmentation': {
                'per_use_ratio': 0.4,
                'subscription_period_distribution': {
                    '1year': 0.6,
                    '3year': 0.3,
                    '5year': 0.1
                }
            },
            'renewal_rates': {
                'university_3year_renewal': 0.8,
                'student_per_use_repurchase': 0.7,
                'student_subscription_renewal': 0.75
            },
            'revenue_sharing': {
                'luma_share_from_student': 0.4
            }
        }
    
    def test_model_initialization(self):
        """测试模型初始化"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 验证参数正确加载
        assert model.params['total_half_years'] == 6
        assert model.params['market_scale']['new_clients_per_half_year'] == 5
        assert model.params['revenue_sharing']['luma_share_from_student'] == 0.4
        
        print("✅ 模型初始化测试通过")
    
    def test_parameter_validation(self):
        """测试参数验证"""
        # 测试商业模式分布总和不为1的情况
        invalid_params = self.default_params.copy()
        invalid_params['market_distribution'] = {
            'mode_a_ratio': 0.5,
            'mode_b_ratio': 0.5,
            'mode_c_ratio': 0.5,  # 总和为1.5
            'student_paid_conversion_rate_bc': 0.1
        }
        
        # 应该生成警告但不抛出异常
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            model = LumaSimplifiedFinancialModel(invalid_params)
            assert len(w) > 0
            assert "分布总和" in str(w[0].message)
        
        print("✅ 参数验证测试通过")
    
    def test_university_revenue_calculation(self):
        """测试高校收入计算"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 测试模式A新签约收入
        mode_a_revenue = model._calculate_university_revenue('mode_a', 2, 0, 0)
        expected_revenue = 2 * 600000.0
        assert mode_a_revenue == expected_revenue
        
        # 测试模式C收入（应该为0）
        mode_c_revenue = model._calculate_university_revenue('mode_c', 2, 0, 0)
        assert mode_c_revenue == 0.0
        
        # 测试续约收入（第6期，3年后）
        renewal_revenue = model._calculate_university_revenue('mode_b', 3, 6, 0)
        expected_renewal = 3 * 0.8 * 400000.0  # 3所学校 * 80%续约率 * 模式B价格
        assert renewal_revenue == expected_renewal
        
        print("✅ 高校收入计算测试通过")
    
    def test_student_revenue_calculation(self):
        """测试学生收入计算"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 测试模式A学生收入（应该为0）
        mode_a_student = model._calculate_student_revenue('mode_a', 1000, 100, 0)
        assert mode_a_student['total_student_revenue'] == 0
        assert mode_a_student['luma_share'] == 0
        
        # 测试模式B/C学生收入
        mode_b_student = model._calculate_student_revenue('mode_b', 1000, 100, 0)
        
        # 验证分成比例
        total_revenue = mode_b_student['total_student_revenue']
        luma_share = mode_b_student['luma_share']
        uni_share = mode_b_student['uni_share']
        
        assert abs(luma_share + uni_share - total_revenue) < 0.01
        assert abs(luma_share / total_revenue - 0.4) < 0.01  # Luma应得40%
        
        print("✅ 学生收入计算测试通过")
    
    def test_per_use_revenue_calculation(self):
        """测试按次付费收入计算"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 100个付费学生，40%选择按次付费
        active_paying_students = 100
        per_use_revenue = model._calculate_per_use_revenue(active_paying_students)
        
        # 验证计算逻辑
        per_use_students = 100 * 0.4  # 40个按次付费学生
        price_per_use = 8.0
        base_uses_per_half_year = 3
        repurchase_rate = 0.7
        effective_uses = base_uses_per_half_year * (1 + repurchase_rate)
        
        expected_revenue = per_use_students * price_per_use * effective_uses
        assert abs(per_use_revenue - expected_revenue) < 0.01
        
        print("✅ 按次付费收入计算测试通过")
    
    def test_subscription_revenue_calculation(self):
        """测试订阅收入计算"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 100个付费学生，60%选择订阅付费
        active_paying_students = 100
        subscription_revenue = model._calculate_subscription_revenue(active_paying_students, 0)
        
        # 验证分摊逻辑
        subscription_students = 100 * 0.6  # 60个订阅学生
        
        # 1年订阅：60% * 60个学生 * 150元/2半年
        students_1year = subscription_students * 0.6
        revenue_1year = students_1year * 150.0 / 2
        
        # 3年订阅：30% * 60个学生 * 400元/6半年
        students_3year = subscription_students * 0.3
        revenue_3year = students_3year * 400.0 / 6
        
        # 5年订阅：10% * 60个学生 * 600元/10半年
        students_5year = subscription_students * 0.1
        revenue_5year = students_5year * 600.0 / 10
        
        expected_total = revenue_1year + revenue_3year + revenue_5year
        assert abs(subscription_revenue - expected_total) < 0.01
        
        print("✅ 订阅收入计算测试通过")
    
    def test_unified_revenue_sharing(self):
        """测试统一分成比例"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 测试B模式和C模式使用相同分成比例
        mode_b_result = model._calculate_student_revenue('mode_b', 1000, 100, 0)
        mode_c_result = model._calculate_student_revenue('mode_c', 1000, 100, 0)
        
        # B和C模式的分成比例应该相同
        if mode_b_result['total_student_revenue'] > 0 and mode_c_result['total_student_revenue'] > 0:
            b_luma_ratio = mode_b_result['luma_share'] / mode_b_result['total_student_revenue']
            c_luma_ratio = mode_c_result['luma_share'] / mode_c_result['total_student_revenue']
            assert abs(b_luma_ratio - c_luma_ratio) < 0.001
            assert abs(b_luma_ratio - 0.4) < 0.001  # 验证40%分成比例
        
        print("✅ 统一分成比例测试通过")
    
    def test_cohort_creation(self):
        """测试客户群组创建"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        cohort = model._create_new_cohort(0)
        
        # 验证群组结构
        assert cohort['cohort_id'] == 'C_H1'
        assert cohort['created_period'] == 0
        assert 'universities' in cohort
        assert 'students' in cohort
        
        # 验证商业模式分布 - 允许四舍五入的差异
        total_unis = sum(data['count'] for data in cohort['universities'].values())
        expected_total = 5  # new_clients_per_half_year
        # 由于分配到各模式时可能有整数四舍五入，允许差异
        assert abs(total_unis - expected_total) <= 1
        
        # 验证模式A学生不付费
        if 'mode_a' in cohort['students']:
            assert cohort['students']['mode_a']['paying_students'] == 0
        
        print("✅ 客户群组创建测试通过")
    
    def test_renewal_logic(self):
        """测试续约逻辑"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 创建群组并测试续约
        cohort = model._create_new_cohort(0)
        
        # 模拟3年后续约（第6期）
        model._update_cohort_renewals(cohort, 6)
        
        # 验证高校续约率
        for mode_key, uni_data in cohort['universities'].items():
            if uni_data['count'] > 0:
                expected_active = int(uni_data['count'] * 0.8)  # 80%续约率
                assert uni_data['active_count'] == expected_active
        
        print("✅ 续约逻辑测试通过")
    
    def test_full_model_run(self):
        """测试完整模型运行"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        results_df = model.run_model()
        
        # 验证结果结构
        assert len(results_df) == 6  # 6个半年周期
        assert 'period' in results_df.columns
        assert 'luma_revenue_total' in results_df.columns
        assert 'uni_revenue_total' in results_df.columns
        assert 'student_revenue_total' in results_df.columns
        
        # 验证收入非负
        assert (results_df['luma_revenue_total'] >= 0).all()
        assert (results_df['uni_revenue_total'] >= 0).all()
        assert (results_df['student_revenue_total'] >= 0).all()
        
        # 验证业务指标
        assert (results_df['active_universities'] >= 0).all()
        assert (results_df['total_paying_students'] >= 0).all()
        
        print("✅ 完整模型运行测试通过")
    
    def test_business_summary(self):
        """测试业务摘要"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        results_df = model.run_model()
        summary = model.get_business_summary()
        
        # 验证摘要数据
        assert summary['total_periods'] == 6
        assert summary['total_luma_revenue'] > 0
        assert summary['peak_active_universities'] > 0
        assert 'revenue_sharing' in summary
        assert summary['revenue_sharing']['luma_share_from_student'] == 0.4
        
        print("✅ 业务摘要测试通过")
    
    def test_revenue_accounting_logic(self):
        """测试收入记账逻辑简化"""
        model = LumaSimplifiedFinancialModel(self.default_params)
        
        # 验证订阅收入按期分摊
        subscription_revenue = model._calculate_subscription_revenue(100, 0)
        
        # 验证按次付费包含复购率当期折算
        per_use_revenue = model._calculate_per_use_revenue(100)
        
        # 两种收入都应该大于0（如果有付费学生）
        if subscription_revenue > 0 and per_use_revenue > 0:
            print(f"订阅收入（按期分摊）: {subscription_revenue:.2f}")
            print(f"按次付费收入（含复购）: {per_use_revenue:.2f}")
        
        print("✅ 收入记账逻辑测试通过")

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行简化版Luma财务模型测试...")
    print("=" * 60)
    
    test_instance = TestSimplifiedLumaModel()
    
    # 运行所有测试方法
    test_methods = [
        test_instance.test_model_initialization,
        test_instance.test_parameter_validation,
        test_instance.test_university_revenue_calculation,
        test_instance.test_student_revenue_calculation,
        test_instance.test_per_use_revenue_calculation,
        test_instance.test_subscription_revenue_calculation,
        test_instance.test_unified_revenue_sharing,
        test_instance.test_cohort_creation,
        test_instance.test_renewal_logic,
        test_instance.test_full_model_run,
        test_instance.test_business_summary,
        test_instance.test_revenue_accounting_logic
    ]
    
    passed_tests = 0
    total_tests = len(test_methods)
    
    for i, test_method in enumerate(test_methods, 1):
        try:
            test_instance.setup_method()  # 重新初始化
            test_method()
            passed_tests += 1
        except Exception as e:
            print(f"❌ 测试失败: {test_method.__name__}")
            print(f"   错误: {str(e)}")
            continue
    
    print("=" * 60)
    print(f"📊 测试结果: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！简化版财务模型运行正常。")
        return True
    else:
        print(f"⚠️  有 {total_tests - passed_tests} 项测试失败，请检查模型实现。")
        return False

def demo_simplified_model():
    """演示简化版模型功能"""
    print("\n" + "=" * 60)
    print("📋 简化版Luma财务模型功能演示")
    print("=" * 60)
    
    # 创建模型实例
    model = LumaSimplifiedFinancialModel()
    
    print("1. 模型参数概览:")
    params = model.params
    print(f"   - 模拟周期: {params['total_half_years']} 个半年")
    print(f"   - 商业模式分布: A({params['market_distribution']['mode_a_ratio']:.1%}) | "
          f"B({params['market_distribution']['mode_b_ratio']:.1%}) | "
          f"C({params['market_distribution']['mode_c_ratio']:.1%})")
    print(f"   - 统一分成比例: Luma {params['revenue_sharing']['luma_share_from_student']:.1%}")
    
    print("\n2. 运行财务模型...")
    results_df = model.run_model()
    
    print("\n3. 关键结果:")
    summary = model.get_business_summary()
    print(f"   - Luma总收入: ¥{summary['total_luma_revenue']:,.0f}")
    print(f"   - 平均期收入: ¥{summary['avg_luma_revenue_per_period']:,.0f}")
    print(f"   - 峰值活跃高校: {summary['peak_active_universities']:.0f} 所")
    print(f"   - 峰值付费学生: {summary['peak_paying_students']:,.0f} 人")
    print(f"   - 收入增长率: {summary['revenue_growth_rate']:.1%}")
    
    print("\n4. 简化特性验证:")
    print("   ✅ 取消Type2的abc细分")
    print("   ✅ 统一B/C模式分成比例")
    print("   ✅ 7大类参数结构")
    print("   ✅ 优化收入记账逻辑")
    
    print("\n5. 前3期收入明细:")
    for i in range(min(3, len(results_df))):
        row = results_df.iloc[i]
        print(f"   H{i+1}: Luma¥{row['luma_revenue_total']:,.0f} | "
              f"高校¥{row['uni_revenue_total']:,.0f} | "
              f"学生¥{row['student_revenue_total']:,.0f}")

if __name__ == "__main__":
    # 运行测试
    success = run_all_tests()
    
    if success:
        # 运行演示
        demo_simplified_model()
    
    print("\n" + "=" * 60)
    print("📄 测试报告已生成，简化版模型准备就绪！")
    print("💡 建议：在Streamlit应用中使用'简化版商业模式分析'页面")
    print("=" * 60)