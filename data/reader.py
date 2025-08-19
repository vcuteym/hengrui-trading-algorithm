import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any


class DataReader:
    """PE数据读取器"""
    
    COLUMN_MAPPING = {
        'PE-TTM-S': 'PE',
        '投数网前复权': '股价',
        '分位点': 'PE分位数',
        '危险值': 'PE危险值',
        '中位值': 'PE中位值',
        '机会值': 'PE机会值'
    }
    
    def __init__(self, file_path: str = 'PE.xlsx'):
        """
        初始化数据读取器
        
        Args:
            file_path: Excel文件路径
        """
        self.file_path = Path(file_path)
        self.data = None
        self.processed_data = None
        
    def read_data(self) -> pd.DataFrame:
        """
        读取Excel数据
        
        Returns:
            原始数据DataFrame
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.file_path}")
        
        self.data = pd.read_excel(self.file_path)
        print(f"成功读取数据，形状: {self.data.shape}")
        print(f"列名: {list(self.data.columns)}")
        
        return self.data
    
    def fill_missing_values(self, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        处理缺失值，使用邻近值填充
        
        Args:
            data: 要处理的数据，如果为None则使用self.data
            
        Returns:
            处理后的数据DataFrame
        """
        if data is None:
            if self.data is None:
                raise ValueError("请先调用read_data()读取数据")
            data = self.data.copy()
        else:
            data = data.copy()
        
        print(f"\n处理前缺失值统计:")
        print(data.isnull().sum())
        
        # 使用前向填充，然后后向填充处理边界情况
        data = data.ffill()
        data = data.bfill()
        
        # 如果还有缺失值（整列都是NaN的情况），使用该列的均值或0
        for col in data.columns:
            if data[col].isnull().any():
                if data[col].dtype in ['float64', 'int64']:
                    # 数值列使用0填充
                    data[col] = data[col].fillna(0)
                else:
                    # 非数值列使用空字符串
                    data[col] = data[col].fillna('')
        
        print(f"\n处理后缺失值统计:")
        print(data.isnull().sum())
        
        return data
    
    def rename_columns(self, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        重命名列以便更好理解
        
        Args:
            data: 要处理的数据
            
        Returns:
            重命名后的数据DataFrame
        """
        if data is None:
            if self.data is None:
                raise ValueError("请先调用read_data()读取数据")
            data = self.data.copy()
        else:
            data = data.copy()
        
        # 创建重命名映射，保留原列名中存在的列
        rename_dict = {k: v for k, v in self.COLUMN_MAPPING.items() if k in data.columns}
        
        if rename_dict:
            data = data.rename(columns=rename_dict)
            print(f"\n已重命名列: {rename_dict}")
        
        return data
    
    def process_data(self) -> pd.DataFrame:
        """
        完整的数据处理流程
        
        Returns:
            处理后的数据DataFrame
        """
        # 读取数据
        self.read_data()
        
        # 处理缺失值
        processed = self.fill_missing_values()
        
        # 重命名列
        processed = self.rename_columns(processed)
        
        # 特殊处理PE分位数列中的"--"
        if 'PE分位数' in processed.columns:
            processed['PE分位数'] = processed['PE分位数'].replace('--', np.nan)
            # 尝试转换为数值类型
            processed['PE分位数'] = pd.to_numeric(processed['PE分位数'], errors='coerce')
        
        # 计算回撤（当前股价/一年内最高股价 - 1）
        if '股价' in processed.columns:
            processed = self.calculate_drawdown(processed)
        
        self.processed_data = processed
        
        print(f"\n数据处理完成!")
        print(f"最终数据形状: {processed.shape}")
        print(f"最终列名: {list(processed.columns)}")
        
        return processed
    
    def calculate_drawdown(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算回撤（当前股价/一年内最高股价 - 1）
        
        Args:
            data: 包含股价的数据DataFrame
            
        Returns:
            添加了回撤列的DataFrame
        """
        data = data.copy()
        
        # 确保日期列是datetime类型
        if '日期' in data.columns:
            data['日期'] = pd.to_datetime(data['日期'])
            # 按日期排序（从旧到新）
            data = data.sort_values('日期')
        
        # 计算252个交易日（约一年）的滚动最高价
        window_size = 252
        data['一年内最高价'] = data['股价'].rolling(window=window_size, min_periods=1).max()
        
        # 计算回撤
        data['回撤'] = data['股价'] / data['一年内最高价'] - 1
        
        # 回撤以百分比形式存储
        data['回撤'] = data['回撤'] * 100
        
        print(f"回撤计算完成，范围: {data['回撤'].min():.2f}% 到 {data['回撤'].max():.2f}%")
        
        return data
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要信息
        
        Returns:
            包含数据摘要信息的字典
        """
        if self.processed_data is None:
            raise ValueError("请先调用process_data()处理数据")
        
        summary = {
            '数据形状': self.processed_data.shape,
            '列名': list(self.processed_data.columns),
            '数据类型': self.processed_data.dtypes.to_dict(),
            '基本统计': {}
        }
        
        # 对数值列进行统计
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            summary['基本统计'][col] = {
                '均值': self.processed_data[col].mean(),
                '标准差': self.processed_data[col].std(),
                '最小值': self.processed_data[col].min(),
                '最大值': self.processed_data[col].max(),
                '中位数': self.processed_data[col].median()
            }
        
        return summary


def main():
    """主函数，演示数据读取器的使用"""
    reader = DataReader('PE.xlsx')
    
    # 处理数据
    processed_data = reader.process_data()
    
    # 获取摘要
    summary = reader.get_summary()
    
    print("\n数据摘要信息:")
    print(f"数据形状: {summary['数据形状']}")
    print(f"列数: {len(summary['列名'])}")
    
    # 显示前几行数据
    print("\n前5行数据:")
    print(processed_data.head())
    
    return processed_data


if __name__ == "__main__":
    main()