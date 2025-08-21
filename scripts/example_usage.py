import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.reader import DataReader


def main():
    """演示数据读取器的使用"""
    
    # 创建数据读取器实例
    reader = DataReader('PE.xlsx')
    
    # 执行完整的数据处理流程
    print("开始处理PE.xlsx数据...")
    processed_data = reader.process_data()
    
    # 获取数据摘要
    summary = reader.get_summary()
    
    print("\n" + "="*60)
    print("数据处理完成！")
    print("="*60)
    
    # 显示数据概览
    print(f"\n数据形状: {processed_data.shape[0]} 行 x {processed_data.shape[1]} 列")
    print(f"\n列信息:")
    for col in processed_data.columns:
        dtype = processed_data[col].dtype
        print(f"  - {col}: {dtype}")
    
    # 显示前10行数据
    print("\n前10行数据预览:")
    print(processed_data.head(10))
    
    # 显示数值列的统计信息
    print("\n数值列统计信息:")
    for col, stats in summary['基本统计'].items():
        print(f"\n{col}:")
        print(f"  均值: {stats['均值']:.2f}")
        print(f"  标准差: {stats['标准差']:.2f}")
        print(f"  最小值: {stats['最小值']:.2f}")
        print(f"  最大值: {stats['最大值']:.2f}")
        print(f"  中位数: {stats['中位数']:.2f}")
    
    # 检查缺失值
    missing_count = processed_data.isnull().sum().sum()
    print(f"\n缺失值总数: {missing_count}")
    
    # 保存处理后的数据（可选）
    # processed_data.to_csv('processed_data.csv', index=False)
    # print("\n处理后的数据已保存至 processed_data.csv")
    
    return processed_data


if __name__ == "__main__":
    data = main()