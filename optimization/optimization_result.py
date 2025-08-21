"""
优化结果分析和可视化模块
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class OptimizationResult:
    """优化结果分析类"""
    
    def __init__(self, optimizer=None, result_file: Optional[str] = None):
        """
        初始化优化结果
        
        Args:
            optimizer: 优化器实例
            result_file: 结果文件路径
        """
        if optimizer:
            self.trials = optimizer.trials
            self.best_trial = optimizer.best_trial
            self.config = optimizer.config
        elif result_file:
            self.load_from_file(result_file)
        else:
            raise ValueError("必须提供optimizer或result_file")
    
    def load_from_file(self, filepath: str):
        """从文件加载结果"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 重构数据
        self.trials = data.get('all_trials', [])
        self.best_trial = data.get('best_trial')
        self.config = data.get('config', {})
    
    def create_summary_report(self) -> pd.DataFrame:
        """创建优化摘要报告"""
        if not self.trials:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(self.trials)
        
        # 展开嵌套的字典
        if 'parameters' in df.columns:
            params_df = pd.json_normalize(df['parameters'])
            df = pd.concat([df.drop('parameters', axis=1), params_df], axis=1)
        
        if 'metrics' in df.columns:
            metrics_df = pd.json_normalize(df['metrics'])
            df = pd.concat([df.drop('metrics', axis=1), metrics_df], axis=1)
        
        # 排序
        if 'total_return' in df.columns:
            df = df.sort_values('total_return', ascending=False)
        
        return df
    
    def plot_optimization_history(self, save_path: Optional[str] = None):
        """绘制优化历史"""
        df = self.create_summary_report()
        
        if df.empty:
            print("没有数据可以绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('参数优化历史分析', fontsize=16, fontweight='bold')
        
        # 1. 目标值演化
        ax = axes[0, 0]
        objective_values = [trial.metrics.get('total_return', 0) if hasattr(trial, 'metrics') else trial.get('metrics', {}).get('total_return', 0) for trial in self.trials]
        cummax = pd.Series(objective_values).cummax()
        
        ax.plot(objective_values, 'o-', alpha=0.5, label='试验值')
        ax.plot(cummax, 'r-', linewidth=2, label='累计最优')
        ax.axhline(y=objective_values[cummax.idxmax()], color='g', linestyle='--', 
                   label=f'最优值: {objective_values[cummax.idxmax()]:.2f}%')
        ax.set_xlabel('试验次数')
        ax.set_ylabel('总收益率 (%)')
        ax.set_title('优化收敛过程')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. 参数分布热图
        ax = axes[0, 1]
        param_cols = ['buy_pe_threshold', 'sell_pe_threshold', 'drawdown_threshold']
        if all(col in df.columns for col in param_cols):
            top_10 = df.head(10)[param_cols + ['total_return']]
            
            # 归一化参数值
            normalized = top_10[param_cols].copy()
            for col in param_cols:
                min_val = normalized[col].min()
                max_val = normalized[col].max()
                if max_val > min_val:
                    normalized[col] = (normalized[col] - min_val) / (max_val - min_val)
            
            sns.heatmap(normalized.T, annot=True, fmt='.2f', cmap='YlOrRd', 
                       ax=ax, cbar_kws={'label': '归一化值'})
            ax.set_title('前10组最优参数分布')
            ax.set_xlabel('试验排名')
            ax.set_ylabel('参数')
        
        # 3. 性能指标对比
        ax = axes[1, 0]
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        metric_labels = ['总收益率(%)', '夏普比率', '最大回撤(%)']
        
        if all(m in df.columns for m in metrics):
            top_5 = df.head(5)
            x = np.arange(5)
            width = 0.25
            
            for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
                values = top_5[metric].values
                ax.bar(x + i*width, values, width, label=label)
            
            ax.set_xlabel('试验排名')
            ax.set_ylabel('指标值')
            ax.set_title('前5组参数性能对比')
            ax.set_xticks(x + width)
            ax.set_xticklabels(['第' + str(i+1) for i in range(5)])
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # 4. 参数敏感性分析
        ax = axes[1, 1]
        if 'buy_pe_threshold' in df.columns and 'total_return' in df.columns:
            scatter = ax.scatter(df['buy_pe_threshold'], df['sell_pe_threshold'], 
                               c=df['total_return'], s=50, cmap='viridis', alpha=0.6)
            plt.colorbar(scatter, ax=ax, label='总收益率(%)')
            
            # 标记最优点
            if self.best_trial:
                best_params = self.best_trial.parameters if hasattr(self.best_trial, 'parameters') else self.best_trial.get('parameters', {})
                ax.scatter(best_params.get('buy_pe_threshold', 0), 
                          best_params.get('sell_pe_threshold', 0),
                          color='red', s=200, marker='*', 
                          edgecolors='black', linewidth=2,
                          label='最优参数', zorder=5)
            
            ax.set_xlabel('买入PE阈值')
            ax.set_ylabel('卖出PE阈值')
            ax.set_title('参数空间探索图')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        
        plt.show()
    
    def plot_parameter_importance(self, save_path: Optional[str] = None):
        """绘制参数重要性分析"""
        df = self.create_summary_report()
        
        if df.empty:
            print("没有数据可以绘制")
            return
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('参数敏感性分析', fontsize=16, fontweight='bold')
        
        param_cols = ['buy_pe_threshold', 'sell_pe_threshold', 'drawdown_threshold']
        param_labels = ['买入PE阈值', '卖出PE阈值', '回撤阈值']
        
        for ax, param, label in zip(axes, param_cols, param_labels):
            if param in df.columns and 'total_return' in df.columns:
                ax.scatter(df[param], df['total_return'], alpha=0.6)
                
                # 添加趋势线
                z = np.polyfit(df[param], df['total_return'], 1)
                p = np.poly1d(z)
                x_line = np.linspace(df[param].min(), df[param].max(), 100)
                ax.plot(x_line, p(x_line), "r-", alpha=0.8, label='趋势线')
                
                # 标记最优点
                if self.best_trial:
                    best_params = self.best_trial.parameters if hasattr(self.best_trial, 'parameters') else self.best_trial.get('parameters', {})
                    best_metrics = self.best_trial.metrics if hasattr(self.best_trial, 'metrics') else self.best_trial.get('metrics', {})
                    ax.scatter(best_params.get(param, 0), best_metrics.get('total_return', 0),
                             color='red', s=100, marker='*', 
                             edgecolors='black', linewidth=1,
                             label='最优值', zorder=5)
                
                ax.set_xlabel(label)
                ax.set_ylabel('总收益率 (%)')
                ax.set_title(f'{label}对收益的影响')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        
        plt.show()
    
    def generate_report(self, output_dir: str = './optimization_results'):
        """生成完整的优化报告"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. 保存摘要报告
        df = self.create_summary_report()
        csv_path = os.path.join(output_dir, f'optimization_summary_{timestamp}.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"摘要报告已保存到: {csv_path}")
        
        # 2. 保存最优参数
        if self.best_trial:
            best_params_path = os.path.join(output_dir, f'best_parameters_{timestamp}.json')
            with open(best_params_path, 'w', encoding='utf-8') as f:
                best_params = self.best_trial.parameters if hasattr(self.best_trial, 'parameters') else self.best_trial.get('parameters', {})
                best_metrics = self.best_trial.metrics if hasattr(self.best_trial, 'metrics') else self.best_trial.get('metrics', {})
                # 转换为可JSON序列化的格式
                json_params = {k: float(v) if hasattr(v, 'item') else v for k, v in best_params.items()}
                json_metrics = {k: float(v) if hasattr(v, 'item') else v for k, v in best_metrics.items()}
                json.dump({
                    'parameters': json_params,
                    'metrics': json_metrics,
                    'timestamp': timestamp
                }, f, indent=2, ensure_ascii=False)
            print(f"最优参数已保存到: {best_params_path}")
        
        # 3. 生成文本报告
        report_path = os.path.join(output_dir, f'optimization_report_{timestamp}.txt')
        self._generate_text_report(report_path)
        
        # 4. 生成图表
        plot_path1 = os.path.join(output_dir, f'optimization_history_{timestamp}.png')
        self.plot_optimization_history(plot_path1)
        
        plot_path2 = os.path.join(output_dir, f'parameter_importance_{timestamp}.png')
        self.plot_parameter_importance(plot_path2)
        
        print(f"\n完整报告已生成到: {output_dir}")
        
        return output_dir
    
    def _generate_text_report(self, filepath: str):
        """生成文本格式的报告"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("                        参数优化报告\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            objective = self.config.objective if hasattr(self.config, 'objective') else self.config.get('objective', 'N/A') if isinstance(self.config, dict) else 'N/A'
            f.write(f"优化目标: {objective}\n")
            f.write(f"试验次数: {len(self.trials)}\n\n")
            
            if self.best_trial:
                f.write("-" * 40 + "\n")
                f.write("最优参数组合:\n")
                f.write("-" * 40 + "\n")
                best_params = self.best_trial.parameters if hasattr(self.best_trial, 'parameters') else self.best_trial.get('parameters', {})
                for param, value in best_params.items():
                    if param == 'drawdown_threshold':
                        f.write(f"  {param}: {value:.2%}\n")
                    else:
                        f.write(f"  {param}: {value:.2f}\n")
                
                f.write("\n" + "-" * 40 + "\n")
                f.write("最优性能指标:\n")
                f.write("-" * 40 + "\n")
                metrics = self.best_trial.metrics if hasattr(self.best_trial, 'metrics') else self.best_trial.get('metrics', {})
                f.write(f"  总收益率: {metrics.get('total_return', 0):.2f}%\n")
                f.write(f"  年化收益率: {metrics.get('annual_return', 0):.2f}%\n")
                f.write(f"  最大回撤: {metrics.get('max_drawdown', 0):.2f}%\n")
                f.write(f"  夏普比率: {metrics.get('sharpe_ratio', 0):.2f}\n")
                f.write(f"  盈利因子: {metrics.get('profit_factor', 0):.2f}\n")
                f.write(f"  总交易次数: {metrics.get('total_trades', 0)}\n")
                f.write(f"  买入次数: {metrics.get('buy_trades', 0)}\n")
                f.write(f"  卖出次数: {metrics.get('sell_trades', 0)}\n")
                f.write(f"  胜率: {metrics.get('win_rate', 0):.2f}%\n")
            
            # 添加前10名结果
            f.write("\n" + "=" * 80 + "\n")
            f.write("前10组最优参数:\n")
            f.write("=" * 80 + "\n\n")
            
            df = self.create_summary_report()
            if not df.empty:
                top_10 = df.head(10)
                for i, row in top_10.iterrows():
                    f.write(f"第{i+1}名:\n")
                    f.write(f"  买入PE: {row.get('buy_pe_threshold', 0):.2f}, ")
                    f.write(f"卖出PE: {row.get('sell_pe_threshold', 0):.2f}, ")
                    f.write(f"回撤阈值: {row.get('drawdown_threshold', 0):.2%}\n")
                    f.write(f"  收益率: {row.get('total_return', 0):.2f}%, ")
                    f.write(f"夏普比率: {row.get('sharpe_ratio', 0):.2f}, ")
                    f.write(f"最大回撤: {row.get('max_drawdown', 0):.2f}%\n\n")
        
        print(f"文本报告已保存到: {filepath}")