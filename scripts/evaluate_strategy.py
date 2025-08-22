import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class StrategyEvaluator:
    """策略评估器"""
    
    def __init__(self, trades_file='report/strategy_trades_enhanced.xlsx', 
                 daily_data_file='PE.xlsx', risk_free_rate=0.03):
        """
        初始化评估器
        
        Args:
            trades_file: 交易记录文件路径
            daily_data_file: 日数据文件路径
            risk_free_rate: 无风险利率（默认3%年化）
        """
        self.risk_free_rate = risk_free_rate
        
        # 读取交易记录
        self.trades_df = pd.read_excel(trades_file, header=0)
        self.trades_df = self.trades_df.iloc[1:].reset_index(drop=True)  # 删除单位行
        
        # 确保数值列的类型正确
        numeric_columns = ['股价', '现金流出', '现金流入', '净现金流', '当前市值', 
                          '总资产', '总资产收益率', '期初现金']
        for col in numeric_columns:
            if col in self.trades_df.columns:
                self.trades_df[col] = pd.to_numeric(self.trades_df[col], errors='coerce')
        
        self.trades_df['日期'] = pd.to_datetime(self.trades_df['日期'])
        
        # 读取完整的日数据
        self.daily_data = pd.read_excel(daily_data_file)
        self.daily_data['日期'] = pd.to_datetime(self.daily_data['日期'])
        
        # 构建完整的资产曲线（每日）
        self._build_daily_asset_curve()
    
    def _build_daily_asset_curve(self):
        """构建每日资产曲线"""
        # 获取策略期间（只考虑有交易的时间段）
        trades_only = self.trades_df[self.trades_df['操作'].isin(['BUY', 'SELL'])]
        if len(trades_only) > 0:
            start_date = trades_only['日期'].min()
            end_date = self.trades_df['日期'].max()  # 包括最后的HOLD记录
        else:
            start_date = self.trades_df['日期'].min()
            end_date = self.trades_df['日期'].max()
        
        print(f"策略期间: {start_date} 至 {end_date}")
        
        # 筛选期间内的日数据并按日期排序
        self.daily_curve = self.daily_data[(self.daily_data['日期'] >= start_date) & 
                                          (self.daily_data['日期'] <= end_date)].copy()
        self.daily_curve = self.daily_curve.sort_values('日期').reset_index(drop=True)
        
        print(f"日线数据条数: {len(self.daily_curve)}")
        
        # 初始化列
        self.daily_curve['总持仓'] = 0.0
        self.daily_curve['现金流出'] = 0.0
        self.daily_curve['现金流入'] = 0.0
        self.daily_curve['当前市值'] = 0.0
        self.daily_curve['净现金流'] = 0.0
        self.daily_curve['期初现金'] = self.trades_df['期初现金'].iloc[0]
        
        # 逐日填充持仓和现金流数据
        current_shares = 0.0
        current_outflow = 0.0
        current_inflow = 0.0
        
        # 转换交易记录为查找字典以提高效率
        trade_dict = {}
        for _, trade in self.trades_df.iterrows():
            trade_date = pd.Timestamp(trade['日期']).normalize()
            trade_dict[trade_date] = trade
        
        for idx, row in self.daily_curve.iterrows():
            date = pd.Timestamp(row['日期']).normalize()
            
            # 检查当天是否有交易
            if date in trade_dict:
                trade = trade_dict[date]
                current_shares = trade['总持仓']
                current_outflow = abs(trade['现金流出'])  # 转为正数
                current_inflow = trade['现金流入']
            
            # 更新当日数据
            self.daily_curve.at[idx, '总持仓'] = current_shares
            self.daily_curve.at[idx, '现金流出'] = current_outflow
            self.daily_curve.at[idx, '现金流入'] = current_inflow
            self.daily_curve.at[idx, '当前市值'] = current_shares * row['投数网前复权']
            self.daily_curve.at[idx, '净现金流'] = current_inflow - current_outflow
            
        # 计算总资产和收益率
        self.daily_curve['总资产'] = (self.daily_curve['期初现金'] + 
                                    self.daily_curve['净现金流'] + 
                                    self.daily_curve['当前市值'])
        self.daily_curve['总资产收益率'] = ((self.daily_curve['总资产'] / 
                                         self.daily_curve['期初现金'] - 1) * 100)
        
        # 计算日收益率
        self.daily_curve['日收益率'] = self.daily_curve['总资产'].pct_change() * 100
        
    def calculate_metrics(self):
        """计算所有评估指标"""
        metrics = {}
        
        # 基础信息
        metrics['起始日期'] = self.daily_curve['日期'].min()
        metrics['结束日期'] = self.daily_curve['日期'].max()
        metrics['交易天数'] = len(self.daily_curve)
        metrics['交易年数'] = metrics['交易天数'] / 252
        
        # 收益指标
        metrics['期初现金'] = self.daily_curve['期初现金'].iloc[0]
        metrics['最终总资产'] = self.daily_curve['总资产'].iloc[-1]
        metrics['总收益'] = metrics['最终总资产'] - metrics['期初现金']
        metrics['总收益率'] = (metrics['总收益'] / metrics['期初现金']) * 100
        metrics['年化收益率'] = ((metrics['最终总资产'] / metrics['期初现金']) ** 
                              (1 / metrics['交易年数']) - 1) * 100
        
        # 风险指标
        daily_returns = self.daily_curve['日收益率'].dropna()
        metrics['日收益率均值'] = daily_returns.mean()
        metrics['日收益率标准差'] = daily_returns.std()
        metrics['年化波动率'] = metrics['日收益率标准差'] * np.sqrt(252)
        
        # 夏普比率 (年化)
        excess_return = metrics['年化收益率'] - (self.risk_free_rate * 100)
        metrics['夏普比率'] = excess_return / metrics['年化波动率'] if metrics['年化波动率'] > 0 else 0
        
        # 索提诺比率 (只考虑下行风险)
        negative_returns = daily_returns[daily_returns < 0]
        downside_std = negative_returns.std() * np.sqrt(252)
        metrics['索提诺比率'] = excess_return / downside_std if downside_std > 0 else 0
        
        # 最大回撤
        cummax = self.daily_curve['总资产'].cummax()
        drawdown = (self.daily_curve['总资产'] - cummax) / cummax * 100
        metrics['最大回撤'] = drawdown.min()
        metrics['最大回撤日期'] = self.daily_curve.loc[drawdown.idxmin(), '日期']
        
        # 回撤恢复
        if metrics['最大回撤'] < 0:
            drawdown_start_idx = drawdown[:drawdown.idxmin()].idxmax()
            if drawdown.iloc[drawdown.idxmin():].max() >= -0.01:  # 恢复到接近0
                recovery_idx = drawdown.iloc[drawdown.idxmin():][drawdown.iloc[drawdown.idxmin():] >= -0.01].index[0]
                metrics['回撤恢复天数'] = recovery_idx - drawdown.idxmin()
            else:
                metrics['回撤恢复天数'] = '未完全恢复'
        else:
            metrics['回撤恢复天数'] = 0
        
        # 卡尔玛比率 (收益/最大回撤)
        metrics['卡尔玛比率'] = abs(metrics['年化收益率'] / metrics['最大回撤']) if metrics['最大回撤'] < 0 else float('inf')
        
        # 胜率统计
        positive_days = (daily_returns > 0).sum()
        negative_days = (daily_returns < 0).sum()
        metrics['盈利天数'] = positive_days
        metrics['亏损天数'] = negative_days
        metrics['日胜率'] = (positive_days / len(daily_returns)) * 100 if len(daily_returns) > 0 else 0
        
        # 盈亏比
        avg_win = daily_returns[daily_returns > 0].mean() if positive_days > 0 else 0
        avg_loss = abs(daily_returns[daily_returns < 0].mean()) if negative_days > 0 else 0
        metrics['平均盈利'] = avg_win
        metrics['平均亏损'] = avg_loss
        metrics['盈亏比'] = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        # 最长连续盈利/亏损
        metrics['最长连涨天数'] = self._max_consecutive(daily_returns > 0)
        metrics['最长连跌天数'] = self._max_consecutive(daily_returns < 0)
        
        # 交易统计
        buy_trades = self.trades_df[self.trades_df['操作'] == 'BUY']
        sell_trades = self.trades_df[self.trades_df['操作'] == 'SELL']
        metrics['买入次数'] = len(buy_trades)
        metrics['卖出次数'] = len(sell_trades)
        
        # VaR (95%置信度)
        metrics['VaR_95'] = np.percentile(daily_returns, 5)
        
        # CVaR (条件VaR)
        var_threshold = metrics['VaR_95']
        metrics['CVaR_95'] = daily_returns[daily_returns <= var_threshold].mean()
        
        return metrics
    
    def _max_consecutive(self, condition):
        """计算最大连续True的长度"""
        max_count = 0
        current_count = 0
        for value in condition:
            if value:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        return max_count
    
    def print_evaluation_report(self, metrics):
        """打印评估报告"""
        print("=" * 80)
        print(" " * 25 + "策略评估报告")
        print("=" * 80)
        
        print("\n📅 基础信息")
        print("-" * 40)
        print(f"  策略起始: {metrics['起始日期'].strftime('%Y-%m-%d')}")
        print(f"  策略结束: {metrics['结束日期'].strftime('%Y-%m-%d')}")
        print(f"  运行天数: {metrics['交易天数']}天")
        print(f"  运行年数: {metrics['交易年数']:.2f}年")
        
        print("\n💰 收益指标")
        print("-" * 40)
        print(f"  期初资金: {metrics['期初现金']:,.0f}元")
        print(f"  最终资产: {metrics['最终总资产']:,.0f}元")
        print(f"  总收益率: {metrics['总收益率']:.2f}%")
        print(f"  年化收益率: {metrics['年化收益率']:.2f}%")
        
        print("\n📊 风险指标")
        print("-" * 40)
        print(f"  年化波动率: {metrics['年化波动率']:.2f}%")
        print(f"  最大回撤: {metrics['最大回撤']:.2f}%")
        print(f"  最大回撤日期: {metrics['最大回撤日期'].strftime('%Y-%m-%d')}")
        if isinstance(metrics['回撤恢复天数'], int):
            print(f"  回撤恢复天数: {metrics['回撤恢复天数']}天")
        else:
            print(f"  回撤恢复天数: {metrics['回撤恢复天数']}")
        print(f"  VaR (95%): {metrics['VaR_95']:.2f}%")
        print(f"  CVaR (95%): {metrics['CVaR_95']:.2f}%")
        
        print("\n🎯 风险调整收益")
        print("-" * 40)
        print(f"  夏普比率: {metrics['夏普比率']:.3f}")
        print(f"  索提诺比率: {metrics['索提诺比率']:.3f}")
        print(f"  卡尔玛比率: {metrics['卡尔玛比率']:.3f}")
        
        print("\n📈 交易统计")
        print("-" * 40)
        print(f"  买入次数: {metrics['买入次数']}次")
        print(f"  卖出次数: {metrics['卖出次数']}次")
        print(f"  日胜率: {metrics['日胜率']:.2f}%")
        print(f"  盈亏比: {metrics['盈亏比']:.2f}")
        print(f"  最长连涨: {metrics['最长连涨天数']}天")
        print(f"  最长连跌: {metrics['最长连跌天数']}天")
        
        print("\n⭐ 策略评级")
        print("-" * 40)
        
        # 根据指标给出评级
        score = 0
        if metrics['夏普比率'] > 1.5:
            score += 3
            print("  ✓ 夏普比率优秀 (>1.5)")
        elif metrics['夏普比率'] > 1:
            score += 2
            print("  ✓ 夏普比率良好 (>1.0)")
        elif metrics['夏普比率'] > 0.5:
            score += 1
            print("  ○ 夏普比率一般 (>0.5)")
        else:
            print("  ✗ 夏普比率偏低 (<0.5)")
        
        if abs(metrics['最大回撤']) < 10:
            score += 3
            print("  ✓ 回撤控制优秀 (<10%)")
        elif abs(metrics['最大回撤']) < 20:
            score += 2
            print("  ✓ 回撤控制良好 (<20%)")
        elif abs(metrics['最大回撤']) < 30:
            score += 1
            print("  ○ 回撤控制一般 (<30%)")
        else:
            print("  ✗ 回撤较大 (>30%)")
        
        if metrics['年化收益率'] > 30:
            score += 3
            print("  ✓ 收益率优秀 (>30%)")
        elif metrics['年化收益率'] > 20:
            score += 2
            print("  ✓ 收益率良好 (>20%)")
        elif metrics['年化收益率'] > 10:
            score += 1
            print("  ○ 收益率一般 (>10%)")
        else:
            print("  ✗ 收益率偏低 (<10%)")
        
        # 总体评级
        print(f"\n  综合得分: {score}/9")
        if score >= 8:
            rating = "⭐⭐⭐⭐⭐ 卓越"
        elif score >= 6:
            rating = "⭐⭐⭐⭐ 优秀"
        elif score >= 4:
            rating = "⭐⭐⭐ 良好"
        elif score >= 2:
            rating = "⭐⭐ 一般"
        else:
            rating = "⭐ 需改进"
        print(f"  策略评级: {rating}")
        
        print("\n" + "=" * 80)
    
    def plot_evaluation_charts(self, save_path='report/strategy_evaluation.png'):
        """绘制评估图表"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('策略评估分析', fontsize=16, fontweight='bold')
        
        # 1. 总资产曲线与回撤
        ax1 = axes[0, 0]
        ax1.plot(self.daily_curve['日期'], self.daily_curve['总资产'], 'b-', linewidth=1.5)
        ax1.set_title('总资产曲线')
        ax1.set_ylabel('总资产（万元）')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/10000:.0f}'))
        ax1.grid(True, alpha=0.3)
        
        # 添加回撤阴影
        ax1_twin = ax1.twinx()
        cummax = self.daily_curve['总资产'].cummax()
        drawdown = (self.daily_curve['总资产'] - cummax) / cummax * 100
        ax1_twin.fill_between(self.daily_curve['日期'], 0, drawdown, 
                              where=(drawdown < 0), color='red', alpha=0.2)
        ax1_twin.set_ylabel('回撤（%）', color='red')
        ax1_twin.tick_params(axis='y', labelcolor='red')
        
        # 2. 日收益率分布
        ax2 = axes[0, 1]
        daily_returns = self.daily_curve['日收益率'].dropna()
        ax2.hist(daily_returns, bins=50, alpha=0.7, color='blue', edgecolor='black')
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        ax2.axvline(x=daily_returns.mean(), color='green', linestyle='-', alpha=0.7, 
                   label=f'均值: {daily_returns.mean():.2f}%')
        ax2.set_title('日收益率分布')
        ax2.set_xlabel('日收益率（%）')
        ax2.set_ylabel('频次')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 累计收益率对比
        ax3 = axes[0, 2]
        self.daily_curve['累计收益率'] = (self.daily_curve['总资产'] / 
                                      self.daily_curve['期初现金'] - 1) * 100
        self.daily_curve['股价累计收益率'] = (self.daily_curve['投数网前复权'] / 
                                         self.daily_curve['投数网前复权'].iloc[0] - 1) * 100
        
        ax3.plot(self.daily_curve['日期'], self.daily_curve['累计收益率'], 
                'b-', linewidth=1.5, label='策略收益率')
        ax3.plot(self.daily_curve['日期'], self.daily_curve['股价累计收益率'], 
                'r--', linewidth=1.5, alpha=0.7, label='买入持有收益率')
        ax3.set_title('策略 vs 买入持有')
        ax3.set_ylabel('累计收益率（%）')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 滚动夏普比率
        ax4 = axes[1, 0]
        window = 252  # 一年
        rolling_returns = self.daily_curve['日收益率'].rolling(window=window)
        rolling_sharpe = (rolling_returns.mean() * 252) / (rolling_returns.std() * np.sqrt(252))
        ax4.plot(self.daily_curve['日期'], rolling_sharpe, 'g-', linewidth=1.5)
        ax4.axhline(y=1, color='red', linestyle='--', alpha=0.5, label='夏普=1')
        ax4.set_title(f'滚动夏普比率（{window}天窗口）')
        ax4.set_ylabel('夏普比率')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 5. 月度收益热力图
        ax5 = axes[1, 1]
        self.daily_curve['年'] = self.daily_curve['日期'].dt.year
        self.daily_curve['月'] = self.daily_curve['日期'].dt.month
        monthly_returns = self.daily_curve.groupby(['年', '月'])['日收益率'].sum().unstack()
        
        im = ax5.imshow(monthly_returns.values, cmap='RdYlGn', aspect='auto', vmin=-20, vmax=20)
        ax5.set_yticks(range(len(monthly_returns.index)))
        ax5.set_yticklabels(monthly_returns.index)
        ax5.set_xticks(range(12))
        ax5.set_xticklabels(['1月', '2月', '3月', '4月', '5月', '6月', 
                            '7月', '8月', '9月', '10月', '11月', '12月'])
        ax5.set_title('月度收益热力图')
        plt.colorbar(im, ax=ax5, label='月收益率（%）')
        
        # 6. 风险收益散点图
        ax6 = axes[1, 2]
        # 计算年度统计
        yearly_stats = self.daily_curve.groupby('年').agg({
            '日收益率': lambda x: ((1 + x/100).prod() - 1) * 100,  # 年收益率
            '总资产': lambda x: x.iloc[-1] / x.iloc[0] - 1  # 年度总资产增长率
        })
        yearly_std = self.daily_curve.groupby('年')['日收益率'].std() * np.sqrt(252)
        
        scatter = ax6.scatter(yearly_std, yearly_stats['日收益率'], 
                            c=yearly_stats.index, cmap='viridis', s=100)
        ax6.set_xlabel('年化波动率（%）')
        ax6.set_ylabel('年收益率（%）')
        ax6.set_title('风险-收益散点图')
        ax6.grid(True, alpha=0.3)
        
        # 添加年份标签
        for idx, year in enumerate(yearly_stats.index):
            ax6.annotate(str(year), (yearly_std.iloc[idx], yearly_stats['日收益率'].iloc[idx]),
                        fontsize=8, alpha=0.7)
        
        # 设置日期格式
        for ax in [ax1, ax3, ax4]:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        print(f"\n评估图表已保存至: {save_path}")
        plt.show()
    
    def save_evaluation_report(self, metrics, output_path='report/strategy_evaluation.xlsx'):
        """保存评估报告到Excel"""
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # 评估指标表
            metrics_df = pd.DataFrame([metrics]).T
            metrics_df.columns = ['数值']
            metrics_df.index.name = '指标'
            metrics_df.to_excel(writer, sheet_name='评估指标')
            
            # 日度数据
            self.daily_curve[['日期', '总资产', '总资产收益率', '日收益率', '投数网前复权']].to_excel(
                writer, sheet_name='日度数据', index=False)
            
            # 交易记录
            self.trades_df.to_excel(writer, sheet_name='交易记录', index=False)
            
            print(f"评估报告已保存至: {output_path}")


def main():
    """主函数"""
    print("\n开始策略评估...")
    
    # 创建评估器
    evaluator = StrategyEvaluator()
    
    # 计算评估指标
    metrics = evaluator.calculate_metrics()
    
    # 打印评估报告
    evaluator.print_evaluation_report(metrics)
    
    # 绘制评估图表
    evaluator.plot_evaluation_charts()
    
    # 保存评估报告
    evaluator.save_evaluation_report(metrics)
    
    return metrics


if __name__ == "__main__":
    main()