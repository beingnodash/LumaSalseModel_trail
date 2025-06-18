import pandas as pd
import os
import sys
import inspect

from luma_sales_model.financial_model import LumaFinancialModel

def main():
    """
    主函数，用于演示模型的使用。
    """
    print("--- Luma高校销售与收益分析模型 ---")

    # 1. 初始化模型 (使用默认参数)
    model = LumaFinancialModel()

    # 2. 运行模型
    results_df = model.run_model()

    # 3. 打印关键结果摘要到控制台
    print("\n--- 模型周期摘要 (控制台输出) ---")
    summary_cols = [
        'Luma_Fixed_Fee_New',
        'Luma_Student_Share_New',
        'Luma_Student_Share_Renewed',
        'Luma_Revenue_Total',
        'Uni_Fund_New_Total',
        'Uni_Fund_Renewed_Total',
        'Uni_Fund_Total'
    ]
    # 确保所有列都存在，以防某些周期没有特定类型的数据
    display_df = results_df.reindex(columns=summary_cols, fill_value=0)
    print(display_df)

    # 4. 打印总体摘要信息
    total_luma_revenue = results_df['Luma_Revenue_Total'].sum()
    total_uni_fund = results_df['Uni_Fund_Total'].sum()

    print("\n--- 总体结果摘要 ---")
    print(f"预测周期内Luma总收入: {total_luma_revenue:,.2f} 元")
    print(f"预测周期内高校基金总额: {total_uni_fund:,.2f} 元")

    # 5. 将详细结果保存到CSV文件
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    csv_filename = os.path.join(output_dir, "luma_financial_model_results.csv")
    try:
        results_df.to_csv(csv_filename)
        print(f"\n详细结果已保存到: {csv_filename}")
    except Exception as e:
        print(f"\n保存CSV文件失败: {e}")

    # 6. 打印完整的原始DataFrame (可选，可能较宽)
    # print("\n--- 完整模型计算结果 (DataFrame) ---")
    # print(results_df)

    # 7. 生成并保存图表
    print("\n--- 生成图表 ---")
    model.plot_results() # 调用新的绘图方法

    # 8. 运行敏感性分析示例
    print("\n--- 运行敏感性分析 ---")
    params_to_test = {
        'new_clients_per_half_year': [3, 5, 7], # 测试不同的每半年新签约客户数
        'renewal_rate_uni': [0.7, 0.8, 0.9],    # 测试不同的高校年度续约率
        'type2_luma_share_from_student.a': [0.4, 0.5, 0.6] # 测试模式2a下Luma的分成比例
    }
    metrics_to_track = ['Luma_Revenue_Total'] # 我们关心总收入的变化

    sensitivity_results_df = model.run_sensitivity_analysis(
        params_to_vary=params_to_test,
        output_metrics=metrics_to_track
    )

    if not sensitivity_results_df.empty:
        print("\n--- 敏感性分析结果 ---")
        print(sensitivity_results_df)
        
        sensitivity_csv_filename = os.path.join(output_dir, "luma_sensitivity_analysis_results.csv")
        try:
            sensitivity_results_df.to_csv(sensitivity_csv_filename, index=False)
            print(f"\n敏感性分析结果已保存到: {sensitivity_csv_filename}")
        except Exception as e:
            print(f"\n保存敏感性分析CSV文件失败: {e}")
    else:
        print("\n敏感性分析未返回结果或执行失败。")

if __name__ == "__main__":
    main()
