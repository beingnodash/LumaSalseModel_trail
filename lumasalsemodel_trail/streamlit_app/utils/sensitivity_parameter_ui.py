"""
敏感性分析参数UI组件
Sensitivity Analysis Parameter UI Components

为简化版7大类参数结构设计的敏感性分析界面组件
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from .enhanced_sensitivity_analysis import EnhancedSensitivityAnalyzer

class SensitivityParameterUI:
    """敏感性分析参数UI类"""
    
    def __init__(self, base_params: Dict[str, Any]):
        """
        初始化UI组件
        
        Args:
            base_params: 基础参数配置
        """
        self.base_params = base_params
        self.analyzer = EnhancedSensitivityAnalyzer(base_params)
        self.parameter_definitions = self.analyzer.parameter_definitions
    
    def render_analysis_type_selection(self) -> str:
        """渲染分析类型选择"""
        st.subheader("🔍 选择分析类型")
        
        analysis_types = {
            "single": "单参数敏感性分析 - 分析单个参数对结果的影响",
            "multi": "多参数敏感性分析 - 同时分析多个参数的影响",
            "importance": "参数重要性排序 - 识别影响最大的关键参数"
        }
        
        analysis_type = st.radio(
            "分析类型",
            options=list(analysis_types.keys()),
            format_func=lambda x: analysis_types[x].split(" - ")[0],
            help="选择您想要进行的敏感性分析类型"
        )
        
        # 显示选择的分析类型说明
        st.info(f"📋 **{analysis_types[analysis_type]}**")
        
        return analysis_type
    
    def render_single_parameter_controls(self) -> Tuple[str, List[float], bool]:
        """
        渲染单参数分析控件
        
        Returns:
            Tuple[str, List[float], bool]: 参数名、测试值列表、是否使用自定义范围
        """
        st.subheader("📊 单参数敏感性分析设置")
        
        # 按类别组织参数
        categories = {}
        for param_key, param_def in self.parameter_definitions.items():
            category = param_def['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((param_key, param_def))
        
        # 参数选择
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_category = st.selectbox(
                "参数类别",
                options=list(categories.keys()),
                help="选择要分析的参数类别"
            )
        
        with col2:
            category_params = categories[selected_category]
            param_options = [(key, f"{def_['name']} ({def_['unit']})") for key, def_ in category_params]
            
            selected_param_key = st.selectbox(
                "具体参数",
                options=[key for key, _ in param_options],
                format_func=lambda x: next(label for key, label in param_options if key == x),
                help="选择要进行敏感性分析的具体参数"
            )
        
        # 显示参数信息
        param_def = self.parameter_definitions[selected_param_key]
        current_value = self._get_current_parameter_value(selected_param_key)
        
        st.markdown(f"""
        **当前参数信息:**
        - **参数名称**: {param_def['name']}
        - **当前值**: {current_value:.2f} {param_def['unit']}
        - **参数描述**: {param_def['description']}
        """)
        
        # 测试范围设置
        st.subheader("🎯 测试范围设置")
        
        use_custom_range = st.checkbox(
            "自定义测试范围",
            value=False,
            help="是否使用自定义的参数测试范围"
        )
        
        if use_custom_range:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_val = st.number_input(
                    f"最小值 ({param_def['unit']})",
                    value=float(param_def['min']),
                    step=float(param_def['min']) * 0.1,
                    format=param_def['format']
                )
            
            with col2:
                max_val = st.number_input(
                    f"最大值 ({param_def['unit']})",
                    value=float(param_def['max']),
                    step=float(param_def['max']) * 0.1,
                    format=param_def['format']
                )
            
            with col3:
                steps = st.slider(
                    "测试点数量",
                    min_value=5, max_value=20,
                    value=param_def['steps'],
                    help="生成的测试值数量"
                )
            
            if min_val >= max_val:
                st.error("最小值必须小于最大值")
                test_values = []
            else:
                test_values = np.linspace(min_val, max_val, steps).tolist()
        else:
            test_values = self.analyzer.generate_test_values(selected_param_key)
        
        # 显示测试值
        if test_values:
            st.write(f"**测试值预览** ({len(test_values)} 个):")
            try:
                # 安全的格式化处理
                formatted_values = []
                for val in test_values[:10]:
                    if param_def['format'] == '%.1%':
                        formatted_values.append(f"{val:.1%}")
                    elif param_def['format'] == '%.0f':
                        formatted_values.append(f"{val:.0f}")
                    elif param_def['format'] == '%.1f':
                        formatted_values.append(f"{val:.1f}")
                    elif param_def['format'] == '%.2f':
                        formatted_values.append(f"{val:.2f}")
                    else:
                        formatted_values.append(str(val))
                
                if len(test_values) > 10:
                    formatted_values.append("...")
                st.code(" | ".join(formatted_values))
            except Exception as e:
                st.write(f"测试值: {test_values[:10]}")
                if len(test_values) > 10:
                    st.write("...")
        
        return selected_param_key, test_values, use_custom_range
    
    def render_multi_parameter_controls(self) -> Dict[str, Dict]:
        """
        渲染多参数分析控件
        
        Returns:
            Dict[str, Dict]: 多参数配置
        """
        st.subheader("📊 多参数敏感性分析设置")
        
        # 参数选择
        st.write("**选择要分析的参数 (最多5个):**")
        
        # 按类别组织参数选择
        categories = {}
        for param_key, param_def in self.parameter_definitions.items():
            category = param_def['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((param_key, param_def['name']))
        
        selected_params = []
        
        for category, params in categories.items():
            with st.expander(f"📂 {category}", expanded=True):
                for param_key, param_name in params:
                    if st.checkbox(f"{param_name}", key=f"multi_{param_key}"):
                        selected_params.append(param_key)
        
        if len(selected_params) > 5:
            st.warning("⚠️ 最多只能选择5个参数进行多参数分析")
            selected_params = selected_params[:5]
        
        # 为每个选中的参数设置测试范围
        param_configs = {}
        
        if selected_params:
            st.subheader("🎯 参数测试范围设置")
            
            for param_key in selected_params:
                param_def = self.parameter_definitions[param_key]
                current_value = self._get_current_parameter_value(param_key)
                
                with st.expander(f"⚙️ {param_def['name']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        use_default = st.checkbox(
                            "使用默认范围",
                            value=True,
                            key=f"default_{param_key}"
                        )
                    
                    with col2:
                        st.metric(
                            "当前值",
                            f"{current_value:.2f} {param_def['unit']}"
                        )
                    
                    if use_default:
                        test_values = self.analyzer.generate_test_values(param_key)
                    else:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            min_val = st.number_input(
                                "最小值",
                                value=float(param_def['min']),
                                key=f"min_{param_key}",
                                format=param_def['format']
                            )
                        
                        with col2:
                            max_val = st.number_input(
                                "最大值",
                                value=float(param_def['max']),
                                key=f"max_{param_key}",
                                format=param_def['format']
                            )
                        
                        with col3:
                            steps = st.slider(
                                "测试点数",
                                min_value=3, max_value=10,
                                value=min(param_def['steps'], 8),
                                key=f"steps_{param_key}"
                            )
                        
                        if min_val < max_val:
                            test_values = np.linspace(min_val, max_val, steps).tolist()
                        else:
                            st.error("最小值必须小于最大值")
                            test_values = self.analyzer.generate_test_values(param_key)
                    
                    param_configs[param_key] = {'values': test_values}
                    
                    # 显示测试值预览
                    try:
                        formatted_values = []
                        for val in test_values[:5]:
                            if param_def['format'] == '%.1%':
                                formatted_values.append(f"{val:.1%}")
                            elif param_def['format'] == '%.0f':
                                formatted_values.append(f"{val:.0f}")
                            elif param_def['format'] == '%.1f':
                                formatted_values.append(f"{val:.1f}")
                            elif param_def['format'] == '%.2f':
                                formatted_values.append(f"{val:.2f}")
                            else:
                                formatted_values.append(str(val))
                        
                        if len(test_values) > 5:
                            formatted_values.append("...")
                        st.code(" | ".join(formatted_values))
                    except Exception as e:
                        st.write(f"测试值: {test_values[:5]}")
                        if len(test_values) > 5:
                            st.write("...")
        
        return param_configs
    
    def render_output_metrics_selection(self, analysis_type: str = "single") -> List[str]:
        """
        渲染输出指标选择
        
        Args:
            analysis_type: 分析类型
            
        Returns:
            List[str]: 选择的输出指标列表
        """
        st.subheader("📈 选择输出指标")
        
        # 定义可用的输出指标
        available_metrics = {
            # 收入指标
            'luma_revenue_total': {
                'name': 'Luma总收入',
                'category': '收入指标',
                'description': 'Luma公司的总收入（包括高校付费和学生分成）'
            },
            'uni_revenue_total': {
                'name': '高校总收入',
                'category': '收入指标',
                'description': '高校的总收入（主要是固定接入费）'
            },
            'student_revenue_total': {
                'name': '学生总收入',
                'category': '收入指标',
                'description': '学生付费的总收入（按次付费+订阅付费）'
            },
            'luma_revenue_from_uni': {
                'name': 'Luma来自高校收入',
                'category': '收入指标',
                'description': 'Luma从高校获得的固定收入'
            },
            'luma_revenue_from_student_share': {
                'name': 'Luma学生分成收入',
                'category': '收入指标',
                'description': 'Luma从学生付费中获得的分成收入'
            },
            
            # 业务指标
            'active_universities': {
                'name': '活跃高校数',
                'category': '业务指标',
                'description': '活跃合作的高校数量'
            },
            'total_paying_students': {
                'name': '付费学生数',
                'category': '业务指标',
                'description': '付费使用服务的学生总数'
            },
            'avg_revenue_per_period': {
                'name': '平均期收入',
                'category': '业务指标',
                'description': '每个半年周期的平均收入'
            },
            'revenue_growth_rate': {
                'name': '收入增长率',
                'category': '业务指标',
                'description': '收入的增长趋势'
            }
        }
        
        # 按类别组织指标选择
        metric_categories = {}
        for metric_key, metric_info in available_metrics.items():
            category = metric_info['category']
            if category not in metric_categories:
                metric_categories[category] = []
            metric_categories[category].append((metric_key, metric_info))
        
        selected_metrics = []
        
        # 默认选择
        default_metrics = ['luma_revenue_total', 'active_universities', 'total_paying_students']
        
        for category, metrics in metric_categories.items():
            with st.expander(f"📊 {category}", expanded=True):
                for metric_key, metric_info in metrics:
                    default_value = metric_key in default_metrics
                    if st.checkbox(
                        f"{metric_info['name']}", 
                        value=default_value,
                        key=f"metric_{metric_key}",
                        help=metric_info['description']
                    ):
                        selected_metrics.append(metric_key)
        
        if not selected_metrics:
            st.warning("⚠️ 请至少选择一个输出指标")
        else:
            st.success(f"✅ 已选择 {len(selected_metrics)} 个输出指标")
        
        return selected_metrics
    
    def render_analysis_settings(self) -> Dict[str, Any]:
        """
        渲染分析设置
        
        Returns:
            Dict[str, Any]: 分析设置
        """
        st.subheader("⚙️ 分析设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            show_progress = st.checkbox(
                "显示详细进度",
                value=True,
                help="是否显示模型运行的详细进度信息"
            )
            
            generate_insights = st.checkbox(
                "生成业务洞察",
                value=True,
                help="是否根据分析结果生成业务策略建议"
            )
        
        with col2:
            export_results = st.checkbox(
                "提供结果导出",
                value=True,
                help="是否提供分析结果的CSV导出功能"
            )
            
            detailed_charts = st.checkbox(
                "生成详细图表",
                value=True,
                help="是否生成详细的可视化图表"
            )
        
        return {
            'show_progress': show_progress,
            'generate_insights': generate_insights,
            'export_results': export_results,
            'detailed_charts': detailed_charts
        }
    
    def _get_current_parameter_value(self, param_key: str) -> float:
        """获取当前参数值"""
        param_path = self.analyzer.get_parameter_path(param_key)
        try:
            return self.analyzer.get_nested_value(self.base_params, param_path)
        except KeyError:
            # 如果参数不存在，返回默认值
            return self.parameter_definitions[param_key]['min']
    
    def display_parameter_summary(self, analysis_type: str, **kwargs) -> None:
        """
        显示参数分析摘要
        
        Args:
            analysis_type: 分析类型
            **kwargs: 其他配置参数
        """
        st.subheader("📋 分析配置摘要")
        
        if analysis_type == "single":
            param_key = kwargs.get('param_key')
            test_values = kwargs.get('test_values', [])
            
            if param_key and test_values:
                param_def = self.parameter_definitions[param_key]
                current_value = self._get_current_parameter_value(param_key)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("分析参数", param_def['name'])
                    st.metric("参数类别", param_def['category'])
                
                with col2:
                    st.metric("当前值", f"{current_value:.2f} {param_def['unit']}")
                    st.metric("测试点数", len(test_values))
                
                with col3:
                    if test_values:
                        st.metric("测试范围", f"{min(test_values):.2f} - {max(test_values):.2f}")
                        st.metric("测试间隔", f"±{((max(test_values) - min(test_values)) / len(test_values)):.2f}")
        
        elif analysis_type == "multi":
            param_configs = kwargs.get('param_configs', {})
            
            if param_configs:
                st.write(f"**多参数分析配置** (共 {len(param_configs)} 个参数):")
                
                for param_key, config in param_configs.items():
                    param_def = self.parameter_definitions[param_key]
                    test_values = config['values']
                    
                    st.write(f"• **{param_def['name']}** ({param_def['category']}): "
                           f"{len(test_values)} 个测试点, "
                           f"范围 {min(test_values):.2f} - {max(test_values):.2f}")
        
        # 显示输出指标
        output_metrics = kwargs.get('output_metrics', [])
        if output_metrics:
            st.write(f"**输出指标** (共 {len(output_metrics)} 个):")
            for metric in output_metrics:
                if metric in {
                    'luma_revenue_total': 'Luma总收入',
                    'uni_revenue_total': '高校总收入',
                    'student_revenue_total': '学生总收入',
                    'active_universities': '活跃高校数',
                    'total_paying_students': '付费学生数'
                }:
                    metric_name = {
                        'luma_revenue_total': 'Luma总收入',
                        'uni_revenue_total': '高校总收入',
                        'student_revenue_total': '学生总收入',
                        'active_universities': '活跃高校数',
                        'total_paying_students': '付费学生数'
                    }.get(metric, metric)
                    st.write(f"  - {metric_name}")
        
        # 分析设置
        analysis_settings = kwargs.get('analysis_settings', {})
        if analysis_settings:
            settings_text = []
            if analysis_settings.get('show_progress'):
                settings_text.append("显示详细进度")
            if analysis_settings.get('generate_insights'):
                settings_text.append("生成业务洞察")
            if analysis_settings.get('export_results'):
                settings_text.append("提供结果导出")
            if analysis_settings.get('detailed_charts'):
                settings_text.append("生成详细图表")
            
            if settings_text:
                st.write(f"**分析设置**: {' | '.join(settings_text)}")