import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        import os
        os.makedirs('report', exist_ok=True)
        
        # 保存为Excel格式，使用xlsxwriter引擎以正确处理日期格式
        output_file = 'report/strategy_trades.xlsx'
        with pd.ExcelWriter(output_file, engine='xlsxwriter', datetime_format='yyyy-mm-dd') as writer:
            # 从第二行开始写入数据，为单位行留出空间
            trades_df.to_excel(writer, index=False, sheet_name='交易记录', startrow=1)
            
            # 获取工作簿和工作表对象
            workbook = writer.book
            worksheet = writer.sheets['交易记录']
            
            # 添加格式
            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'bg_color': '#F0F0F0'
            })
            
            unit_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'italic': True,
                'font_size': 9,
                'bg_color': '#FAFAFA'
            })
            
            # 写入列名（第一行）
            for col_num, value in enumerate(trades_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # 写入单位行（第二行，原数据的第一行位置）
            units = ['', '', '元', '', '%', '股', '元', '股', '元', '元', '元', '元', '元']
            for col_num, unit in enumerate(units):
                worksheet.write(1, col_num, unit, unit_format)
            
            # 设置列宽
            worksheet.set_column('A:A', 12)  # 日期列
            worksheet.set_column('B:B', 8)   # 操作列
            worksheet.set_column('C:M', 12)  # 其他列（现在有13列）
            
        print(f"\n交易记录已保存至: {output_file} (Excel格式)")
        
        # 也保存一份CSV备份
        csv_file = 'report/strategy_trades.csv'
        trades_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"CSV备份已保存至: {csv_file}")
    
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
            
            if final_trade['现金流出'] > 0:
                return_rate = (final_trade['总收益'] / final_trade['现金流出']) * 100
            else:
                return_rate = 0
            
            results.append({
                '策略': desc,
                '回撤阈值': f"{drawdown*100:.0f}%",
                '买入PE': buy_pe,
                '卖出PE': sell_pe,
                '买入次数': buy_count,
                '卖出次数': sell_count,
                '现金流出': final_trade['现金流出'],
                '现金流入': final_trade['现金流入'],
                '当前市值': final_trade['当前市值'],
                '总收益': final_trade['总收益'],
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