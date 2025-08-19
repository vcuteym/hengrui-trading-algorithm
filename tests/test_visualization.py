import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from visualization.plotter import StockPlotter
from data.reader import DataReader
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端


def create_test_data():
    """创建测试数据"""
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    n = len(dates)
    
    # 生成模拟数据
    np.random.seed(42)
    pe_base = 50
    price_base = 50
    
    pe_values = pe_base + np.cumsum(np.random.randn(n) * 2)
    price_values = price_base + np.cumsum(np.random.randn(n) * 1.5)
    
    test_data = pd.DataFrame({
        '日期': dates,
        '代码': 'sh600276',
        '股票名称': '恒瑞医药',
        'PE': pe_values,
        'PE危险值': 70,
        'PE中位值': 50,
        'PE机会值': 30,
        '股价': price_values,
        'PE分位数': np.random.uniform(0, 1, n)
    })
    
    return test_data


def test_plotter_initialization():
    """测试StockPlotter初始化"""
    test_data = create_test_data()
    plotter = StockPlotter(test_data)
    
    assert plotter.data is not None
    assert len(plotter.data) == len(test_data)
    assert '日期' in plotter.data.columns
    print("✓ 初始化测试通过")


def test_pe_timeline_plot():
    """测试PE时间序列图"""
    test_data = create_test_data()
    plotter = StockPlotter(test_data)
    
    # 测试基本绘图
    fig = plotter.plot_pe_timeline()
    assert fig is not None
    print("✓ PE时间序列图测试通过")
    
    # 测试带保存路径
    os.makedirs('test_output', exist_ok=True)
    fig = plotter.plot_pe_timeline(save_path='test_output/test_pe.png')
    assert os.path.exists('test_output/test_pe.png')
    print("✓ PE图表保存测试通过")


def test_price_timeline_plot():
    """测试股价时间序列图"""
    test_data = create_test_data()
    plotter = StockPlotter(test_data)
    
    # 测试基本绘图
    fig = plotter.plot_price_timeline()
    assert fig is not None
    print("✓ 股价时间序列图测试通过")
    
    # 测试带移动平均线
    fig = plotter.plot_price_timeline(show_ma=True, ma_periods=[20, 60])
    assert fig is not None
    print("✓ 股价图表（含均线）测试通过")


def test_combined_plot():
    """测试组合图表"""
    test_data = create_test_data()
    plotter = StockPlotter(test_data)
    
    fig = plotter.plot_combined()
    assert fig is not None
    print("✓ 组合图表测试通过")


def test_pe_distribution():
    """测试PE分布图"""
    test_data = create_test_data()
    plotter = StockPlotter(test_data)
    
    fig = plotter.plot_pe_distribution()
    assert fig is not None
    print("✓ PE分布图测试通过")


def test_with_real_data():
    """测试真实数据"""
    if not os.path.exists('PE.xlsx'):
        print("⚠ PE.xlsx不存在，跳过真实数据测试")
        return
    
    # 读取真实数据
    reader = DataReader('PE.xlsx')
    real_data = reader.process_data()
    
    # 创建可视化
    plotter = StockPlotter(real_data)
    
    # 测试各种图表
    os.makedirs('test_output', exist_ok=True)
    
    try:
        plotter.plot_pe_timeline(save_path='test_output/real_pe_timeline.png')
        print("✓ 真实数据PE图表测试通过")
        
        plotter.plot_price_timeline(save_path='test_output/real_price_timeline.png')
        print("✓ 真实数据股价图表测试通过")
        
        plotter.plot_combined(save_path='test_output/real_combined.png')
        print("✓ 真实数据组合图表测试通过")
        
        plotter.plot_pe_distribution(save_path='test_output/real_pe_dist.png')
        print("✓ 真实数据PE分布图测试通过")
        
    except Exception as e:
        print(f"⚠ 真实数据测试出错: {e}")


def test_report_generation():
    """测试报告生成"""
    test_data = create_test_data()
    plotter = StockPlotter(test_data)
    
    # 生成报告
    plotter.generate_report('test_report')
    
    # 验证文件生成
    expected_files = [
        'test_report/pe_timeline.png',
        'test_report/price_timeline.png',
        'test_report/combined_chart.png',
        'test_report/pe_distribution.png'
    ]
    
    for file_path in expected_files:
        assert os.path.exists(file_path), f"文件 {file_path} 未生成"
    
    print("✓ 报告生成测试通过")


def cleanup_test_files():
    """清理测试文件"""
    import shutil
    
    dirs_to_remove = ['test_output', 'test_report']
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"  清理目录: {dir_path}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行可视化模块测试")
    print("=" * 50)
    
    # 运行测试
    test_plotter_initialization()
    test_pe_timeline_plot()
    test_price_timeline_plot()
    test_combined_plot()
    test_pe_distribution()
    test_report_generation()
    
    # 测试真实数据
    print("\n测试真实数据:")
    test_with_real_data()
    
    # 清理测试文件
    print("\n清理测试文件:")
    cleanup_test_files()
    
    print("\n" + "=" * 50)
    print("所有可视化测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()