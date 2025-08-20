from data.reader import DataReader
from strategy.trading_strategy import TradingStrategy, StrategyConfig
import pandas as pd


def main():
    """运行交易策略"""
    
    print("=" * 60)
    print("恒瑞医药 PE回撤交易策略")
    print("=" * 60)
    
    # 1. 读取数据
    print("\n1. 读取数据...")
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    print(f"   数据范围: {data['日期'].min()} 至 {data['日期'].max()}")
    
    # 2. 配置策略参数（可以根据需要修改）
    config = StrategyConfig(
        drawdown_threshold=-0.25,      # 参数1：回撤阈值 -25%
        buy_pe_threshold=55,            # 参数2：买入PE阈值
        sell_pe_threshold=75,           # 参数3：卖出PE阈值
        start_date='2010-07-22',        # 参数4：起始日期
        buy_amount=10000,               # 每次买入金额
        min_shares=0.01,                # 最小买入股数
        min_trade_interval_days=30,     # 最小交易间隔（天）
        sell_ratio=0.5                  # 每次卖出比例
    )
    
    print("\n2. 策略参数配置:")
    print(f"   起始日期: {config.start_date}")
    print(f"   回撤阈值: {config.drawdown_threshold * 100:.0f}%")
    print(f"   买入PE阈值: {config.buy_pe_threshold}")
    print(f"   卖出PE阈值: {config.sell_pe_threshold}")
    print(f"   每次买入金额: {config.buy_amount}元")
    print(f"   卖出比例: {config.sell_ratio * 100:.0f}%")
    print(f"   最小交易间隔: {config.min_trade_interval_days}天")
    
    # 3. 运行策略
    print("\n3. 运行策略...")
    strategy = TradingStrategy(data, config)
    trades_df = strategy.run_strategy()
    
    # 4. 打印详细报告
    strategy.print_report()
    
    # 5. 保存交易记录到文件
    if len(trades_df) > 0:
        output_file = 'strategy_trades.csv'
        trades_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n交易记录已保存至: {output_file}")
    
    return trades_df


def test_different_parameters():
    """测试不同参数组合"""
    
    print("\n" + "=" * 60)
    print("测试不同参数组合")
    print("=" * 60)
    
    # 读取数据
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    
    # 测试参数组合
    test_configs = [
        # (回撤阈值, 买入PE, 卖出PE, 描述)
        (-0.20, 50, 70, "保守策略"),
        (-0.25, 55, 75, "标准策略"),
        (-0.30, 60, 80, "激进策略"),
    ]
    
    results = []
    for drawdown, buy_pe, sell_pe, desc in test_configs:
        config = StrategyConfig(
            drawdown_threshold=drawdown,
            buy_pe_threshold=buy_pe,
            sell_pe_threshold=sell_pe,
            start_date='2010-07-22'
        )
        
        strategy = TradingStrategy(data, config)
        trades_df = strategy.run_strategy()
        
        if len(trades_df) > 0:
            final_trade = trades_df.iloc[-1]
            buy_count = len(trades_df[trades_df['操作'] == 'BUY'])
            sell_count = len(trades_df[trades_df['操作'] == 'SELL'])
            
            if final_trade['总投入'] > 0:
                return_rate = (final_trade['收益'] / final_trade['总投入']) * 100
            else:
                return_rate = 0
            
            results.append({
                '策略': desc,
                '回撤阈值': f"{drawdown*100:.0f}%",
                '买入PE': buy_pe,
                '卖出PE': sell_pe,
                '买入次数': buy_count,
                '卖出次数': sell_count,
                '总投入': final_trade['总投入'],
                '最终收益': final_trade['收益'],
                '收益率': f"{return_rate:.2f}%"
            })
    
    # 打印对比结果
    print("\n策略对比结果:")
    print("-" * 100)
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    print("-" * 100)
    
    return results_df


if __name__ == "__main__":
    # 运行主策略
    trades = main()
    
    # 测试不同参数（可选）
    # test_results = test_different_parameters()