"""
贝叶斯优化器
使用贝叶斯优化方法智能搜索最优参数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import time
import warnings
warnings.filterwarnings('ignore')

from .optimizer import ParameterOptimizer, OptimizationConfig, OptimizationTrial

# 尝试导入scikit-optimize，如果没有安装则使用简化版本
try:
    from skopt import gp_minimize
    from skopt.space import Real
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    print("警告: scikit-optimize未安装，将使用简化的贝叶斯优化")


class BayesianOptimizer(ParameterOptimizer):
    """贝叶斯优化器"""
    
    def __init__(self, data: pd.DataFrame, config: OptimizationConfig):
        """
        初始化贝叶斯优化器
        
        Args:
            data: 历史数据
            config: 优化配置
        """
        super().__init__(data, config)
        self.search_space = self._create_search_space()
        self.param_names = list(self.config.parameter_ranges.keys())
        
    def _create_search_space(self) -> List:
        """创建搜索空间"""
        if SKOPT_AVAILABLE:
            space = []
            for name, param_range in self.config.parameter_ranges.items():
                space.append(
                    Real(param_range.min_value, param_range.max_value, name=name)
                )
            return space
        else:
            # 简化版本：返回参数范围
            return [(r.min_value, r.max_value) for r in self.config.parameter_ranges.values()]
    
    def _objective_function(self, params: List[float]) -> float:
        """
        目标函数（贝叶斯优化需要最小化，所以返回负值）
        
        Args:
            params: 参数列表
            
        Returns:
            负的目标值（用于最小化）
        """
        # 构建参数字典
        param_dict = dict(zip(self.param_names, params))
        
        # 评估策略
        try:
            metrics = self.evaluate_strategy(param_dict)
            objective_value = self.get_objective_value(metrics)
        except Exception as e:
            print(f"评估参数 {param_dict} 时出错: {e}")
            objective_value = -1000  # 惩罚值
        
        # 记录试验
        trial = OptimizationTrial(
            trial_id=len(self.trials),
            parameters=param_dict,
            metrics=metrics if 'metrics' in locals() else {
                'total_return': -100,
                'annual_return': -100,
                'max_drawdown': -100,
                'sharpe_ratio': -10,
                'profit_factor': 0,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate': 0
            },
            execution_time=0  # 将在optimize中更新
        )
        self.trials.append(trial)
        
        # 更新最优结果
        if 'metrics' in locals() and metrics:
            if self.best_trial is None or objective_value > self.get_objective_value(self.best_trial.metrics):
                self.best_trial = trial
        
        # 打印进度
        if len(self.trials) % 5 == 0:
            self.print_progress(trial)
        
        return -objective_value  # 返回负值用于最小化
    
    def optimize(self) -> OptimizationTrial:
        """
        执行贝叶斯优化
        
        Returns:
            最优试验结果
        """
        print(f"\n开始贝叶斯优化")
        print(f"参数空间: {self.param_names}")
        print(f"优化目标: {self.config.objective}")
        print(f"试验次数: {self.config.n_trials}")
        print("-" * 50)
        
        start_time = time.time()
        
        if SKOPT_AVAILABLE:
            # 使用scikit-optimize进行贝叶斯优化
            result = gp_minimize(
                func=self._objective_function,
                dimensions=self.search_space,
                n_calls=self.config.n_trials,
                n_initial_points=min(10, self.config.n_trials // 3),
                acq_func='EI',  # Expected Improvement
                random_state=self.config.random_seed,
                verbose=False
            )
            
            # 最优参数
            best_params = dict(zip(self.param_names, result.x))
            
        else:
            # 简化版本：智能随机搜索
            self._simplified_bayesian_search()
            best_params = self.best_trial.parameters if self.best_trial else {}
        
        total_time = time.time() - start_time
        
        # 更新最优试验的执行时间
        if self.best_trial:
            self.best_trial.execution_time = total_time / len(self.trials)
        
        # 打印最终结果
        self._print_final_results()
        
        return self.best_trial
    
    def _simplified_bayesian_search(self):
        """简化的贝叶斯搜索（不依赖scikit-optimize）"""
        n_random = min(10, self.config.n_trials // 3)
        
        # 第一阶段：随机探索
        for i in range(n_random):
            params = self._sample_random_params()
            _ = self._objective_function(params)
        
        # 第二阶段：基于历史结果的智能采样
        remaining_trials = self.config.n_trials - n_random
        
        for i in range(remaining_trials):
            # 获取当前最优的几个点
            sorted_trials = sorted(
                self.trials, 
                key=lambda t: self.get_objective_value(t.metrics),
                reverse=True
            )
            top_trials = sorted_trials[:min(5, len(sorted_trials))]
            
            # 在最优点附近采样
            if np.random.random() < 0.7 and top_trials:  # 70%概率在最优点附近探索
                base_trial = np.random.choice(top_trials)
                params = self._sample_near_point(base_trial.parameters)
            else:  # 30%概率随机探索
                params = self._sample_random_params()
            
            _ = self._objective_function(params)
            
            # 早停检查
            if self.config.early_stopping and i >= self.config.early_stopping_rounds:
                recent_best = max(
                    self.trials[-self.config.early_stopping_rounds:],
                    key=lambda t: self.get_objective_value(t.metrics)
                )
                if recent_best.trial_id == self.best_trial.trial_id:
                    print(f"\n早停: {self.config.early_stopping_rounds} 轮未改善")
                    break
    
    def _sample_random_params(self) -> List[float]:
        """随机采样参数"""
        params = []
        for name, param_range in self.config.parameter_ranges.items():
            value = np.random.uniform(param_range.min_value, param_range.max_value)
            params.append(value)
        return params
    
    def _sample_near_point(self, base_params: Dict[str, float]) -> List[float]:
        """在给定点附近采样"""
        params = []
        for name, param_range in self.config.parameter_ranges.items():
            base_value = base_params[name]
            # 在基准值附近添加高斯噪声
            noise_scale = (param_range.max_value - param_range.min_value) * 0.1
            new_value = base_value + np.random.normal(0, noise_scale)
            # 确保在范围内
            new_value = np.clip(new_value, param_range.min_value, param_range.max_value)
            params.append(new_value)
        return params
    
    def _print_final_results(self):
        """打印最终优化结果"""
        if not self.best_trial:
            print("\n未找到有效的优化结果")
            return
        
        print("\n" + "=" * 60)
        print("贝叶斯优化完成")
        print("=" * 60)
        
        print(f"\n最优参数组合:")
        for param, value in self.best_trial.parameters.items():
            if param == 'drawdown_threshold':
                print(f"  {param}: {value:.2%}")
            else:
                print(f"  {param}: {value:.2f}")
        
        print(f"\n最优性能指标:")
        metrics = self.best_trial.metrics
        print(f"  总收益率: {metrics.get('total_return', 0):.2f}%")
        print(f"  年化收益率: {metrics.get('annual_return', 0):.2f}%")
        print(f"  最大回撤: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"  夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"  盈利因子: {metrics.get('profit_factor', 0):.2f}")
        print(f"  总交易次数: {metrics.get('total_trades', 0)}")
        print(f"  胜率: {metrics.get('win_rate', 0):.2f}%")
        
        print(f"\n优化统计:")
        print(f"  总试验次数: {len(self.trials)}")
        print(f"  收敛速度: 第 {self.best_trial.trial_id} 次试验找到最优解")
        
        # 显示优化改进曲线
        self._show_convergence_info()
    
    def _show_convergence_info(self):
        """显示收敛信息"""
        if len(self.trials) < 5:
            return
        
        # 计算每10次试验的最优值
        print("\n收敛过程:")
        chunk_size = max(1, len(self.trials) // 10)
        
        for i in range(0, len(self.trials), chunk_size):
            chunk = self.trials[i:min(i+chunk_size, len(self.trials))]
            best_in_chunk = max(
                chunk,
                key=lambda t: self.get_objective_value(t.metrics)
            )
            print(f"  试验 {i+1}-{min(i+chunk_size, len(self.trials))}: "
                  f"最优目标值 = {self.get_objective_value(best_in_chunk.metrics):.4f}")
    
    def get_convergence_history(self) -> List[float]:
        """
        获取收敛历史
        
        Returns:
            每次试验后的最优目标值列表
        """
        history = []
        current_best = float('-inf')
        
        for trial in self.trials:
            value = self.get_objective_value(trial.metrics)
            current_best = max(current_best, value)
            history.append(current_best)
        
        return history