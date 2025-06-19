#!/usr/bin/env python3
"""
现实约束测试运行脚本
Realistic Constraints Test Runner

此脚本提供便捷的方式来运行现实约束功能的自动化测试，
替代手动调整滑块的人工测试行为。

用法:
    python run_constraint_tests.py          # 运行所有测试
    python run_constraint_tests.py -v       # 详细输出
    python run_constraint_tests.py --quick  # 快速测试（仅核心功能）
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_tests(verbose=False, quick=False):
    """运行现实约束测试"""
    
    print("🧪 Luma现实约束功能自动化测试")
    print("=" * 50)
    print("📝 替代手动滑块测试，自动验证约束功能")
    print()
    
    # 构建pytest命令
    cmd = ["poetry", "run", "pytest", "tests/test_realistic_constraints.py"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if quick:
        # 只运行核心测试类
        cmd.extend(["-k", "TestRealisticConstraintHandler"])
        print("🚀 运行快速测试（仅核心约束功能）...")
    else:
        print("🚀 运行完整测试套件...")
    
    # 添加输出格式
    cmd.extend(["--tb=short", "--color=yes"])
    
    try:
        # 运行测试
        result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ 所有测试通过！现实约束功能工作正常。")
            print("💡 系统已成功防止极值参数优化，确保业务策略现实可行。")
        else:
            print("\n❌ 测试失败！请检查约束功能实现。")
            return False
            
    except Exception as e:
        print(f"\n💥 测试运行出错: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="运行现实约束测试")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="详细输出测试信息")
    parser.add_argument("--quick", action="store_true",
                       help="快速测试（仅核心功能）")
    
    args = parser.parse_args()
    
    success = run_tests(verbose=args.verbose, quick=args.quick)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()