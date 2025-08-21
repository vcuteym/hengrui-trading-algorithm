import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.dates as mdates
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def calculate_asset_curve(file_path='report/strategy_trades.xlsx', data_file='PE.xlsx'):
    """
    计算收益率和资产曲线
    
    Args:
        file_path: Excel文件路径
        data_file: 原始数据文件路径（包含完整的日股价数据）
    
    Returns:
        tuple: (交易记录DataFrame, 完整日数据DataFrame)
    """
    # 读取Excel文件（跳过单位行）
    df = pd.read_excel(file_path, header=0)
    
    # 删除单位行（第一行数据）
    df = df.iloc[1:].reset_index(drop=True)
    
    # 确保数值列的类型正确
    numeric_columns = ['股价', 'PE', '回撤', '交易股数', '交易金额', '总持仓', 
                       '当前市值', '现金流出', '现金流入', '净现金流', '总收益']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 确保日期列是datetime类型
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 读取完整的日数据
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.reader import DataReader
    reader = DataReader(data_file)
    daily_data = reader.process_data()
    daily_data['日期'] = pd.to_datetime(daily_data['日期'])
    
    print("=" * 60)
    print("收益率和资产曲线计算")
    print("=" * 60)
    
    # 1. 计算期初现金（净现金流最小值的绝对值）
    min_net_cash_flow = df['净现金流'].min()
    initial_cash = abs(min_net_cash_flow)
    
    print(f"\n1. 期初现金计算:")
    print(f"   净现金流最小值: {min_net_cash_flow:.0f}元")
    print(f"   期初现金: {initial_cash:.0f}元")
    
    # 2. 计算总资产 = 期初现金 + 净现金流 + 当前市值
    df['期初现金'] = initial_cash
    df['总资产'] = initial_cash + df['净现金流'] + df['当前市值']
    
    # 3. 计算总资产收益率 = 总资产/期初现金 - 1
    df['总资产收益率'] = (df['总资产'] / initial_cash - 1) * 100
    
    # 打印关键时点的数据
    print(f"\n2. 关键时点数据:")
    print(f"   {'时间':<15} {'净现金流':>12} {'当前市值':>12} {'总资产':>12} {'收益率':>10}")
    print("   " + "-" * 65)
    
    # 第一笔交易
    first_row = df.iloc[0]
    print(f"   {first_row['日期'].strftime('%Y-%m-%d'):<15} "
          f"{first_row['净现金流']:>12.0f} "
          f"{first_row['当前市值']:>12.0f} "
          f"{first_row['总资产']:>12.0f} "
          f"{first_row['总资产收益率']:>9.2f}%")
    
    # 净现金流最低点
    min_idx = df['净现金流'].idxmin()
    min_row = df.iloc[min_idx]
    print(f"   {min_row['日期'].strftime('%Y-%m-%d'):<15} "
          f"{min_row['净现金流']:>12.0f} "
          f"{min_row['当前市值']:>12.0f} "
          f"{min_row['总资产']:>12.0f} "
          f"{min_row['总资产收益率']:>9.2f}%")
    
    # 最高点
    max_idx = df['总资产'].idxmax()
    max_row = df.iloc[max_idx]
    print(f"   {max_row['日期'].strftime('%Y-%m-%d'):<15} "
          f"{max_row['净现金流']:>12.0f} "
          f"{max_row['当前市值']:>12.0f} "
          f"{max_row['总资产']:>12.0f} "
          f"{max_row['总资产收益率']:>9.2f}%")
    
    # 最后一笔
    last_row = df.iloc[-1]
    print(f"   {last_row['日期'].strftime('%Y-%m-%d'):<15} "
          f"{last_row['净现金流']:>12.0f} "
          f"{last_row['当前市值']:>12.0f} "
          f"{last_row['总资产']:>12.0f} "
          f"{last_row['总资产收益率']:>9.2f}%")
    
    print("\n3. 最终结果:")
    print(f"   期初现金: {initial_cash:,.0f}元")
    print(f"   最终总资产: {last_row['总资产']:,.0f}元")
    print(f"   总资产收益率: {last_row['总资产收益率']:.2f}%")
    print(f"   最大回撤: {(df['总资产'].min() / initial_cash - 1) * 100:.2f}%")
    print(f"   最高收益率: {df['总资产收益率'].max():.2f}%")
    
    return df, daily_data


def plot_asset_curve(df, daily_data=None, save_path='report/asset_curve.png'):
    """
    绘制资产曲线和收益率曲线（含股价）
    
    Args:
        df: 包含资产数据的DataFrame（交易记录）
        daily_data: 完整的日数据DataFrame（包含每日股价）
        save_path: 图表保存路径
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('恒瑞医药 PE回撤策略 - 资产曲线分析', fontsize=16, fontweight='bold')
    
    # 1. 总资产曲线
    ax1 = axes[0]
    ax1.plot(df['日期'], df['总资产'], 'b-', linewidth=2, label='总资产')
    ax1.axhline(y=df['期初现金'].iloc[0], color='gray', linestyle='--', alpha=0.5, label='期初现金')
    ax1.fill_between(df['日期'], df['期初现金'].iloc[0], df['总资产'], 
                      where=(df['总资产'] >= df['期初现金'].iloc[0]), 
                      color='green', alpha=0.1, label='盈利区域')
    ax1.fill_between(df['日期'], df['期初现金'].iloc[0], df['总资产'], 
                      where=(df['总资产'] < df['期初现金'].iloc[0]), 
                      color='red', alpha=0.1, label='亏损区域')
    
    # 标记买卖点
    buy_points = df[df['操作'] == 'BUY']
    sell_points = df[df['操作'] == 'SELL']
    ax1.scatter(buy_points['日期'], buy_points['总资产'], 
                color='green', marker='^', s=30, alpha=0.6, label='买入')
    ax1.scatter(sell_points['日期'], sell_points['总资产'], 
                color='red', marker='v', s=30, alpha=0.6, label='卖出')
    
    ax1.set_ylabel('总资产（元）', fontsize=12)
    ax1.set_title('总资产曲线', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/10000:.0f}万'))
    
    # 2. 收益率曲线 + 股价（双Y轴）
    ax2 = axes[1]
    
    # 左Y轴：收益率
    ax2.plot(df['日期'], df['总资产收益率'], 'r-', linewidth=2, label='总资产收益率', zorder=5)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.fill_between(df['日期'], 0, df['总资产收益率'], 
                      where=(df['总资产收益率'] >= 0), 
                      color='green', alpha=0.2)
    ax2.fill_between(df['日期'], 0, df['总资产收益率'], 
                      where=(df['总资产收益率'] < 0), 
                      color='red', alpha=0.2)
    
    ax2.set_xlabel('日期', fontsize=12)
    ax2.set_ylabel('总资产收益率（%）', fontsize=12, color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    ax2.set_title('总资产收益率与股价走势', fontsize=14)
    ax2.grid(True, alpha=0.3)
    
    # 右Y轴：股价
    ax2_twin = ax2.twinx()
    
    # 如果有完整的日数据，使用它；否则使用交易记录中的股价
    if daily_data is not None:
        # 筛选出策略期间的数据
        start_date = df['日期'].min()
        end_date = df['日期'].max()
        daily_subset = daily_data[(daily_data['日期'] >= start_date) & (daily_data['日期'] <= end_date)]
        ax2_twin.plot(daily_subset['日期'], daily_subset['股价'], 'b-', linewidth=1, alpha=0.6, label='股价（日线）')
    else:
        ax2_twin.plot(df['日期'], df['股价'], 'b-', linewidth=1.5, alpha=0.7, label='股价')
    
    ax2_twin.set_ylabel('股价（元）', fontsize=12, color='b')
    ax2_twin.tick_params(axis='y', labelcolor='b')
    
    # 在股价曲线上标记买卖点
    ax2_twin.scatter(buy_points['日期'], buy_points['股价'], 
                     color='green', marker='^', s=40, alpha=0.8, zorder=10, label='买入点')
    ax2_twin.scatter(sell_points['日期'], sell_points['股价'], 
                     color='red', marker='v', s=40, alpha=0.8, zorder=10, label='卖出点')
    
    # 添加关键点标注（收益率）
    max_return_idx = df['总资产收益率'].idxmax()
    max_return_date = df.iloc[max_return_idx]['日期']
    max_return_value = df.iloc[max_return_idx]['总资产收益率']
    max_price = df.iloc[max_return_idx]['股价']
    
    ax2.annotate(f'最高收益: {max_return_value:.1f}%\n股价: {max_price:.1f}元', 
                 xy=(max_return_date, max_return_value),
                 xytext=(10, 10), textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    # 最终收益率和股价
    final_return = df.iloc[-1]['总资产收益率']
    final_date = df.iloc[-1]['日期']
    final_price = df.iloc[-1]['股价']
    
    ax2.annotate(f'最终收益: {final_return:.1f}%\n股价: {final_price:.1f}元', 
                 xy=(final_date, final_return),
                 xytext=(-80, 30), textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.3),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    # 合并图例
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    # 设置日期格式
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    print(f"\n资产曲线图已保存至: {save_path}")
    plt.show()
    
    return fig


def save_enhanced_excel(df, output_path='report/strategy_trades_enhanced.xlsx'):
    """
    保存增强版的Excel文件，包含资产曲线数据
    
    Args:
        df: 包含所有数据的DataFrame
        output_path: 输出文件路径
    """
    with pd.ExcelWriter(output_path, engine='xlsxwriter', datetime_format='yyyy-mm-dd') as writer:
        # 从第二行开始写入数据，为单位行留出空间
        df.to_excel(writer, index=False, sheet_name='交易记录', startrow=1)
        
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
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # 写入单位行（第二行）
        units = ['', '', '元', '', '%', '股', '元', '股', '元', '元', '元', '元', '元', '元', '元', '%']
        for col_num, unit in enumerate(units[:len(df.columns)]):
            worksheet.write(1, col_num, unit, unit_format)
        
        # 设置列宽
        worksheet.set_column('A:A', 12)  # 日期列
        worksheet.set_column('B:B', 8)   # 操作列
        worksheet.set_column('C:P', 12)  # 其他列
        
        # 添加条件格式（收益率为正显示绿色，为负显示红色）
        worksheet.conditional_format(2, df.columns.get_loc('总资产收益率'), 
                                    len(df)+1, df.columns.get_loc('总资产收益率'),
                                    {'type': 'cell',
                                     'criteria': '>',
                                     'value': 0,
                                     'format': workbook.add_format({'font_color': 'green'})})
        
        worksheet.conditional_format(2, df.columns.get_loc('总资产收益率'), 
                                    len(df)+1, df.columns.get_loc('总资产收益率'),
                                    {'type': 'cell',
                                     'criteria': '<',
                                     'value': 0,
                                     'format': workbook.add_format({'font_color': 'red'})})
    
    print(f"增强版Excel文件已保存至: {output_path}")


def main():
    """主函数"""
    # 计算资产曲线
    df, daily_data = calculate_asset_curve('report/strategy_trades.xlsx')
    
    # 绘制资产曲线图（传入完整的日数据）
    plot_asset_curve(df, daily_data)
    
    # 保存增强版Excel
    save_enhanced_excel(df)
    
    print("\n" + "=" * 60)
    print("计算完成！")
    print("=" * 60)
    
    return df


if __name__ == "__main__":
    main()