from data.reader import DataReader
from visualization.plotter import StockPlotter

def main():
    """简化的可视化程序 - 只生成all_in_one图表"""
    
    print("=" * 60)
    print("恒瑞医药数据可视化")
    print("=" * 60)
    
    # 读取数据
    print("\n正在读取数据...")
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    
    # 创建可视化对象
    plotter = StockPlotter(data)
    
    # 生成综合图表
    print("\n生成综合分析图表...")
    plotter.plot_all_in_one(save_path='all_in_one.png')
    
    # 数据统计
    print("\n数据统计:")
    print("-" * 40)
    
    # 检查PE分位数的缺失情况
    if 'PE分位数' in data.columns:
        pe_percentile = data['PE分位数']
        missing_count = pe_percentile.isna().sum()
        total_count = len(pe_percentile)
        valid_count = total_count - missing_count
        
        print(f"PE分位数数据:")
        print(f"  总数据点: {total_count}")
        print(f"  有效数据: {valid_count} ({valid_count/total_count*100:.1f}%)")
        print(f"  缺失数据: {missing_count} ({missing_count/total_count*100:.1f}%)")
        
        # 找出有数据的年份范围
        data_with_percentile = data[~pe_percentile.isna()]
        if len(data_with_percentile) > 0:
            first_date = data_with_percentile['日期'].min()
            last_date = data_with_percentile['日期'].max()
            print(f"  有效数据时间范围: {first_date} 至 {last_date}")
    
    # 最新数据
    latest = data.iloc[-1]
    print(f"\n最新数据 ({latest['日期']}):")
    print(f"  PE: {latest['PE']:.2f}")
    print(f"  股价: {latest['股价']:.2f} 元")
    if not pd.isna(latest['PE分位数']):
        print(f"  PE分位数: {latest['PE分位数']*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("图表已生成: all_in_one.png")
    print("=" * 60)

if __name__ == "__main__":
    import pandas as pd
    main()