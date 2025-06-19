# 参数约束处理系统
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable, Optional, Any
import warnings
import copy

class ConstraintHandler:
    """
    参数约束处理系统，用于确保优化过程中生成的参数满足各种约束条件。
    
    支持的约束类型：
    1. 边界约束：参数在指定范围内
    2. 分布约束：多个参数的总和等于指定值（如分布总和为1）
    3. 关系约束：参数间的相关性约束
    4. 业务逻辑约束：基于业务规则的约束
    """
    
    def __init__(self):
        self.boundary_constraints = {}
        self.distribution_constraints = []
        self.relationship_constraints = []
        self.business_logic_constraints = []
        self.constraint_tolerance = 1e-6
    
    def add_boundary_constraints(self, param_ranges: Dict[str, Tuple[float, float]]):
        """
        添加边界约束
        
        Args:
            param_ranges: 参数范围字典，格式为 {param_name: (min_val, max_val)}
        """
        self.boundary_constraints.update(param_ranges)
    
    def add_distribution_constraint(self, param_group: List[str], target_sum: float = 1.0,
                                  constraint_name: Optional[str] = None):
        """
        添加分布约束（参数组总和约束）
        
        Args:
            param_group: 需要满足总和约束的参数列表
            target_sum: 目标总和值，默认为1.0
            constraint_name: 约束名称，用于错误报告
        """
        constraint = {
            "params": param_group,
            "target_sum": target_sum,
            "name": constraint_name or f"分布约束_{len(self.distribution_constraints)+1}",
            "type": "distribution"
        }
        self.distribution_constraints.append(constraint)
    
    def add_relationship_constraint(self, constraint_func: Callable, 
                                  involved_params: List[str],
                                  constraint_name: str,
                                  constraint_description: str = ""):
        """
        添加关系约束
        
        Args:
            constraint_func: 约束函数，接受参数字典，返回True表示满足约束
            involved_params: 涉及的参数列表
            constraint_name: 约束名称
            constraint_description: 约束描述
        """
        constraint = {
            "function": constraint_func,
            "params": involved_params,
            "name": constraint_name,
            "description": constraint_description,
            "type": "relationship"
        }
        self.relationship_constraints.append(constraint)
    
    def add_luma_business_constraints(self):
        """
        添加Luma模型特定的业务逻辑约束
        """
        # 1. 模式分布总和约束
        mode_params = [
            "mode_distribution.Type1",
            "mode_distribution.Type2a", 
            "mode_distribution.Type2b",
            "mode_distribution.Type2c",
            "mode_distribution.Type3"
        ]
        self.add_distribution_constraint(mode_params, 1.0, "模式分布约束")
        
        # 2. 付费用户类型分布约束
        user_type_params = [
            "share_paid_user_per_use_only",
            "share_paid_user_membership"
        ]
        self.add_distribution_constraint(user_type_params, 1.0, "付费用户类型分布约束")
        
        # 3. 会员购买类型分布约束
        member_type_params = [
            "member_purchase_shares.annual",
            "member_purchase_shares.3year",
            "member_purchase_shares.5year"
        ]
        self.add_distribution_constraint(member_type_params, 1.0, "会员购买类型分布约束")
        
        # 4. 价格逻辑约束：长期会员应该更便宜（按年计算）
        def price_logic_constraint(params):
            try:
                annual_price = self._get_nested_param_value(params, "price_annual_member")
                price_3year = self._get_nested_param_value(params, "price_3year_member")
                price_5year = self._get_nested_param_value(params, "price_5year_member")
                
                # 计算年均价格
                annual_per_year = annual_price
                three_year_per_year = price_3year / 3
                five_year_per_year = price_5year / 5
                
                # 长期会员应该有折扣
                return (annual_per_year >= three_year_per_year >= five_year_per_year)
            except:
                return True  # 如果参数不存在，跳过约束
        
        self.add_relationship_constraint(
            price_logic_constraint,
            ["price_annual_member", "price_3year_member", "price_5year_member"],
            "会员价格逻辑约束",
            "长期会员的年均价格应该递减"
        )
        
        # 5. 分成比例约束：确保在[0,1]范围内
        share_params = [
            "type2_luma_share_from_student.a",
            "type2_luma_share_from_student.b", 
            "type2_luma_share_from_student.c"
        ]
        for param in share_params:
            if param not in self.boundary_constraints:
                self.boundary_constraints[param] = (0.0, 1.0)
        
        # 6. 续约率约束
        renewal_params = ["renewal_rate_uni", "renewal_rate_student"]
        for param in renewal_params:
            if param not in self.boundary_constraints:
                self.boundary_constraints[param] = (0.0, 1.0)
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证参数是否满足所有约束
        
        Args:
            params: 参数字典
            
        Returns:
            (is_valid, violation_messages): 是否有效和违反约束的消息列表
        """
        violations = []
        
        # 检查边界约束
        boundary_violations = self._check_boundary_constraints(params)
        violations.extend(boundary_violations)
        
        # 检查分布约束
        distribution_violations = self._check_distribution_constraints(params)
        violations.extend(distribution_violations)
        
        # 检查关系约束
        relationship_violations = self._check_relationship_constraints(params)
        violations.extend(relationship_violations)
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def repair_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        修复违反约束的参数
        
        Args:
            params: 原始参数字典
            
        Returns:
            修复后的参数字典
        """
        repaired_params = copy.deepcopy(params)
        
        # 1. 修复边界约束
        repaired_params = self._repair_boundary_constraints(repaired_params)
        
        # 2. 修复分布约束
        repaired_params = self._repair_distribution_constraints(repaired_params)
        
        # 3. 验证修复后的参数
        is_valid, violations = self.validate_params(repaired_params)
        if not is_valid:
            warnings.warn(f"参数修复后仍有约束违反: {violations}")
        
        return repaired_params
    
    def _check_boundary_constraints(self, params: Dict[str, Any]) -> List[str]:
        """检查边界约束"""
        violations = []
        
        for param_name, (min_val, max_val) in self.boundary_constraints.items():
            try:
                value = self._get_nested_param_value(params, param_name)
                if value < min_val or value > max_val:
                    violations.append(
                        f"参数 '{param_name}' 值 {value} 超出边界 [{min_val}, {max_val}]"
                    )
            except KeyError:
                # 参数不存在，跳过检查
                continue
        
        return violations
    
    def _check_distribution_constraints(self, params: Dict[str, Any]) -> List[str]:
        """检查分布约束"""
        violations = []
        
        for constraint in self.distribution_constraints:
            try:
                param_values = []
                missing_params = []
                
                for param_name in constraint["params"]:
                    try:
                        value = self._get_nested_param_value(params, param_name)
                        param_values.append(value)
                    except KeyError:
                        missing_params.append(param_name)
                
                if missing_params:
                    continue  # 有参数缺失，跳过此约束
                
                actual_sum = sum(param_values)
                target_sum = constraint["target_sum"]
                
                if abs(actual_sum - target_sum) > self.constraint_tolerance:
                    violations.append(
                        f"{constraint['name']}: 参数总和 {actual_sum:.4f} 应为 {target_sum}"
                    )
            except Exception as e:
                violations.append(f"{constraint['name']}: 检查时出错 - {str(e)}")
        
        return violations
    
    def _check_relationship_constraints(self, params: Dict[str, Any]) -> List[str]:
        """检查关系约束"""
        violations = []
        
        for constraint in self.relationship_constraints:
            try:
                # 检查所需参数是否存在
                missing_params = []
                for param_name in constraint["params"]:
                    try:
                        self._get_nested_param_value(params, param_name)
                    except KeyError:
                        missing_params.append(param_name)
                
                if missing_params:
                    continue  # 有参数缺失，跳过此约束
                
                # 执行约束检查
                if not constraint["function"](params):
                    violations.append(
                        f"{constraint['name']}: {constraint.get('description', '约束违反')}"
                    )
            except Exception as e:
                violations.append(f"{constraint['name']}: 检查时出错 - {str(e)}")
        
        return violations
    
    def _repair_boundary_constraints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """修复边界约束"""
        for param_name, (min_val, max_val) in self.boundary_constraints.items():
            try:
                value = self._get_nested_param_value(params, param_name)
                if value < min_val or value > max_val:
                    # 投影到边界
                    repaired_value = max(min_val, min(max_val, value))
                    self._set_nested_param_value(params, param_name, repaired_value)
            except KeyError:
                continue
        
        return params
    
    def _repair_distribution_constraints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """修复分布约束"""
        for constraint in self.distribution_constraints:
            try:
                param_values = []
                param_names = []
                
                # 收集当前值
                for param_name in constraint["params"]:
                    try:
                        value = self._get_nested_param_value(params, param_name)
                        param_values.append(value)
                        param_names.append(param_name)
                    except KeyError:
                        continue
                
                if len(param_values) == 0:
                    continue
                
                current_sum = sum(param_values)
                target_sum = constraint["target_sum"]
                
                if abs(current_sum - target_sum) > self.constraint_tolerance:
                    # 按比例调整参数值
                    if current_sum > 0:
                        scale_factor = target_sum / current_sum
                        for i, param_name in enumerate(param_names):
                            new_value = param_values[i] * scale_factor
                            # 确保修复后的值仍在边界内
                            if param_name in self.boundary_constraints:
                                min_val, max_val = self.boundary_constraints[param_name]
                                new_value = max(min_val, min(max_val, new_value))
                            self._set_nested_param_value(params, param_name, new_value)
                    else:
                        # 如果当前总和为0，平均分配
                        avg_value = target_sum / len(param_names)
                        for param_name in param_names:
                            if param_name in self.boundary_constraints:
                                min_val, max_val = self.boundary_constraints[param_name]
                                avg_value = max(min_val, min(max_val, avg_value))
                            self._set_nested_param_value(params, param_name, avg_value)
            
            except Exception as e:
                warnings.warn(f"修复分布约束 {constraint['name']} 时出错: {str(e)}")
        
        return params
    
    def _get_nested_param_value(self, params: Dict[str, Any], param_path: str) -> Any:
        """获取嵌套参数的值"""
        keys = param_path.split('.')
        value = params
        for key in keys:
            value = value[key]
        return value
    
    def _set_nested_param_value(self, params: Dict[str, Any], param_path: str, value: Any):
        """设置嵌套参数的值"""
        keys = param_path.split('.')
        target = params
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
    
    def generate_constraint_report(self) -> str:
        """生成约束配置报告"""
        report = """# 参数约束配置报告

## 边界约束
"""
        if self.boundary_constraints:
            for param, (min_val, max_val) in self.boundary_constraints.items():
                report += f"- {param}: [{min_val}, {max_val}]\\n"
        else:
            report += "- 无边界约束\\n"
        
        report += """
## 分布约束
"""
        if self.distribution_constraints:
            for constraint in self.distribution_constraints:
                params_str = ", ".join(constraint["params"])
                report += f"- {constraint['name']}: {params_str} 总和 = {constraint['target_sum']}\\n"
        else:
            report += "- 无分布约束\\n"
        
        report += """
## 关系约束
"""
        if self.relationship_constraints:
            for constraint in self.relationship_constraints:
                params_str = ", ".join(constraint["params"])
                report += f"- {constraint['name']}: 涉及参数 {params_str}\\n"
                if constraint.get("description"):
                    report += f"  描述: {constraint['description']}\\n"
        else:
            report += "- 无关系约束\\n"
        
        return report

class LumaConstraintHandler(ConstraintHandler):
    """
    Luma模型专用的约束处理器，预配置了所有相关约束
    """
    
    def __init__(self, param_ranges: Optional[Dict[str, Tuple[float, float]]] = None):
        super().__init__()
        
        # 添加边界约束
        if param_ranges:
            self.add_boundary_constraints(param_ranges)
        
        # 添加Luma业务约束
        self.add_luma_business_constraints()
    
    def validate_and_repair_optimization_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并修复优化参数，专门用于优化算法中
        
        Args:
            params: 待优化的参数字典
            
        Returns:
            修复后的参数字典
        """
        # 首先验证
        is_valid, violations = self.validate_params(params)
        
        if not is_valid:
            # 记录违反的约束（用于调试）
            if violations:
                warnings.warn(f"参数约束违反，正在修复: {'; '.join(violations[:3])}")
            
            # 修复参数
            repaired_params = self.repair_params(params)
            return repaired_params
        
        return params