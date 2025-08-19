import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from typing import Optional, Tuple, List
import numpy as np
from datetime import datetime


class StockPlotter:
    """股票数据可视化工具"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化可视化工具
        
        Args:
            data: 包含日期、PE、股价等数据的DataFrame
        """
        self.data = data.copy()
        self._prepare_data()
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
    def _prepare_data(self):
        """准备数据，确保日期列是datetime类型"""
        if '日期' in self.data.columns:
            # 尝试转换日期
            try:
                self.data['日期'] = pd.to_datetime(self.data['日期'])
            except:
                print("警告：日期转换失败，将使用原始数据")
            
            # 按日期排序
            self.data = self.data.sort_values('日期')
    
    def plot_pe_timeline(self, 
                         figsize: Tuple[int, int] = (14, 6),
                         show_bands: bool = True,
                         save_path: Optional[str] = None) -> Figure:
        """
        绘制PE时间序列图
        
        Args:
            figsize: 图表大小
            show_bands: 是否显示危险值、中位值、机会值区间
            save_path: 保存路径（如果提供）
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # 绘制PE主线
        ax.plot(self.data['日期'], self.data['PE'], 
                label='PE值', color='blue', linewidth=2)
        
        # 添加区间带
        if show_bands and all(col in self.data.columns for col in ['PE危险值', 'PE中位值', 'PE机会值']):
            # 转换为数值类型
            try:
                danger_vals = pd.to_numeric(self.data['PE危险值'], errors='coerce')
                median_vals = pd.to_numeric(self.data['PE中位值'], errors='coerce')
                chance_vals = pd.to_numeric(self.data['PE机会值'], errors='coerce')
                
                # 绘制水平线
                if not danger_vals.isna().all():
                    ax.axhline(y=danger_vals.iloc[-1], color='red', 
                              linestyle='--', alpha=0.5, label=f'危险值: {danger_vals.iloc[-1]:.2f}')
                if not median_vals.isna().all():
                    ax.axhline(y=median_vals.iloc[-1], color='orange', 
                              linestyle='--', alpha=0.5, label=f'中位值: {median_vals.iloc[-1]:.2f}')
                if not chance_vals.isna().all():
                    ax.axhline(y=chance_vals.iloc[-1], color='green', 
                              linestyle='--', alpha=0.5, label=f'机会值: {chance_vals.iloc[-1]:.2f}')
                
                # 添加背景色带
                ax.fill_between(self.data['日期'], 
                               danger_vals.max() if not danger_vals.isna().all() else self.data['PE'].max(),
                               self.data['PE'].max() * 1.1,
                               alpha=0.1, color='red', label='危险区域')
                
                ax.fill_between(self.data['日期'],
                               chance_vals.min() if not chance_vals.isna().all() else self.data['PE'].min(),
                               self.data['PE'].min() * 0.9,
                               alpha=0.1, color='green', label='机会区域')
            except Exception as e:
                print(f"绘制区间带时出错: {e}")
        
        # 设置标题和标签
        ax.set_title('恒瑞医药 PE 时间序列图', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('PE值', fontsize=12)
        
        # 格式化x轴日期 - 只显示年月，间隔更大
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"PE图表已保存至: {save_path}")
        
        return fig
    
    def plot_price_timeline(self,
                           figsize: Tuple[int, int] = (14, 6),
                           show_ma: bool = False,
                           ma_periods: List[int] = [],
                           save_path: Optional[str] = None) -> Figure:
        """
        绘制股价时间序列图
        
        Args:
            figsize: 图表大小
            show_ma: 是否显示移动平均线
            ma_periods: 移动平均线周期
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # 绘制股价主线
        ax.plot(self.data['日期'], self.data['股价'],
                label='股价', color='darkblue', linewidth=2)
        
        # 添加移动平均线
        if show_ma:
            for period in ma_periods:
                if len(self.data) >= period:
                    ma = self.data['股价'].rolling(window=period).mean()
                    ax.plot(self.data['日期'], ma,
                           label=f'MA{period}', alpha=0.7, linewidth=1.5)
        
        # 设置标题和标签
        ax.set_title('恒瑞医药 股价走势图', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('股价 (元)', fontsize=12)
        
        # 格式化x轴日期 - 只显示年月，间隔更大
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"股价图表已保存至: {save_path}")
        
        return fig
    
    def plot_combined(self,
                     figsize: Tuple[int, int] = (14, 10),
                     save_path: Optional[str] = None) -> Figure:
        """
        绘制PE和股价的组合图
        
        Args:
            figsize: 图表大小
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        
        # 上图：PE值
        ax1.plot(self.data['日期'], self.data['PE'],
                label='PE值', color='blue', linewidth=2)
        
        # 添加PE区间线
        if all(col in self.data.columns for col in ['PE危险值', 'PE中位值', 'PE机会值']):
            try:
                danger_vals = pd.to_numeric(self.data['PE危险值'], errors='coerce')
                median_vals = pd.to_numeric(self.data['PE中位值'], errors='coerce')
                chance_vals = pd.to_numeric(self.data['PE机会值'], errors='coerce')
                
                if not danger_vals.isna().all():
                    ax1.axhline(y=danger_vals.iloc[-1], color='red',
                               linestyle='--', alpha=0.5, label=f'危险值')
                if not median_vals.isna().all():
                    ax1.axhline(y=median_vals.iloc[-1], color='orange',
                               linestyle='--', alpha=0.5, label=f'中位值')
                if not chance_vals.isna().all():
                    ax1.axhline(y=chance_vals.iloc[-1], color='green',
                               linestyle='--', alpha=0.5, label=f'机会值')
            except:
                pass
        
        ax1.set_title('恒瑞医药 PE与股价走势对比', fontsize=16, fontweight='bold')
        ax1.set_ylabel('PE值', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best')
        
        # 下图：股价
        ax2.plot(self.data['日期'], self.data['股价'],
                label='股价', color='darkgreen', linewidth=2)
        
        # 不显示均线，保持图表简洁
        
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('股价 (元)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best')
        
        # 格式化x轴日期
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"组合图表已保存至: {save_path}")
        
        return fig
    
    def plot_pe_distribution(self,
                            figsize: Tuple[int, int] = (10, 6),
                            bins: int = 50,
                            save_path: Optional[str] = None) -> Figure:
        """
        绘制PE分布直方图
        
        Args:
            figsize: 图表大小
            bins: 直方图组数
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # 绘制直方图
        n, bins, patches = ax.hist(self.data['PE'], bins=bins,
                                   edgecolor='black', alpha=0.7)
        
        # 添加统计线
        mean_pe = self.data['PE'].mean()
        median_pe = self.data['PE'].median()
        
        ax.axvline(mean_pe, color='red', linestyle='--',
                  linewidth=2, label=f'均值: {mean_pe:.2f}')
        ax.axvline(median_pe, color='green', linestyle='--',
                  linewidth=2, label=f'中位数: {median_pe:.2f}')
        
        # 添加当前PE位置
        current_pe = self.data['PE'].iloc[-1]
        ax.axvline(current_pe, color='blue', linestyle='-',
                  linewidth=2, label=f'当前PE: {current_pe:.2f}')
        
        ax.set_title('PE值分布图', fontsize=16, fontweight='bold')
        ax.set_xlabel('PE值', fontsize=12)
        ax.set_ylabel('频数', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"PE分布图已保存至: {save_path}")
        
        return fig
    
    def plot_all_in_one(self,
                        figsize: Tuple[int, int] = (16, 12),
                        save_path: Optional[str] = None) -> Figure:
        """
        在一个图中显示所有图表
        
        Args:
            figsize: 图表大小
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig = plt.figure(figsize=figsize)
        
        # 创建2x2的子图布局
        # 左上：PE时间序列与股价双轴图
        ax1 = plt.subplot(2, 2, 1)
        
        # 绘制PE（左轴）
        ax1_pe = ax1
        line1 = ax1_pe.plot(self.data['日期'], self.data['PE'],
                           label='PE值', color='blue', linewidth=2)
        ax1_pe.set_ylabel('PE值', fontsize=10, color='blue')
        ax1_pe.tick_params(axis='y', labelcolor='blue')
        
        # 添加PE区间线
        if all(col in self.data.columns for col in ['PE危险值', 'PE中位值', 'PE机会值']):
            try:
                danger_vals = pd.to_numeric(self.data['PE危险值'], errors='coerce')
                median_vals = pd.to_numeric(self.data['PE中位值'], errors='coerce')
                chance_vals = pd.to_numeric(self.data['PE机会值'], errors='coerce')
                
                if not danger_vals.isna().all():
                    ax1_pe.axhline(y=danger_vals.iloc[-1], color='red',
                                  linestyle='--', alpha=0.5, label='PE危险值')
                if not median_vals.isna().all():
                    ax1_pe.axhline(y=median_vals.iloc[-1], color='orange',
                                  linestyle='--', alpha=0.5, label='PE中位值')
                if not chance_vals.isna().all():
                    ax1_pe.axhline(y=chance_vals.iloc[-1], color='green',
                                  linestyle='--', alpha=0.5, label='PE机会值')
            except:
                pass
        
        # 创建右轴用于股价
        ax1_price = ax1.twinx()
        line2 = ax1_price.plot(self.data['日期'], self.data['股价'],
                              label='股价', color='purple', linewidth=1.5, alpha=0.7)
        ax1_price.set_ylabel('股价 (元)', fontsize=10, color='purple')
        ax1_price.tick_params(axis='y', labelcolor='purple')
        
        # 合并图例
        lines1, labels1 = ax1_pe.get_legend_handles_labels()
        lines2, labels2 = ax1_price.get_legend_handles_labels()
        ax1_pe.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=7)
        
        ax1.set_title('PE与股价时间序列', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)
        
        # 右上：股价走势与PE分位数
        ax2 = plt.subplot(2, 2, 2)
        
        # 绘制股价（左轴）
        ax2_price = ax2
        line1 = ax2_price.plot(self.data['日期'], self.data['股价'],
                               label='股价', color='darkgreen', linewidth=2)
        ax2_price.set_ylabel('股价 (元)', fontsize=10, color='darkgreen')
        ax2_price.tick_params(axis='y', labelcolor='darkgreen')
        ax2_price.grid(True, alpha=0.3)
        
        # 创建右轴用于PE分位数
        ax2_percentile = ax2.twinx()
        
        # 处理PE分位数数据
        if 'PE分位数' in self.data.columns:
            try:
                # PE分位数应该已经在数据处理阶段转换为数值类型
                pe_percentile = self.data['PE分位数']
                if pe_percentile.dtype == 'object':
                    # 如果还是字符串类型，再次转换
                    pe_percentile = pd.to_numeric(pe_percentile, errors='coerce')
                
                # 只绘制非缺失值
                valid_mask = ~pe_percentile.isna()
                if valid_mask.any():
                    line2 = ax2_percentile.plot(self.data.loc[valid_mask, '日期'], 
                                               pe_percentile[valid_mask] * 100,
                                               label='PE分位数', color='orange', 
                                               linewidth=1.5, alpha=0.7, marker='.', markersize=1)
                    ax2_percentile.set_ylabel('PE分位数 (%)', fontsize=10, color='orange')
                    ax2_percentile.tick_params(axis='y', labelcolor='orange')
                    ax2_percentile.set_ylim(0, 100)
                    
                    # 添加分位数参考线
                    ax2_percentile.axhline(y=80, color='red', linestyle=':', alpha=0.3, label='80%')
                    ax2_percentile.axhline(y=50, color='gray', linestyle=':', alpha=0.3, label='50%')
                    ax2_percentile.axhline(y=20, color='green', linestyle=':', alpha=0.3, label='20%')
                    
                    # 显示缺失值统计
                    missing_pct = pe_percentile.isna().sum() / len(pe_percentile) * 100
                    if missing_pct > 0:
                        ax2_percentile.text(0.02, 0.95, f'PE分位数缺失率: {missing_pct:.1f}%', 
                                          transform=ax2_percentile.transAxes, 
                                          fontsize=8, alpha=0.6, verticalalignment='top')
            except Exception as e:
                print(f"绘制PE分位数时出错: {e}")
        
        ax2.set_title('股价走势与PE分位数', fontsize=12, fontweight='bold')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)
        
        # 合并图例
        lines1, labels1 = ax2_price.get_legend_handles_labels()
        lines2, labels2 = ax2_percentile.get_legend_handles_labels()
        ax2_price.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=8)
        
        # 下方：PE分布直方图（占据整个下半部分）
        ax3 = plt.subplot(2, 1, 2)
        n, bins, patches = ax3.hist(self.data['PE'], bins=50,
                                   edgecolor='black', alpha=0.7)
        
        mean_pe = self.data['PE'].mean()
        median_pe = self.data['PE'].median()
        current_pe = self.data['PE'].iloc[-1]
        
        # 添加均值、中位数、当前值线
        ax3.axvline(mean_pe, color='red', linestyle='--',
                   linewidth=1.5, label=f'均值: {mean_pe:.1f}')
        ax3.axvline(median_pe, color='green', linestyle='--',
                   linewidth=1.5, label=f'中位数: {median_pe:.1f}')
        ax3.axvline(current_pe, color='blue', linestyle='-',
                   linewidth=2, label=f'当前: {current_pe:.1f}')
        
        # 添加危险值、中位值、机会值线（如果数据存在）
        if 'PE危险值' in self.data.columns:
            try:
                danger_val = pd.to_numeric(self.data['PE危险值'].iloc[-1], errors='coerce')
                if not pd.isna(danger_val):
                    ax3.axvline(danger_val, color='darkred', linestyle=':',
                               linewidth=2, label=f'危险值: {danger_val:.1f}')
            except:
                pass
        
        if 'PE机会值' in self.data.columns:
            try:
                chance_val = pd.to_numeric(self.data['PE机会值'].iloc[-1], errors='coerce')
                if not pd.isna(chance_val):
                    ax3.axvline(chance_val, color='darkgreen', linestyle=':',
                               linewidth=2, label=f'机会值: {chance_val:.1f}')
            except:
                pass
        
        ax3.set_title('PE历史分布', fontsize=12, fontweight='bold')
        ax3.set_xlabel('PE值', fontsize=10)
        ax3.set_ylabel('频数', fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=8)
        
        # 添加总标题
        fig.suptitle('恒瑞医药 综合分析图表', fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"综合图表已保存至: {save_path}")
        
        return fig
    
    def generate_report(self, output_dir: str = 'charts'):
        """
        生成完整的可视化报告（只生成综合图表）
        
        Args:
            output_dir: 输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 只生成综合图表
        self.plot_all_in_one(save_path=f'{output_dir}/all_in_one.png')
        
        print(f"\n综合分析图表已生成至: {output_dir}/all_in_one.png")