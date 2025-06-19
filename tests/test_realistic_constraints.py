# 现实约束功能自动化测试套件
# Automated Test Suite for Realistic Constraints Functionality

import pytest
import numpy as np
import pandas as pd
import sys
import os
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lumasalsemodel_trail'))

from streamlit_app.utils.realistic_constraints import RealisticConstraintHandler
from streamlit_app.utils.enhanced_optimization import (
    run_model_with_realistic_constraints,
    enhanced_grid_search_optimizer,
    enhanced_bayesian_optimizer,
    enhanced_genetic_algorithm_optimizer
)

class TestRealisticConstraintHandler:
    """测试现实约束处理器的核心功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.handler = RealisticConstraintHandler()
        
        # 测试用的标准参数集
        self.normal_params = {
            'price_annual_member': 30.0,
            'price_3year_member': 80.0,
            'price_5year_member': 120.0,
            'price_per_feature_use': 5.0,
            'type2_luma_share_from_student.a': 0.5,
            'type2_luma_share_from_student.b': 0.6,
            'type2_luma_share_from_student.c': 0.7,
            'new_clients_per_half_year': 8,
            'renewal_rate_uni': 0.8,
            'student_total_paid_cr': 0.05
        }
        
        # 极值参数集（模拟优化器找到的不现实解）
        self.extreme_params = {
            'price_annual_member': 100.0,  # 极高价格
            'price_3year_member': 300.0,   # 极高价格
            'price_5year_member': 500.0,   # 极高价格
            'price_per_feature_use': 50.0, # 极高价格
            'type2_luma_share_from_student.a': 0.95,  # 极高分成
            'type2_luma_share_from_student.b': 0.98,  # 极高分成
            'type2_luma_share_from_student.c': 0.99,  # 极高分成
            'new_clients_per_half_year': 25,  # 不现实的获客目标
            'renewal_rate_uni': 0.99,  # 不现实的续约率
            'student_total_paid_cr': 0.2   # 不现实的转化率
        }

    def test_penalty_scoring_normal_params(self):
        """测试正常参数的惩罚得分应该很低"""
        penalty = self.handler.calculate_penalty_score(self.normal_params)
        assert penalty < 50, f"正常参数的惩罚分数应该低于50，实际: {penalty}"
        print(f"✅ 正常参数惩罚分数: {penalty:.2f}")

    def test_penalty_scoring_extreme_params(self):
        """测试极值参数的惩罚得分应该很高"""
        penalty = self.handler.calculate_penalty_score(self.extreme_params)
        assert penalty > 200, f"极值参数的惩罚分数应该高于200，实际: {penalty}"
        print(f"✅ 极值参数惩罚分数: {penalty:.2f}")

    def test_price_elasticity_application(self):
        """测试价格弹性约束的应用"""
        high_price_params = {
            'price_annual_member': 80.0,  # 高价格
            'student_total_paid_cr': 0.05  # 原始转化率
        }
        
        # 应用价格弹性约束
        result = self.handler._apply_price_elasticity(high_price_params.copy())
        
        # 高价格应该导致转化率下降
        original_cr = high_price_params['student_total_paid_cr']
        adjusted_cr = result.get('student_total_paid_cr', original_cr)
        
        assert adjusted_cr < original_cr, f"高价格应该降低转化率: 原始{original_cr} vs 调整后{adjusted_cr}"
        print(f"✅ 价格弹性测试: 转化率从 {original_cr:.3f} 调整到 {adjusted_cr:.3f}")

    def test_share_acceptance_constraints(self):
        """测试分成比例接受度约束"""
        high_share_params = {
            'type2_luma_share_from_student.a': 0.8,  # 超过60%阈值
            'renewal_rate_uni': 0.85  # 原始续约率
        }
        
        result = self.handler._apply_share_acceptance(high_share_params.copy())
        
        # 高分成比例应该降低续约率
        original_renewal = high_share_params['renewal_rate_uni']
        adjusted_renewal = result.get('renewal_rate_uni', original_renewal)
        
        assert adjusted_renewal < original_renewal, f"高分成应该降低续约率: 原始{original_renewal} vs 调整后{adjusted_renewal}"
        print(f"✅ 分成接受度测试: 续约率从 {original_renewal:.3f} 调整到 {adjusted_renewal:.3f}")

    def test_market_cost_constraints(self):
        """测试市场扩张成本约束"""
        high_client_params = {
            'new_clients_per_half_year': 20  # 过高的获客目标
        }
        
        result = self.handler._apply_market_costs(high_client_params.copy())
        
        # 过高的获客目标应该被调整
        adjusted_clients = result['new_clients_per_half_year']
        assert adjusted_clients <= 12, f"过高获客目标应该被调整到12以下: {adjusted_clients}"
        print(f"✅ 市场成本约束测试: 获客目标从 {high_client_params['new_clients_per_half_year']} 调整到 {adjusted_clients}")

    def test_competitive_constraints(self):
        """测试竞争性约束"""
        high_price_all_params = {
            'price_annual_member': 55.0,   # 接近上限
            'price_3year_member': 140.0,   # 接近上限
            'price_5year_member': 190.0,   # 接近上限
            'student_total_paid_cr': 0.05  # 原始转化率
        }
        
        result = self.handler._apply_competitive_constraints(high_price_all_params.copy())
        
        # 多个高价格应该触发竞争约束，降低转化率
        original_cr = high_price_all_params['student_total_paid_cr']
        adjusted_cr = result.get('student_total_paid_cr', original_cr)
        
        assert adjusted_cr < original_cr, f"多个高价格应该降低转化率: 原始{original_cr} vs 调整后{adjusted_cr}"
        print(f"✅ 竞争约束测试: 转化率从 {original_cr:.3f} 调整到 {adjusted_cr:.3f}")

    def test_constraint_report_generation(self):
        """测试约束分析报告生成"""
        # 测试正常参数报告
        normal_report = self.handler.generate_constraint_report(self.normal_params)
        assert "✅" in normal_report, "正常参数报告应包含通过标志"
        
        # 测试极值参数报告
        extreme_report = self.handler.generate_constraint_report(self.extreme_params)
        assert "❌" in extreme_report or "🔶" in extreme_report, "极值参数报告应包含警告标志"
        
        print("✅ 约束报告生成测试通过")

    def test_parameter_boundary_enforcement(self):
        """测试参数边界强制执行"""
        # 测试每个参数的边界
        for param_name, (min_val, max_val) in self.handler.reasonable_ranges.items():
            # 测试超出上界的情况
            over_params = {param_name: max_val * 1.5}
            penalty = self.handler.calculate_penalty_score(over_params)
            assert penalty > 0, f"参数 {param_name} 超出上界应有惩罚"
            
            # 测试低于下界的情况
            under_params = {param_name: min_val * 0.5}
            penalty = self.handler.calculate_penalty_score(under_params)
            assert penalty > 0, f"参数 {param_name} 低于下界应有惩罚"
        
        print("✅ 参数边界强制执行测试通过")

class TestEnhancedOptimization:
    """测试集成现实约束的优化函数"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.base_params = {
            'total_half_years': 4,
            'new_clients_per_half_year': 5,
            'mode_distribution': {'Type1': 0.2, 'Type2a': 0.0, 'Type2b': 0.0, 'Type2c': 0.2, 'Type3': 0.6},
            'avg_students_per_uni': 10000,
            'student_total_paid_cr': 0.05
        }
        
        self.param_ranges = {
            'price_annual_member': (20, 60),
            'price_per_feature_use': (3, 15),
            'type2_luma_share_from_student.a': (0.3, 0.8)
        }

    @patch('luma_sales_model.financial_model.LumaFinancialModel')
    def test_realistic_constraint_model_evaluation(self, mock_model_class):
        """测试现实约束模型评估函数"""
        # 模拟模型返回结果
        mock_model = MagicMock()
        mock_results_df = pd.DataFrame({'total_revenue': [100000, 120000, 110000]})
        mock_model.run_model.return_value = mock_results_df
        mock_model_class.return_value = mock_model
        
        # 测试正常参数
        normal_params = {'price_annual_member': 30.0}
        score = run_model_with_realistic_constraints(
            self.base_params, normal_params, 'total_revenue'
        )
        
        assert score > 0, f"正常参数应该得到正分数: {score}"
        
        # 测试极值参数
        extreme_params = {'price_annual_member': 200.0}  # 极高价格
        extreme_score = run_model_with_realistic_constraints(
            self.base_params, extreme_params, 'total_revenue'
        )
        
        assert extreme_score < score, f"极值参数分数应该更低: 正常{score} vs 极值{extreme_score}"
        print(f"✅ 现实约束评估: 正常参数{score:.2f} vs 极值参数{extreme_score:.2f}")

    def test_optimization_prevents_extreme_values(self):
        """测试优化算法是否防止极值解"""
        # 这个测试验证现实约束是否有效防止优化器找到极值解
        
        # 模拟一个简单的优化场景
        constraint_handler = RealisticConstraintHandler()
        
        # 生成一系列测试参数，包括极值
        test_cases = [
            {'price_annual_member': 25.0, 'expected_penalty': 'low'},
            {'price_annual_member': 45.0, 'expected_penalty': 'low'},
            {'price_annual_member': 80.0, 'expected_penalty': 'medium'},
            {'price_annual_member': 150.0, 'expected_penalty': 'very_high'}
        ]
        
        penalties = []
        for case in test_cases:
            penalty = constraint_handler.calculate_penalty_score(case)
            penalties.append(penalty)
            
            if case['expected_penalty'] == 'low':
                assert penalty < 30, f"价格{case['price_annual_member']}的惩罚应该很低: {penalty}"
            elif case['expected_penalty'] == 'medium':
                assert penalty > 20, f"价格{case['price_annual_member']}的惩罚应该中等: {penalty}"
            elif case['expected_penalty'] == 'very_high':
                assert penalty > 100, f"价格{case['price_annual_member']}的惩罚应该很高: {penalty}"
        
        # 验证惩罚分数随着参数极值程度递增
        assert penalties[0] < penalties[2] < penalties[3], f"惩罚分数应该递增: {penalties}"
        print(f"✅ 极值防止测试: 惩罚分数 {penalties}")

    def test_constraint_integration_with_algorithms(self):
        """测试约束与各算法的集成"""
        constraint_handler = RealisticConstraintHandler()
        
        # 测试参数集合
        test_params_list = [
            # 正常参数
            {'price_annual_member': 30.0, 'type2_luma_share_from_student.a': 0.5},
            # 边界参数
            {'price_annual_member': 15.0, 'type2_luma_share_from_student.a': 0.2},
            # 过高参数
            {'price_annual_member': 80.0, 'type2_luma_share_from_student.a': 0.9}
        ]
        
        for i, params in enumerate(test_params_list):
            # 应用约束
            constrained_params = constraint_handler.apply_realistic_constraints(params)
            
            # 计算惩罚
            penalty = constraint_handler.calculate_penalty_score(params)
            
            print(f"✅ 测试案例{i+1}: 原始参数{params} -> 惩罚分数{penalty:.2f}")
            
            # 验证约束应用不会产生无效参数
            for key, value in constrained_params.items():
                assert isinstance(value, (int, float)), f"约束后参数{key}应该是数值类型"
                assert not (isinstance(value, float) and np.isnan(value)), f"约束后参数{key}不应该是NaN"

class TestOptimizationRealism:
    """测试优化结果的现实性"""
    
    def test_parameter_combination_realism(self):
        """测试参数组合的现实性"""
        handler = RealisticConstraintHandler()
        
        # 定义几种典型的策略场景
        scenarios = {
            'aggressive_pricing': {
                'price_annual_member': 55.0,
                'price_3year_member': 140.0,
                'type2_luma_share_from_student.a': 0.4,
                'new_clients_per_half_year': 6
            },
            'balanced_strategy': {
                'price_annual_member': 35.0,
                'price_3year_member': 90.0,
                'type2_luma_share_from_student.a': 0.5,
                'new_clients_per_half_year': 8
            },
            'unrealistic_extreme': {
                'price_annual_member': 80.0,
                'price_3year_member': 200.0,
                'type2_luma_share_from_student.a': 0.9,
                'new_clients_per_half_year': 20
            }
        }
        
        for scenario_name, params in scenarios.items():
            penalty = handler.calculate_penalty_score(params)
            constrained_params = handler.apply_realistic_constraints(params)
            
            if scenario_name == 'unrealistic_extreme':
                assert penalty > 100, f"不现实场景{scenario_name}的惩罚分数应该很高: {penalty}"
            else:
                assert penalty < 100, f"现实场景{scenario_name}的惩罚分数应该较低: {penalty}"
            
            print(f"✅ 场景'{scenario_name}': 惩罚分数 {penalty:.2f}")

    def test_business_logic_constraints(self):
        """测试业务逻辑约束"""
        handler = RealisticConstraintHandler()
        
        # 测试价格梯度逻辑：长期会员应该比短期更优惠（单位时间价格更低）
        test_pricing = {
            'price_annual_member': 30.0,    # 30/年
            'price_3year_member': 80.0,     # 26.7/年
            'price_5year_member': 120.0     # 24/年
        }
        
        annual_per_year = test_pricing['price_annual_member']
        three_year_per_year = test_pricing['price_3year_member'] / 3
        five_year_per_year = test_pricing['price_5year_member'] / 5
        
        # 验证价格梯度合理性（长期会员单价更低）
        assert annual_per_year > three_year_per_year, "3年会员年单价应低于1年会员"
        assert three_year_per_year > five_year_per_year, "5年会员年单价应低于3年会员"
        
        # 计算这种定价的约束分数
        penalty = handler.calculate_penalty_score(test_pricing)
        print(f"✅ 业务逻辑测试: 合理价格梯度惩罚分数 {penalty:.2f}")

    def test_market_realistic_bounds(self):
        """测试市场现实边界"""
        handler = RealisticConstraintHandler()
        
        # 测试各参数的现实边界
        boundary_tests = [
            # 价格边界测试
            {'param': 'price_annual_member', 'low': 5.0, 'high': 100.0, 'reasonable': 30.0},
            {'param': 'new_clients_per_half_year', 'low': 0, 'high': 30, 'reasonable': 8},
            {'param': 'type2_luma_share_from_student.a', 'low': 0.1, 'high': 0.95, 'reasonable': 0.5}
        ]
        
        for test in boundary_tests:
            # 测试过低值
            low_penalty = handler.calculate_penalty_score({test['param']: test['low']})
            
            # 测试过高值  
            high_penalty = handler.calculate_penalty_score({test['param']: test['high']})
            
            # 测试合理值
            reasonable_penalty = handler.calculate_penalty_score({test['param']: test['reasonable']})
            
            # 合理值的惩罚应该最低
            assert reasonable_penalty <= low_penalty, f"{test['param']}合理值惩罚应不高于过低值"
            assert reasonable_penalty <= high_penalty, f"{test['param']}合理值惩罚应不高于过高值"
            
            print(f"✅ 边界测试 {test['param']}: 过低{low_penalty:.1f}, 合理{reasonable_penalty:.1f}, 过高{high_penalty:.1f}")

def test_integration_workflow():
    """集成工作流测试：模拟完整的约束优化流程"""
    print("🚀 开始集成工作流测试...")
    
    # 1. 初始化约束处理器
    handler = RealisticConstraintHandler()
    
    # 2. 模拟优化器可能找到的解（包括不现实的极值解）
    optimization_candidates = [
        {'price_annual_member': 25.0, 'type2_luma_share_from_student.a': 0.4, 'new_clients_per_half_year': 6},
        {'price_annual_member': 80.0, 'type2_luma_share_from_student.a': 0.9, 'new_clients_per_half_year': 18},
        {'price_annual_member': 45.0, 'type2_luma_share_from_student.a': 0.6, 'new_clients_per_half_year': 10}
    ]
    
    results = []
    for i, candidate in enumerate(optimization_candidates):
        # 应用现实约束
        constrained = handler.apply_realistic_constraints(candidate)
        
        # 计算惩罚分数
        penalty = handler.calculate_penalty_score(candidate)
        
        # 生成报告
        report = handler.generate_constraint_report(candidate)
        
        results.append({
            'candidate_id': i + 1,
            'original': candidate,
            'constrained': constrained,
            'penalty': penalty,
            'realistic': penalty < 100
        })
        
        print(f"候选解{i+1}: 惩罚分数{penalty:.1f}, 现实性{'✅' if penalty < 100 else '❌'}")
    
    # 3. 验证约束系统能够识别和惩罚不现实的解
    realistic_solutions = [r for r in results if r['realistic']]
    unrealistic_solutions = [r for r in results if not r['realistic']]
    
    assert len(realistic_solutions) > 0, "应该至少有一个现实的解"
    assert len(unrealistic_solutions) > 0, "应该至少有一个不现实的解被识别"
    
    print(f"✅ 集成测试完成: {len(realistic_solutions)}个现实解, {len(unrealistic_solutions)}个不现实解")

if __name__ == "__main__":
    print("🧪 Luma现实约束功能自动化测试套件")
    print("=" * 60)
    
    # 可以直接运行这个文件进行快速测试
    pytest.main([__file__, "-v", "--tb=short"])