#!/usr/bin/env python
"""
查看策略分析结果
"""

import pandas as pd
import os


def view_results():
    """查看策略分析结果"""
    
    print("=" * 80)
    print(" " * 25 + "恒瑞医药 PE回撤策略 - 结果概览")
    print("=" * 80)
    
    # 读取增强版Excel文件
    file_path = 'report/strategy_trades_enhanced.xlsx'
    
    if not os.path.exists(file_path):
        print("错误：请先运行 python run_full_analysis.py 生成分析结果")
        return
    
    # 读取数据（跳过单位行）
    df = pd.read_excel(file_path, header=0)
    df = df.iloc[1:].reset_index(drop=True)
    
    # 确保数值列的类型正确
    numeric_columns = ['股价', '现金流出', '现金流入', '净现金流', '当前市值', '总资产', '总资产收益率']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 1. 交易统计
    buy_trades = df[df['操作'] == 'BUY']
    sell_trades = df[df['操作'] == 'SELL']
    
    print("\n📊 交易统计")
    print("-" * 40)
    print(f"  买入次数: {len(buy_trades)}次")
    print(f"  卖出次数: {len(sell_trades)}次")
    print(f"  总交易次数: {len(buy_trades) + len(sell_trades)}次")
    
    # 2. 资金流动
    last_row = df.iloc[-1]
    print("\n💰 资金流动")
    print("-" * 40)
    print(f"  期初现金: {df['期初现金'].iloc[0]:,.0f}元")
    print(f"  现金流出: {last_row['现金流出']:,.0f}元（累计买入）")
    print(f"  现金流入: {last_row['现金流入']:,.0f}元（累计卖出）")
    print(f"  净现金流: {last_row['净现金流']:,.0f}元")
    print(f"  当前市值: {last_row['当前市值']:,.0f}元")
    
    # 3. 收益情况
    print("\n📈 收益情况")
    print("-" * 40)
    print(f"  最终总资产: {last_row['总资产']:,.0f}元")
    print(f"  总收益: {last_row['总收益']:,.0f}元")
    print(f"  总资产收益率: {last_row['总资产收益率']:.2f}%")
    
    # 4. 风险指标
    max_return = df['总资产收益率'].max()
    min_return = df['总资产收益率'].min()
    max_drawdown = min_return if min_return < 0 else 0
    
    print("\n⚠️ 风险指标")
    print("-" * 40)
    print(f"  最高收益率: {max_return:.2f}%")
    print(f"  最低收益率: {min_return:.2f}%")
    print(f"  最大回撤: {max_drawdown:.2f}%")
    
    # 5. 关键时点
    print("\n📅 关键时点")
    print("-" * 40)
    
    # 第一次买入
    first_buy = buy_trades.iloc[0]
    print(f"  首次买入: {first_buy['日期']} (股价: {first_buy['股价']:.2f}元)")
    
    # 最后一次交易
    trades_only = df[df['操作'].isin(['BUY', 'SELL'])]
    if len(trades_only) > 0:
        last_trade = trades_only.iloc[-1]
        print(f"  最后交易: {last_trade['日期']} ({last_trade['操作']}, 股价: {last_trade['股价']:.2f}元)")
    
    # 收益率最高点
    max_idx = df['总资产收益率'].idxmax()
    max_row = df.iloc[max_idx]
    print(f"  收益最高: {max_row['日期']} (收益率: {max_row['总资产收益率']:.2f}%, 股价: {max_row['股价']:.2f}元)")
    
    # 当前状态
    print(f"  当前日期: {last_row['日期']} (股价: {last_row['股价']:.2f}元)")
    
    # 6. 持仓状态
    print("\n📦 持仓状态")
    print("-" * 40)
    print(f"  当前持仓: {last_row['总持仓']:.2f}股")
    if last_row['总持仓'] > 0:
        avg_cost = abs(last_row['现金流出'] - last_row['现金流入']) / last_row['总持仓']
        print(f"  平均成本: {avg_cost:.2f}元/股")
        print(f"  当前股价: {last_row['股价']:.2f}元")
        profit_per_share = last_row['股价'] - avg_cost
        profit_rate = (profit_per_share / avg_cost) * 100
        print(f"  每股盈亏: {profit_per_share:.2f}元 ({profit_rate:+.2f}%)")
    else:
        print(f"  状态: 已清仓")
    
    # 7. 文件清单
    print("\n📁 生成的文件")
    print("-" * 40)
    files = {
        'report/strategy_trades.xlsx': '基础交易记录',
        'report/strategy_trades_enhanced.xlsx': '增强版记录（含收益率）',
        'report/asset_curve.png': '资产曲线图',
        'report/all_in_one.png': 'PE股价综合图'
    }
    
    for file, desc in files.items():
        if os.path.exists(file):
            size = os.path.getsize(file) / 1024  # KB
            print(f"  ✓ {desc}: {file} ({size:.1f}KB)")
        else:
            print(f"  ✗ {desc}: {file} (未生成)")
    
    print("\n" + "=" * 80)
    print("提示：运行 python run_full_analysis.py 重新生成完整分析")
    print("=" * 80)


if __name__ == "__main__":
    view_results()