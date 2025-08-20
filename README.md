# 恒瑞医药 PE回撤交易策略

## 项目概述
本项目实现了基于PE值和股价回撤的量化交易策略，用于恒瑞医药（600276）的历史回测分析。

## 策略核心逻辑

### 买入条件（同时满足）
1. 股价回撤 < -25%（相对一年内最高价）
2. PE < 55
3. 距离上次买入 > 30天

### 卖出条件
1. PE > 75
2. 每次卖出50%持仓
3. 距离上次卖出 > 30天

### 资金管理
- 每次买入金额：10,000元
- 最小买入股数：0.01股
- 起始日期：2010-07-22

## 策略表现（2011-2025）

### 收益指标
- **总收益率**：655.03%
- **年化收益率**：15.68%
- **最终总资产**：453,019元（初始60,000元）

### 风险指标
- **年化波动率**：19.90%
- **最大回撤**：-24.72%
- **夏普比率**：0.637
- **卡尔玛比率**：0.634

### 交易统计
- **买入次数**：25次
- **卖出次数**：33次
- **日胜率**：50.73%
- **盈亏比**：1.16

## 与买入持有对比

| 指标 | PE回撤策略 | 买入持有 | 优势 |
|------|-----------|---------|------|
| 总收益率 | 655% | 1209% | 买入持有 |
| 年化波动率 | 19.90% | 33.08% | **PE策略✓** |
| 最大回撤 | -24.72% | -70.99% | **PE策略✓** |
| 夏普比率 | 0.637 | 0.525 | **PE策略✓** |

**结论**：PE回撤策略虽然绝对收益低于买入持有，但风险控制能力显著更优，适合风险厌恶型投资者。

## 项目结构

```
.
├── PE.xlsx                         # 原始数据文件
├── README.md                       # 项目说明（本文件）
├── 工作日志.md                     # 开发日志
│
├── data/                          # 数据处理模块
│   └── reader.py                  # 数据读取和预处理
│
├── strategy/                      # 策略模块
│   └── trading_strategy.py        # 交易策略实现
│
├── visualization/                 # 可视化模块
│   └── plotter.py                # 图表绘制
│
├── calculate_returns.py           # 收益率和资产曲线计算
├── evaluate_strategy.py           # 策略评估（夏普比率等）
├── strategy_comparison.py         # 策略对比分析
├── run_full_analysis.py          # 完整分析流程
├── view_results.py               # 快速查看结果
│
└── report/                       # 输出文件夹
    ├── strategy_trades.xlsx      # 交易记录
    ├── strategy_trades_enhanced.xlsx  # 增强版记录
    ├── asset_curve.png           # 资产曲线图
    ├── strategy_evaluation.png   # 评估图表
    ├── strategy_evaluation.xlsx  # 评估报告
    └── strategy_comparison.png   # 对比图表
```

## 快速开始

### 环境要求
```bash
pip install pandas numpy matplotlib openpyxl xlsxwriter
```

### 运行分析
```bash
# 完整分析流程
python run_full_analysis.py

# 单独运行策略回测
python run_strategy.py

# 计算收益率曲线
python calculate_returns.py

# 策略评估
python evaluate_strategy.py

# 策略对比
python strategy_comparison.py

# 查看结果
python view_results.py
```

## 主要功能

### 1. 数据处理（data/reader.py）
- 读取Excel数据
- 处理缺失值
- 计算股价回撤

### 2. 交易策略（strategy/trading_strategy.py）
- 可配置的策略参数
- 买卖信号生成
- 持仓管理
- 收益计算

### 3. 收益分析（calculate_returns.py）
- 计算期初现金（净现金流最小值的绝对值）
- 构建资产曲线
- 计算总资产收益率
- 生成包含日线股价的图表

### 4. 策略评估（evaluate_strategy.py）
- 夏普比率、索提诺比率、卡尔玛比率
- 最大回撤及恢复时间
- VaR和CVaR
- 日胜率和盈亏比
- 自动评级系统

### 5. 策略对比（strategy_comparison.py）
- PE策略vs买入持有
- 风险收益对比
- 滚动指标分析
- 可视化对比

## 关键发现

1. **风险控制优秀**：最大回撤仅25%，远低于买入持有的71%
2. **波动性低**：年化波动率20%，显著低于市场
3. **稳定性强**：夏普比率0.637，风险调整收益良好
4. **现金流管理**：通过高位卖出获得大量现金流（62万），远超投入（25万）

## 注意事项

- 本策略基于历史数据回测，不构成投资建议
- 实际交易需考虑交易成本、滑点等因素
- PE数据可能存在缺失（2015年前约40%缺失）

## 作者
Claude AI Assistant

## 更新日期
2024-08-20