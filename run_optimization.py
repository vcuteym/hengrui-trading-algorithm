#!/usr/bin/env python3
"""
参数优化运行脚本
用于优化交易策略的买入PE、卖出PE和回撤比例参数
"""

import sys
import os
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.reader import DataReader
from optimization.optimizer import OptimizationConfig, ParameterRange
from optimization.grid_search import GridSearchOptimizer
from optimization.bayesian_optimizer import BayesianOptimizer
from optimization.optimization_result import OptimizationResult


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_optimization_config(config_dict: dict) -> OptimizationConfig:
    """创建优化配置"""
    # 解析参数范围
    parameter_ranges = {}
    for param_name, param_config in config_dict['parameter_ranges'].items():
        parameter_ranges[param_name] = ParameterRange(
            name=param_name,
            min_value=param_config['min'],
            max_value=param_config['max'],
            step=param_config.get('step')
        )
    
    # 创建优化配置
    opt_settings = config_dict['optimization_settings']
    
    return OptimizationConfig(
        parameter_ranges=parameter_ranges,
        objective=opt_settings['objective'],
        n_trials=opt_settings['n_trials'],
        n_jobs=opt_settings['n_jobs'],
        random_seed=opt_settings['random_seed'],
        early_stopping=opt_settings['early_stopping'],
        early_stopping_rounds=opt_settings['early_stopping_rounds'],
        verbose=opt_settings['verbose']
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行参数优化')
    parser.add_argument('--method', type=str, default='grid', 
                       choices=['grid', 'bayesian', 'both'],
                       help='优化方法：grid（网格搜索）、bayesian（贝叶斯优化）或both（两种方法）')
    parser.add_argument('--config', type=str, default='config/optimization_config.json',
                       help='配置文件路径')
    parser.add_argument('--data', type=str, default='data/恒瑞医药历史数据.xlsx',
                       help='数据文件路径')
    parser.add_argument('--n_trials', type=int, default=None,
                       help='试验次数（覆盖配置文件中的设置）')
    parser.add_argument('--objective', type=str, default=None,
                       choices=['total_return', 'sharpe_ratio', 'max_drawdown', 'profit_factor'],
                       help='优化目标（覆盖配置文件中的设置）')
    parser.add_argument('--output', type=str, default='./optimization_results',
                       help='输出目录')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("                      交易策略参数优化")
    print("=" * 80)
    
    # 加载配置
    print(f"\n加载配置文件: {args.config}")
    config_dict = load_config(args.config)
    
    # 覆盖配置（如果命令行指定了参数）
    if args.n_trials:
        config_dict['optimization_settings']['n_trials'] = args.n_trials
    if args.objective:
        config_dict['optimization_settings']['objective'] = args.objective
    
    # 创建优化配置
    opt_config = create_optimization_config(config_dict)
    
    # 加载数据
    print(f"加载数据文件: {args.data}")
    reader = DataReader(args.data)
    data = reader.read_data()
    print(f"数据加载完成，共 {len(data)} 条记录")
    print(f"数据时间范围: {data['日期'].min()} 至 {data['日期'].max()}")
    
    # 显示优化设置
    print("\n" + "-" * 40)
    print("优化设置:")
    print("-" * 40)
    print(f"优化方法: {args.method}")
    print(f"优化目标: {opt_config.objective}")
    print(f"试验次数: {opt_config.n_trials}")
    print(f"并行任务数: {opt_config.n_jobs}")
    print("\n参数搜索范围:")
    for name, param_range in opt_config.parameter_ranges.items():
        if name == 'drawdown_threshold':
            print(f"  {name}: {param_range.min_value:.1%} 至 {param_range.max_value:.1%}")
        else:
            print(f"  {name}: {param_range.min_value:.0f} 至 {param_range.max_value:.0f}")
    
    results = {}
    
    # 运行网格搜索
    if args.method in ['grid', 'both']:
        print("\n" + "=" * 60)
        print("执行网格搜索优化")
        print("=" * 60)
        
        grid_optimizer = GridSearchOptimizer(data, opt_config)
        grid_best = grid_optimizer.optimize()
        
        # 保存结果
        grid_result_file = os.path.join(args.output, f'grid_search_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        grid_optimizer.save_results(grid_result_file)
        
        results['grid'] = {
            'optimizer': grid_optimizer,
            'best_trial': grid_best,
            'result_file': grid_result_file
        }
    
    # 运行贝叶斯优化
    if args.method in ['bayesian', 'both']:
        print("\n" + "=" * 60)
        print("执行贝叶斯优化")
        print("=" * 60)
        
        bayesian_optimizer = BayesianOptimizer(data, opt_config)
        bayesian_best = bayesian_optimizer.optimize()
        
        # 保存结果
        bayesian_result_file = os.path.join(args.output, f'bayesian_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        bayesian_optimizer.save_results(bayesian_result_file)
        
        results['bayesian'] = {
            'optimizer': bayesian_optimizer,
            'best_trial': bayesian_best,
            'result_file': bayesian_result_file
        }
    
    # 生成综合报告
    print("\n" + "=" * 60)
    print("生成优化报告")
    print("=" * 60)
    
    for method_name, result in results.items():
        print(f"\n{method_name.upper()} 方法最优结果:")
        
        if result['best_trial']:
            best_params = result['best_trial'].parameters
            best_metrics = result['best_trial'].metrics
            
            print("最优参数:")
            print(f"  买入PE阈值: {best_params['buy_pe_threshold']:.2f}")
            print(f"  卖出PE阈值: {best_params['sell_pe_threshold']:.2f}")
            print(f"  回撤阈值: {best_params['drawdown_threshold']:.2%}")
            
            print("性能指标:")
            print(f"  总收益率: {best_metrics['total_return']:.2f}%")
            print(f"  年化收益率: {best_metrics['annual_return']:.2f}%")
            print(f"  夏普比率: {best_metrics['sharpe_ratio']:.2f}")
            print(f"  最大回撤: {best_metrics['max_drawdown']:.2f}%")
            print(f"  交易次数: {best_metrics['total_trades']}")
            
            # 生成详细报告
            opt_result = OptimizationResult(optimizer=result['optimizer'])
            report_dir = opt_result.generate_report(args.output)
    
    # 如果同时运行了两种方法，进行对比
    if args.method == 'both' and len(results) == 2:
        print("\n" + "=" * 60)
        print("方法对比")
        print("=" * 60)
        
        comparison_data = []
        for method_name, result in results.items():
            if result['best_trial']:
                row = {
                    '方法': method_name,
                    **result['best_trial'].parameters,
                    **result['best_trial'].metrics
                }
                comparison_data.append(row)
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            print("\n对比表格:")
            print(comparison_df.to_string())
            
            # 保存对比结果
            comparison_file = os.path.join(args.output, f'method_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            comparison_df.to_csv(comparison_file, index=False, encoding='utf-8')
            print(f"\n对比结果已保存到: {comparison_file}")
    
    print("\n" + "=" * 80)
    print("优化完成！")
    print(f"所有结果已保存到: {args.output}")
    print("=" * 80)


if __name__ == '__main__':
    main()