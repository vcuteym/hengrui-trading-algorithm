import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from data.reader import DataReader


def test_data_reader_initialization():
    """测试DataReader初始化"""
    reader = DataReader('PE.xlsx')
    assert reader.file_path == Path('PE.xlsx')
    assert reader.data is None
    assert reader.processed_data is None
    print("✓ 初始化测试通过")


def test_read_data():
    """测试数据读取功能"""
    reader = DataReader('PE.xlsx')
    
    try:
        data = reader.read_data()
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        print(f"✓ 数据读取测试通过，读取到 {len(data)} 行数据")
        return True
    except FileNotFoundError:
        print("⚠ PE.xlsx 文件不存在，跳过读取测试")
        return False


def test_fill_missing_values():
    """测试缺失值处理"""
    reader = DataReader('PE.xlsx')
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'col1': [1, np.nan, 3, np.nan, 5],
        'col2': [np.nan, 2, np.nan, 4, 5],
        'col3': [1, 2, 3, 4, 5]
    })
    
    filled_data = reader.fill_missing_values(test_data)
    
    # 验证没有缺失值
    assert filled_data.isnull().sum().sum() == 0
    
    # 验证填充逻辑
    assert filled_data['col1'].tolist() == [1, 1, 3, 3, 5]
    assert filled_data['col2'].tolist() == [2, 2, 2, 4, 5]
    
    print("✓ 缺失值处理测试通过")


def test_rename_columns():
    """测试列重命名功能"""
    reader = DataReader('PE.xlsx')
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'PE-TTM-S': [10, 20, 30],
        '投数网前复权': [100, 200, 300],
        '分位点': [0.1, 0.5, 0.9],
        '其他列': [1, 2, 3]
    })
    
    renamed_data = reader.rename_columns(test_data)
    
    # 验证重命名
    assert 'PE' in renamed_data.columns
    assert '股价' in renamed_data.columns
    assert 'PE分位数' in renamed_data.columns
    assert '其他列' in renamed_data.columns  # 未映射的列保持原名
    
    print("✓ 列重命名测试通过")


def test_process_data():
    """测试完整的数据处理流程"""
    reader = DataReader('PE.xlsx')
    
    if reader.file_path.exists():
        processed_data = reader.process_data()
        
        # 验证数据处理结果
        assert processed_data is not None
        assert isinstance(processed_data, pd.DataFrame)
        assert processed_data.isnull().sum().sum() == 0  # 无缺失值
        
        print(f"✓ 完整数据处理测试通过")
        print(f"  处理后数据形状: {processed_data.shape}")
        print(f"  列名: {list(processed_data.columns)[:5]}...")  # 显示前5个列名
        
        return processed_data
    else:
        print("⚠ PE.xlsx 文件不存在，跳过完整处理测试")
        return None


def test_get_summary():
    """测试数据摘要功能"""
    reader = DataReader('PE.xlsx')
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'PE': [10, 20, 30, 40, 50],
        '股价': [100, 200, 300, 400, 500],
        '文本列': ['A', 'B', 'C', 'D', 'E']
    })
    reader.processed_data = test_data
    
    summary = reader.get_summary()
    
    # 验证摘要结构
    assert '数据形状' in summary
    assert '列名' in summary
    assert '数据类型' in summary
    assert '基本统计' in summary
    
    # 验证统计信息
    assert 'PE' in summary['基本统计']
    assert '均值' in summary['基本统计']['PE']
    assert summary['基本统计']['PE']['均值'] == 30
    
    print("✓ 数据摘要测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行数据读取器测试")
    print("=" * 50)
    
    test_data_reader_initialization()
    test_fill_missing_values()
    test_rename_columns()
    
    # 测试实际文件操作
    if test_read_data():
        processed_data = test_process_data()
        if processed_data is not None:
            # 使用实际数据测试摘要
            reader = DataReader('PE.xlsx')
            reader.processed_data = processed_data
            summary = reader.get_summary()
            print(f"\n实际数据摘要:")
            print(f"  数据形状: {summary['数据形状']}")
            print(f"  数值列数量: {len(summary['基本统计'])}")
    
    test_get_summary()
    
    print("\n" + "=" * 50)
    print("所有测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()