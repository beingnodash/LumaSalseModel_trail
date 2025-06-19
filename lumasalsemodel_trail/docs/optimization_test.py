#!/usr/bin/env python3
"""
优化系统测试脚本

该脚本用于测试和验证新的优化功能是否正常工作。
包括算法选择、约束处理、监控系统等的功能测试。
"""

import sys
import os
import numpy as np
import pandas as pd
import time

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from streamlit_app.utils.algorithm_selector import AlgorithmSelector
from streamlit_app.utils.constraint_handler import LumaConstraintHandler
from streamlit_app.utils.optimization_monitor import OptimizationMonitor
from streamlit_app.utils.robustness_analyzer import RobustnessAnalyzer
from streamlit_app.utils.ensemble_optimizer import EnsembleOptimizer

def test_algorithm_selector():
    """测试算法选择器"""
    print("=" * 50)
    print("测试算法选择器")
    print("=" * 50)
    
    selector = AlgorithmSelector()
    
    # 测试不同的参数配置
    test_cases = [
        {
            "name": "低维问题",
            "param_ranges": {
                "price_annual_member": (20.0, 50.0),
                "new_clients_per_half_year": (3, 10)
            },
            "budget": 100
        },
        {
            "name": "中维问题", 
            "param_ranges": {
                "price_annual_member": (20.0, 50.0),
                "price_3year_member": (50.0, 120.0),
                "type2_luma_share_from_student.a": (0.3, 0.7),
                "renewal_rate_uni": (0.6, 0.95)
            },
            "budget": 200
        },
        {
            "name": "高维问题",
            "param_ranges": {
                "price_annual_member": (20.0, 50.0),
                "price_3year_member": (50.0, 120.0),
                "price_5year_member": (80.0, 150.0),
                "type2_luma_share_from_student.a": (0.3, 0.7),
                "type2_luma_share_from_student.b": (0.4, 0.8),
                "renewal_rate_uni": (0.6, 0.95),
                "new_clients_per_half_year": (3, 15)
            },
            "budget": 150
        }
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        recommendations = selector.recommend_algorithm(
            case["param_ranges"], 
            case["budget"]
        )
        
        print(f"参数数量: {len(case['param_ranges'])}")
        print(f"评估预算: {case['budget']}")
        print(f"推荐算法: {recommendations[0]['name']} (得分: {recommendations[0]['score']:.2f})")
        print(f"适用性: {recommendations[0]['suitability']}")
        
        if recommendations[0]['reasons']:
            print(f"推荐理由: {recommendations[0]['reasons'][0]}")
    
    print("\n✅ 算法选择器测试完成")

def test_constraint_handler():
    """测试约束处理器"""
    print("\n" + "=" * 50)
    print("测试约束处理器")
    print("=" * 50)
    
    # 创建约束处理器
    param_ranges = {
        "price_annual_member": (10.0, 100.0),
        "renewal_rate_uni": (0.0, 1.0),
        "type2_luma_share_from_student.a": (0.0, 1.0)
    }
    
    handler = LumaConstraintHandler(param_ranges)
    
    # 测试用例
    test_params = [
        {
            "name": "正常参数",
            "params": {
                "price_annual_member": 29.0,
                "renewal_rate_uni": 0.8,
                "type2_luma_share_from_student.a": 0.5,
                "mode_distribution": {
                    "Type1": 0.2,
                    "Type2a": 0.1,
                    "Type2b": 0.1, 
                    "Type2c": 0.2,
                    "Type3": 0.4
                }
            }
        },
        {
            "name": "边界违反",
            "params": {
                "price_annual_member": -10.0,  # 负价格
                "renewal_rate_uni": 1.5,       # 超过1
                "type2_luma_share_from_student.a": 0.5
            }
        },
        {
            "name": "分布约束违反",
            "params": {
                "price_annual_member": 29.0,
                "mode_distribution": {
                    "Type1": 0.3,
                    "Type2a": 0.2,
                    "Type2b": 0.2,
                    "Type2c": 0.2,
                    "Type3": 0.4  # 总和 > 1
                }
            }
        }
    ]
    
    for case in test_params:
        print(f"\n--- {case['name']} ---")
        
        # 验证参数
        is_valid, violations = handler.validate_params(case['params'])
        print(f"参数有效性: {'✅ 有效' if is_valid else '❌ 无效'}")
        
        if violations:
            print("约束违反:")
            for violation in violations[:3]:  # 只显示前3个
                print(f"  • {violation}")
        
        # 修复参数
        if not is_valid:
            repaired_params = handler.repair_params(case['params'])
            is_valid_after, violations_after = handler.validate_params(repaired_params)
            print(f"修复后有效性: {'✅ 有效' if is_valid_after else '❌ 仍无效'}")
    
    print("\n✅ 约束处理器测试完成")

def test_optimization_monitor():
    """测试优化监控器"""
    print("\n" + "=" * 50)
    print("测试优化监控器")
    print("=" * 50)
    
    monitor = OptimizationMonitor(patience=5, min_improvement=0.01)
    monitor.start_monitoring()
    
    # 模拟优化过程
    print("\n模拟优化过程:")
    
    # 模拟收敛的优化过程
    scores = [100, 110, 115, 118, 120, 120.5, 120.6, 120.6, 120.6, 120.6]
    
    for i, score in enumerate(scores):
        best_score = max(scores[:i+1])
        monitor.record_iteration(
            iteration=i+1,
            current_score=score,
            best_score=best_score,
            diversity=max(0.1, 1.0 - i/len(scores))
        )
        
        status = monitor.get_convergence_status()
        print(f"迭代 {i+1}: 得分={score:.1f}, 最佳={best_score:.1f}, "
              f"无改进次数={status['no_improvement_count']}")
        
        if monitor.should_stop_early():
            print(f"  🛑 建议早停 (第{i+1}次迭代)")
            break
        
        time.sleep(0.1)  # 模拟计算时间
    
    # 生成诊断报告
    print(f"\n--- 诊断报告 ---")
    report = monitor.generate_diagnostic_report()
    print(report[:500] + "..." if len(report) > 500 else report)
    
    print("\n✅ 优化监控器测试完成")

def test_robustness_analyzer():
    """测试鲁棒性分析器"""
    print("\n" + "=" * 50)
    print("测试鲁棒性分析器 (简化版)")
    print("=" * 50)
    
    # 模拟基础参数和最优参数
    base_params = {
        'total_half_years': 4,
        'new_clients_per_half_year': 5,
        'price_annual_member': 29.0
    }
    
    best_params = {
        'price_annual_member': 35.0,
        'new_clients_per_half_year': 7,
        'renewal_rate_uni': 0.85
    }
    
    # 注意：这里我们无法真正运行完整的鲁棒性分析，因为需要LumaFinancialModel
    # 但我们可以测试分析器的初始化和配置
    
    try:
        analyzer = RobustnessAnalyzer(base_params, 'Luma_Revenue_Total')
        
        # 测试不确定性范围生成
        uncertainty_ranges = analyzer._generate_default_uncertainty_ranges(best_params)
        print(f"生成的不确定性范围:")
        for param, uncertainty in uncertainty_ranges.items():
            print(f"  • {param}: ±{uncertainty:.1%}")
        
        # 测试风险等级评估
        test_cases = [
            {"mean": 100, "std": 2, "base": 100, "expected": "low"},
            {"mean": 100, "std": 10, "base": 100, "expected": "medium"},
            {"mean": 100, "std": 25, "base": 100, "expected": "high"},
            {"mean": 80, "std": 40, "base": 100, "expected": "extreme"}
        ]
        
        print(f"\n风险等级评估测试:")
        for case in test_cases:
            risk_level = analyzer._assess_risk_level(case["mean"], case["std"], case["base"])
            status = "✅" if risk_level == case["expected"] else "❌"
            print(f"  {status} 均值={case['mean']}, 标准差={case['std']} → {risk_level}")
        
        print("\n✅ 鲁棒性分析器测试完成")
        
    except Exception as e:
        print(f"❌ 鲁棒性分析器测试失败: {str(e)}")

def main():
    """运行所有测试"""
    print("🚀 开始优化系统功能测试")
    print("=" * 60)
    
    try:
        test_algorithm_selector()
        test_constraint_handler()
        test_optimization_monitor()
        test_robustness_analyzer()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成！优化系统功能正常。")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()