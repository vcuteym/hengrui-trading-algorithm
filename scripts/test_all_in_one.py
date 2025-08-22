import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.reader import DataReader
from visualization.plotter import StockPlotter
import matplotlib.pyplot as plt


def main():
    """测试综合图表功能"""
    
    print("正在读取数据...")
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    
    print("\n生成综合图表...")
    plotter = StockPlotter(data)
    
    # 生成并显示综合图表
    fig = plotter.plot_all_in_one(figsize=(16, 12))
    plt.show()
    
    # 保存综合图表
    plotter.plot_all_in_one(save_path='all_in_one_chart.png')
    print("\n综合图表已保存为 all_in_one_chart.png")
    
    # 获取数据摘要
    latest = data.iloc[-1]
    print(f"\n数据摘要:")
    print(f"  最新日期: {latest['日期']}")
    print(f"  当前PE: {latest['PE']:.2f}")
    print(f"  当前股价: {latest['股价']:.2f} 元")
    print(f"  PE均值: {data['PE'].mean():.2f}")
    print(f"  PE中位数: {data['PE'].median():.2f}")


if __name__ == "__main__":
    main()