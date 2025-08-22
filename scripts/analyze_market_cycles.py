"""
市场周期分析脚本
识别牛熊市区间并分析策略在不同市场环境下的表现
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
from datetime import datetime

from data.reader import DataReader
from strategy.market_cycle import MarketCycleAnalyzer

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")


def plot_market_cycles(df, cycles, save_path='report/market_cycles.png'):
    """
    绘制市场周期图
    
    Args:
        df: 市场数据
        cycles: 周期列表
        save_path: 保存路径
    """
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))
    fig.suptitle('恒瑞医药 - 牛熊市周期分析', fontsize=16, fontweight='bold')
    
    # 1. 股价走势与牛熊市区间
    ax1 = axes[0]
    ax1.plot(df['日期'], df['股价'], 'k-', linewidth=1.5, label='股价', zorder=5)
    
    # 添加牛熊市背景
    for cycle in cycles:
        color = 'lightgreen' if cycle['type'] == 'bull' else 'lightcoral'
        alpha = 0.3
        ax1.axvspan(cycle['start_date'], cycle['end_date'], 
                   alpha=alpha, color=color, label=None)
        
        # 在区间中心标注类型
        mid_date = cycle['start_date'] + (cycle['end_date'] - cycle['start_date']) / 2
        y_pos = ax1.get_ylim()[1] * 0.9
        label = f"{'牛市' if cycle['type'] == 'bull' else '熊市'}\n{cycle['duration_years']:.1f}年\n{cycle['price_change_pct']:.1f}%"
        ax1.text(mid_date, y_pos, label, 
                ha='center', va='top', fontsize=8,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    ax1.set_ylabel('股价 (元)', fontsize=12)
    ax1.set_title('股价走势与牛熊市周期', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(['股价'], loc='upper left')
    
    # 2. PE分位数与牛熊市
    ax2 = axes[1]
    ax2.plot(df['日期'], df['PE分位数'], 'b-', linewidth=1.5, label='PE分位数', zorder=5)
    
    # 添加参考线
    ax2.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='高位(80)')
    ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='中位(50)')
    ax2.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='低位(20)')
    
    # 添加牛熊市背景
    for cycle in cycles:
        color = 'lightgreen' if cycle['type'] == 'bull' else 'lightcoral'
        ax2.axvspan(cycle['start_date'], cycle['end_date'], 
                   alpha=0.2, color=color)
    
    ax2.set_ylabel('PE分位数 (%)', fontsize=12)
    ax2.set_title('PE分位数变化', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')
    ax2.set_ylim(0, 100)
    
    # 3. 回撤幅度
    ax3 = axes[2]
    ax3.fill_between(df['日期'], 0, df['回撤'], 
                     where=(df['回撤'] < 0), color='red', alpha=0.5, label='回撤')
    ax3.plot(df['日期'], df['回撤'], 'r-', linewidth=1, zorder=5)
    
    # 添加牛熊市背景
    for cycle in cycles:
        color = 'lightgreen' if cycle['type'] == 'bull' else 'lightcoral'
        ax3.axvspan(cycle['start_date'], cycle['end_date'], 
                   alpha=0.2, color=color)
    
    ax3.set_ylabel('回撤 (%)', fontsize=12)
    ax3.set_xlabel('日期', fontsize=12)
    ax3.set_title('价格回撤幅度', fontsize=14)
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='lower left')
    
    # 设置日期格式
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    print(f"市场周期图已保存至: {save_path}")
    plt.show()


def create_cycle_summary_table(cycles):
    """
    创建周期汇总表
    
    Args:
        cycles: 周期列表
        
    Returns:
        汇总DataFrame
    """
    summary_data = []
    
    for i, cycle in enumerate(cycles, 1):
        summary_data.append({
            '序号': i,
            '类型': '牛市' if cycle['type'] == 'bull' else '熊市',
            '开始日期': cycle['start_date'].strftime('%Y-%m-%d'),
            '结束日期': cycle['end_date'].strftime('%Y-%m-%d'),
            '持续时间(年)': f"{cycle['duration_years']:.1f}",
            '起始价格': f"{cycle['start_price']:.2f}",
            '结束价格': f"{cycle['end_price']:.2f}",
            '涨跌幅(%)': f"{cycle['price_change_pct']:.1f}",
            '最高价': f"{cycle['highest_price']:.2f}",
            '最低价': f"{cycle['lowest_price']:.2f}",
            '最大回撤(%)': f"{cycle['max_drawdown']:.1f}",
            '平均PE': f"{cycle['avg_pe']:.1f}",
            '平均PE分位': f"{cycle['avg_pe_percentile']:.1f}"
        })
    
    return pd.DataFrame(summary_data)


def analyze_strategy_by_cycle(cycles, trades_df):
    """
    分析策略在不同周期的表现
    
    Args:
        cycles: 周期列表
        trades_df: 交易记录
        
    Returns:
        分析结果DataFrame
    """
    if trades_df is None or len(trades_df) == 0:
        return None
        
    analysis = []
    
    for cycle in cycles:
        # 筛选该周期内的交易
        cycle_trades = trades_df[
            (trades_df['日期'] >= cycle['start_date']) &
            (trades_df['日期'] <= cycle['end_date'])
        ]
        
        if len(cycle_trades) > 0:
            # 获取周期开始和结束时的资产
            first_trade = cycle_trades.iloc[0]
            last_trade = cycle_trades.iloc[-1]
            
            # 计算收益
            if '总资产' in cycle_trades.columns:
                start_asset = first_trade['总资产']
                end_asset = last_trade['总资产']
                cycle_return = ((end_asset / start_asset) - 1) * 100 if start_asset > 0 else 0
            else:
                cycle_return = 0
            
            # 统计交易
            buy_count = len(cycle_trades[cycle_trades['操作'] == 'BUY'])
            sell_count = len(cycle_trades[cycle_trades['操作'] == 'SELL'])
            
            analysis.append({
                '周期类型': '牛市' if cycle['type'] == 'bull' else '熊市',
                '开始日期': cycle['start_date'].strftime('%Y-%m-%d'),
                '结束日期': cycle['end_date'].strftime('%Y-%m-%d'),
                '市场涨跌(%)': cycle['price_change_pct'],
                '策略收益(%)': cycle_return,
                '超额收益(%)': cycle_return - cycle['price_change_pct'],
                '买入次数': buy_count,
                '卖出次数': sell_count,
                '总交易次数': buy_count + sell_count
            })
    
    return pd.DataFrame(analysis) if analysis else None


def main():
    """主函数"""
    print("=" * 80)
    print("                    恒瑞医药 - 牛熊市周期分析")
    print("=" * 80)
    
    # 1. 读取数据
    print("\n[步骤1] 读取市场数据")
    print("-" * 40)
    reader = DataReader('PE.xlsx')
    df = reader.process_data()
    print(f"数据范围: {df['日期'].min()} 至 {df['日期'].max()}")
    
    # 2. 识别市场周期
    print("\n[步骤2] 识别牛熊市周期")
    print("-" * 40)
    analyzer = MarketCycleAnalyzer(min_cycle_years=2.0)
    cycles = analyzer.identify_cycles(df)
    
    print(f"共识别出 {len(cycles)} 个市场周期")
    bull_cycles = [c for c in cycles if c['type'] == 'bull']
    bear_cycles = [c for c in cycles if c['type'] == 'bear']
    print(f"  - 牛市: {len(bull_cycles)} 个")
    print(f"  - 熊市: {len(bear_cycles)} 个")
    
    # 3. 创建周期汇总表
    print("\n[步骤3] 生成周期汇总")
    print("-" * 40)
    summary_df = create_cycle_summary_table(cycles)
    print(summary_df.to_string(index=False))
    
    # 保存汇总表
    summary_df.to_excel('report/market_cycles_summary.xlsx', index=False)
    print("\n周期汇总已保存至: report/market_cycles_summary.xlsx")
    
    # 4. 绘制市场周期图
    print("\n[步骤4] 绘制市场周期图")
    print("-" * 40)
    plot_market_cycles(df, cycles)
    
    # 5. 分析策略表现（如果有交易记录）
    print("\n[步骤5] 分析策略在不同周期的表现")
    print("-" * 40)
    
    try:
        trades_df = pd.read_excel('report/strategy_trades_enhanced.xlsx')
        trades_df['日期'] = pd.to_datetime(trades_df['日期'])
        
        strategy_analysis = analyze_strategy_by_cycle(cycles, trades_df)
        if strategy_analysis is not None and len(strategy_analysis) > 0:
            print("\n策略在不同市场周期的表现:")
            print(strategy_analysis.to_string(index=False))
            
            # 保存分析结果
            strategy_analysis.to_excel('report/strategy_by_cycle.xlsx', index=False)
            print("\n策略周期分析已保存至: report/strategy_by_cycle.xlsx")
            
            # 计算汇总统计
            bull_perf = strategy_analysis[strategy_analysis['周期类型'] == '牛市']['策略收益(%)'].mean()
            bear_perf = strategy_analysis[strategy_analysis['周期类型'] == '熊市']['策略收益(%)'].mean()
            
            print("\n策略表现汇总:")
            print(f"  - 牛市平均收益: {bull_perf:.2f}%")
            print(f"  - 熊市平均收益: {bear_perf:.2f}%")
    except FileNotFoundError:
        print("未找到交易记录文件，跳过策略分析")
    
    # 6. 导出周期数据
    print("\n[步骤6] 导出周期数据")
    print("-" * 40)
    analyzer.export_cycles(cycles, 'report/market_cycles.json')
    
    print("\n" + "=" * 80)
    print("                         分析完成")
    print("=" * 80)


if __name__ == "__main__":
    main()