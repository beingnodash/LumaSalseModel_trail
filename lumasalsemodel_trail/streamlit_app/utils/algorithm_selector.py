# 算法选择指导系统
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import math

class AlgorithmSelector:
    """
    智能算法选择系统，基于问题特性为用户推荐最适合的优化算法。
    
    该系统考虑以下因素：
    - 问题维度（参数数量）
    - 评估预算（可承受的计算次数）
    - 搜索空间特性
    - 用户偏好
    """
    
    def __init__(self):
        self.algorithm_profiles = {
            "grid_search": {
                "name": "网格搜索",
                "best_dimensions": (1, 3),
                "min_budget": 27,  # 3^3
                "max_budget": float('inf'),
                "strengths": ["全局最优保证", "结果可重现", "实现简单"],
                "weaknesses": ["维度诅咒", "计算成本高", "搜索效率低"],
                "suitable_for": ["低维问题", "充足预算", "精确解需求"]
            },
            "bayesian_optimization": {
                "name": "贝叶斯优化",
                "best_dimensions": (2, 10),
                "min_budget": 20,
                "max_budget": 200,
                "strengths": ["采样效率高", "全局优化", "不确定性量化"],
                "weaknesses": ["需要连续参数", "超参数敏感", "黑盒限制"],
                "suitable_for": ["中维问题", "昂贵函数", "有限预算"]
            },
            "genetic_algorithm": {
                "name": "遗传算法",
                "best_dimensions": (3, 20),
                "min_budget": 100,
                "max_budget": 10000,
                "strengths": ["全局搜索", "处理约束", "并行友好"],
                "weaknesses": ["收敛慢", "参数敏感", "随机性强"],
                "suitable_for": ["高维问题", "复杂约束", "多模态函数"]
            }
        }
    
    def analyze_problem_characteristics(self, 
                                      param_ranges: Dict[str, Tuple[float, float]], 
                                      budget: Optional[int] = None) -> Dict:
        """
        分析优化问题的特征
        
        Args:
            param_ranges: 参数范围字典
            budget: 可用的评估预算
            
        Returns:
            问题特征字典
        """
        num_params = len(param_ranges)
        
        # 估算搜索空间大小
        search_space_size = 1
        continuous_params = 0
        integer_params = 0
        
        for param_name, (min_val, max_val) in param_ranges.items():
            range_size = max_val - min_val
            search_space_size *= range_size
            
            # 简单启发式判断参数类型
            if self._is_likely_integer_param(param_name, min_val, max_val):
                integer_params += 1
            else:
                continuous_params += 1
        
        # 估算问题复杂度
        complexity_score = self._calculate_complexity_score(
            num_params, search_space_size, continuous_params, integer_params
        )
        
        return {
            "num_parameters": num_params,
            "search_space_size": search_space_size,
            "continuous_params": continuous_params,
            "integer_params": integer_params,
            "complexity_score": complexity_score,
            "estimated_budget_needed": self._estimate_budget_needed(num_params),
            "is_high_dimensional": num_params > 5,
            "is_mixed_type": continuous_params > 0 and integer_params > 0
        }
    
    def recommend_algorithm(self, 
                           param_ranges: Dict[str, Tuple[float, float]], 
                           budget: Optional[int] = None,
                           user_preferences: Optional[Dict] = None) -> List[Dict]:
        """
        推荐优化算法
        
        Args:
            param_ranges: 参数范围
            budget: 评估预算
            user_preferences: 用户偏好设置
            
        Returns:
            推荐算法列表，按推荐度排序
        """
        problem_chars = self.analyze_problem_characteristics(param_ranges, budget)
        
        recommendations = []
        
        for algo_key, profile in self.algorithm_profiles.items():
            score = self._calculate_algorithm_score(
                algo_key, profile, problem_chars, budget, user_preferences
            )
            
            recommendation = {
                "algorithm": algo_key,
                "name": profile["name"],
                "score": score,
                "suitability": self._get_suitability_level(score),
                "reasons": self._generate_recommendation_reasons(
                    algo_key, profile, problem_chars, budget
                ),
                "warnings": self._generate_warnings(
                    algo_key, profile, problem_chars, budget
                ),
                "suggested_params": self._suggest_algorithm_params(
                    algo_key, problem_chars, budget
                )
            }
            recommendations.append(recommendation)
        
        # 按得分排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations
    
    def _is_likely_integer_param(self, param_name: str, min_val: float, max_val: float) -> bool:
        """判断参数是否可能是整数类型"""
        # 启发式规则
        if "per_half_year" in param_name or "clients" in param_name:
            return True
        if isinstance(min_val, int) and isinstance(max_val, int) and (max_val - min_val) < 20:
            return True
        return False
    
    def _calculate_complexity_score(self, num_params: int, search_space_size: float, 
                                   continuous_params: int, integer_params: int) -> float:
        """计算问题复杂度得分"""
        # 维度复杂度
        dim_complexity = min(num_params / 10.0, 1.0)
        
        # 搜索空间复杂度
        space_complexity = min(math.log10(search_space_size) / 10.0, 1.0)
        
        # 类型混合复杂度
        type_complexity = 0.2 if continuous_params > 0 and integer_params > 0 else 0.0
        
        return dim_complexity + space_complexity + type_complexity
    
    def _estimate_budget_needed(self, num_params: int) -> Dict[str, int]:
        """估算不同算法所需的预算"""
        return {
            "grid_search": int(5 ** num_params),  # 每维5个点
            "bayesian_optimization": max(20, num_params * 10),  # 至少20次，每维10次
            "genetic_algorithm": max(100, num_params * 50)  # 至少100次，每维50次
        }
    
    def _calculate_algorithm_score(self, algo_key: str, profile: Dict, 
                                  problem_chars: Dict, budget: Optional[int],
                                  user_preferences: Optional[Dict]) -> float:
        """计算算法适用性得分"""
        score = 0.0
        
        num_params = problem_chars["num_parameters"]
        
        # 维度适用性得分 (40%)
        best_dim_min, best_dim_max = profile["best_dimensions"]
        if best_dim_min <= num_params <= best_dim_max:
            dim_score = 1.0
        elif num_params < best_dim_min:
            dim_score = 0.7  # 维度过低
        else:
            # 维度过高，按指数衰减
            dim_score = max(0.1, math.exp(-0.3 * (num_params - best_dim_max)))
        
        score += dim_score * 0.4
        
        # 预算适用性得分 (30%)
        if budget is not None:
            min_budget = profile["min_budget"]
            if budget >= min_budget:
                budget_score = min(1.0, budget / (min_budget * 2))  # 预算越充足得分越高
            else:
                budget_score = max(0.1, budget / min_budget)  # 预算不足时得分很低
        else:
            budget_score = 0.8  # 未指定预算时给中等得分
        
        score += budget_score * 0.3
        
        # 问题类型适用性得分 (20%)
        type_score = 1.0
        if algo_key == "bayesian_optimization" and problem_chars["integer_params"] > problem_chars["continuous_params"]:
            type_score = 0.6  # 贝叶斯优化不太适合整数参数占多数的情况
        
        score += type_score * 0.2
        
        # 用户偏好得分 (10%)
        preference_score = 1.0
        if user_preferences:
            if user_preferences.get("prefer_fast", False) and algo_key == "genetic_algorithm":
                preference_score = 0.7
            if user_preferences.get("prefer_accurate", False) and algo_key == "grid_search":
                preference_score = 1.2
        
        score += preference_score * 0.1
        
        return min(score, 1.0)  # 限制在[0,1]范围内
    
    def _get_suitability_level(self, score: float) -> str:
        """根据得分获取适用性等级"""
        if score >= 0.8:
            return "强烈推荐"
        elif score >= 0.6:
            return "推荐"
        elif score >= 0.4:
            return "可考虑"
        else:
            return "不推荐"
    
    def _generate_recommendation_reasons(self, algo_key: str, profile: Dict, 
                                       problem_chars: Dict, budget: Optional[int]) -> List[str]:
        """生成推荐理由"""
        reasons = []
        num_params = problem_chars["num_parameters"]
        
        if algo_key == "grid_search":
            if num_params <= 3:
                reasons.append(f"参数数量较少({num_params}个)，网格搜索能保证找到全局最优解")
            if budget is None or budget >= 5 ** num_params:
                reasons.append("计算预算充足，可以进行完整的网格搜索")
        
        elif algo_key == "bayesian_optimization":
            if 2 <= num_params <= 10:
                reasons.append(f"参数数量适中({num_params}个)，贝叶斯优化效率高")
            if problem_chars["continuous_params"] > problem_chars["integer_params"]:
                reasons.append("连续参数较多，适合贝叶斯优化")
            if budget and 20 <= budget <= 200:
                reasons.append("预算范围适合贝叶斯优化的采样策略")
        
        elif algo_key == "genetic_algorithm":
            if num_params > 5:
                reasons.append(f"高维问题({num_params}个参数)，遗传算法搜索能力强")
            if problem_chars["complexity_score"] > 0.5:
                reasons.append("问题复杂度较高，遗传算法具有全局搜索优势")
        
        return reasons
    
    def _generate_warnings(self, algo_key: str, profile: Dict, 
                          problem_chars: Dict, budget: Optional[int]) -> List[str]:
        """生成警告信息"""
        warnings = []
        num_params = problem_chars["num_parameters"]
        
        if algo_key == "grid_search":
            if num_params > 4:
                warnings.append(f"参数维度较高({num_params}个)，计算时间可能很长")
            estimated_evaluations = 5 ** num_params
            if estimated_evaluations > 10000:
                warnings.append(f"预计需要约{estimated_evaluations:,}次评估，建议减少参数或选择其他算法")
        
        elif algo_key == "bayesian_optimization":
            if problem_chars["integer_params"] > problem_chars["continuous_params"]:
                warnings.append("整数参数较多，可能影响贝叶斯优化效果")
            if budget and budget < 20:
                warnings.append("预算较少，可能无法充分发挥贝叶斯优化优势")
        
        elif algo_key == "genetic_algorithm":
            if num_params < 3:
                warnings.append("参数数量较少，遗传算法可能过于复杂")
            warnings.append("遗传算法具有随机性，结果可能不完全可重现")
        
        return warnings
    
    def _suggest_algorithm_params(self, algo_key: str, problem_chars: Dict, 
                                 budget: Optional[int]) -> Dict:
        """建议算法参数设置"""
        num_params = problem_chars["num_parameters"]
        
        if algo_key == "grid_search":
            # 根据维度和预算建议采样点数
            if budget:
                max_points_per_dim = int(budget ** (1/num_params))
                points_per_dim = min(max_points_per_dim, 7)
            else:
                points_per_dim = max(3, min(5, 8 - num_params))
            
            return {
                "points_per_dim": points_per_dim,
                "estimated_evaluations": points_per_dim ** num_params
            }
        
        elif algo_key == "bayesian_optimization":
            if budget:
                n_iterations = min(budget, max(20, num_params * 10))
            else:
                n_iterations = max(30, num_params * 8)
            
            n_initial_points = min(n_iterations // 3, max(5, num_params * 2))
            
            return {
                "n_iterations": n_iterations,
                "n_initial_points": n_initial_points,
                "exploitation_vs_exploration": 0.1 if num_params <= 5 else 0.2
            }
        
        elif algo_key == "genetic_algorithm":
            if budget:
                max_generations = budget // (num_params * 10)
                population_size = min(50, max(20, num_params * 5))
            else:
                max_generations = max(20, 50 - num_params * 3)
                population_size = max(30, num_params * 6)
            
            return {
                "population_size": population_size,
                "n_generations": max_generations,
                "mutation_rate": 0.15 if num_params > 7 else 0.1
            }
        
        return {}
    
    def generate_selection_report(self, param_ranges: Dict[str, Tuple[float, float]], 
                                budget: Optional[int] = None) -> str:
        """生成算法选择报告"""
        problem_chars = self.analyze_problem_characteristics(param_ranges, budget)
        recommendations = self.recommend_algorithm(param_ranges, budget)
        
        report = f"""
# 算法选择分析报告

## 问题特征分析
- 参数数量: {problem_chars['num_parameters']}
- 连续参数: {problem_chars['continuous_params']} 个
- 整数参数: {problem_chars['integer_params']} 个
- 复杂度得分: {problem_chars['complexity_score']:.2f}
- 预算限制: {budget if budget else '未指定'}

## 算法推荐结果

"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"""### {i}. {rec['name']} - {rec['suitability']}
**适用性得分**: {rec['score']:.2f}

**推荐理由**:
{chr(10).join(f"- {reason}" for reason in rec['reasons'])}

**注意事项**:
{chr(10).join(f"- {warning}" for warning in rec['warnings']) if rec['warnings'] else '- 无特殊注意事项'}

**建议参数设置**:
{chr(10).join(f"- {k}: {v}" for k, v in rec['suggested_params'].items())}

---
"""
        
        return report