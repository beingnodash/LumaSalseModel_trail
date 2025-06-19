# 现实约束处理器 - 解决"极值寻找"问题
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import warnings

class RealisticConstraintHandler:
    """
    现实约束处理器
    
    该模块通过引入现实的业务约束，避免优化结果总是选择极值。
    主要约束包括：价格弹性、竞争约束、市场容量限制等。
    """
    
    def __init__(self):
        # 价格弹性系数
        self.price_elasticity = {
            'price_per_feature_use': -0.5,    # 价格弹性：价格每增加1%，需求下降0.5%
            'price_annual_member': -0.3,      # 年费弹性相对较小
            'price_3year_member': -0.4,       # 长期会员价格敏感性中等
            'price_5year_member': -0.5        # 长期会员价格敏感性较高
        }
        
        # 分成比例接受度阈值
        self.share_acceptance_thresholds = {
            'type2_luma_share_from_student.a': 0.6,  # Type2a分成超过60%，高校接受度下降
            'type2_luma_share_from_student.b': 0.7,  # Type2b分成超过70%，高校接受度下降  
            'type2_luma_share_from_student.c': 0.8   # Type2c分成超过80%，高校接受度下降
        }
        
        # 市场拓展成本模型
        self.market_expansion_costs = {
            'new_clients_per_half_year': {
                'base_cost_per_client': 50000,    # 基础获客成本5万/客户
                'marginal_cost_multiplier': 1.5   # 边际成本递增倍数
            }
        }
        
        # 合理参数范围（基于市场调研）
        self.reasonable_ranges = {
            'price_annual_member': (15, 60),         # 年费合理范围
            'price_3year_member': (40, 150),         # 三年费合理范围
            'price_5year_member': (60, 200),         # 五年费合理范围
            'price_per_feature_use': (2, 20),        # 单次使用费
            'type2_luma_share_from_student.a': (0.2, 0.7),
            'type2_luma_share_from_student.b': (0.3, 0.8),
            'type2_luma_share_from_student.c': (0.4, 0.9),
            'new_clients_per_half_year': (2, 15),    # 半年新客户数
            'renewal_rate_uni': (0.6, 0.95)          # 续约率合理范围
        }
    
    def apply_realistic_constraints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用现实约束，修正参数以反映真实的业务约束
        
        Args:
            params: 原始参数字典
            
        Returns:
            修正后的参数字典，包含现实约束的影响
        """
        constrained_params = params.copy()
        
        # 1. 应用价格弹性约束
        constrained_params = self._apply_price_elasticity(constrained_params)
        
        # 2. 应用分成比例接受度约束
        constrained_params = self._apply_share_acceptance(constrained_params)
        
        # 3. 应用市场拓展成本约束
        constrained_params = self._apply_market_costs(constrained_params)
        
        # 4. 应用竞争性约束
        constrained_params = self._apply_competitive_constraints(constrained_params)
        
        return constrained_params
    
    def _apply_price_elasticity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """应用价格弹性约束"""
        for param_name, elasticity in self.price_elasticity.items():
            if param_name in params:
                price_value = params[param_name]
                
                # 获取合理价格范围的中位数作为基准
                if param_name in self.reasonable_ranges:
                    min_price, max_price = self.reasonable_ranges[param_name]
                    base_price = (min_price + max_price) / 2
                    
                    # 计算价格相对于基准的涨幅
                    price_increase_rate = (price_value - base_price) / base_price
                    
                    # 根据价格弹性计算需求下降
                    demand_change = elasticity * price_increase_rate
                    
                    # 调整相关的转化率参数
                    if 'student_total_paid_cr' in params:
                        original_cr = params.get('student_total_paid_cr', 0.05)
                        # 价格上涨导致转化率下降
                        adjusted_cr = original_cr * (1 + demand_change)
                        params['student_total_paid_cr'] = max(0.01, min(0.2, adjusted_cr))
        
        return params
    
    def _apply_share_acceptance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """应用分成比例接受度约束"""
        for param_name, threshold in self.share_acceptance_thresholds.items():
            if param_name in params:
                share_value = params[param_name]
                
                # 如果分成比例超过阈值，降低高校续约率
                if share_value > threshold:
                    over_threshold_rate = (share_value - threshold) / (1 - threshold)
                    
                    # 续约率下降（最多下降20%）
                    renewal_penalty = 0.2 * over_threshold_rate
                    
                    if 'renewal_rate_uni' in params:
                        original_renewal = params.get('renewal_rate_uni', 0.8)
                        adjusted_renewal = original_renewal * (1 - renewal_penalty)
                        params['renewal_rate_uni'] = max(0.4, adjusted_renewal)
        
        return params
    
    def _apply_market_costs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """应用市场拓展成本约束"""
        if 'new_clients_per_half_year' in params:
            new_clients = params['new_clients_per_half_year']
            cost_config = self.market_expansion_costs['new_clients_per_half_year']
            
            # 计算获客成本（边际成本递增）
            base_cost = cost_config['base_cost_per_client']
            multiplier = cost_config['marginal_cost_multiplier']
            
            # 获客数量越多，单位成本越高
            if new_clients > 10:
                cost_multiplier = 1 + (new_clients - 10) * 0.2
                # 这个成本可以用来调整其他参数，比如降低利润率等
                # 这里简化处理：获客成本过高时，适当降低目标
                if new_clients > 15:
                    # 高获客目标不现实，调整为更合理的水平
                    params['new_clients_per_half_year'] = min(new_clients, 12)
        
        return params
    
    def _apply_competitive_constraints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """应用竞争性约束"""
        # 如果多个价格参数都很高，引入竞争压力
        price_params = ['price_annual_member', 'price_3year_member', 'price_5year_member']
        
        high_price_count = 0
        for param in price_params:
            if param in params and param in self.reasonable_ranges:
                value = params[param]
                min_val, max_val = self.reasonable_ranges[param]
                
                # 如果价格超过合理范围的80%，认为是高价
                if value > min_val + 0.8 * (max_val - min_val):
                    high_price_count += 1
        
        # 如果多个价格都偏高，引入竞争约束
        if high_price_count >= 2:
            # 市场竞争压力：降低学生付费转化率
            if 'student_total_paid_cr' in params:
                original_cr = params.get('student_total_paid_cr', 0.05)
                competitive_penalty = 0.15 * (high_price_count - 1)
                adjusted_cr = original_cr * (1 - competitive_penalty)
                params['student_total_paid_cr'] = max(0.02, adjusted_cr)
        
        return params
    
    def calculate_penalty_score(self, params: Dict[str, Any]) -> float:
        """
        计算约束违反的惩罚分数
        
        Args:
            params: 参数字典
            
        Returns:
            惩罚分数，0表示无违反，值越大表示违反越严重
        """
        penalty = 0.0
        
        # 价格合理性惩罚
        for param_name, (min_val, max_val) in self.reasonable_ranges.items():
            if param_name in params:
                value = params[param_name]
                
                # 超出合理范围的惩罚
                if value < min_val:
                    penalty += (min_val - value) / min_val * 100
                elif value > max_val:
                    penalty += (value - max_val) / max_val * 100
        
        # 分成比例过高的惩罚
        for param_name, threshold in self.share_acceptance_thresholds.items():
            if param_name in params:
                value = params[param_name]
                if value > threshold:
                    penalty += (value - threshold) * 200  # 分成过高重罚
        
        # 获客目标不切实际的惩罚
        if 'new_clients_per_half_year' in params:
            new_clients = params['new_clients_per_half_year']
            if new_clients > 15:
                penalty += (new_clients - 15) * 50
        
        return penalty
    
    def generate_constraint_report(self, params: Dict[str, Any]) -> str:
        """生成约束分析报告"""
        report = "# 现实约束分析报告\n\n"
        
        penalty_score = self.calculate_penalty_score(params)
        
        if penalty_score == 0:
            report += "✅ **约束状态**: 所有参数均在合理范围内\n\n"
        elif penalty_score < 50:
            report += "⚠️ **约束状态**: 存在轻微的现实性问题\n\n"
        elif penalty_score < 200:
            report += "🔶 **约束状态**: 存在明显的现实性问题\n\n"
        else:
            report += "❌ **约束状态**: 参数设置严重偏离现实\n\n"
        
        report += f"**惩罚分数**: {penalty_score:.1f}\n\n"
        
        # 详细分析
        report += "## 参数现实性分析\n\n"
        
        for param_name, value in params.items():
            if param_name in self.reasonable_ranges:
                min_val, max_val = self.reasonable_ranges[param_name]
                
                if min_val <= value <= max_val:
                    status = "✅ 合理"
                elif value < min_val:
                    status = f"⚠️ 偏低 (建议范围: {min_val}-{max_val})"
                else:
                    status = f"🔶 偏高 (建议范围: {min_val}-{max_val})"
                
                report += f"- **{param_name}**: {value:.2f} - {status}\n"
        
        # 业务风险提示
        report += "\n## 业务风险提示\n\n"
        
        high_price_params = []
        for param in ['price_annual_member', 'price_3year_member', 'price_5year_member']:
            if param in params and param in self.reasonable_ranges:
                value = params[param]
                min_val, max_val = self.reasonable_ranges[param]
                if value > min_val + 0.8 * (max_val - min_val):
                    high_price_params.append(param)
        
        if high_price_params:
            report += f"🔸 **定价风险**: {len(high_price_params)} 个价格参数偏高，可能面临竞争压力\n"
        
        high_share_params = []
        for param_name, threshold in self.share_acceptance_thresholds.items():
            if param_name in params and params[param_name] > threshold:
                high_share_params.append(param_name)
        
        if high_share_params:
            report += f"🔸 **合作风险**: {len(high_share_params)} 个分成比例过高，可能影响高校接受度\n"
        
        if params.get('new_clients_per_half_year', 0) > 12:
            report += "🔸 **扩张风险**: 新客户获取目标可能过于激进\n"
        
        return report

def create_penalty_adjusted_objective_function(base_params: Dict[str, Any], 
                                              objective_metric: str,
                                              penalty_weight: float = 0.1):
    """
    创建包含现实约束惩罚的目标函数
    
    Args:
        base_params: 基础参数
        objective_metric: 原始目标指标
        penalty_weight: 惩罚权重
        
    Returns:
        调整后的目标函数
    """
    constraint_handler = RealisticConstraintHandler()
    
    def penalty_adjusted_objective(params_to_update: Dict[str, Any]) -> float:
        # 应用现实约束
        constrained_params = constraint_handler.apply_realistic_constraints(params_to_update)
        
        # 计算原始目标值（这里需要调用实际的模型评估函数）
        from .optimization import run_model_with_params
        try:
            original_score = run_model_with_params(base_params, constrained_params, objective_metric)
        except:
            original_score = -1e6
        
        # 计算惩罚分数
        penalty_score = constraint_handler.calculate_penalty_score(params_to_update)
        
        # 调整后的目标值 = 原始值 - 惩罚值
        adjusted_score = original_score - penalty_weight * penalty_score
        
        return adjusted_score
    
    return penalty_adjusted_objective