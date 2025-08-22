"""
市场周期划分模块
基于PE数据和股价走势识别牛市和熊市区间
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json


class MarketCycleAnalyzer:
    """
    市场周期分析器
    通过分析PE分位数、股价走势等指标识别牛熊市周期
    """
    
    def __init__(self, min_cycle_years: float = 2.0):
        """
        初始化市场周期分析器
        
        Args:
            min_cycle_years: 最小周期长度（年）
        """
        self.min_cycle_years = min_cycle_years
        self.min_cycle_days = int(min_cycle_years * 365)
        
    def identify_cycles(self, df: pd.DataFrame) -> List[Dict]:
        """
        识别市场周期
        
        策略：
        1. 计算股价的长期移动平均线（250日）
        2. 识别主要的峰值和谷值
        3. 基于PE分位数确认市场状态
        4. 合并短期波动，确保每个周期至少2年
        
        Args:
            df: 包含日期、股价、PE、PE分位数等数据的DataFrame
            
        Returns:
            周期列表，每个周期包含起止日期、类型、收益率等信息
        """
        df = df.copy()
        df = df.sort_values('日期').reset_index(drop=True)
        
        # 计算技术指标
        df['MA250'] = df['股价'].rolling(window=250, min_periods=50).mean()
        df['价格相对强度'] = df['股价'] / df['MA250']
        
        # 计算股价的峰值和谷值
        peaks, troughs = self._find_peaks_and_troughs(df)
        
        # 基于峰谷值初步划分周期
        raw_cycles = self._create_raw_cycles(df, peaks, troughs)
        
        # 合并短周期
        merged_cycles = self._merge_short_cycles(raw_cycles, df)
        
        # 计算周期统计信息
        final_cycles = self._calculate_cycle_stats(merged_cycles, df)
        
        return final_cycles
    
    def _find_peaks_and_troughs(self, df: pd.DataFrame, window: int = 120) -> Tuple[List[int], List[int]]:
        """
        寻找股价的主要峰值和谷值
        
        Args:
            df: 数据DataFrame
            window: 滚动窗口大小（天）
            
        Returns:
            (峰值索引列表, 谷值索引列表)
        """
        prices = df['股价'].values
        n = len(prices)
        
        # 计算滚动最大值和最小值
        peaks = []
        troughs = []
        
        for i in range(window, n - window):
            # 检查是否为局部最大值
            if prices[i] == max(prices[max(0, i-window):min(n, i+window+1)]):
                # 避免重复的峰值
                if not peaks or i - peaks[-1] > window:
                    peaks.append(i)
            
            # 检查是否为局部最小值
            if prices[i] == min(prices[max(0, i-window):min(n, i+window+1)]):
                # 避免重复的谷值
                if not troughs or i - troughs[-1] > window:
                    troughs.append(i)
        
        return peaks, troughs
    
    def _create_raw_cycles(self, df: pd.DataFrame, peaks: List[int], troughs: List[int]) -> List[Dict]:
        """
        基于峰谷值创建初步的市场周期
        
        Args:
            df: 数据DataFrame
            peaks: 峰值索引列表
            troughs: 谷值索引列表
            
        Returns:
            初步周期列表
        """
        # 合并峰谷值并排序
        turning_points = []
        for p in peaks:
            turning_points.append({'index': p, 'type': 'peak'})
        for t in troughs:
            turning_points.append({'index': t, 'type': 'trough'})
        
        turning_points.sort(key=lambda x: x['index'])
        
        # 创建周期
        cycles = []
        for i in range(len(turning_points) - 1):
            current = turning_points[i]
            next_point = turning_points[i + 1]
            
            # 从谷到峰为牛市，从峰到谷为熊市
            if current['type'] == 'trough' and next_point['type'] == 'peak':
                cycle_type = 'bull'
            elif current['type'] == 'peak' and next_point['type'] == 'trough':
                cycle_type = 'bear'
            else:
                # 相同类型的转折点，取中点作为分界
                mid_point = (current['index'] + next_point['index']) // 2
                if current['type'] == 'trough':
                    # 两个谷值之间，前半段上涨，后半段下跌
                    cycles.append({
                        'start_idx': current['index'],
                        'end_idx': mid_point,
                        'type': 'bull',
                        'start_date': df.iloc[current['index']]['日期'],
                        'end_date': df.iloc[mid_point]['日期']
                    })
                    cycles.append({
                        'start_idx': mid_point,
                        'end_idx': next_point['index'],
                        'type': 'bear',
                        'start_date': df.iloc[mid_point]['日期'],
                        'end_date': df.iloc[next_point['index']]['日期']
                    })
                else:
                    # 两个峰值之间，前半段下跌，后半段上涨
                    cycles.append({
                        'start_idx': current['index'],
                        'end_idx': mid_point,
                        'type': 'bear',
                        'start_date': df.iloc[current['index']]['日期'],
                        'end_date': df.iloc[mid_point]['日期']
                    })
                    cycles.append({
                        'start_idx': mid_point,
                        'end_idx': next_point['index'],
                        'type': 'bull',
                        'start_date': df.iloc[mid_point]['日期'],
                        'end_date': df.iloc[next_point['index']]['日期']
                    })
                continue
            
            cycles.append({
                'start_idx': current['index'],
                'end_idx': next_point['index'],
                'type': cycle_type,
                'start_date': df.iloc[current['index']]['日期'],
                'end_date': df.iloc[next_point['index']]['日期']
            })
        
        return cycles
    
    def _merge_short_cycles(self, cycles: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """
        合并过短的周期，确保每个周期至少2年
        
        Args:
            cycles: 初步周期列表
            df: 数据DataFrame
            
        Returns:
            合并后的周期列表
        """
        if not cycles:
            return []
        
        merged = []
        current = cycles[0].copy()
        
        for next_cycle in cycles[1:]:
            # 计算当前周期的长度
            current_days = (current['end_date'] - current['start_date']).days
            
            if current_days < self.min_cycle_days:
                # 如果当前周期太短，尝试与下一个周期合并
                if current['type'] == next_cycle['type']:
                    # 相同类型，直接合并
                    current['end_idx'] = next_cycle['end_idx']
                    current['end_date'] = next_cycle['end_date']
                else:
                    # 不同类型，根据整体趋势决定类型
                    combined_start_idx = current['start_idx']
                    combined_end_idx = next_cycle['end_idx']
                    
                    start_price = df.iloc[combined_start_idx]['股价']
                    end_price = df.iloc[combined_end_idx]['股价']
                    
                    # 根据起止价格判断整体趋势
                    if end_price > start_price * 1.2:  # 上涨超过20%认为是牛市
                        combined_type = 'bull'
                    elif end_price < start_price * 0.8:  # 下跌超过20%认为是熊市
                        combined_type = 'bear'
                    else:
                        # 横盘震荡，根据PE分位数判断
                        avg_pe_percentile = df.iloc[combined_start_idx:combined_end_idx+1]['PE分位数'].mean()
                        combined_type = 'bull' if avg_pe_percentile < 50 else 'bear'
                    
                    current['end_idx'] = next_cycle['end_idx']
                    current['end_date'] = next_cycle['end_date']
                    current['type'] = combined_type
            else:
                # 当前周期足够长，保存并开始新周期
                merged.append(current)
                current = next_cycle.copy()
        
        # 添加最后一个周期
        if current:
            # 检查最后一个周期是否太短
            current_days = (current['end_date'] - current['start_date']).days
            if current_days < self.min_cycle_days and merged:
                # 与前一个周期合并
                last = merged[-1]
                last['end_idx'] = current['end_idx']
                last['end_date'] = current['end_date']
                # 重新判断类型
                start_price = df.iloc[last['start_idx']]['股价']
                end_price = df.iloc[last['end_idx']]['股价']
                if end_price > start_price:
                    last['type'] = 'bull'
                else:
                    last['type'] = 'bear'
            else:
                merged.append(current)
        
        return merged
    
    def _calculate_cycle_stats(self, cycles: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """
        计算每个周期的统计信息
        
        Args:
            cycles: 周期列表
            df: 数据DataFrame
            
        Returns:
            包含统计信息的周期列表
        """
        enhanced_cycles = []
        
        for cycle in cycles:
            start_idx = cycle['start_idx']
            end_idx = cycle['end_idx']
            cycle_data = df.iloc[start_idx:end_idx+1]
            
            # 基本信息
            enhanced = cycle.copy()
            enhanced['duration_days'] = (cycle['end_date'] - cycle['start_date']).days
            enhanced['duration_years'] = enhanced['duration_days'] / 365
            
            # 价格变化
            start_price = df.iloc[start_idx]['股价']
            end_price = df.iloc[end_idx]['股价']
            enhanced['start_price'] = start_price
            enhanced['end_price'] = end_price
            enhanced['price_change'] = end_price - start_price
            enhanced['price_change_pct'] = ((end_price / start_price) - 1) * 100
            
            # PE统计
            enhanced['avg_pe'] = cycle_data['PE'].mean()
            enhanced['max_pe'] = cycle_data['PE'].max()
            enhanced['min_pe'] = cycle_data['PE'].min()
            enhanced['avg_pe_percentile'] = cycle_data['PE分位数'].mean()
            
            # 最高最低价
            enhanced['highest_price'] = cycle_data['股价'].max()
            enhanced['lowest_price'] = cycle_data['股价'].min()
            enhanced['max_drawdown'] = ((cycle_data['股价'].min() / cycle_data['股价'].max()) - 1) * 100
            
            # 验证周期类型
            if enhanced['price_change_pct'] > 20 and cycle['type'] == 'bear':
                enhanced['type'] = 'bull'  # 修正类型
            elif enhanced['price_change_pct'] < -20 and cycle['type'] == 'bull':
                enhanced['type'] = 'bear'  # 修正类型
            
            enhanced_cycles.append(enhanced)
        
        return enhanced_cycles
    
    def analyze_cycles_with_strategy(self, df: pd.DataFrame, trades_df: pd.DataFrame) -> Dict:
        """
        分析市场周期中的策略表现
        
        Args:
            df: 市场数据DataFrame
            trades_df: 交易记录DataFrame
            
        Returns:
            包含周期分析和策略表现的字典
        """
        # 识别市场周期
        cycles = self.identify_cycles(df)
        
        # 分析每个周期中的策略表现
        for cycle in cycles:
            # 获取该周期内的交易
            cycle_trades = trades_df[
                (trades_df['日期'] >= cycle['start_date']) &
                (trades_df['日期'] <= cycle['end_date'])
            ]
            
            # 统计交易信息
            buy_trades = cycle_trades[cycle_trades['操作'] == 'BUY']
            sell_trades = cycle_trades[cycle_trades['操作'] == 'SELL']
            
            cycle['num_trades'] = len(cycle_trades)
            cycle['num_buys'] = len(buy_trades)
            cycle['num_sells'] = len(sell_trades)
            
            # 计算周期内的收益
            if len(cycle_trades) > 0:
                cycle['cycle_profit'] = cycle_trades['总收益'].iloc[-1] - (
                    cycle_trades['总收益'].iloc[0] if len(cycle_trades) > 0 else 0
                )
            else:
                cycle['cycle_profit'] = 0
        
        # 汇总统计
        bull_cycles = [c for c in cycles if c['type'] == 'bull']
        bear_cycles = [c for c in cycles if c['type'] == 'bear']
        
        summary = {
            'total_cycles': len(cycles),
            'bull_cycles': len(bull_cycles),
            'bear_cycles': len(bear_cycles),
            'avg_bull_duration_years': np.mean([c['duration_years'] for c in bull_cycles]) if bull_cycles else 0,
            'avg_bear_duration_years': np.mean([c['duration_years'] for c in bear_cycles]) if bear_cycles else 0,
            'avg_bull_return': np.mean([c['price_change_pct'] for c in bull_cycles]) if bull_cycles else 0,
            'avg_bear_return': np.mean([c['price_change_pct'] for c in bear_cycles]) if bear_cycles else 0,
            'cycles': cycles
        }
        
        return summary
    
    def export_cycles(self, cycles: List[Dict], filename: str):
        """
        导出周期数据到文件
        
        Args:
            cycles: 周期列表
            filename: 输出文件名
        """
        # 转换日期格式以便JSON序列化
        export_cycles = []
        for cycle in cycles:
            export_cycle = cycle.copy()
            export_cycle['start_date'] = cycle['start_date'].strftime('%Y-%m-%d')
            export_cycle['end_date'] = cycle['end_date'].strftime('%Y-%m-%d')
            export_cycles.append(export_cycle)
        
        # 保存为JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_cycles, f, ensure_ascii=False, indent=2)
        
        # 同时保存为Excel
        df_cycles = pd.DataFrame(export_cycles)
        excel_filename = filename.replace('.json', '.xlsx')
        df_cycles.to_excel(excel_filename, index=False)
        
        print(f"周期数据已保存至: {filename}")
        print(f"Excel版本已保存至: {excel_filename}")