"""
Luma高校销售与收益分析模型 - Streamlit应用主入口
"""
import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# 添加项目根目录到Python路径，确保可以导入luma_sales_model模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luma_sales_model.financial_model import LumaFinancialModel

# 设置页面配置
st.set_page_config(
    page_title="Luma高校销售与收益分析模型",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用标题和介绍
st.title("Luma高校销售与收益分析模型")

# 添加新功能提示
st.info("""
🚀 **最新更新**: 已推出全新的**增强版商业模式分析**！  
新版本支持三种真实商业模式（A/B/C），提供更准确的财务预测和业务分析。  
👉 请在左侧导航栏选择 "Enhanced Business Model" 体验新版本
""")

st.markdown("""

本模型可以帮助您预测和分析Luma与高校合作的收入和收益情况。即使您不是财务专家，也能轻松使用。

### 如何使用本应用：
1. 在左侧设置参数（每个参数都有详细说明）
2. 点击“运行模型”按钮生成结果
3. 在主页查看基本结果
4. 使用页面顶部的导航栏查看更多可视化和敏感性分析

### 本应用可以帮助您：
- 模拟不同的市场条件和业务策略
- 分析收入结构和发展趋势
- 了解关键参数如何影响最终结果
- 通过直观的图表和数据分析支持决策

> 提示：鼠标悬停在大多数参数上可以查看详细说明！  
> 💡 **推荐使用新的增强版商业模式分析获得更准确的结果！**
""")

# 初始化会话状态
if 'model_results' not in st.session_state:
    st.session_state.model_results = None
if 'model_params' not in st.session_state:
    st.session_state.model_params = {}
if 'sensitivity_results' not in st.session_state:
    st.session_state.sensitivity_results = None

# 侧边栏 - 参数设置
st.sidebar.header("模型参数设置")
st.sidebar.markdown("""
请调整以下参数来模拟不同的业务场景。鼠标悬停在参数上可查看详细说明。
""") 

# 基础参数
st.sidebar.subheader("基础参数")
st.sidebar.markdown("""
<small>这些是模型的核心参数，决定了模拟的时间范围和客户获取速度</small>
""", unsafe_allow_html=True)

total_half_years = st.sidebar.slider(
    "模拟周期数（半年）", 
    2, 10, 4, 
    help="设置要模拟的半年周期数量。例如，选择4表示模拟2年的业务情况。"
)

new_clients_per_half_year = st.sidebar.slider(
    "每半年新签约客户数", 
    1, 20, 5,
    help="每半年新获取的高校客户数量。这决定了业务增长速度。"
)

# 商业模式分布参数  
st.sidebar.subheader("商业模式分布")
st.sidebar.markdown("""
<small>三种基本商业模式的占比，总和应为1.0（100%）：</small>
- <small>**模式A**: 高校付费 + 学生免费使用全部功能</small>
- <small>**模式B**: 高校付费 + 学生免费基础功能 + 学生付费高级功能</small>
- <small>**模式C**: 高校免费 + 学生免费基础功能 + 学生付费高级功能</small>
""", unsafe_allow_html=True)

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    mode_a_share = st.number_input(
        "模式A占比", 
        0.0, 1.0, 0.3, 
        format="%.2f",
        help="模式A：高校付费 + 学生免费使用全部功能"
    )
with col2:
    mode_b_share = st.number_input(
        "模式B占比", 
        0.0, 1.0, 0.4, 
        format="%.2f",
        help="模式B：高校付费 + 学生分层付费"
    )
with col3:
    mode_c_share = st.number_input(
        "模式C占比", 
        0.0, 1.0, 0.3, 
        format="%.2f",
        help="模式C：高校免费 + 学生分层付费"
    )

# 计算总和并显示警告
mode_sum = mode_a_share + mode_b_share + mode_c_share
if not np.isclose(mode_sum, 1.0):
    st.sidebar.warning(f"商业模式分布总和为 {mode_sum:.2f}，应为 1.0（100%）")
else:
    st.sidebar.success("商业模式分布总和正确！")

# 续约率参数
st.sidebar.subheader("续约率参数")
st.sidebar.markdown("""
<small>续约率决定了客户和学生的留存率，对长期收入有重要影响</small>
""", unsafe_allow_html=True)

# 高校3年续约率
uni_renewal_rate_3year = st.sidebar.slider(
    "高校3年续约率", 
    0.0, 1.0, 0.8, 
    format="%.2f",
    help="高校客户3年服务期到期后续约的概率。例如，0.8表示80%的高校在3年后会续约。"
)

# 学生续约参数
st.sidebar.markdown("**学生续约参数**")
student_subscription_renewal_rate = st.sidebar.slider(
    "学生订阅续费率", 
    0.0, 1.0, 0.75, 
    format="%.2f",
    help="学生订阅到期后续费的概率。例如，0.75表示75%的学生会续费订阅。"
)

student_per_use_repurchase_rate = st.sidebar.slider(
    "学生按次付费复购率", 
    0.0, 1.0, 0.7, 
    format="%.2f",
    help="学生继续进行按次付费的概率。例如，0.7表示70%的学生会继续按次付费。"
)

# 高级参数折叠区域
with st.sidebar.expander("高级参数设置（点击展开）"):
    st.markdown("""
    <small>这些参数影响模型的细节表现。如果您是初次使用，可以保持默认值。</small>
    """, unsafe_allow_html=True)
    
    # 学校规模参数
    st.markdown("#### 学校规模参数")
    avg_students_per_uni = st.number_input(
        "平均学生数/校", 
        1000, 50000, 10000,
        help="每所高校的平均学生数量。这影响潜在的学生付费用户基数。"
    )
    
    # 付费转化参数
    st.markdown("#### 付费转化参数")
    st.markdown("""
    <small>这些参数决定了有多少学生会成为付费用户，以及他们的付费方式</small>
    """, unsafe_allow_html=True)
    
    student_total_paid_cr = st.slider(
        "学生付费转化率", 
        0.0, 0.2, 0.05, 
        format="%.3f",
        help="学生成为付费用户的比例。例如，0.05表示5%的学生会付费使用服务。"
    )
    
    # 价格参数设置
    st.markdown("#### 价格参数设置")
    st.markdown("""
    <small>这些参数决定了各类产品和服务的价格，直接影响收入计算</small>
    """, unsafe_allow_html=True)
    
    # 学生端价格参数
    st.markdown("##### 学生端价格")
    col1, col2 = st.columns(2)
    with col1:
        price_per_feature_use = st.number_input(
            "单次功能价格(元)", 
            min_value=0.0, 
            max_value=50.0, 
            value=7.9, 
            step=0.1,
            format="%.1f",
            help="学生使用单次功能的价格。默认为7.9元/次。"
        )
        price_annual_member = st.number_input(
            "年度会员价格(元)", 
            min_value=0.0, 
            max_value=100.0, 
            value=29.0, 
            step=1.0,
            format="%.1f",
            help="学生购买年度会员的价格。默认为29元。"
        )
    with col2:
        price_3year_member = st.number_input(
            "三年会员价格(元)", 
            min_value=0.0, 
            max_value=200.0, 
            value=69.0, 
            step=1.0,
            format="%.1f",
            help="学生购买三年会员的价格。默认为69元。"
        )
        price_5year_member = st.number_input(
            "五年会员价格(元)", 
            min_value=0.0, 
            max_value=300.0, 
            value=99.0, 
            step=1.0,
            format="%.1f",
            help="学生购买五年会员的价格。默认为99元。"
        )
    
    # 高校端定价参数 
    st.markdown("##### 高校端定价（3年服务周期）")
    col1, col2, col3 = st.columns(3)
    with col1:
        mode_a_price = st.number_input(
            "模式A定价(元)", 
            min_value=0.0, 
            max_value=1000000.0, 
            value=600000.0, 
            step=50000.0,
            format="%.1f",
            help="模式A：高校付费 + 学生免费使用全部功能。3年服务周期一次性费用。"
        )
    with col2:
        mode_b_price = st.number_input(
            "模式B定价(元)", 
            min_value=0.0, 
            max_value=1000000.0, 
            value=400000.0, 
            step=50000.0,
            format="%.1f",
            help="模式B：高校付费 + 学生分层付费。3年服务周期一次性费用。"
        )
    with col3:
        # 模式C固定为0
        st.metric("模式C定价", "免费", help="模式C：高校免费 + 学生分层付费")
    
    # 学生付费分成比例参数
    st.markdown("##### 学生付费分成比例")
    st.markdown("""
    <small>**重要说明**: 模式B和C都涉及学生付费，共享相同的分成比例</small>
    """, unsafe_allow_html=True)
    
    luma_student_share_ratio = st.slider(
        "Luma学生付费分成比例", 
        0.0, 1.0, 0.4, 
        format="%.2f",
        help="模式B和C中，Luma从学生付费中获得的比例。例如，0.4表示Luma获得40%，高校获得60%。"
    )
    
    st.info(f"高校获得学生付费分成比例: {1-luma_student_share_ratio:.1%}")
    
    # 付费用户类型分布
    st.subheader("学生付费用户分布")
    st.markdown("""
    <small>付费用户分为两种类型，总和应为1.0（100%）：</small>
    - <small>**单次付费用户**: 按次付费，收入较低</small>
    - <small>**会员付费用户**: 订阅会员服务，收入较高</small>
    """, unsafe_allow_html=True)
    
    share_paid_user_per_use_only = st.slider(
        "单次付费用户占比", 
        0.0, 1.0, 0.3, 
        format="%.2f",
        help="选择单次付费模式的用户比例。例如，0.3表示30%的付费用户选择单次付费。"
    )
    
    share_paid_user_membership = st.slider(
        "会员付费用户占比", 
        0.0, 1.0, 0.7, 
        format="%.2f",
        help="选择会员付费模式的用户比例。例如，0.7表示70%的付费用户选择会员付费。"
    )
    
    # 计算总和并显示警告
    user_type_sum = share_paid_user_per_use_only + share_paid_user_membership
    if not np.isclose(user_type_sum, 1.0):
        st.warning(f"付费用户分布总和为 {user_type_sum:.2f}，应为1.0（100%）")
    else:
        st.success("付费用户分布总和正确！")

# 运行模型按钮
st.sidebar.markdown("""
<div style="text-align: center; margin-top: 15px; margin-bottom: 5px">
    <small>设置完参数后，点击下面的按钮运行模型</small>
</div>
""", unsafe_allow_html=True)

run_button = st.sidebar.button(
    "运行模型", 
    help="点击此按钮将使用当前参数运行模型并生成结果",
    use_container_width=True,
    type="primary"
)

if run_button:
    # 收集所有参数
    params = {
        'total_half_years': total_half_years,
        'new_clients_per_half_year': new_clients_per_half_year,
        'mode_distribution': {
            'Type1': type1_share,
            'Type2a': type2a_share,
            'Type2b': type2b_share,
            'Type2c': type2c_share,
            'Type3': type3_share
        },
        'avg_students_per_uni': avg_students_per_uni,
        'student_total_paid_cr': student_total_paid_cr,
        'share_paid_user_per_use_only': share_paid_user_per_use_only,
        'share_paid_user_membership': share_paid_user_membership,
        'renewal_rate_uni': renewal_rate_uni,
        'renewal_rate_student': renewal_rate_student,
        # 价格参数
        'price_per_feature_use': price_per_feature_use,
        'price_annual_member': price_annual_member,
        'price_3year_member': price_3year_member,
        'price_5year_member': price_5year_member,
        'type1_access_fee': type1_access_fee,
        'type2_access_fees': {
            'a': type2a_access_fee,
            'b': type2b_access_fee,
            'c': type2c_access_fee
        },
        'type2_luma_share_from_student': {
            'a': type2a_luma_share,
            'b': type2b_luma_share,
            'c': type2c_luma_share
        }
    }
    
    # 保存参数到会话状态
    st.session_state.model_params = params
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 运行模型
    try:
        status_text.text("步骤1/4: 初始化模型...")
        progress_bar.progress(10)
        
        model = LumaFinancialModel(params=params)
        
        status_text.text("步骤2/4: 运行计算...")
        progress_bar.progress(40)
        
        results_df = model.run_model()
        
        status_text.text("步骤3/4: 处理结果...")
        progress_bar.progress(70)
        
        # 保存结果到会话状态
        st.session_state.model_results = results_df
        
        status_text.text("步骤4/4: 生成可视化...")
        progress_bar.progress(90)
        
        # 小延时以显示进度
        import time
        time.sleep(0.5)
        
        progress_bar.progress(100)
        status_text.text("计算完成！请在右侧查看结果。")
        
        # 添加成功消息
        st.sidebar.success("模型运行成功！请在右侧查看结果。")
        
    except Exception as e:
        st.error(f"模型运行出错: {str(e)}")
        st.sidebar.error("运行失败，请检查参数设置。")

# 主区域 - 结果展示
if st.session_state.model_results is not None:
    st.info("下面的标签页展示了不同角度的分析结果。点击标签页切换不同视图。更多详细分析可以在页面顶部导航栏中找到")

    results_df = st.session_state.model_results
    
    # 创建标签页
    tab1, tab2 = st.tabs([
        "💰 收入概览", 
        "📈 收入结构分析"
    ])
    
    with tab1:
        st.header("收入概览")
        
        # 显示总收入和基金数据
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Luma总收入", f"{results_df['Luma_Revenue_Total'].sum():.2f}")
            st.line_chart(results_df['Luma_Revenue_Total'])
        
        with col2:
            st.metric("高校基金总额", f"{results_df['Uni_Fund_Total'].sum():.2f}")
            st.line_chart(results_df['Uni_Fund_Total'])
        
        # 收入趋势图
        st.subheader("收入趋势")
        st.markdown("""
        <small>下图展示了不同类型收入随时间的变化趋势：</small>
        - <small>**总收入**: 所有收入来源的总和</small>
        - <small>**Luma收入**: Luma公司获得的收入部分</small>
        - <small>**高校基金收入**: 高校基金获得的收入部分</small>
        """, unsafe_allow_html=True)
        
        # 创建周期列（半年序号）
        results_df = results_df.reset_index()
        results_df['half_year_period'] = [f'H{i+1}' for i in range(len(results_df))]
        
        fig = px.line(
            results_df, 
            x='half_year_period', 
            y=['Luma_Revenue_Total', 'Uni_Fund_Total'],
            labels={
                'half_year_period': '周期（半年）',
                'value': '收入 (元)',
                'variable': '收入类型'
            },
            title='收入趋势分析',
            color_discrete_map={
                'Luma_Revenue_Total': '#19A7CE',
                'Uni_Fund_Total': '#146C94' 
            }
        )
        
        # 更新图例标签
        newnames = {'Luma_Revenue_Total': '总收入', 
                   'Uni_Fund_Total': '高校基金收入'}
        
        fig.for_each_trace(lambda t: t.update(name = newnames[t.name]))
        fig.update_layout(
            legend_title_text='收入类型',
            hovermode="x unified",
            hoverlabel=dict(bgcolor="white"),
            height=450
        )
        
        # 添加网格线和标记点
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
        fig.update_traces(mode='lines+markers')
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("提示：您可以在图表上悬停鼠标查看具体数值，或者点击图例项隐藏/显示特定线条。")
    
    with tab2:
        st.header("收入结构分析")
        
        st.markdown("""
        <small>本页面展示了收入的详细构成分析，帮助您了解不同来源的收入贡献和比例。</small>
        """, unsafe_allow_html=True)
        
        # 创建收入来源分解图表
        st.subheader("Luma收入来源分解")
        
        # 准备收入来源数据
        luma_revenue_sources = [
            '固定接入费 (新签)', 
            '学生付费分成 (新签)', 
            '学生付费分成 (续约)'
        ]
        
        # 创建收入来源数据框
        luma_revenue_df = pd.DataFrame({
            '收入来源': luma_revenue_sources,
            '金额': [
                results_df['Luma_Fixed_Fee_New'].sum(),
                results_df['Luma_Student_Share_New'].sum(),
                results_df['Luma_Student_Share_Renewed'].sum()
            ]
        })
        
        # 创建饼图
        fig1 = px.pie(
            luma_revenue_df, 
            values='金额', 
            names='收入来源',
            title='Luma收入来源分布',
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)
        
        # 解释说明
        st.markdown("""
        <small>**收入来源解释**：</small>
        - <small>**固定接入费 (新签)**：来自新签约高校的一次性固定接入费</small>
        - <small>**学生付费分成 (新签)**：来自新签约高校学生的付费分成</small>
        - <small>**学生付费分成 (续约)**：来自续约高校学生的付费分成</small>
        """, unsafe_allow_html=True)
        
        # 按高校类型分析
        st.subheader("按高校合作模式分析")
        
        # 提取各模式收入数据
        mode_columns = [col for col in results_df.columns if col.startswith('Luma_Revenue_Type') and ('_New' in col or '_Renewed' in col)]
        if mode_columns:
            # 合并各模式的新签和续约收入
            mode_summary = {}
            for col in mode_columns:
                mode_type = col.split('_')[2]  # 提取Type1, Type2a等
                if mode_type not in mode_summary:
                    mode_summary[mode_type] = 0
                mode_summary[mode_type] += results_df[col].sum()
            
            # 创建模式收入数据框
            mode_df = pd.DataFrame({
                '合作模式': list(mode_summary.keys()),
                '收入贡献': list(mode_summary.values())
            })
            
            # 创建条形图
            fig2 = px.bar(
                mode_df,
                x='合作模式',
                y='收入贡献',
                title='各合作模式收入贡献',
                color='合作模式',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # 解释说明
            st.markdown("""
            <small>**商业模式说明**：</small>
            - <small>**模式A**：高校付费 + 学生免费使用全部功能（无学生付费分成）</small>
            - <small>**模式B**：高校付费 + 学生分层付费（Luma与高校按比例分成学生付费）</small>
            - <small>**模式C**：高校免费 + 学生分层付费（Luma与高校按比例分成学生付费）</small>
            """, unsafe_allow_html=True)
        else:
            st.warning("未找到合作模式相关的收入数据列，请确认模型输出格式是否正确。")
        
        # 新签与续约收入对比
        st.subheader("新签与续约收入对比")
        new_vs_renewed = pd.DataFrame({
            '收入类型': ['新签收入', '续约收入'],
            '金额': [
                results_df['Luma_Fixed_Fee_New'].sum() + results_df['Luma_Student_Share_New'].sum(),
                results_df['Luma_Student_Share_Renewed'].sum()
            ]
        })
        
        fig3 = px.bar(
            new_vs_renewed,
            x='收入类型',
            y='金额',
            title='新签与续约收入对比',
            color='收入类型',
            color_discrete_sequence=['#19A7CE', '#146C94']
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # 添加交互提示
        st.info("提示：您可以在图表上悬停鼠标查看具体数值，或者点击图例项隐藏/显示特定数据。图表支持缩放和下载等操作。")
    
    # 敏感性分析功能已移至单独页面
else:
    st.info("请在左侧设置参数并点击'运行模型'按钮开始分析。")

# 页脚
st.markdown("---")
st.markdown("© 2025 Luma高校销售与收益分析模型 | Zhaojiu Tech Inc. All rights reserved.")
