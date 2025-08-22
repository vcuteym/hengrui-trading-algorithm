#!/usr/bin/env python
"""
测试优化后的参数
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.reader import DataReader
from strategy.trading_strategy import TradingStrategy, StrategyConfig

def test_parameters():
    """测试不同参数组合"""
    
    # 读取数据
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    
    # 测试不同参数
    test_configs = [
        {
            'name': '原始参数（已更新的新规则）',
            'config': StrategyConfig(
                drawdown_threshold=-0.25,
                buy_pe_threshold=55,
                sell_pe_threshold=75
            )
        },
        {
            'name': '优化后参数（最佳综合）',
            'config': StrategyConfig(
                drawdown_threshold=-0.30,
                buy_pe_threshold=65,
                sell_pe_threshold=90
            )
        },
        {
            'name': '优化后参数（第二名）',
            'config': StrategyConfig(
                drawdown_threshold=-0.30,
                buy_pe_threshold=60,
                sell_pe_threshold=90
            )
        },
        {
            'name': '优化后参数（最佳风控）',
            'config': StrategyConfig(
                drawdown_threshold=-0.30,
                buy_pe_threshold=55,
                sell_pe_threshold=90
            )
        }
    ]
    
    print("=" * 80)
    print("                    参数测试对比")
    print("=" * 80)
    
    for test in test_configs:
        print(f"\n测试: {test['name']}")
        print("-" * 40)
        
        config = test['config']
        print(f"参数设置:")
        print(f"  - 回撤阈值: {config.drawdown_threshold}")
        print(f"  - 买入PE: {config.buy_pe_threshold}")
        print(f"  - 卖出PE: {config.sell_pe_threshold}")
        
        # 运行策略
        strategy = TradingStrategy(data, config)
        strategy.run_strategy()
        
        # 获取结果
        trades_df = strategy.get_trades_dataframe()
        
        if len(trades_df) > 0:
            buy_count = len(trades_df[trades_df['操作'] == 'BUY'])
            sell_count = len(trades_df[trades_df['操作'] == 'SELL'])
            final_profit = trades_df['总收益'].iloc[-1]
            
            # 计算期初资金
            min_cash_flow = trades_df['净现金流'].min()
            initial_capital = abs(min_cash_flow) if min_cash_flow < 0 else 10000
            
            # 计算收益率
            total_return = (final_profit / initial_capital) * 100 if initial_capital > 0 else 0
            
            print(f"\n结果:")
            print(f"  - 买入次数: {buy_count}")
            print(f"  - 卖出次数: {sell_count}")
            print(f"  - 期初资金: {initial_capital:,.0f}元")
            print(f"  - 最终收益: {final_profit:,.0f}元")
            print(f"  - 总收益率: {total_return:.2f}%")
        else:
            print("\n无交易记录")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_parameters()