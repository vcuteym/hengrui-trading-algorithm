import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.reader import DataReader
from visualization.plotter import StockPlotter
import matplotlib.pyplot as plt


def main():
    """可视化示例：展示如何使用可视化模块"""
    
    print("=" * 60)
    print("恒瑞医药数据可视化示例")
    print("=" * 60)
    
    # 步骤1：读取数据
    print("\n1. 读取PE数据...")
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    
    # 步骤2：创建可视化对象
    print("\n2. 创建可视化对象...")
    plotter = StockPlotter(data)
    
    # 步骤3：生成各种图表
    print("\n3. 生成可视化图表...")
    
    # PE时间序列图
    print("   - 生成PE时间序列图...")
    fig1 = plotter.plot_pe_timeline(figsize=(14, 6), show_bands=True)
    plt.show()
    
    # 股价走势图
    print("   - 生成股价走势图...")
    fig2 = plotter.plot_price_timeline(figsize=(14, 6), show_ma=True, ma_periods=[20, 60])
    plt.show()
    
    # 组合图表
    print("   - 生成PE与股价组合图...")
    fig3 = plotter.plot_combined(figsize=(14, 10))
    plt.show()
    
    # PE分布图
    print("   - 生成PE分布图...")
    fig4 = plotter.plot_pe_distribution(figsize=(10, 6), bins=50)
    plt.show()
    
    # 步骤4：生成完整报告（保存到文件）
    print("\n4. 生成完整可视化报告...")
    plotter.generate_report(output_dir='visualization_report')
    
    # 步骤5：数据分析摘要
    print("\n5. 数据分析摘要:")
    print("-" * 40)
    
    # 获取最新数据
    latest_data = data.iloc[-1]
    print(f"最新日期: {latest_data['日期']}")
    print(f"当前PE: {latest_data['PE']:.2f}")
    print(f"当前股价: {latest_data['股价']:.2f} 元")
    
    # PE统计
    pe_stats = {
        '平均值': data['PE'].mean(),
        '中位数': data['PE'].median(),
        '标准差': data['PE'].std(),
        '最小值': data['PE'].min(),
        '最大值': data['PE'].max()
    }
    
    print("\nPE统计信息:")
    for key, value in pe_stats.items():
        print(f"  {key}: {value:.2f}")
    
    # 股价统计
    price_stats = {
        '平均值': data['股价'].mean(),
        '中位数': data['股价'].median(),
        '标准差': data['股价'].std(),
        '最小值': data['股价'].min(),
        '最大值': data['股价'].max()
    }
    
    print("\n股价统计信息:")
    for key, value in price_stats.items():
        print(f"  {key}: {value:.2f} 元")
    
    # PE估值判断
    print("\n估值分析:")
    current_pe = latest_data['PE']
    
    try:
        danger_val = float(latest_data['PE危险值'])
        median_val = float(latest_data['PE中位值'])
        chance_val = float(latest_data['PE机会值'])
        
        if current_pe >= danger_val:
            print(f"  ⚠️  当前PE ({current_pe:.2f}) 处于危险区域 (>= {danger_val:.2f})")
        elif current_pe <= chance_val:
            print(f"  ✅ 当前PE ({current_pe:.2f}) 处于机会区域 (<= {chance_val:.2f})")
        else:
            print(f"  ℹ️  当前PE ({current_pe:.2f}) 处于正常区域")
            
        # 计算PE分位数
        pe_percentile = (data['PE'] < current_pe).sum() / len(data) * 100
        print(f"  当前PE处于历史 {pe_percentile:.1f}% 分位")
        
    except:
        print("  无法进行估值判断（数据格式问题）")
    
    print("\n" + "=" * 60)
    print("可视化示例完成！")
    print("图表已保存至 visualization_report 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()