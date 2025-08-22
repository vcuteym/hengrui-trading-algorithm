import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.reader import DataReader
import pandas as pd
import numpy as np

# 读取数据
reader = DataReader('PE.xlsx')
data = reader.process_data()

# 检查PE分位数列
print("PE分位数列的数据类型:", data['PE分位数'].dtype)
print("\n前10行PE分位数:")
print(data[['日期', 'PE分位数']].head(10))

print("\n后10行PE分位数:")
print(data[['日期', 'PE分位数']].tail(10))

# 转换为数值类型并检查
pe_percentile = pd.to_numeric(data['PE分位数'], errors='coerce')
print("\n转换后的数据类型:", pe_percentile.dtype)

# 统计缺失值
null_count = pe_percentile.isnull().sum()
print(f"\n缺失值数量: {null_count} / {len(pe_percentile)} ({null_count/len(pe_percentile)*100:.1f}%)")

# 找出第一个非缺失值的位置
first_valid_idx = pe_percentile.first_valid_index()
if first_valid_idx is not None:
    print(f"\n第一个有效值位置: {first_valid_idx}")
    print(f"对应日期: {data.loc[first_valid_idx, '日期']}")
    
# 按年统计缺失情况
data['年份'] = pd.to_datetime(data['日期']).dt.year
yearly_null = data.groupby('年份').apply(lambda x: pd.to_numeric(x['PE分位数'], errors='coerce').isnull().sum())
yearly_total = data.groupby('年份').size()

print("\n各年度PE分位数缺失情况:")
for year in sorted(data['年份'].unique())[:10]:  # 显示前10年
    null_count = yearly_null.get(year, 0)
    total_count = yearly_total.get(year, 0)
    print(f"{year}: {null_count}/{total_count} 缺失 ({null_count/total_count*100:.1f}%)" if total_count > 0 else f"{year}: 无数据")