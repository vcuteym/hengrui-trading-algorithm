#!/usr/bin/env python
"""
参数优化脚本
对买入PE、卖出PE和回撤比例进行网格搜索优化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from itertools import product
from typing import Dict, List, Tuple
import json
from datetime import datetime
from tqdm import tqdm

from data.reader import DataReader
from strategy.trading_strategy import TradingStrategy, StrategyConfig


def evaluate_strategy(data: pd.DataFrame, config: StrategyConfig) -> Dict:
    """
    评估策略性能
    
    Args:
        data: 市场数据
        config: 策略配置
        
    Returns:
        性能指标字典
    """
    try:
        # 运行策略
        strategy = TradingStrategy(data, config)
        strategy.run_strategy()
        
        # 获取交易记录
        trades_df = strategy.get_trades_dataframe()
        
        if len(trades_df) == 0:
            return {
                'total_return': 0,
                'num_trades': 0,
                'num_buys': 0,
                'num_sells': 0,
                'final_profit': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'win_rate': 0
            }
        
        # 计算关键指标
        buy_trades = trades_df[trades_df['操作'] == 'BUY']
        sell_trades = trades_df[trades_df['操作'] == 'SELL']
        
        # 获取最终收益
        final_profit = trades_df['总收益'].iloc[-1] if len(trades_df) > 0 else 0
        
        # 计算所需资金（最大现金流出）
        min_cash_flow = trades_df['净现金流'].min()
        initial_capital = abs(min_cash_flow) if min_cash_flow < 0 else 10000
        
        # 计算总收益率
        total_return = (final_profit / initial_capital) * 100 if initial_capital > 0 else 0
        
        # 计算最大回撤
        cumulative_returns = trades_df['总收益'].values
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / np.maximum(peak, 1)
        max_drawdown = drawdown.min() * 100
        
        # 计算胜率（卖出时盈利的比例）
        win_rate = 0
        if len(sell_trades) > 0:
            profitable_sells = 0
            for i, sell in sell_trades.iterrows():
                if sell['总收益'] > 0:
                    profitable_sells += 1
            win_rate = (profitable_sells / len(sell_trades)) * 100
        
        # 计算夏普比率（简化版）
        if len(trades_df) > 1:
            returns = trades_df['总收益'].diff().dropna()
            if len(returns) > 0 and returns.std() > 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': total_return,
            'num_trades': len(trades_df),
            'num_buys': len(buy_trades),
            'num_sells': len(sell_trades),
            'final_profit': final_profit,
            'initial_capital': initial_capital,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate
        }
    
    except Exception as e:
        print(f"策略评估出错: {e}")
        return {
            'total_return': -999,
            'num_trades': 0,
            'num_buys': 0,
            'num_sells': 0,
            'final_profit': 0,
            'initial_capital': 0,
            'max_drawdown': -100,
            'sharpe_ratio': 0,
            'win_rate': 0
        }


def grid_search_optimization(data: pd.DataFrame, param_grid: Dict) -> pd.DataFrame:
    """
    网格搜索参数优化
    
    Args:
        data: 市场数据
        param_grid: 参数搜索范围
        
    Returns:
        优化结果DataFrame
    """
    results = []
    
    # 生成所有参数组合
    param_combinations = list(product(
        param_grid['drawdown_threshold'],
        param_grid['buy_pe_threshold'],
        param_grid['sell_pe_threshold']
    ))
    
    print(f"总共需要测试 {len(param_combinations)} 种参数组合")
    
    # 使用进度条
    for params in tqdm(param_combinations, desc="参数优化进度"):
        drawdown, buy_pe, sell_pe = params
        
        # 跳过不合理的参数组合（买入PE应小于卖出PE）
        if buy_pe >= sell_pe:
            continue
        
        # 创建配置
        config = StrategyConfig(
            drawdown_threshold=drawdown,
            buy_pe_threshold=buy_pe,
            sell_pe_threshold=sell_pe
        )
        
        # 评估策略
        metrics = evaluate_strategy(data, config)
        
        # 记录结果
        result = {
            'drawdown_threshold': drawdown,
            'buy_pe_threshold': buy_pe,
            'sell_pe_threshold': sell_pe,
            **metrics
        }
        results.append(result)
    
    return pd.DataFrame(results)


def analyze_optimization_results(results_df: pd.DataFrame) -> Dict:
    """
    分析优化结果
    
    Args:
        results_df: 优化结果DataFrame
        
    Returns:
        分析结果字典
    """
    # 过滤掉无效结果
    valid_results = results_df[results_df['total_return'] > 0].copy()
    
    if len(valid_results) == 0:
        print("没有找到有效的参数组合")
        return {}
    
    # 计算综合得分（可以调整权重）
    valid_results['score'] = (
        valid_results['total_return'] * 0.4 +  # 收益率权重40%
        valid_results['sharpe_ratio'] * 10 * 0.2 +  # 夏普比率权重20%
        valid_results['win_rate'] * 0.2 +  # 胜率权重20%
        (100 + valid_results['max_drawdown']) * 0.2  # 回撤控制权重20%
    )
    
    # 排序
    valid_results = valid_results.sort_values('score', ascending=False)
    
    # 获取最佳参数
    best_params = valid_results.iloc[0]
    
    # 获取不同指标的最佳参数
    best_return = valid_results.nlargest(1, 'total_return').iloc[0]
    best_sharpe = valid_results.nlargest(1, 'sharpe_ratio').iloc[0]
    best_drawdown = valid_results.nlargest(1, 'max_drawdown').iloc[0]  # 最大回撤越大越好（负数）
    
    return {
        'best_overall': best_params.to_dict(),
        'best_return': best_return.to_dict(),
        'best_sharpe': best_sharpe.to_dict(),
        'best_drawdown': best_drawdown.to_dict(),
        'top_10': valid_results.head(10).to_dict('records')
    }


def main():
    """主函数"""
    print("=" * 80)
    print("                    参数优化 - 网格搜索")
    print("=" * 80)
    
    # 1. 读取数据
    print("\n[步骤1] 读取数据")
    print("-" * 40)
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    print(f"数据范围: {data['日期'].min()} 至 {data['日期'].max()}")
    
    # 2. 设置参数搜索范围
    print("\n[步骤2] 设置参数搜索范围")
    print("-" * 40)
    
    param_grid = {
        'drawdown_threshold': [-0.15, -0.20, -0.25, -0.30, -0.35, -0.40],  # 回撤阈值
        'buy_pe_threshold': [45, 50, 55, 60, 65],  # 买入PE阈值
        'sell_pe_threshold': [70, 75, 80, 85, 90]  # 卖出PE阈值
    }
    
    print("参数搜索范围:")
    print(f"  - 回撤阈值: {param_grid['drawdown_threshold']}")
    print(f"  - 买入PE阈值: {param_grid['buy_pe_threshold']}")
    print(f"  - 卖出PE阈值: {param_grid['sell_pe_threshold']}")
    
    # 3. 运行网格搜索
    print("\n[步骤3] 运行网格搜索优化")
    print("-" * 40)
    
    results_df = grid_search_optimization(data, param_grid)
    
    # 保存原始结果
    results_df.to_excel('report/optimization_results.xlsx', index=False)
    print(f"\n优化结果已保存至: report/optimization_results.xlsx")
    
    # 4. 分析结果
    print("\n[步骤4] 分析优化结果")
    print("-" * 40)
    
    analysis = analyze_optimization_results(results_df)
    
    if analysis:
        # 打印最佳参数
        print("\n最佳参数组合（综合评分）:")
        best = analysis['best_overall']
        print(f"  - 回撤阈值: {best['drawdown_threshold']:.2f}")
        print(f"  - 买入PE: {best['buy_pe_threshold']:.0f}")
        print(f"  - 卖出PE: {best['sell_pe_threshold']:.0f}")
        print(f"  - 总收益率: {best['total_return']:.2f}%")
        print(f"  - 交易次数: {best['num_trades']:.0f}")
        print(f"  - 最大回撤: {best['max_drawdown']:.2f}%")
        print(f"  - 综合得分: {best['score']:.2f}")
        
        print("\n最高收益率参数:")
        best_ret = analysis['best_return']
        print(f"  - 回撤阈值: {best_ret['drawdown_threshold']:.2f}")
        print(f"  - 买入PE: {best_ret['buy_pe_threshold']:.0f}")
        print(f"  - 卖出PE: {best_ret['sell_pe_threshold']:.0f}")
        print(f"  - 总收益率: {best_ret['total_return']:.2f}%")
        
        print("\n最佳风险控制参数:")
        best_dd = analysis['best_drawdown']
        print(f"  - 回撤阈值: {best_dd['drawdown_threshold']:.2f}")
        print(f"  - 买入PE: {best_dd['buy_pe_threshold']:.0f}")
        print(f"  - 卖出PE: {best_dd['sell_pe_threshold']:.0f}")
        print(f"  - 最大回撤: {best_dd['max_drawdown']:.2f}%")
        print(f"  - 总收益率: {best_dd['total_return']:.2f}%")
        
        # 保存分析结果
        with open('report/optimization_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"\n分析结果已保存至: report/optimization_analysis.json")
        
        # 保存TOP10结果
        top10_df = pd.DataFrame(analysis['top_10'])
        top10_df.to_excel('report/optimization_top10.xlsx', index=False)
        print(f"TOP10参数组合已保存至: report/optimization_top10.xlsx")
    
    print("\n" + "=" * 80)
    print("                         优化完成")
    print("=" * 80)


if __name__ == "__main__":
    main()