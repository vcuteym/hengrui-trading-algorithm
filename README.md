# 恒瑞医药 PE回撤量化交易策略

## 项目概述
本项目实现了一个基于PE分位数和价格回撤的量化交易策略，用于分析恒瑞医药（600276）的历史数据并进行策略回测。通过参数优化和规则改进，实现了优异的回测表现。

## 策略核心
### 买入条件
1. 价格回撤超过30%（优化后阈值）
2. PE值低于65（优化后阈值）
3. 连续买入最多5次（风险控制）

### 卖出条件
1. PE值超过90（优化后阈值）
2. 每次卖出数量 = 总持股数 / 连续买入次数

## 最新成果

### 📊 策略表现
- **总资产收益率**: 670.60%
- **期初资金**: 50,000元
- **最终总资产**: 385,301元
- **最大回撤**: -2.10%
- **交易次数**: 14次买入，6次卖出

### 🎯 参数优化结果
通过网格搜索优化，找到最佳参数组合：
- **回撤阈值**: -30%（原-25%）
- **买入PE**: 65（原55）
- **卖出PE**: 90（原75）
- **优化后收益率**: 1639.72%（仅需1万初始资金）

### 🐂🐻 牛熊市分析
- 识别出6个市场周期（5个牛市，1个熊市）
- 牛市平均持续2.6年
- 熊市持续3.8年
- 策略在不同市场环境下均表现稳健

## 项目结构
```
├── data/                    # 数据处理模块
├── strategy/                # 策略实现
│   ├── trading_strategy.py  # 交易策略
│   └── market_cycle.py      # 牛熊市分析
├── optimization/            # 参数优化
├── visualization/           # 可视化
├── scripts/                 # 执行脚本
│   ├── run_full_analysis.py # 完整分析
│   ├── optimize_parameters.py # 参数优化
│   └── analyze_market_cycles.py # 周期分析
├── report/                  # 输出报告
└── PE.xlsx                  # 原始数据
```

## 运行指南

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行完整分析
```bash
python scripts/run_full_analysis.py
```

### 参数优化
```bash
python scripts/optimize_parameters.py
```

### 牛熊市分析
```bash
python scripts/analyze_market_cycles.py
```

## 关键创新

1. **连续买入限制**: 最多连续买入5次，避免过度集中
2. **动态卖出策略**: 根据买入次数动态调整卖出数量
3. **参数优化**: 通过网格搜索找到最优参数组合
4. **市场周期识别**: 自动识别牛熊市，分析策略表现

## 输出文件
- `report/strategy_trades.xlsx` - 交易记录
- `report/strategy_trades_enhanced.xlsx` - 增强版记录
- `report/asset_curve.png` - 资产曲线图
- `report/all_in_one.png` - 综合分析图
- `report/market_cycles.xlsx` - 牛熊市周期
- `report/optimization_results.xlsx` - 优化结果

## 技术栈
- Python 3.10+
- Pandas - 数据处理
- NumPy - 数值计算
- Matplotlib - 数据可视化
- Seaborn - 统计图表
- Openpyxl - Excel处理

## 贡献者
- 策略设计与实现
- 参数优化
- 市场周期分析

## License
MIT License

## 更新日志
- 2024-12 - 增加连续买入限制和动态卖出策略
- 2024-12 - 完成参数优化，收益率提升至1639%
- 2024-12 - 增加牛熊市周期识别功能
- 2024-12 - 项目结构重构和文档完善