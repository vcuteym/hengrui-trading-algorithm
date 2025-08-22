"""
策略对比分析
比较PE回撤策略与买入持有策略
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.dates as mdates
from evaluate_strategy import StrategyEvaluator

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class StrategyComparison:
    """策略对比分析器"""
    
    def __init__(self):
        """初始化对比分析器"""
        # 创建评估器获取数据
        self.evaluator = StrategyEvaluator()
        self.metrics = self.evaluator.calculate_metrics()
        
        # 计算买入持有策略的数据
        self._calculate_buy_hold()
    
    def _calculate_buy_hold(self):
        """计算买入持有策略的表现"""
        # 假设同样的初始资金全部买入
        initial_capital = self.evaluator.daily_curve['期初现金'].iloc[0]
        initial_price = self.evaluator.daily_curve['投数网前复权'].iloc[0]
        
        # 计算买入股数
        shares = initial_capital / initial_price
        
        # 计算每日市值
        self.evaluator.daily_curve['买持市值'] = shares * self.evaluator.daily_curve['投数网前复权']
        self.evaluator.daily_curve['买持收益率'] = (self.evaluator.daily_curve['买持市值'] / initial_capital - 1) * 100
        
        # 计算买持策略的日收益率
        self.evaluator.daily_curve['买持日收益率'] = self.evaluator.daily_curve['投数网前复权'].pct_change() * 100
        
    def compare_strategies(self):
        """对比两种策略"""
        comparison = {}
        
        # 基础信息
        comparison['起始日期'] = self.evaluator.daily_curve['日期'].min()
        comparison['结束日期'] = self.evaluator.daily_curve['日期'].max()
        comparison['交易年数'] = self.metrics['交易年数']
        
        # PE回撤策略
        comparison['策略_总收益率'] = self.metrics['总收益率']
        comparison['策略_年化收益率'] = self.metrics['年化收益率']
        comparison['策略_年化波动率'] = self.metrics['年化波动率']
        comparison['策略_夏普比率'] = self.metrics['夏普比率']
        comparison['策略_最大回撤'] = self.metrics['最大回撤']
        comparison['策略_日胜率'] = self.metrics['日胜率']
        
        # 买入持有策略
        buy_hold_returns = self.evaluator.daily_curve['买持日收益率'].dropna()
        final_value = self.evaluator.daily_curve['买持市值'].iloc[-1]
        initial_value = self.evaluator.daily_curve['期初现金'].iloc[0]
        
        comparison['买持_总收益率'] = (final_value / initial_value - 1) * 100
        comparison['买持_年化收益率'] = ((final_value / initial_value) ** (1 / comparison['交易年数']) - 1) * 100
        comparison['买持_年化波动率'] = buy_hold_returns.std() * np.sqrt(252)
        
        # 买持夏普比率
        excess_return = comparison['买持_年化收益率'] - 3  # 假设无风险利率3%
        comparison['买持_夏普比率'] = excess_return / comparison['买持_年化波动率']
        
        # 买持最大回撤
        cummax = self.evaluator.daily_curve['买持市值'].cummax()
        drawdown = (self.evaluator.daily_curve['买持市值'] - cummax) / cummax * 100
        comparison['买持_最大回撤'] = drawdown.min()
        
        # 买持日胜率
        positive_days = (buy_hold_returns > 0).sum()
        comparison['买持_日胜率'] = (positive_days / len(buy_hold_returns)) * 100
        
        # 对比指标
        comparison['超额收益率'] = comparison['策略_总收益率'] - comparison['买持_总收益率']
        comparison['夏普比率差'] = comparison['策略_夏普比率'] - comparison['买持_夏普比率']
        comparison['回撤改善'] = comparison['买持_最大回撤'] - comparison['策略_最大回撤']
        
        return comparison
    
    def print_comparison_report(self, comparison):
        """打印对比报告"""
        print("\n" + "=" * 80)
        print(" " * 25 + "策略对比分析报告")
        print("=" * 80)
        
        print(f"\n📅 分析期间: {comparison['起始日期'].strftime('%Y-%m-%d')} 至 {comparison['结束日期'].strftime('%Y-%m-%d')} ({comparison['交易年数']:.1f}年)")
        
        print("\n" + "─" * 80)
        print(f"{'指标':<20} {'PE回撤策略':>20} {'买入持有':>20} {'差异':>20}")
        print("─" * 80)
        
        # 收益指标
        print(f"{'总收益率':<20} {comparison['策略_总收益率']:>19.2f}% {comparison['买持_总收益率']:>19.2f}% {comparison['超额收益率']:>19.2f}%")
        print(f"{'年化收益率':<20} {comparison['策略_年化收益率']:>19.2f}% {comparison['买持_年化收益率']:>19.2f}% {comparison['策略_年化收益率']-comparison['买持_年化收益率']:>19.2f}%")
        
        # 风险指标
        print(f"{'年化波动率':<20} {comparison['策略_年化波动率']:>19.2f}% {comparison['买持_年化波动率']:>19.2f}% {comparison['策略_年化波动率']-comparison['买持_年化波动率']:>19.2f}%")
        print(f"{'最大回撤':<20} {comparison['策略_最大回撤']:>19.2f}% {comparison['买持_最大回撤']:>19.2f}% {comparison['回撤改善']:>19.2f}%")
        print(f"{'日胜率':<20} {comparison['策略_日胜率']:>19.2f}% {comparison['买持_日胜率']:>19.2f}% {comparison['策略_日胜率']-comparison['买持_日胜率']:>19.2f}%")
        
        # 风险调整收益
        print(f"{'夏普比率':<20} {comparison['策略_夏普比率']:>20.3f} {comparison['买持_夏普比率']:>20.3f} {comparison['夏普比率差']:>20.3f}")
        
        print("─" * 80)
        
        # 评价
        print("\n📊 策略评价:")
        if comparison['策略_总收益率'] > comparison['买持_总收益率']:
            print("  ✓ PE回撤策略获得了更高的总收益")
        else:
            print("  ✗ 买入持有策略的总收益更高")
        
        if comparison['策略_最大回撤'] > comparison['买持_最大回撤']:
            print("  ✓ PE回撤策略的回撤控制更好")
        else:
            print("  ✗ 买入持有策略的回撤更小")
        
        if comparison['策略_夏普比率'] > comparison['买持_夏普比率']:
            print("  ✓ PE回撤策略的风险调整收益更优")
        else:
            print("  ✗ 买入持有策略的风险调整收益更优")
        
        if comparison['策略_年化波动率'] < comparison['买持_年化波动率']:
            print("  ✓ PE回撤策略的波动性更低")
        else:
            print("  ✗ 买入持有策略的波动性更低")
        
        print("\n" + "=" * 80)
    
    def plot_comparison(self, save_path='report/strategy_comparison.png'):
        """绘制对比图表"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('PE回撤策略 vs 买入持有策略', fontsize=16, fontweight='bold')
        
        # 1. 累计收益对比
        ax1 = axes[0, 0]
        ax1.plot(self.evaluator.daily_curve['日期'], self.evaluator.daily_curve['总资产收益率'], 
                'b-', linewidth=2, label='PE回撤策略')
        ax1.plot(self.evaluator.daily_curve['日期'], self.evaluator.daily_curve['买持收益率'], 
                'r--', linewidth=2, label='买入持有')
        ax1.set_title('累计收益率对比')
        ax1.set_ylabel('收益率（%）')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 回撤对比
        ax2 = axes[0, 1]
        
        # 计算两种策略的回撤
        strategy_cummax = self.evaluator.daily_curve['总资产'].cummax()
        strategy_dd = (self.evaluator.daily_curve['总资产'] - strategy_cummax) / strategy_cummax * 100
        
        buyhold_cummax = self.evaluator.daily_curve['买持市值'].cummax()
        buyhold_dd = (self.evaluator.daily_curve['买持市值'] - buyhold_cummax) / buyhold_cummax * 100
        
        ax2.fill_between(self.evaluator.daily_curve['日期'], 0, strategy_dd, 
                         where=(strategy_dd < 0), color='blue', alpha=0.3, label='PE策略回撤')
        ax2.fill_between(self.evaluator.daily_curve['日期'], 0, buyhold_dd, 
                         where=(buyhold_dd < 0), color='red', alpha=0.3, label='买持回撤')
        ax2.set_title('回撤对比')
        ax2.set_ylabel('回撤（%）')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 滚动夏普比率对比
        ax3 = axes[1, 0]
        window = 252
        
        # PE策略滚动夏普
        strategy_rolling = self.evaluator.daily_curve['日收益率'].rolling(window=window)
        strategy_sharpe = (strategy_rolling.mean() * 252 - 3) / (strategy_rolling.std() * np.sqrt(252))
        
        # 买持滚动夏普
        buyhold_rolling = self.evaluator.daily_curve['买持日收益率'].rolling(window=window)
        buyhold_sharpe = (buyhold_rolling.mean() * 252 - 3) / (buyhold_rolling.std() * np.sqrt(252))
        
        ax3.plot(self.evaluator.daily_curve['日期'], strategy_sharpe, 
                'b-', linewidth=1.5, label='PE策略')
        ax3.plot(self.evaluator.daily_curve['日期'], buyhold_sharpe, 
                'r--', linewidth=1.5, label='买入持有')
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax3.set_title(f'滚动夏普比率对比（{window}天窗口）')
        ax3.set_ylabel('夏普比率')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 风险收益散点图
        ax4 = axes[1, 1]
        
        # 计算年度数据
        yearly_data = self.evaluator.daily_curve.copy()
        yearly_data['年'] = yearly_data['日期'].dt.year
        
        yearly_stats = yearly_data.groupby('年').agg({
            '日收益率': lambda x: ((1 + x/100).prod() - 1) * 100,
            '买持日收益率': lambda x: ((1 + x/100).prod() - 1) * 100
        })
        
        yearly_vol = yearly_data.groupby('年').agg({
            '日收益率': lambda x: x.std() * np.sqrt(252),
            '买持日收益率': lambda x: x.std() * np.sqrt(252)
        })
        
        # 绘制散点
        ax4.scatter(yearly_vol['日收益率'], yearly_stats['日收益率'], 
                   color='blue', s=100, alpha=0.6, label='PE策略')
        ax4.scatter(yearly_vol['买持日收益率'], yearly_stats['买持日收益率'], 
                   color='red', s=100, alpha=0.6, label='买入持有')
        
        # 添加效率前沿线
        ax4.plot([0, 50], [0, 50], 'g--', alpha=0.3, label='1:1线')
        
        ax4.set_xlabel('年化波动率（%）')
        ax4.set_ylabel('年收益率（%）')
        ax4.set_title('风险-收益散点图')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 设置日期格式
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        print(f"\n对比图表已保存至: {save_path}")
        plt.show()


def main():
    """主函数"""
    print("\n开始策略对比分析...")
    
    # 创建对比分析器
    comparator = StrategyComparison()
    
    # 执行对比
    comparison = comparator.compare_strategies()
    
    # 打印报告
    comparator.print_comparison_report(comparison)
    
    # 绘制对比图表
    comparator.plot_comparison()
    
    return comparison


if __name__ == "__main__":
    main()