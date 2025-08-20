from data.reader import DataReader
import pandas as pd

def test_drawdown():
    """测试回撤计算功能"""
    
    print("=" * 60)
    print("测试回撤计算功能")
    print("=" * 60)
    
    # 读取数据
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    
    # 检查回撤列是否存在
    if '回撤' not in data.columns:
        print("❌ 回撤列不存在")
        return
    
    print("\n✅ 回撤列已生成")
    
    # 显示回撤统计
    print("\n回撤统计信息:")
    print(f"  最大回撤: {data['回撤'].min():.2f}%")
    print(f"  最小回撤: {data['回撤'].max():.2f}%")
    print(f"  平均回撤: {data['回撤'].mean():.2f}%")
    print(f"  中位数回撤: {data['回撤'].median():.2f}%")
    
    # 找出最大回撤的时间点
    max_drawdown_idx = data['回撤'].idxmin()
    max_drawdown_row = data.loc[max_drawdown_idx]
    print(f"\n最大回撤详情:")
    print(f"  日期: {max_drawdown_row['日期']}")
    print(f"  回撤: {max_drawdown_row['回撤']:.2f}%")
    print(f"  股价: {max_drawdown_row['股价']:.2f}")
    print(f"  一年内最高价: {max_drawdown_row['一年内最高价']:.2f}")
    
    # 显示最近10个交易日的回撤
    print("\n最近10个交易日的回撤:")
    recent_data = data.tail(10)[['日期', '股价', '一年内最高价', '回撤']]
    for idx, row in recent_data.iterrows():
        print(f"  {row['日期'].strftime('%Y-%m-%d')}: "
              f"股价={row['股价']:.2f}, "
              f"最高价={row['一年内最高价']:.2f}, "
              f"回撤={row['回撤']:.2f}%")
    
    # 统计不同回撤区间的数量
    print("\n回撤分布:")
    bins = [0, -5, -10, -20, -30, -40, -50, -100]
    labels = ['0~-5%', '-5~-10%', '-10~-20%', '-20~-30%', '-30~-40%', '-40~-50%', '<-50%']
    data['回撤区间'] = pd.cut(data['回撤'], bins=bins[::-1], labels=labels[::-1])
    distribution = data['回撤区间'].value_counts()
    
    for interval in labels:
        count = distribution.get(interval, 0)
        percentage = count / len(data) * 100
        print(f"  {interval}: {count} ({percentage:.1f}%)")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_drawdown()