"""
参数优化器基类和主优化框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import time
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.trading_strategy import TradingStrategy, StrategyConfig


@dataclass
class ParameterRange:
    """参数范围定义"""
    name: str
    min_value: float
    max_value: float
    step: Optional[float] = None
    values: Optional[List[float]] = None
    
    def get_values(self) -> List[float]:
        """获取参数的所有可能值"""
        if self.values is not None:
            return self.values
        elif self.step is not None:
            return list(np.arange(self.min_value, self.max_value + self.step, self.step))
        else:
            return [self.min_value, self.max_value]


@dataclass
class OptimizationConfig:
    """优化配置"""
    parameter_ranges: Dict[str, ParameterRange]
    objective: str = 'sharpe_ratio'  # 优化目标：'total_return', 'sharpe_ratio', 'max_drawdown', 'profit_factor'
    n_trials: int = 100  # 优化试验次数
    n_jobs: int = 1  # 并行任务数
    random_seed: int = 42
    early_stopping: bool = True
    early_stopping_rounds: int = 20
    verbose: bool = True


@dataclass
class OptimizationTrial:
    """单次优化试验结果"""
    trial_id: int
    parameters: Dict[str, float]
    metrics: Dict[str, float]
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'trial_id': self.trial_id,
            'parameters': self.parameters,
            'metrics': self.metrics,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat()
        }


class ParameterOptimizer(ABC):
    """参数优化器基类"""
    
    def __init__(self, data: pd.DataFrame, config: OptimizationConfig):
        """
        初始化优化器
        
        Args:
            data: 历史数据
            config: 优化配置
        """
        self.data = data
        self.config = config
        self.trials: List[OptimizationTrial] = []
        self.best_trial: Optional[OptimizationTrial] = None
        self.optimization_history: List[Dict] = []
        
    @abstractmethod
    def optimize(self) -> OptimizationTrial:
        """执行优化"""
        pass
    
    def evaluate_strategy(self, parameters: Dict[str, float]) -> Dict[str, float]:
        """
        评估策略性能
        
        Args:
            parameters: 策略参数
            
        Returns:
            性能指标字典
        """
        # 创建策略配置
        config = StrategyConfig(
            buy_pe_threshold=parameters.get('buy_pe_threshold', 55),
            sell_pe_threshold=parameters.get('sell_pe_threshold', 75),
            drawdown_threshold=parameters.get('drawdown_threshold', -0.25)
        )
        
        # 运行策略
        strategy = TradingStrategy(self.data, config)
        result_df = strategy.run_strategy()
        
        # 计算性能指标
        metrics = self.calculate_metrics(result_df, strategy.trades)
        
        return metrics
    
    def calculate_metrics(self, result_df: pd.DataFrame, trades: List) -> Dict[str, float]:
        """
        计算策略性能指标
        
        Args:
            result_df: 策略运行结果
            trades: 交易记录
            
        Returns:
            性能指标字典
        """
        metrics = {}
        
        # 计算总收益率
        if len(trades) > 0:
            initial_investment = trades[0].cash_outflow if trades else 10000
            final_value = trades[-1].total_profit if trades else 0
            metrics['total_return'] = (final_value / initial_investment - 1) * 100 if initial_investment > 0 else 0
            
            # 计算年化收益率
            days = (trades[-1].date - trades[0].date).days if len(trades) > 1 else 365
            years = days / 365.0
            metrics['annual_return'] = ((1 + metrics['total_return'] / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
            
            # 计算最大回撤
            values = [t.total_profit for t in trades]
            if len(values) > 0:
                peak = values[0]
                max_dd = 0
                for value in values:
                    if value > peak:
                        peak = value
                    dd = (value - peak) / peak if peak > 0 else 0
                    max_dd = min(max_dd, dd)
                metrics['max_drawdown'] = max_dd * 100
            else:
                metrics['max_drawdown'] = 0
            
            # 计算夏普比率（简化版本）
            if len(values) > 1:
                returns = pd.Series(values).pct_change().dropna()
                if len(returns) > 0 and returns.std() > 0:
                    metrics['sharpe_ratio'] = (returns.mean() / returns.std()) * np.sqrt(252)
                else:
                    metrics['sharpe_ratio'] = 0
            else:
                metrics['sharpe_ratio'] = 0
            
            # 计算盈利因子
            buy_trades = [t for t in trades if t.action == 'BUY']
            sell_trades = [t for t in trades if t.action == 'SELL']
            
            if len(sell_trades) > 0:
                total_profit = sum(t.amount for t in sell_trades)
                total_cost = sum(t.amount for t in buy_trades)
                metrics['profit_factor'] = total_profit / total_cost if total_cost > 0 else 0
            else:
                metrics['profit_factor'] = 0
            
            # 交易统计
            metrics['total_trades'] = len(trades)
            metrics['buy_trades'] = len(buy_trades)
            metrics['sell_trades'] = len(sell_trades)
            
            # 胜率（简化计算）
            if len(sell_trades) > 0:
                profitable_sells = sum(1 for t in sell_trades if t.total_profit > 0)
                metrics['win_rate'] = (profitable_sells / len(sell_trades)) * 100
            else:
                metrics['win_rate'] = 0
                
        else:
            # 没有交易的情况
            metrics = {
                'total_return': 0,
                'annual_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'profit_factor': 0,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate': 0
            }
        
        return metrics
    
    def get_objective_value(self, metrics: Dict[str, float]) -> float:
        """
        获取优化目标值
        
        Args:
            metrics: 性能指标
            
        Returns:
            目标值
        """
        objective = self.config.objective
        
        if objective == 'total_return':
            return metrics['total_return']
        elif objective == 'sharpe_ratio':
            return metrics['sharpe_ratio']
        elif objective == 'max_drawdown':
            return -metrics['max_drawdown']  # 最大回撤越小越好
        elif objective == 'profit_factor':
            return metrics['profit_factor']
        else:
            # 综合评分
            score = (
                metrics['total_return'] * 0.3 +
                metrics['sharpe_ratio'] * 10 * 0.3 +
                (-metrics['max_drawdown']) * 0.2 +
                metrics['profit_factor'] * 10 * 0.2
            )
            return score
    
    def save_results(self, filepath: str):
        """保存优化结果"""
        results = {
            'config': {
                'objective': self.config.objective,
                'n_trials': self.config.n_trials,
                'parameter_ranges': {
                    name: {
                        'min': r.min_value,
                        'max': r.max_value,
                        'step': r.step
                    }
                    for name, r in self.config.parameter_ranges.items()
                }
            },
            'best_trial': self.best_trial.to_dict() if self.best_trial else None,
            'all_trials': [trial.to_dict() for trial in self.trials],
            'optimization_time': sum(t.execution_time for t in self.trials)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        if self.config.verbose:
            print(f"优化结果已保存到: {filepath}")
    
    def print_progress(self, trial: OptimizationTrial):
        """打印优化进度"""
        if self.config.verbose:
            print(f"\n试验 #{trial.trial_id}")
            print(f"参数: {trial.parameters}")
            print(f"目标值: {self.get_objective_value(trial.metrics):.4f}")
            print(f"指标: 收益率={trial.metrics['total_return']:.2f}%, "
                  f"夏普比率={trial.metrics['sharpe_ratio']:.2f}, "
                  f"最大回撤={trial.metrics['max_drawdown']:.2f}%")
            
            if self.best_trial:
                best_value = self.get_objective_value(self.best_trial.metrics)
                print(f"当前最优: {best_value:.4f}")
    
    def get_best_parameters(self) -> Dict[str, float]:
        """获取最优参数"""
        if self.best_trial:
            return self.best_trial.parameters
        return {}
    
    def get_optimization_summary(self) -> pd.DataFrame:
        """获取优化摘要"""
        if not self.trials:
            return pd.DataFrame()
        
        data = []
        for trial in self.trials:
            row = {
                'trial_id': trial.trial_id,
                **trial.parameters,
                **trial.metrics,
                'objective_value': self.get_objective_value(trial.metrics),
                'execution_time': trial.execution_time
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df = df.sort_values('objective_value', ascending=False)
        
        return df