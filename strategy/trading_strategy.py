import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class StrategyConfig:
    """策略配置参数"""
    # 参数1：回撤阈值（负数，例如-0.25表示-25%）
    drawdown_threshold: float = -0.30  # 优化后的最佳值（原-0.25）
    
    # 参数2：买入PE阈值
    buy_pe_threshold: float = 65  # 优化后的最佳值（原55）
    
    # 参数3：卖出PE阈值
    sell_pe_threshold: float = 90  # 优化后的最佳值（原75）
    
    # 参数4：起始日期
    start_date: str = '2010-07-22'
    
    # 其他固定参数
    buy_amount: float = 10000  # 每次买入金额
    min_shares: float = 0.01   # 最小允许买入数量
    min_trade_interval_days: int = 30  # 最小交易间隔（天）
    sell_ratio: float = 0.5     # 每次卖出比例（废弃，改用新规则）
    max_consecutive_buys: int = 5  # 最大连续买入次数


@dataclass
class TradeRecord:
    """交易记录"""
    date: pd.Timestamp
    action: str  # 'BUY' or 'SELL'
    price: float
    pe: float
    drawdown: float
    shares: float
    amount: float
    total_shares: float
    cash_outflow: float  # 现金流出（累计买入金额）
    current_value: float
    cash_inflow: float   # 现金流入（累计卖出金额）
    total_profit: float   # 总收益 = 当前市值 - 现金流出 + 现金流入


class TradingStrategy:
    """PE回撤交易策略"""
    
    def __init__(self, data: pd.DataFrame, config: Optional[StrategyConfig] = None):
        """
        初始化策略
        
        Args:
            data: 包含日期、PE、股价、回撤等数据的DataFrame
            config: 策略配置参数
        """
        self.data = data.copy()
        self.config = config if config else StrategyConfig()
        
        # 确保日期列是datetime类型
        self.data['日期'] = pd.to_datetime(self.data['日期'])
        self.data = self.data.sort_values('日期')
        
        # 初始化交易状态
        self.trades: List[TradeRecord] = []
        self.total_shares = 0.0
        self.cash_outflow = 0.0  # 现金流出（累计买入金额）
        self.cash_inflow = 0.0   # 现金流入（累计卖出金额）
        self.last_buy_date = None
        self.last_sell_date = None
        self.consecutive_buys = 0  # 连续买入次数
        self.total_buy_times = 0   # 总买入次数（用于计算卖出数量）
        
    def check_buy_condition(self, row: pd.Series) -> bool:
        """
        检查买入条件
        
        Args:
            row: 当前数据行
            
        Returns:
            是否满足买入条件
        """
        # 条件1：回撤比例小于阈值（注意回撤是负数）
        condition1 = row['回撤'] < self.config.drawdown_threshold * 100
        
        # 条件2：PE小于买入阈值
        condition2 = row['PE'] < self.config.buy_pe_threshold
        
        # 条件3：距离上次买入超过最小间隔
        if self.last_buy_date:
            days_since_last_buy = (row['日期'] - self.last_buy_date).days
            condition3 = days_since_last_buy >= self.config.min_trade_interval_days
        else:
            condition3 = True
        
        # 条件4：连续买入次数不超过最大限制
        condition4 = self.consecutive_buys < self.config.max_consecutive_buys
        
        return condition1 and condition2 and condition3 and condition4
    
    def check_sell_condition(self, row: pd.Series) -> bool:
        """
        检查卖出条件
        
        Args:
            row: 当前数据行
            
        Returns:
            是否满足卖出条件
        """
        # 必须有持仓
        if self.total_shares <= 0:
            return False
        
        # 条件1：PE超过卖出阈值
        condition1 = row['PE'] > self.config.sell_pe_threshold
        
        # 条件2：距离上次卖出超过最小间隔
        if self.last_sell_date:
            days_since_last_sell = (row['日期'] - self.last_sell_date).days
            condition2 = days_since_last_sell >= self.config.min_trade_interval_days
        else:
            condition2 = True
        
        return condition1 and condition2
    
    def execute_buy(self, date: pd.Timestamp, price: float, pe: float, drawdown: float) -> TradeRecord:
        """执行买入操作"""
        shares = self.config.buy_amount / price
        
        # 检查最小买入数量
        if shares < self.config.min_shares:
            shares = 0
            amount = 0
        else:
            amount = self.config.buy_amount
            self.total_shares += shares
            self.cash_outflow += amount  # 买入增加现金流出
            self.last_buy_date = date
            self.consecutive_buys += 1  # 增加连续买入次数
            self.total_buy_times += 1   # 增加总买入次数
        
        current_value = self.total_shares * price
        total_profit = current_value - self.cash_outflow + self.cash_inflow
        
        return TradeRecord(
            date=date,
            action='BUY',
            price=price,
            pe=pe,
            drawdown=drawdown,
            shares=shares,
            amount=amount,
            total_shares=self.total_shares,
            cash_outflow=self.cash_outflow,
            current_value=current_value,
            cash_inflow=self.cash_inflow,
            total_profit=total_profit
        )
    
    def execute_sell(self, date: pd.Timestamp, price: float, pe: float, drawdown: float) -> TradeRecord:
        """执行卖出操作"""
        # 新规则：每次卖出数量 = 总持股数 / 连续买入次数
        # 使用连续买入次数，如果为0则使用1（至少卖出全部）
        divisor = max(self.consecutive_buys, 1)
        shares_to_sell = self.total_shares / divisor
        amount = shares_to_sell * price
        
        self.total_shares -= shares_to_sell
        self.cash_inflow += amount  # 卖出增加现金流入
        self.last_sell_date = date
        self.consecutive_buys = 0  # 卖出后重置连续买入次数
        
        current_value = self.total_shares * price
        total_profit = current_value - self.cash_outflow + self.cash_inflow
        
        return TradeRecord(
            date=date,
            action='SELL',
            price=price,
            pe=pe,
            drawdown=drawdown,
            shares=-shares_to_sell,  # 负数表示卖出
            amount=amount,
            total_shares=self.total_shares,
            cash_outflow=self.cash_outflow,
            current_value=current_value,
            cash_inflow=self.cash_inflow,
            total_profit=total_profit
        )
    
    def run_strategy(self) -> pd.DataFrame:
        """
        运行策略
        
        Returns:
            交易记录DataFrame
        """
        # 筛选起始日期之后的数据
        start_date = pd.to_datetime(self.config.start_date)
        strategy_data = self.data[self.data['日期'] >= start_date]
        
        # 遍历数据执行策略
        for idx, row in strategy_data.iterrows():
            # 检查买入条件
            if self.check_buy_condition(row):
                trade = self.execute_buy(
                    date=row['日期'],
                    price=row.get('股价', row.get('收盘', 0)),
                    pe=row['PE'],
                    drawdown=row['回撤']
                )
                if trade.shares > 0:  # 只记录实际发生的交易
                    self.trades.append(trade)
            
            # 检查卖出条件
            elif self.check_sell_condition(row):
                trade = self.execute_sell(
                    date=row['日期'],
                    price=row.get('股价', row.get('收盘', 0)),
                    pe=row['PE'],
                    drawdown=row['回撤']
                )
                self.trades.append(trade)
        
        # 计算最终收益（使用最后一天的价格）
        if len(strategy_data) > 0 and self.total_shares > 0:
            last_row = strategy_data.iloc[-1]
            final_value = self.total_shares * last_row.get('股价', last_row.get('收盘', 0))
            final_profit = final_value - self.cash_outflow + self.cash_inflow
            
            # 添加最终持仓记录
            self.trades.append(TradeRecord(
                date=last_row['日期'],
                action='HOLD',
                price=last_row.get('股价', last_row.get('收盘', 0)),
                pe=last_row['PE'],
                drawdown=last_row['回撤'],
                shares=0,
                amount=0,
                total_shares=self.total_shares,
                cash_outflow=self.cash_outflow,
                current_value=final_value,
                cash_inflow=self.cash_inflow,
                total_profit=final_profit
            ))
        
        return self.get_trades_dataframe()
    
    def get_trades_dataframe(self) -> pd.DataFrame:
        """
        将交易记录转换为DataFrame
        
        Returns:
            交易记录DataFrame
        """
        if not self.trades:
            return pd.DataFrame()
        
        records = []
        for trade in self.trades:
            records.append({
                '日期': trade.date,
                '操作': trade.action,
                '股价': trade.price,
                'PE': trade.pe,
                '回撤': trade.drawdown,
                '交易股数': trade.shares,
                '交易金额': trade.amount,
                '总持仓': trade.total_shares,
                '当前市值': trade.current_value,
                '现金流出': -trade.cash_outflow,  # 用负数表示流出
                '现金流入': trade.cash_inflow,
                '净现金流': -trade.cash_outflow + trade.cash_inflow,  # 净现金流 = 现金流出 + 现金流入
                '总收益': trade.total_profit
            })
        
        return pd.DataFrame(records)
    
    def print_report(self):
        """打印交易报告"""
        if not self.trades:
            print("没有交易记录")
            return
        
        print("\n" + "=" * 100)
        print("交易策略报告")
        print("=" * 100)
        print(f"\n策略参数:")
        print(f"  起始日期: {self.config.start_date}")
        print(f"  回撤阈值: {self.config.drawdown_threshold * 100:.1f}%")
        print(f"  买入PE阈值: {self.config.buy_pe_threshold}")
        print(f"  卖出PE阈值: {self.config.sell_pe_threshold}")
        print(f"  每次买入金额: {self.config.buy_amount:.0f}元")
        
        print(f"\n交易记录:")
        print("-" * 130)
        print(f"{'日期':<12} {'操作':<6} {'PE':>8} {'股价':>8} {'回撤':>8} {'交易股数':>10} {'交易金额':>10} {'总持仓':>10} {'当前市值':>10} {'现金流出':>10} {'现金流入':>10} {'净现金流':>10} {'总收益':>10}")
        print("-" * 130)
        
        for trade in self.trades:
            net_cash_flow = -trade.cash_outflow + trade.cash_inflow
            print(f"{trade.date.strftime('%Y-%m-%d'):<12} "
                  f"{trade.action:<6} "
                  f"{trade.pe:>8.2f} "
                  f"{trade.price:>8.2f} "
                  f"{trade.drawdown:>8.1f}% "
                  f"{trade.shares:>10.2f} "
                  f"{trade.amount:>10.0f} "
                  f"{trade.total_shares:>10.2f} "
                  f"{trade.current_value:>10.0f} "
                  f"{-trade.cash_outflow:>10.0f} "
                  f"{trade.cash_inflow:>10.0f} "
                  f"{net_cash_flow:>10.0f} "
                  f"{trade.total_profit:>10.0f}")
        
        # 统计汇总
        buy_trades = [t for t in self.trades if t.action == 'BUY']
        sell_trades = [t for t in self.trades if t.action == 'SELL']
        
        print("\n" + "=" * 100)
        print("交易统计:")
        print(f"  总买入次数: {len(buy_trades)}")
        print(f"  总卖出次数: {len(sell_trades)}")
        
        if self.trades:
            final_trade = self.trades[-1]
            print(f"  最终持仓: {final_trade.total_shares:.2f}股")
            print(f"  现金流出: {final_trade.cash_outflow:.0f}元")
            print(f"  现金流入: {final_trade.cash_inflow:.0f}元")
            print(f"  当前市值: {final_trade.current_value:.0f}元")
            print(f"  总收益: {final_trade.total_profit:.0f}元")
            if final_trade.cash_outflow > 0:
                return_rate = (final_trade.total_profit / final_trade.cash_outflow) * 100
                print(f"  收益率: {return_rate:.2f}%")
        
        print("=" * 100)