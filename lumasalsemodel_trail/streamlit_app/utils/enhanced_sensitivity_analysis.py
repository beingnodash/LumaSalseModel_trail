"""
增强版敏感性分析工具
Enhanced Sensitivity Analysis Tools

专为简化版7大类参数结构设计的敏感性分析功能：
1. 支持7大类参数的敏感性分析
2. 多参数同时分析
3. 相关性分析
4. 参数影响排序
5. 业务策略建议
"""

import pandas as pd
import numpy as np
import streamlit as st
import copy
from typing import Dict, List, Tuple, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class EnhancedSensitivityAnalyzer:
    """增强版敏感性分析器"""
    
    def __init__(self, base_params: Dict[str, Any]):
        """
        初始化分析器
        
        Args:
            base_params: 基础参数配置
        """
        self.base_params = copy.deepcopy(base_params)
        self.results = None
        self.parameter_definitions = self._get_parameter_definitions()
    
    def _get_parameter_definitions(self) -> Dict[str, Dict]:
        """获取参数定义和测试范围"""
        return {
            # 基础参数
            'total_half_years': {
                'category': '基础参数',
                'name': '模拟周期数',
                'min': 1, 'max': 16, 'steps': 8,
                'format': '%.0f', 'unit': '个半年',
                'description': '模拟的半年周期数量'
            },
            
            # 价格参数 - 学生端
            'price_single_use': {
                'category': '价格参数',
                'name': '学生单次付费价格',
                'min': 5.0, 'max': 20.0, 'steps': 8,
                'format': '%.1f', 'unit': '元',
                'description': '学生单次使用功能的价格'
            },
            'price_5_times_card': {
                'category': '价格参数',
                'name': '学生5次卡价格',
                'min': 20.0, 'max': 60.0, 'steps': 9,
                'format': '%.1f', 'unit': '元',
                'description': '学生购买5次卡的价格'
            },
            'price_10_times_card': {
                'category': '价格参数',
                'name': '学生10次卡价格',
                'min': 30.0, 'max': 80.0, 'steps': 8,
                'format': '%.1f', 'unit': '元',
                'description': '学生购买10次卡的价格'
            },
            'price_20_times_card': {
                'category': '价格参数',
                'name': '学生20次卡价格',
                'min': 50.0, 'max': 120.0, 'steps': 8,
                'format': '%.1f', 'unit': '元',
                'description': '学生购买20次卡的价格'
            },
            
            # 价格参数 - 高校端
            'mode_a_price': {
                'category': '价格参数',
                'name': '模式A高校定价',
                'min': 400000.0, 'max': 1000000.0, 'steps': 7,
                'format': '%.0f', 'unit': '元',
                'description': '模式A高校3年服务费用'
            },
            'mode_b_price': {
                'category': '价格参数',
                'name': '模式B高校定价',
                'min': 200000.0, 'max': 600000.0, 'steps': 9,
                'format': '%.0f', 'unit': '元',
                'description': '模式B高校3年服务费用'
            },
            
            # 市场规模
            'new_clients_per_half_year': {
                'category': '市场规模',
                'name': '每半年新客户数',
                'min': 2, 'max': 15, 'steps': 8,
                'format': '%.0f', 'unit': '所',
                'description': '每半年新获取的高校客户数'
            },
            'avg_students_per_uni': {
                'category': '市场规模',
                'name': '平均学校规模',
                'min': 5000, 'max': 20000, 'steps': 8,
                'format': '%.0f', 'unit': '人',
                'description': '每所高校的平均学生数量'
            },
            
            # 市场分布
            'mode_a_ratio': {
                'category': '市场分布',
                'name': '模式A占比',
                'min': 0.1, 'max': 0.6, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '选择模式A的高校比例'
            },
            'mode_b_ratio': {
                'category': '市场分布',
                'name': '模式B占比',
                'min': 0.1, 'max': 0.6, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '选择模式B的高校比例'
            },
            'student_paid_conversion_rate_bc': {
                'category': '市场分布',
                'name': 'B/C学生付费转化率',
                'min': 0.02, 'max': 0.25, 'steps': 8,
                'format': '%.1%', 'unit': '',
                'description': 'B/C模式下学生付费转化率'
            },
            
            # 学生市场细分
            'single_use_ratio': {
                'category': '学生市场细分',
                'name': '单次付费用户占比',
                'min': 0.2, 'max': 0.8, 'steps': 7,
                'format': '%.1%', 'unit': '',
                'description': '选择单次付费的学生比例'
            },
            'card_5_times_ratio': {
                'category': '学生市场细分',
                'name': '5次卡用户占比',
                'min': 0.1, 'max': 0.6, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '在次卡用户中选择5次卡的比例'
            },
            'card_10_times_ratio': {
                'category': '学生市场细分',
                'name': '10次卡用户占比',
                'min': 0.1, 'max': 0.6, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '在次卡用户中选择10次卡的比例'
            },
            'card_20_times_ratio': {
                'category': '学生市场细分',
                'name': '20次卡用户占比',
                'min': 0.1, 'max': 0.6, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '在次卡用户中选择20次卡的比例'
            },
            
            # 续费率参数
            'university_3year_renewal': {
                'category': '续费率参数',
                'name': '高校3年续约率',
                'min': 0.5, 'max': 0.95, 'steps': 10,
                'format': '%.1%', 'unit': '',
                'description': '高校3年服务期后的续约率'
            },
            'student_single_use_repurchase': {
                'category': '续费率参数',
                'name': '学生单次付费复购率',
                'min': 0.4, 'max': 0.9, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '学生单次付费的复购概率'
            },
            'student_5_times_card_repurchase': {
                'category': '续费率参数',
                'name': '学生5次卡复购率',
                'min': 0.4, 'max': 0.9, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '学生5次卡到期后的复购率'
            },
            'student_10_times_card_repurchase': {
                'category': '续费率参数',
                'name': '学生10次卡复购率',
                'min': 0.4, 'max': 0.9, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '学生10次卡到期后的复购率'
            },
            'student_20_times_card_repurchase': {
                'category': '续费率参数',
                'name': '学生20次卡复购率',
                'min': 0.4, 'max': 0.9, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '学生20次卡到期后的复购率'
            },
            
            # 分成比例
            'luma_share_from_student_mode_b': {
                'category': '分成比例',
                'name': 'Luma学生分成比例(模式B)',
                'min': 0.2, 'max': 0.7, 'steps': 6,
                'format': '%.1%', 'unit': '',
                'description': '模式B下Luma的分成比例(模式C为100%)'
            }
        }
    
    def get_parameter_path(self, param_key: str) -> List[str]:
        """获取参数在嵌套字典中的路径"""
        path_mapping = {
            # 基础参数
            'total_half_years': ['total_half_years'],
            
            # 学生价格参数
            'price_single_use': ['student_prices', 'price_single_use'],
            'price_5_times_card': ['student_prices', 'price_5_times_card'],
            'price_10_times_card': ['student_prices', 'price_10_times_card'],
            'price_20_times_card': ['student_prices', 'price_20_times_card'],
            
            # 高校价格参数
            'mode_a_price': ['university_prices', 'mode_a_price'],
            'mode_b_price': ['university_prices', 'mode_b_price'],
            
            # 市场规模
            'new_clients_per_half_year': ['market_scale', 'new_clients_per_half_year'],
            'avg_students_per_uni': ['market_scale', 'avg_students_per_uni'],
            
            # 市场分布
            'mode_a_ratio': ['market_distribution', 'mode_a_ratio'],
            'mode_b_ratio': ['market_distribution', 'mode_b_ratio'],
            'mode_c_ratio': ['market_distribution', 'mode_c_ratio'],
            'student_paid_conversion_rate_bc': ['market_distribution', 'student_paid_conversion_rate_bc'],
            
            # 学生市场细分
            'single_use_ratio': ['student_segmentation', 'single_use_ratio'],
            'card_5_times_ratio': ['student_segmentation', 'card_type_distribution', '5_times'],
            'card_10_times_ratio': ['student_segmentation', 'card_type_distribution', '10_times'],
            'card_20_times_ratio': ['student_segmentation', 'card_type_distribution', '20_times'],
            
            # 续费率参数
            'university_3year_renewal': ['renewal_rates', 'university_3year_renewal'],
            'student_single_use_repurchase': ['renewal_rates', 'student_single_use_repurchase'],
            'student_5_times_card_repurchase': ['renewal_rates', 'student_5_times_card_repurchase'],
            'student_10_times_card_repurchase': ['renewal_rates', 'student_10_times_card_repurchase'],
            'student_20_times_card_repurchase': ['renewal_rates', 'student_20_times_card_repurchase'],
            
            # 分成比例
            'luma_share_from_student_mode_b': ['revenue_sharing', 'luma_share_from_student_mode_b']
        }
        return path_mapping.get(param_key, [param_key])
    
    def set_nested_value(self, params: Dict, path: List[str], value: Any) -> None:
        """在嵌套字典中设置值"""
        current = params
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get_nested_value(self, params: Dict, path: List[str]) -> Any:
        """从嵌套字典中获取值"""
        current = params
        for key in path:
            current = current[key]
        return current
    
    def generate_test_values(self, param_key: str, custom_range: Optional[Tuple[float, float, int]] = None) -> List[float]:
        """生成参数测试值"""
        if param_key not in self.parameter_definitions:
            raise ValueError(f"未知参数: {param_key}")
        
        param_def = self.parameter_definitions[param_key]
        
        if custom_range:
            min_val, max_val, steps = custom_range
        else:
            min_val = param_def['min']
            max_val = param_def['max']
            steps = param_def['steps']
        
        test_values = np.linspace(min_val, max_val, steps)
        
        # 对于需要整数的参数，转换为整数
        integer_params = [
            'total_half_years', 
            'new_clients_per_half_year', 
            'avg_students_per_uni'
        ]
        
        if param_key in integer_params:
            test_values = np.round(test_values).astype(int)
            # 去重并保持排序，转换为Python int类型
            test_values = sorted(list(set([int(x) for x in test_values])))
        else:
            test_values = test_values.tolist()
        
        return test_values
    
    def run_single_parameter_analysis(self, param_key: str, model_class, 
                                    test_values: Optional[List[float]] = None,
                                    output_metrics: Optional[List[str]] = None) -> pd.DataFrame:
        """
        运行单参数敏感性分析
        
        Args:
            param_key: 要分析的参数键
            model_class: 模型类
            test_values: 测试值列表，如果为None则使用默认范围
            output_metrics: 要跟踪的输出指标
            
        Returns:
            包含分析结果的DataFrame
        """
        if test_values is None:
            test_values = self.generate_test_values(param_key)
        
        if output_metrics is None:
            output_metrics = [
                'luma_revenue_total', 'uni_revenue_total', 'student_revenue_total',
                'active_universities', 'total_paying_students'
            ]
        
        results = []
        param_path = self.get_parameter_path(param_key)
        
        for i, test_value in enumerate(test_values):
            # 创建参数副本
            test_params = copy.deepcopy(self.base_params)
            
            # 设置测试值
            self.set_nested_value(test_params, param_path, test_value)
            
            # 特殊处理：如果修改了模式A或B的占比，需要调整模式C
            if param_key in ['mode_a_ratio', 'mode_b_ratio']:
                self._adjust_mode_ratios(test_params, param_key, test_value)
            
            try:
                # 运行模型
                model = model_class(test_params)
                results_df = model.run_model()
                
                # 提取指标
                result_row = {param_key: test_value}
                
                for metric in output_metrics:
                    if metric in results_df.columns:
                        # 计算总和（对于收入类指标）或最大值（对于数量类指标）
                        if 'revenue' in metric or 'income' in metric:
                            result_row[metric] = results_df[metric].sum()
                        else:
                            result_row[metric] = results_df[metric].max()
                    else:
                        result_row[metric] = 0
                
                # 添加业务摘要指标
                summary = model.get_business_summary()
                result_row['avg_revenue_per_period'] = summary['avg_luma_revenue_per_period']
                result_row['revenue_growth_rate'] = summary['revenue_growth_rate']
                result_row['peak_active_universities'] = summary['peak_active_universities']
                result_row['peak_paying_students'] = summary['peak_paying_students']
                
                results.append(result_row)
                
            except Exception as e:
                st.warning(f"参数值 {test_value} 运行失败: {str(e)}")
                continue
        
        return pd.DataFrame(results)
    
    def _adjust_mode_ratios(self, params: Dict, changed_param: str, new_value: float) -> None:
        """调整商业模式比例，确保总和为1"""
        dist = params['market_distribution']
        
        # 设置新值
        dist[changed_param] = new_value
        
        if changed_param == 'mode_a_ratio':
            # 按比例调整B和C
            remaining = 1.0 - new_value
            current_bc_sum = dist['mode_b_ratio'] + dist['mode_c_ratio']
            if current_bc_sum > 0:
                ratio = remaining / current_bc_sum
                dist['mode_b_ratio'] *= ratio
                dist['mode_c_ratio'] *= ratio
            else:
                dist['mode_b_ratio'] = remaining / 2
                dist['mode_c_ratio'] = remaining / 2
        
        elif changed_param == 'mode_b_ratio':
            # 按比例调整A和C
            remaining = 1.0 - new_value
            current_ac_sum = dist['mode_a_ratio'] + dist['mode_c_ratio']
            if current_ac_sum > 0:
                ratio = remaining / current_ac_sum
                dist['mode_a_ratio'] *= ratio
                dist['mode_c_ratio'] *= ratio
            else:
                dist['mode_a_ratio'] = remaining / 2
                dist['mode_c_ratio'] = remaining / 2
        
        elif changed_param == 'mode_c_ratio':
            # 按比例调整A和B
            remaining = 1.0 - new_value
            current_ab_sum = dist['mode_a_ratio'] + dist['mode_b_ratio']
            if current_ab_sum > 0:
                ratio = remaining / current_ab_sum
                dist['mode_a_ratio'] *= ratio
                dist['mode_b_ratio'] *= ratio
            else:
                dist['mode_a_ratio'] = remaining / 2
                dist['mode_b_ratio'] = remaining / 2
    
    def run_multi_parameter_analysis(self, param_configs: Dict[str, Dict], model_class,
                                   output_metrics: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        运行多参数敏感性分析
        
        Args:
            param_configs: 参数配置字典，格式为 {param_key: {'values': [...]}}
            model_class: 模型类
            output_metrics: 要跟踪的输出指标
            
        Returns:
            包含各参数分析结果的字典
        """
        results = {}
        
        for param_key, config in param_configs.items():
            st.write(f"正在分析参数: {self.parameter_definitions[param_key]['name']}")
            
            test_values = config.get('values')
            if test_values is None:
                test_values = self.generate_test_values(param_key)
            
            result_df = self.run_single_parameter_analysis(
                param_key, model_class, test_values, output_metrics
            )
            results[param_key] = result_df
        
        return results
    
    def calculate_parameter_importance(self, results: Dict[str, pd.DataFrame], 
                                     target_metric: str = 'luma_revenue_total') -> pd.DataFrame:
        """
        计算参数重要性排序
        
        Args:
            results: 多参数分析结果
            target_metric: 目标指标
            
        Returns:
            参数重要性排序DataFrame
        """
        importance_data = []
        
        for param_key, result_df in results.items():
            if target_metric in result_df.columns and len(result_df) > 1:
                # 计算变异系数（标准差/均值）
                values = result_df[target_metric]
                mean_val = values.mean()
                std_val = values.std()
                cv = std_val / mean_val if mean_val > 0 else 0
                
                # 计算变化幅度（最大值-最小值）/最小值
                min_val = values.min()
                max_val = values.max()
                change_rate = (max_val - min_val) / min_val if min_val > 0 else 0
                
                # 计算相关系数
                param_values = result_df[param_key]
                correlation = np.corrcoef(param_values, values)[0, 1] if len(param_values) > 1 else 0
                
                param_def = self.parameter_definitions[param_key]
                
                importance_data.append({
                    '参数': param_def['name'],
                    '参数类别': param_def['category'],
                    '变异系数': cv,
                    '变化幅度': change_rate,
                    '相关系数': correlation,
                    '重要性得分': cv * abs(correlation),  # 综合得分
                    '最小值': min_val,
                    '最大值': max_val,
                    '平均值': mean_val
                })
        
        importance_df = pd.DataFrame(importance_data)
        importance_df = importance_df.sort_values('重要性得分', ascending=False)
        
        return importance_df
    
    def generate_business_insights(self, importance_df: pd.DataFrame, 
                                 target_metric: str = 'luma_revenue_total') -> List[str]:
        """
        生成业务洞察建议
        
        Args:
            importance_df: 参数重要性分析结果
            target_metric: 目标指标
            
        Returns:
            业务建议列表
        """
        insights = []
        
        if len(importance_df) == 0:
            return ["暂无足够数据生成业务洞察"]
        
        # 识别最重要的参数
        top_params = importance_df.head(3)
        
        insights.append(f"📊 **关键发现**: 影响{target_metric}最重要的3个参数：")
        for i, row in top_params.iterrows():
            change_pct = row['变化幅度'] * 100
            correlation = row['相关系数']
            direction = "正向" if correlation > 0 else "负向"
            insights.append(f"   • **{row['参数']}** ({row['参数类别']}): {direction}影响，变化幅度{change_pct:.1f}%")
        
        # 按类别分析
        category_importance = importance_df.groupby('参数类别')['重要性得分'].sum().sort_values(ascending=False)
        insights.append(f"\n🎯 **参数类别重要性排序**:")
        for category, score in category_importance.head(3).items():
            insights.append(f"   • {category}: 重要性得分 {score:.3f}")
        
        # 生成具体建议
        insights.append(f"\n💡 **优化建议**:")
        
        top_param = importance_df.iloc[0]
        if top_param['相关系数'] > 0:
            insights.append(f"   • 重点关注提升「{top_param['参数']}」，该参数与收入呈正相关")
        else:
            insights.append(f"   • 注意控制「{top_param['参数']}」，该参数与收入呈负相关")
        
        # 识别高变异参数
        high_variation = importance_df[importance_df['变化幅度'] > 0.5]
        if len(high_variation) > 0:
            insights.append("   • 以下参数变化对结果影响较大，建议加强监控:")
            for _, row in high_variation.head(2).iterrows():
                insights.append(f"     - {row['参数']}: 变化幅度{row['变化幅度']*100:.1f}%")
        
        return insights