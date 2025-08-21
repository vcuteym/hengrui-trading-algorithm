"""
网格搜索优化器
通过遍历所有参数组合找到最优参数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import itertools
import time
from tqdm import tqdm
import multiprocessing as mp
from functools import partial

from .optimizer import ParameterOptimizer, OptimizationConfig, OptimizationTrial


class GridSearchOptimizer(ParameterOptimizer):
    """网格搜索优化器"""
    
    def __init__(self, data: pd.DataFrame, config: OptimizationConfig):
        """
        初始化网格搜索优化器
        
        Args:
            data: 历史数据
            config: 优化配置
        """
        super().__init__(data, config)
        self.parameter_grid = self._create_parameter_grid()
        
    def _create_parameter_grid(self) -> List[Dict[str, float]]:
        """创建参数网格"""
        param_values = {}
        
        for name, param_range in self.config.parameter_ranges.items():
            param_values[name] = param_range.get_values()
        
        # 生成所有参数组合
        keys = list(param_values.keys())
        values = list(param_values.values())
        
        combinations = list(itertools.product(*values))
        
        parameter_grid = []
        for combo in combinations:
            params = dict(zip(keys, combo))
            parameter_grid.append(params)
        
        return parameter_grid
    
    def _evaluate_single_combination(self, params: Dict[str, float], trial_id: int) -> OptimizationTrial:
        """评估单个参数组合"""
        start_time = time.time()
        
        try:
            metrics = self.evaluate_strategy(params)
        except Exception as e:
            print(f"评估参数 {params} 时出错: {e}")
            metrics = {
                'total_return': -100,
                'annual_return': -100,
                'max_drawdown': -100,
                'sharpe_ratio': -10,
                'profit_factor': 0,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate': 0
            }
        
        execution_time = time.time() - start_time
        
        trial = OptimizationTrial(
            trial_id=trial_id,
            parameters=params,
            metrics=metrics,
            execution_time=execution_time
        )
        
        return trial
    
    def optimize(self) -> OptimizationTrial:
        """
        执行网格搜索优化
        
        Returns:
            最优试验结果
        """
        print(f"\n开始网格搜索优化")
        print(f"参数空间大小: {len(self.parameter_grid)}")
        print(f"优化目标: {self.config.objective}")
        print("-" * 50)
        
        # 限制试验次数
        n_trials = min(self.config.n_trials, len(self.parameter_grid))
        
        # 如果参数组合少于n_trials，使用所有组合
        if len(self.parameter_grid) <= n_trials:
            selected_params = self.parameter_grid
        else:
            # 随机选择n_trials个组合
            np.random.seed(self.config.random_seed)
            indices = np.random.choice(len(self.parameter_grid), n_trials, replace=False)
            selected_params = [self.parameter_grid[i] for i in indices]
        
        # 单进程或多进程执行
        if self.config.n_jobs == 1:
            # 单进程执行
            for i, params in enumerate(tqdm(selected_params, desc="网格搜索进度")):
                trial = self._evaluate_single_combination(params, i)
                self.trials.append(trial)
                
                # 更新最优结果
                if self.best_trial is None or \
                   self.get_objective_value(trial.metrics) > self.get_objective_value(self.best_trial.metrics):
                    self.best_trial = trial
                
                # 打印进度
                if (i + 1) % 10 == 0:
                    self.print_progress(trial)
                
                # 早停检查
                if self.config.early_stopping and i >= self.config.early_stopping_rounds:
                    recent_best = max(
                        self.trials[-self.config.early_stopping_rounds:],
                        key=lambda t: self.get_objective_value(t.metrics)
                    )
                    if recent_best.trial_id == self.best_trial.trial_id:
                        print(f"\n早停: {self.config.early_stopping_rounds} 轮未改善")
                        break
        else:
            # 多进程执行
            print(f"使用 {self.config.n_jobs} 个进程并行计算...")
            
            with mp.Pool(processes=self.config.n_jobs) as pool:
                # 创建任务
                tasks = [(params, i) for i, params in enumerate(selected_params)]
                
                # 并行执行
                results = pool.starmap(self._evaluate_single_combination, tasks)
                
                # 收集结果
                self.trials = results
                
                # 找出最优结果
                self.best_trial = max(
                    self.trials,
                    key=lambda t: self.get_objective_value(t.metrics)
                )
        
        # 打印最终结果
        self._print_final_results()
        
        return self.best_trial
    
    def _print_final_results(self):
        """打印最终优化结果"""
        if not self.best_trial:
            print("\n未找到有效的优化结果")
            return
        
        print("\n" + "=" * 60)
        print("网格搜索优化完成")
        print("=" * 60)
        
        print(f"\n最优参数组合:")
        for param, value in self.best_trial.parameters.items():
            if param == 'drawdown_threshold':
                print(f"  {param}: {value:.2%}")
            else:
                print(f"  {param}: {value:.2f}")
        
        print(f"\n最优性能指标:")
        metrics = self.best_trial.metrics
        print(f"  总收益率: {metrics['total_return']:.2f}%")
        print(f"  年化收益率: {metrics['annual_return']:.2f}%")
        print(f"  最大回撤: {metrics['max_drawdown']:.2f}%")
        print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
        print(f"  盈利因子: {metrics['profit_factor']:.2f}")
        print(f"  总交易次数: {metrics['total_trades']}")
        print(f"  胜率: {metrics['win_rate']:.2f}%")
        
        print(f"\n优化统计:")
        print(f"  总试验次数: {len(self.trials)}")
        print(f"  总耗时: {sum(t.execution_time for t in self.trials):.2f}秒")
        print(f"  平均每次试验: {np.mean([t.execution_time for t in self.trials]):.2f}秒")
        
    def get_top_n_trials(self, n: int = 10) -> pd.DataFrame:
        """
        获取前N个最优试验结果
        
        Args:
            n: 返回的试验数量
            
        Returns:
            包含前N个最优试验的DataFrame
        """
        if not self.trials:
            return pd.DataFrame()
        
        # 转换为DataFrame并排序
        df = self.get_optimization_summary()
        
        return df.head(n)