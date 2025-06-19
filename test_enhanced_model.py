#!/usr/bin/env python3
"""
增强版财务模型测试脚本
Enhanced Financial Model Test Script

测试新的三种商业模式：
- 模式A: 高校付费 + 学生免费使用全部功能
- 模式B: 高校付费 + 学生免费基础功能 + 学生付费高级功能
- 模式C: 高校免费 + 学生免费基础功能 + 学生付费高级功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'lumasalsemodel_trail'))

from luma_sales_model.enhanced_financial_model import LumaEnhancedFinancialModel
import pandas as pd
import numpy as np

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试1: 基础功能测试")
    
    # 使用默认参数创建模型
    model = LumaEnhancedFinancialModel()
    
    # 运行模型
    results_df = model.run_model()
    
    # 验证结果
    assert results_df is not None, "结果DataFrame不应为空"
    assert len(results_df) > 0, "结果应包含数据"
    assert 'luma_revenue_total' in results_df.columns, "应包含Luma总收入列"
    
    print(f"✅ 基础功能测试通过")
    print(f"   - 生成了 {len(results_df)} 个周期的数据")
    print(f"   - Luma总收入: ¥{results_df['luma_revenue_total'].sum():,.0f}")
    print()

def test_business_modes():
    """测试不同商业模式"""
    print("🧪 测试2: 商业模式测试")
    
    # 测试各种模式分布
    test_distributions = [
        {'mode_a': 1.0, 'mode_b': 0.0, 'mode_c': 0.0},  # 纯模式A
        {'mode_a': 0.0, 'mode_b': 1.0, 'mode_c': 0.0},  # 纯模式B
        {'mode_a': 0.0, 'mode_b': 0.0, 'mode_c': 1.0},  # 纯模式C
        {'mode_a': 0.33, 'mode_b': 0.33, 'mode_c': 0.34}  # 均匀分布
    ]
    
    for i, distribution in enumerate(test_distributions):
        print(f"   测试分布 {i+1}: {distribution}")
        
        params = {
            'total_half_years': 6,
            'business_mode_distribution': distribution
        }
        
        model = LumaEnhancedFinancialModel(params)
        results_df = model.run_model()
        
        total_revenue = results_df['luma_revenue_total'].sum()
        uni_revenue = results_df['luma_revenue_from_uni'].sum()
        student_revenue = results_df['luma_revenue_from_student_share'].sum()
        
        print(f"     总收入: ¥{total_revenue:,.0f}")
        print(f"     高校收入: ¥{uni_revenue:,.0f} ({uni_revenue/total_revenue:.1%})")
        print(f"     学生分成: ¥{student_revenue:,.0f} ({student_revenue/total_revenue:.1%})")
        
        # 验证模式逻辑
        if distribution['mode_a'] == 1.0:
            # 纯模式A应该没有学生付费分成
            assert student_revenue == 0, "模式A不应有学生付费分成"
            print("     ✅ 模式A逻辑正确")
        elif distribution['mode_c'] == 1.0:
            # 纯模式C应该没有高校收入
            assert uni_revenue == 0, "模式C不应有高校收入"
            print("     ✅ 模式C逻辑正确")
        
        print()

def test_pricing_sensitivity():
    """测试定价敏感性"""
    print("🧪 测试3: 定价敏感性测试")
    
    base_params = {
        'total_half_years': 6,
        'business_mode_distribution': {'mode_a': 0.5, 'mode_b': 0.5, 'mode_c': 0.0}
    }
    
    # 测试不同的高校定价
    pricing_tests = [
        {'mode_a_price': 300000, 'mode_b_price': 200000},  # 低价
        {'mode_a_price': 600000, 'mode_b_price': 400000},  # 默认价格
        {'mode_a_price': 900000, 'mode_b_price': 600000}   # 高价
    ]
    
    for i, pricing in enumerate(pricing_tests):
        print(f"   定价测试 {i+1}: 模式A=¥{pricing['mode_a_price']:,}, 模式B=¥{pricing['mode_b_price']:,}")
        
        params = base_params.copy()
        params['uni_pricing'] = {
            'mode_a': {'base_price': pricing['mode_a_price'], 'negotiation_range': (0.8, 1.2), 'price_elasticity': -0.2},
            'mode_b': {'base_price': pricing['mode_b_price'], 'negotiation_range': (0.8, 1.2), 'price_elasticity': -0.15},
            'mode_c': {'base_price': 0, 'negotiation_range': (1.0, 1.0), 'price_elasticity': 0}
        }
        
        model = LumaEnhancedFinancialModel(params)
        results_df = model.run_model()
        
        total_revenue = results_df['luma_revenue_total'].sum()
        print(f"     总收入: ¥{total_revenue:,.0f}")
        print()

def test_student_payment_models():
    """测试学生付费模式"""
    print("🧪 测试4: 学生付费模式测试")
    
    # 测试不同的学生付费参数
    base_params = {
        'total_half_years': 6,
        'business_mode_distribution': {'mode_a': 0.0, 'mode_b': 0.5, 'mode_c': 0.5}
    }
    
    # 测试按次付费 vs 订阅付费比例
    payment_method_tests = [
        {'per_use': 1.0, 'subscription': 0.0},   # 纯按次付费
        {'per_use': 0.0, 'subscription': 1.0},   # 纯订阅付费
        {'per_use': 0.4, 'subscription': 0.6}    # 混合模式
    ]
    
    for i, method_dist in enumerate(payment_method_tests):
        print(f"   付费方式测试 {i+1}: 按次={method_dist['per_use']:.0%}, 订阅={method_dist['subscription']:.0%}")
        
        params = base_params.copy()
        params['student_payment_method_distribution'] = method_dist
        
        model = LumaEnhancedFinancialModel(params)
        results_df = model.run_model()
        
        per_use_revenue = results_df['student_revenue_per_use'].sum()
        subscription_revenue = results_df['student_revenue_subscription'].sum()
        total_student_revenue = per_use_revenue + subscription_revenue
        
        print(f"     按次付费收入: ¥{per_use_revenue:,.0f}")
        print(f"     订阅付费收入: ¥{subscription_revenue:,.0f}")
        print(f"     总学生收入: ¥{total_student_revenue:,.0f}")
        
        if method_dist['per_use'] == 1.0:
            assert subscription_revenue == 0, "纯按次付费模式不应有订阅收入"
            print("     ✅ 纯按次付费逻辑正确")
        elif method_dist['subscription'] == 1.0:
            assert per_use_revenue == 0, "纯订阅模式不应有按次付费收入"
            print("     ✅ 纯订阅付费逻辑正确")
        
        print()

def test_renewal_logic():
    """测试续约逻辑"""
    print("🧪 测试5: 续约逻辑测试")
    
    # 使用较长周期来观察续约效果
    params = {
        'total_half_years': 10,  # 5年，观察续约
        'uni_service_period_years': 3,
        'business_mode_distribution': {'mode_a': 1.0, 'mode_b': 0.0, 'mode_c': 0.0},
        'uni_renewal_rates': {'mode_a': 0.8, 'mode_b': 0.8, 'mode_c': 0.8}
    }
    
    model = LumaEnhancedFinancialModel(params)
    results_df = model.run_model()
    
    print("   续约期分析:")
    print("   周期    活跃高校    新签收入    续约收入")
    for _, row in results_df.iterrows():
        period = int(row['period'])
        active_unis = row['active_universities']
        new_revenue = row['uni_revenue_new_signups']
        renewal_revenue = row['uni_revenue_renewals']
        
        print(f"   H{period:2d}     {active_unis:8.0f}    {new_revenue:10.0f}    {renewal_revenue:10.0f}")
    
    # 验证续约逻辑
    # 在第7期（H7）应该有第一批续约
    h7_data = results_df[results_df['period'] == 7].iloc[0]
    assert h7_data['uni_revenue_renewals'] > 0, "第7期应该有续约收入"
    print("   ✅ 续约逻辑正确")
    print()

def test_business_summary():
    """测试业务摘要功能"""
    print("🧪 测试6: 业务摘要测试")
    
    model = LumaEnhancedFinancialModel()
    results_df = model.run_model()
    
    # 获取业务摘要
    summary = model.get_business_summary()
    
    print("   业务摘要:")
    for key, value in summary.items():
        if isinstance(value, (int, float)):
            if 'revenue' in key.lower():
                print(f"   {key}: ¥{value:,.0f}")
            elif 'rate' in key.lower():
                print(f"   {key}: {value:.1%}")
            else:
                print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    print("   ✅ 业务摘要生成成功")
    print()

def test_parameter_validation():
    """测试参数验证"""
    print("🧪 测试7: 参数验证测试")
    
    # 测试无效参数
    invalid_params_tests = [
        {
            'desc': '商业模式分布不为1',
            'params': {'business_mode_distribution': {'mode_a': 0.5, 'mode_b': 0.3, 'mode_c': 0.3}}
        },
        {
            'desc': '续约率超出范围',
            'params': {'uni_renewal_rates': {'mode_a': 1.5, 'mode_b': 0.8, 'mode_c': 0.8}}
        }
    ]
    
    for test in invalid_params_tests:
        print(f"   测试: {test['desc']}")
        try:
            model = LumaEnhancedFinancialModel(test['params'])
            print(f"     ⚠️ 参数验证应该产生警告")
        except Exception as e:
            print(f"     ❌ 参数验证失败: {e}")
    
    print("   ✅ 参数验证测试完成")
    print()

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 开始增强版财务模型综合测试")
    print("=" * 60)
    
    try:
        test_basic_functionality()
        test_business_modes()
        test_pricing_sensitivity()
        test_student_payment_models()
        test_renewal_logic()
        test_business_summary()
        test_parameter_validation()
        
        print("🎉 所有测试通过！增强版财务模型工作正常。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)