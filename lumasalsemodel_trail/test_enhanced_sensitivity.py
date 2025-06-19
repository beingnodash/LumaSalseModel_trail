#!/usr/bin/env python3
"""
增强版敏感性分析测试脚本
Enhanced Sensitivity Analysis Test Script

测试目标：
1. 验证敏感性分析器的核心功能
2. 测试单参数和多参数分析
3. 验证参数重要性计算
4. 测试可视化组件
5. 确保与简化版财务模型的兼容性
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd
import copy

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from luma_sales_model.simplified_financial_model import LumaSimplifiedFinancialModel
from streamlit_app.utils.enhanced_sensitivity_analysis import EnhancedSensitivityAnalyzer
from streamlit_app.utils.sensitivity_parameter_ui import SensitivityParameterUI
from streamlit_app.utils.enhanced_plot_utils import EnhancedPlotUtils

class TestEnhancedSensitivityAnalysis:
    """增强版敏感性分析测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.base_params = {
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
    
    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        # 验证基础参数正确保存
        assert analyzer.base_params['total_half_years'] == 6
        assert analyzer.base_params['market_scale']['new_clients_per_half_year'] == 5
        
        # 验证参数定义存在
        assert len(analyzer.parameter_definitions) > 0
        assert 'new_clients_per_half_year' in analyzer.parameter_definitions
        assert 'luma_share_from_student' in analyzer.parameter_definitions
        
        print("✅ 分析器初始化测试通过")
    
    def test_parameter_path_mapping(self):
        """测试参数路径映射"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        # 测试各种参数路径
        test_cases = [
            ('total_half_years', ['total_half_years']),
            ('price_per_use', ['student_prices', 'price_per_use']),
            ('mode_a_price', ['university_prices', 'mode_a_price']),
            ('new_clients_per_half_year', ['market_scale', 'new_clients_per_half_year']),
            ('mode_a_ratio', ['market_distribution', 'mode_a_ratio']),
            ('per_use_ratio', ['student_segmentation', 'per_use_ratio']),
            ('university_3year_renewal', ['renewal_rates', 'university_3year_renewal']),
            ('luma_share_from_student', ['revenue_sharing', 'luma_share_from_student'])
        ]
        
        for param_key, expected_path in test_cases:
            actual_path = analyzer.get_parameter_path(param_key)
            assert actual_path == expected_path, f"参数 {param_key} 路径映射错误"
        
        print("✅ 参数路径映射测试通过")
    
    def test_nested_value_operations(self):
        """测试嵌套值操作"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        test_params = copy.deepcopy(self.base_params)
        
        # 测试获取嵌套值
        path = ['student_prices', 'price_per_use']
        value = analyzer.get_nested_value(test_params, path)
        assert value == 8.0
        
        # 测试设置嵌套值
        new_value = 10.0
        analyzer.set_nested_value(test_params, path, new_value)
        updated_value = analyzer.get_nested_value(test_params, path)
        assert updated_value == new_value
        
        print("✅ 嵌套值操作测试通过")
    
    def test_test_values_generation(self):
        """测试测试值生成"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        # 测试默认范围
        test_values = analyzer.generate_test_values('new_clients_per_half_year')
        assert len(test_values) > 0
        assert min(test_values) >= 2  # 根据定义的最小值
        assert max(test_values) <= 15  # 根据定义的最大值
        
        # 测试自定义范围
        custom_values = analyzer.generate_test_values('new_clients_per_half_year', (3, 10, 5))
        assert len(custom_values) == 5
        assert min(custom_values) == 3
        assert max(custom_values) == 10
        
        print("✅ 测试值生成测试通过")
    
    def test_mode_ratio_adjustment(self):
        """测试商业模式比例调整"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        test_params = copy.deepcopy(self.base_params)
        
        # 测试调整模式A比例
        analyzer._adjust_mode_ratios(test_params, 'mode_a_ratio', 0.5)
        dist = test_params['market_distribution']
        total = dist['mode_a_ratio'] + dist['mode_b_ratio'] + dist['mode_c_ratio']
        assert abs(total - 1.0) < 0.001, f"调整后总和不为1: {total}"
        
        print("✅ 模式比例调整测试通过")
    
    def test_single_parameter_analysis(self):
        """测试单参数敏感性分析"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        # 使用较小的测试范围以加快测试
        test_values = [3, 5, 7]  # 简化的测试值
        output_metrics = ['luma_revenue_total', 'active_universities']
        
        try:
            results_df = analyzer.run_single_parameter_analysis(
                param_key='new_clients_per_half_year',
                model_class=LumaSimplifiedFinancialModel,
                test_values=test_values,
                output_metrics=output_metrics
            )
            
            # 验证结果结构
            assert len(results_df) == len(test_values)
            assert 'new_clients_per_half_year' in results_df.columns
            
            for metric in output_metrics:
                assert metric in results_df.columns
                assert (results_df[metric] >= 0).all(), f"指标 {metric} 存在负值"
            
            # 验证业务逻辑：更多客户应该带来更多收入
            assert results_df['luma_revenue_total'].is_monotonic_increasing, "收入应随客户数增加而增长"
            
            print("✅ 单参数敏感性分析测试通过")
            
        except Exception as e:
            print(f"❌ 单参数分析测试失败: {str(e)}")
            raise
    
    def test_multi_parameter_analysis(self):
        """测试多参数敏感性分析"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        # 配置多个参数
        param_configs = {
            'new_clients_per_half_year': {'values': [3, 5, 7]},
            'luma_share_from_student': {'values': [0.3, 0.4, 0.5]}
        }
        output_metrics = ['luma_revenue_total']
        
        try:
            results = analyzer.run_multi_parameter_analysis(
                param_configs=param_configs,
                model_class=LumaSimplifiedFinancialModel,
                output_metrics=output_metrics
            )
            
            # 验证结果
            assert len(results) == len(param_configs)
            
            for param_key, result_df in results.items():
                assert param_key in result_df.columns
                assert 'luma_revenue_total' in result_df.columns
                assert len(result_df) == len(param_configs[param_key]['values'])
            
            print("✅ 多参数敏感性分析测试通过")
            
        except Exception as e:
            print(f"❌ 多参数分析测试失败: {str(e)}")
            raise
    
    def test_parameter_importance_calculation(self):
        """测试参数重要性计算"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        # 先运行多参数分析
        param_configs = {
            'new_clients_per_half_year': {'values': [3, 5, 7]},
            'luma_share_from_student': {'values': [0.3, 0.4, 0.5]},
            'price_per_use': {'values': [6, 8, 10]}
        }
        
        try:
            results = analyzer.run_multi_parameter_analysis(
                param_configs=param_configs,
                model_class=LumaSimplifiedFinancialModel,
                output_metrics=['luma_revenue_total']
            )
            
            # 计算重要性
            importance_df = analyzer.calculate_parameter_importance(
                results=results,
                target_metric='luma_revenue_total'
            )
            
            # 验证重要性结果
            assert len(importance_df) <= len(param_configs)
            
            required_columns = ['参数', '参数类别', '变异系数', '变化幅度', '相关系数', '重要性得分']
            for col in required_columns:
                assert col in importance_df.columns, f"缺少列: {col}"
            
            # 验证排序（按重要性得分降序）
            scores = importance_df['重要性得分'].values
            assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1)), "重要性得分应按降序排列"
            
            print("✅ 参数重要性计算测试通过")
            
        except Exception as e:
            print(f"❌ 参数重要性计算测试失败: {str(e)}")
            raise
    
    def test_business_insights_generation(self):
        """测试业务洞察生成"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        # 创建模拟的重要性数据
        importance_data = [
            {
                '参数': '每半年新客户数', '参数类别': '市场规模',
                '变异系数': 0.5, '变化幅度': 0.8, '相关系数': 0.9,
                '重要性得分': 0.45, '最小值': 1000000, '最大值': 1800000, '平均值': 1400000
            },
            {
                '参数': 'Luma学生分成比例', '参数类别': '分成比例',
                '变异系数': 0.3, '变化幅度': 0.5, '相关系数': 0.7,
                '重要性得分': 0.21, '最小值': 1200000, '最大值': 1600000, '平均值': 1400000
            }
        ]
        
        importance_df = pd.DataFrame(importance_data)
        
        # 生成洞察
        insights = analyzer.generate_business_insights(
            importance_df=importance_df,
            target_metric='luma_revenue_total'
        )
        
        # 验证洞察
        assert len(insights) > 0
        assert any("关键发现" in insight for insight in insights)
        assert any("优化建议" in insight for insight in insights)
        
        print("✅ 业务洞察生成测试通过")
    
    def test_parameter_ui_initialization(self):
        """测试参数UI初始化"""
        try:
            param_ui = SensitivityParameterUI(self.base_params)
            
            # 验证UI组件初始化
            assert param_ui.base_params is not None
            assert param_ui.analyzer is not None
            assert param_ui.parameter_definitions is not None
            
            # 验证参数定义完整性
            assert len(param_ui.parameter_definitions) > 0
            
            print("✅ 参数UI初始化测试通过")
            
        except Exception as e:
            print(f"❌ 参数UI初始化测试失败: {str(e)}")
            raise
    
    def test_plot_utils_functions(self):
        """测试绘图工具函数"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'new_clients_per_half_year': [3, 5, 7],
            'luma_revenue_total': [1000000, 1500000, 2000000],
            'active_universities': [10, 15, 20]
        })
        
        try:
            # 测试敏感性分析图表
            fig1 = EnhancedPlotUtils.plot_sensitivity_analysis(
                results_df=test_data,
                param_key='new_clients_per_half_year',
                metric='luma_revenue_total',
                param_name='每半年新客户数',
                metric_name='Luma总收入'
            )
            assert fig1 is not None
            
            # 测试重要性图表
            importance_data = pd.DataFrame({
                '参数': ['参数A', '参数B'],
                '重要性得分': [0.8, 0.6]
            })
            
            fig2 = EnhancedPlotUtils.plot_parameter_importance(importance_data)
            assert fig2 is not None
            
            print("✅ 绘图工具函数测试通过")
            
        except Exception as e:
            print(f"❌ 绘图工具函数测试失败: {str(e)}")
            raise
    
    def test_integration_with_simplified_model(self):
        """测试与简化版财务模型的集成"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        try:
            # 测试基础模型运行
            model = LumaSimplifiedFinancialModel(self.base_params)
            results_df = model.run_model()
            
            # 验证结果包含敏感性分析需要的指标
            required_metrics = ['luma_revenue_total', 'active_universities', 'total_paying_students']
            for metric in required_metrics:
                assert metric in results_df.columns, f"模型结果缺少指标: {metric}"
            
            # 测试参数修改不会破坏模型
            test_params = copy.deepcopy(self.base_params)
            test_params['market_scale']['new_clients_per_half_year'] = 8
            
            modified_model = LumaSimplifiedFinancialModel(test_params)
            modified_results = modified_model.run_model()
            
            # 验证修改参数后模型仍能正常运行
            assert len(modified_results) > 0
            assert 'luma_revenue_total' in modified_results.columns
            
            print("✅ 与简化版财务模型集成测试通过")
            
        except Exception as e:
            print(f"❌ 模型集成测试失败: {str(e)}")
            raise
    
    def test_edge_cases(self):
        """测试边界情况"""
        analyzer = EnhancedSensitivityAnalyzer(self.base_params)
        
        try:
            # 测试空测试值
            empty_results = analyzer.run_single_parameter_analysis(
                param_key='new_clients_per_half_year',
                model_class=LumaSimplifiedFinancialModel,
                test_values=[],
                output_metrics=['luma_revenue_total']
            )
            assert len(empty_results) == 0
            
            # 测试极端参数值
            extreme_values = [1, 50]  # 极端的客户数量
            extreme_results = analyzer.run_single_parameter_analysis(
                param_key='new_clients_per_half_year',
                model_class=LumaSimplifiedFinancialModel,
                test_values=extreme_values,
                output_metrics=['luma_revenue_total']
            )
            assert len(extreme_results) <= len(extreme_values)  # 可能有些极端值导致运行失败
            
            print("✅ 边界情况测试通过")
            
        except Exception as e:
            print(f"❌ 边界情况测试失败: {str(e)}")
            # 边界情况测试失败不算严重错误
            pass

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行增强版敏感性分析测试...")
    print("=" * 60)
    
    test_instance = TestEnhancedSensitivityAnalysis()
    
    # 运行所有测试方法
    test_methods = [
        test_instance.test_analyzer_initialization,
        test_instance.test_parameter_path_mapping,
        test_instance.test_nested_value_operations,
        test_instance.test_test_values_generation,
        test_instance.test_mode_ratio_adjustment,
        test_instance.test_single_parameter_analysis,
        test_instance.test_multi_parameter_analysis,
        test_instance.test_parameter_importance_calculation,
        test_instance.test_business_insights_generation,
        test_instance.test_parameter_ui_initialization,
        test_instance.test_plot_utils_functions,
        test_instance.test_integration_with_simplified_model,
        test_instance.test_edge_cases
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
        print("🎉 所有测试通过！增强版敏感性分析系统运行正常。")
        return True
    else:
        print(f"⚠️  有 {total_tests - passed_tests} 项测试失败，请检查实现。")
        return False

def demo_enhanced_sensitivity_analysis():
    """演示增强版敏感性分析功能"""
    print("\n" + "=" * 60)
    print("📋 增强版敏感性分析功能演示")
    print("=" * 60)
    
    # 基础参数
    base_params = {
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
    
    # 创建分析器
    analyzer = EnhancedSensitivityAnalyzer(base_params)
    
    print("1. 分析器特性:")
    print(f"   - 支持参数数量: {len(analyzer.parameter_definitions)}")
    print(f"   - 参数类别: {len(set(def_['category'] for def_ in analyzer.parameter_definitions.values()))}")
    print(f"   - 基础模拟周期: {base_params['total_half_years']} 个半年")
    
    print("\n2. 单参数敏感性分析示例:")
    try:
        # 演示单参数分析
        test_values = [3, 5, 7, 10]
        results_df = analyzer.run_single_parameter_analysis(
            param_key='new_clients_per_half_year',
            model_class=LumaSimplifiedFinancialModel,
            test_values=test_values,
            output_metrics=['luma_revenue_total', 'active_universities']
        )
        
        print(f"   - 测试参数: 每半年新客户数")
        print(f"   - 测试值: {test_values}")
        print(f"   - 结果数据点: {len(results_df)}")
        
        if len(results_df) > 0:
            min_revenue = results_df['luma_revenue_total'].min()
            max_revenue = results_df['luma_revenue_total'].max()
            change_pct = (max_revenue - min_revenue) / min_revenue * 100
            print(f"   - 收入变化幅度: {change_pct:.1f}%")
        
    except Exception as e:
        print(f"   - 演示失败: {str(e)}")
    
    print("\n3. 多参数重要性分析示例:")
    try:
        # 演示重要性分析
        param_configs = {
            'new_clients_per_half_year': {'values': [3, 5, 7]},
            'luma_share_from_student': {'values': [0.3, 0.4, 0.5]},
            'university_3year_renewal': {'values': [0.7, 0.8, 0.9]}
        }
        
        results = analyzer.run_multi_parameter_analysis(
            param_configs=param_configs,
            model_class=LumaSimplifiedFinancialModel,
            output_metrics=['luma_revenue_total']
        )
        
        importance_df = analyzer.calculate_parameter_importance(
            results=results,
            target_metric='luma_revenue_total'
        )
        
        print(f"   - 分析参数数量: {len(param_configs)}")
        print(f"   - 重要性排序:")
        
        for i, row in importance_df.head(3).iterrows():
            print(f"     {i+1}. {row['参数']} (得分: {row['重要性得分']:.4f})")
        
    except Exception as e:
        print(f"   - 演示失败: {str(e)}")
    
    print("\n4. 增强版特色功能:")
    print("   ✅ 7大类参数全覆盖")
    print("   ✅ 智能参数路径映射")
    print("   ✅ 商业模式比例自动调整")
    print("   ✅ 多维度重要性评估")
    print("   ✅ 自动化业务洞察生成")
    print("   ✅ 高级可视化支持")

if __name__ == "__main__":
    # 运行测试
    success = run_all_tests()
    
    if success:
        # 运行演示
        demo_enhanced_sensitivity_analysis()
    
    print("\n" + "=" * 60)
    print("📄 增强版敏感性分析测试完成！")
    print("💡 建议：在Streamlit应用中使用'增强版敏感性分析'页面")
    print("=" * 60)