#!/usr/bin/env python
"""
恒瑞医药PE回撤策略 - 完整分析流程
包括：策略回测、资产曲线计算、可视化
"""

import os
import sys
from data.reader import DataReader
from strategy.trading_strategy import TradingStrategy, StrategyConfig
from calculate_returns import calculate_asset_curve, plot_asset_curve, save_enhanced_excel
from simple_visualization import main as run_visualization
import pandas as pd


def main():
    """运行完整分析流程"""
    
    print("=" * 80)
    print(" " * 20 + "恒瑞医药 PE回撤策略 - 完整分析")
    print("=" * 80)
    
    # 1. 运行交易策略
    print("\n[步骤1] 运行交易策略")
    print("-" * 40)
    
    # 读取数据
    reader = DataReader('PE.xlsx')
    data = reader.process_data()
    print(f"数据范围: {data['日期'].min()} 至 {data['日期'].max()}")
    
    # 配置策略参数
    config = StrategyConfig(
        drawdown_threshold=-0.25,      # 回撤阈值 -25%
        buy_pe_threshold=55,            # 买入PE阈值
        sell_pe_threshold=75,           # 卖出PE阈值
        start_date='2010-07-22',        # 起始日期
        buy_amount=10000,               # 每次买入金额
        min_shares=0.01,                # 最小买入股数
        min_trade_interval_days=30,     # 最小交易间隔（天）
        sell_ratio=0.5                  # 每次卖出比例
    )
    
    # 运行策略
    strategy = TradingStrategy(data, config)
    trades_df = strategy.run_strategy()
    
    # 保存交易记录
    if len(trades_df) > 0:
        os.makedirs('report', exist_ok=True)
        
        # 保存为Excel格式
        output_file = 'report/strategy_trades.xlsx'
        with pd.ExcelWriter(output_file, engine='xlsxwriter', datetime_format='yyyy-mm-dd') as writer:
            trades_df.to_excel(writer, index=False, sheet_name='交易记录', startrow=1)
            
            workbook = writer.book
            worksheet = writer.sheets['交易记录']
            
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
            
            for col_num, value in enumerate(trades_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            units = ['', '', '元', '', '%', '股', '元', '股', '元', '元', '元', '元', '元']
            for col_num, unit in enumerate(units):
                worksheet.write(1, col_num, unit, unit_format)
            
            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 8)
            worksheet.set_column('C:M', 12)
        
        print(f"交易记录已保存至: {output_file}")
        
        # 保存CSV备份
        csv_file = 'report/strategy_trades.csv'
        trades_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"CSV备份已保存至: {csv_file}")
    
    # 打印基本统计
    if len(trades_df) > 0:
        buy_count = len(trades_df[trades_df['操作'] == 'BUY'])
        sell_count = len(trades_df[trades_df['操作'] == 'SELL'])
        final_trade = trades_df.iloc[-1]
        
        print(f"\n策略统计:")
        print(f"  买入次数: {buy_count}")
        print(f"  卖出次数: {sell_count}")
        print(f"  现金流出: {final_trade['现金流出']:.0f}元")
        print(f"  现金流入: {final_trade['现金流入']:.0f}元")
        print(f"  总收益: {final_trade['总收益']:.0f}元")
    
    # 2. 计算资产曲线和收益率
    print("\n[步骤2] 计算资产曲线和收益率")
    print("-" * 40)
    
    df_enhanced = calculate_asset_curve('report/strategy_trades.xlsx')
    
    # 3. 生成资产曲线图
    print("\n[步骤3] 生成资产曲线图")
    print("-" * 40)
    
    plot_asset_curve(df_enhanced, save_path='report/asset_curve.png')
    
    # 4. 保存增强版Excel
    print("\n[步骤4] 保存增强版Excel文件")
    print("-" * 40)
    
    save_enhanced_excel(df_enhanced, 'report/strategy_trades_enhanced.xlsx')
    
    # 5. 生成PE和股价可视化
    print("\n[步骤5] 生成PE和股价可视化")
    print("-" * 40)
    
    # 不运行整个visualization，只生成图表
    from visualization.plotter import StockPlotter
    plotter = StockPlotter(data)
    output_path = os.path.join('report', 'all_in_one.png')
    plotter.plot_all_in_one(save_path=output_path)
    print(f"综合分析图表已保存至: {output_path}")
    
    # 6. 生成最终报告
    print("\n" + "=" * 80)
    print(" " * 30 + "分析完成 - 最终报告")
    print("=" * 80)
    
    last_row = df_enhanced.iloc[-1]
    print(f"\n📊 策略表现:")
    print(f"   • 期初现金: {df_enhanced['期初现金'].iloc[0]:,.0f}元")
    print(f"   • 最终总资产: {last_row['总资产']:,.0f}元")
    print(f"   • 总资产收益率: {last_row['总资产收益率']:.2f}%")
    print(f"   • 交易次数: {buy_count}次买入，{sell_count}次卖出")
    
    print(f"\n📁 输出文件:")
    print(f"   • 交易记录: report/strategy_trades.xlsx")
    print(f"   • 增强版记录: report/strategy_trades_enhanced.xlsx")
    print(f"   • 资产曲线图: report/asset_curve.png")
    print(f"   • PE股价图: report/all_in_one.png")
    
    print("\n" + "=" * 80)
    
    return df_enhanced


if __name__ == "__main__":
    main()