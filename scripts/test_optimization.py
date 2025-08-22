#!/usr/bin/env python3
"""
测试参数优化功能的简单脚本
使用模拟数据进行测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from optimization.optimizer import OptimizationConfig, ParameterRange
from optimization.grid_search import GridSearchOptimizer
from optimization.bayesian_optimizer import BayesianOptimizer
from optimization.optimization_result import OptimizationResult


def create_test_data():
    """创建测试数据"""
    print("生成模拟测试数据...")
    
    # 创建日期序列
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    n_days = len(dates)
    
    # 生成模拟数据
    np.random.seed(42)
    
    # 模拟股价（随机游走）
    returns = np.random.normal(0.0005, 0.02, n_days)
    prices = 30 * np.exp(np.cumsum(returns))
    
    # 模拟PE值（与价格相关但有噪声）
    pe_base = 30 + (prices - prices.mean()) / prices.std() * 10
    pe = pe_base + np.random.normal(0, 5, n_days)
    pe = np.clip(pe, 10, 100)
    
    # 计算回撤
    cummax = pd.Series(prices).expanding().max()
    drawdown = (prices - cummax) / cummax * 100
    
    # 创建DataFrame
    data = pd.DataFrame({
        '日期': dates,
        '收盘': prices,
        'PE': pe,
        '回撤': drawdown
    })
    
    print(f"生成数据完成: {len(data)} 条记录")
    print(f"日期范围: {data['日期'].min().date()} 至 {data['日期'].max().date()}")
    print(f"价格范围: {data['收盘'].min():.2f} 至 {data['收盘'].max():.2f}")
    print(f"PE范围: {data['PE'].min():.2f} 至 {data['PE'].max():.2f}")
    print(f"最大回撤: {data['回撤'].min():.2f}%")
    
    return data


def test_grid_search():
    """测试网格搜索优化"""
    print("\n" + "=" * 60)
    print("测试网格搜索优化")
    print("=" * 60)
    
    # 创建测试数据
    data = create_test_data()
    
    # 定义参数范围（使用较小的搜索空间以加快测试）
    parameter_ranges = {
        'buy_pe_threshold': ParameterRange('buy_pe_threshold', 40, 60, 10),
        'sell_pe_threshold': ParameterRange('sell_pe_threshold', 70, 90, 10),
        'drawdown_threshold': ParameterRange('drawdown_threshold', -0.30, -0.15, 0.05)
    }
    
    # 创建优化配置
    config = OptimizationConfig(
        parameter_ranges=parameter_ranges,
        objective='total_return',
        n_trials=20,
        n_jobs=1,
        verbose=True
    )
    
    # 运行优化
    optimizer = GridSearchOptimizer(data, config)
    best_trial = optimizer.optimize()
    
    if best_trial:
        print("\n最优参数:")
        for param, value in best_trial.parameters.items():
            if param == 'drawdown_threshold':
                print(f"  {param}: {value:.2%}")
            else:
                print(f"  {param}: {value:.2f}")
        
        print("\n最优性能:")
        for metric, value in best_trial.metrics.items():
            if 'rate' in metric or 'return' in metric or 'drawdown' in metric:
                print(f"  {metric}: {value:.2f}%")
            else:
                print(f"  {metric}: {value:.2f}")
    
    return optimizer


def test_bayesian_optimization():
    """测试贝叶斯优化"""
    print("\n" + "=" * 60)
    print("测试贝叶斯优化")
    print("=" * 60)
    
    # 创建测试数据
    data = create_test_data()
    
    # 定义参数范围
    parameter_ranges = {
        'buy_pe_threshold': ParameterRange('buy_pe_threshold', 40, 60),
        'sell_pe_threshold': ParameterRange('sell_pe_threshold', 70, 90),
        'drawdown_threshold': ParameterRange('drawdown_threshold', -0.30, -0.15)
    }
    
    # 创建优化配置
    config = OptimizationConfig(
        parameter_ranges=parameter_ranges,
        objective='sharpe_ratio',
        n_trials=15,
        n_jobs=1,
        verbose=True
    )
    
    # 运行优化
    optimizer = BayesianOptimizer(data, config)
    best_trial = optimizer.optimize()
    
    if best_trial:
        print("\n最优参数:")
        for param, value in best_trial.parameters.items():
            if param == 'drawdown_threshold':
                print(f"  {param}: {value:.2%}")
            else:
                print(f"  {param}: {value:.2f}")
        
        print("\n最优性能:")
        for metric, value in best_trial.metrics.items():
            if 'rate' in metric or 'return' in metric or 'drawdown' in metric:
                print(f"  {metric}: {value:.2f}%")
            else:
                print(f"  {metric}: {value:.2f}")
    
    return optimizer


def test_visualization():
    """测试可视化功能"""
    print("\n" + "=" * 60)
    print("测试结果可视化")
    print("=" * 60)
    
    # 运行一个小规模优化
    data = create_test_data()
    
    parameter_ranges = {
        'buy_pe_threshold': ParameterRange('buy_pe_threshold', 45, 55, 5),
        'sell_pe_threshold': ParameterRange('sell_pe_threshold', 75, 85, 5),
        'drawdown_threshold': ParameterRange('drawdown_threshold', -0.25, -0.20, 0.05)
    }
    
    config = OptimizationConfig(
        parameter_ranges=parameter_ranges,
        objective='total_return',
        n_trials=10,
        verbose=False
    )
    
    optimizer = GridSearchOptimizer(data, config)
    optimizer.optimize()
    
    # 生成报告
    result = OptimizationResult(optimizer=optimizer)
    
    # 创建输出目录
    output_dir = './test_optimization_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成可视化
    print("\n生成优化历史图表...")
    result.plot_optimization_history(save_path=os.path.join(output_dir, 'optimization_history.png'))
    
    print("生成参数重要性分析图表...")
    result.plot_parameter_importance(save_path=os.path.join(output_dir, 'parameter_importance.png'))
    
    print("生成完整报告...")
    report_dir = result.generate_report(output_dir)
    
    print(f"\n所有结果已保存到: {report_dir}")
    
    return result


def main():
    """主测试函数"""
    print("=" * 80)
    print("                   参数优化模块测试")
    print("=" * 80)
    
    # 测试网格搜索
    grid_optimizer = test_grid_search()
    
    # 测试贝叶斯优化
    bayesian_optimizer = test_bayesian_optimization()
    
    # 测试可视化
    result = test_visualization()
    
    print("\n" + "=" * 80)
    print("所有测试完成！")
    print("=" * 80)
    
    # 显示摘要
    print("\n测试摘要:")
    print(f"  网格搜索试验数: {len(grid_optimizer.trials)}")
    print(f"  贝叶斯优化试验数: {len(bayesian_optimizer.trials)}")
    print("  可视化报告已生成")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)