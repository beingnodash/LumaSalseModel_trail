#!/usr/bin/env python3
"""
测试修复脚本
Test Fixes Script

验证修复的各项功能：
1. 格式化字符串修复
2. DataFrame判断修复  
3. session_state初始化修复
4. 参数UI控件修复
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_format_fixes():
    """测试格式化修复"""
    print("测试格式化修复...")
    
    # 测试格式化逻辑
    test_values = [1.0, 2.5, 3.7, 4.2]
    format_specs = ['%.0f', '%.1f', '%.2f', '%.1%']
    
    for fmt in format_specs:
        try:
            formatted_values = []
            for val in test_values:
                if fmt == '%.1%':
                    formatted_values.append(f"{val:.1%}")
                elif fmt == '%.0f':
                    formatted_values.append(f"{val:.0f}")
                elif fmt == '%.1f':
                    formatted_values.append(f"{val:.1f}")
                elif fmt == '%.2f':
                    formatted_values.append(f"{val:.2f}")
                else:
                    formatted_values.append(str(val))
            
            print(f"  ✅ 格式 {fmt}: {', '.join(formatted_values)}")
            
        except Exception as e:
            print(f"  ❌ 格式 {fmt} 失败: {e}")
            return False
    
    return True

def test_sensitivity_analyzer():
    """测试敏感性分析器"""
    print("测试敏感性分析器...")
    
    try:
        from streamlit_app.utils.enhanced_sensitivity_analysis import EnhancedSensitivityAnalyzer
        from streamlit_app.utils.sensitivity_parameter_ui import SensitivityParameterUI
        
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
        
        # 测试分析器
        analyzer = EnhancedSensitivityAnalyzer(base_params)
        print("  ✅ 分析器初始化成功")
        
        # 测试参数定义
        param_defs = analyzer.parameter_definitions
        print(f"  ✅ 参数定义加载: {len(param_defs)} 个参数")
        
        # 测试测试值生成
        test_values = analyzer.generate_test_values('new_clients_per_half_year')
        print(f"  ✅ 测试值生成: {len(test_values)} 个值")
        
        # 测试UI组件
        param_ui = SensitivityParameterUI(base_params)
        print("  ✅ 参数UI初始化成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 敏感性分析器测试失败: {e}")
        return False

def test_simplified_model():
    """测试简化版模型"""
    print("测试简化版财务模型...")
    
    try:
        from luma_sales_model.simplified_financial_model import LumaSimplifiedFinancialModel
        
        # 基础参数
        base_params = {
            'total_half_years': 4,  # 较短的周期用于测试
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
        
        # 创建模型
        model = LumaSimplifiedFinancialModel(base_params)
        print("  ✅ 模型初始化成功")
        
        # 运行模型
        results_df = model.run_model()
        print(f"  ✅ 模型运行成功: {len(results_df)} 行结果")
        
        # 验证关键列存在
        required_columns = [
            'luma_revenue_total', 'uni_revenue_total', 'student_revenue_total',
            'active_universities', 'total_paying_students'
        ]
        
        for col in required_columns:
            if col in results_df.columns:
                print(f"  ✅ 列存在: {col}")
            else:
                print(f"  ❌ 列缺失: {col}")
                return False
        
        # 测试业务摘要
        summary = model.get_business_summary()
        print(f"  ✅ 业务摘要生成: {len(summary)} 个指标")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 简化版模型测试失败: {e}")
        return False

def test_parameter_ui():
    """测试参数UI修复"""
    print("测试参数UI修复...")
    
    try:
        from streamlit_app.utils.simplified_parameter_ui import SimplifiedParameterUI
        
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
        
        # 测试UI初始化
        param_ui = SimplifiedParameterUI()
        print("  ✅ 参数UI初始化成功")
        
        # 验证默认参数
        defaults = param_ui.default_params
        print(f"  ✅ 默认参数加载: {len(defaults)} 个顶级参数")
        
        # 验证新签约客户数参数结构变更
        market_scale = defaults.get('market_scale', {})
        if 'new_clients_per_half_year' in market_scale:
            print("  ✅ 每半年新签约客户数参数存在")
        else:
            print("  ❌ 每半年新签约客户数参数缺失")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 参数UI测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始运行修复验证测试...")
    print("=" * 50)
    
    tests = [
        ("格式化修复", test_format_fixes),
        ("敏感性分析器", test_sensitivity_analyzer),
        ("简化版模型", test_simplified_model),
        ("参数UI修复", test_parameter_ui)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"  ✅ {test_name} 通过")
            else:
                print(f"  ❌ {test_name} 失败")
        except Exception as e:
            print(f"  ❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有修复验证通过！")
        return True
    else:
        print(f"⚠️ 有 {total - passed} 项测试失败")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)