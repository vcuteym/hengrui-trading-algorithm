# 恒瑞交易算法测试项目规范

## 项目概述
本项目是一个基于PE分位数和回撤率的量化交易策略系统，用于分析恒瑞医药的历史数据并进行策略回测。

## 文件组织规则

### 目录结构规范
请严格遵循以下文件组织规则，确保文件总是放在适当的文件夹中：

```
项目根目录/
├── data/                    # 数据相关文件
│   ├── *.py                # 数据读取和处理模块
│   └── *.xlsx, *.csv       # 原始数据文件
│
├── strategy/                # 策略相关文件
│   ├── trading_strategy.py # 交易策略实现
│   ├── market_cycle.py     # 牛熊市周期分析
│   └── *.py                # 其他策略模块
│
├── optimization/            # 优化相关文件
│   ├── optimizer.py        # 优化器基类
│   ├── grid_search.py      # 网格搜索
│   ├── bayesian_optimizer.py # 贝叶斯优化
│   └── optimization_result.py # 结果处理
│
├── visualization/           # 可视化相关文件
│   ├── plotter.py          # 绘图模块
│   └── *.py                # 其他可视化工具
│
├── scripts/                 # 可执行脚本
│   ├── run_*.py            # 运行脚本
│   ├── analyze_market_cycles.py # 牛熊市分析脚本
│   ├── test_*.py           # 测试脚本
│   ├── calculate_*.py      # 计算脚本
│   └── *.py                # 其他工具脚本
│
├── tests/                   # 单元测试文件
│   ├── test_*.py           # 测试文件
│   └── conftest.py         # pytest配置
│
├── report/                  # 输出报告和结果
│   ├── *.png               # 图表文件
│   ├── *.xlsx              # Excel报告
│   ├── *.csv               # CSV数据导出
│   ├── *.json              # JSON数据文件
│   └── *.html, *.pdf       # 其他格式报告
│
├── config/                  # 配置文件
│   ├── *.json              # JSON配置
│   ├── *.yaml              # YAML配置
│   └── *.ini               # INI配置
│
├── docs/                    # 文档文件
│   ├── README.md           # 项目说明
│   ├── *.md                # Markdown文档
│   └── 工作日志.md          # 工作记录
│
├── hooks/                   # Git钩子和自动化脚本
│   ├── *.sh                # Shell脚本
│   └── backups/            # 备份文件
│
├── test_optimization_results/ # 参数优化测试结果
│   └── *.json              # 优化结果文件
│
├── PE.xlsx                  # 原始数据文件
├── requirements.txt         # Python依赖
├── CLAUDE.md               # 项目规范文档
└── .gitignore              # Git忽略规则
```

### 文件命名规范

1. **Python模块**：
   - 使用小写字母和下划线：`trading_strategy.py`
   - 测试文件以`test_`开头：`test_reader.py`
   - 运行脚本以动词开头：`run_strategy.py`, `calculate_returns.py`

2. **数据文件**：
   - 原始数据保持原名：`PE.xlsx`
   - 导出数据包含日期或版本：`strategy_trades_20240815.xlsx`

3. **报告文件**：
   - 描述性命名：`asset_curve.png`, `strategy_evaluation.xlsx`
   - 避免使用空格，用下划线代替

### 禁止事项

1. **不要**在根目录创建新的Python脚本，应放入`scripts/`
2. **不要**将测试结果直接保存在根目录，应放入`report/`或`test_optimization_results/`
3. **不要**在代码目录中保存输出文件
4. **不要**创建重复功能的文件

### 最佳实践

1. **新功能开发**：
   - 先在`scripts/`中创建原型脚本
   - 稳定后将核心逻辑提取到相应模块目录

2. **数据处理**：
   - 原始数据放在`data/`或根目录
   - 处理后的数据保存到`report/`

3. **测试和优化**：
   - 测试脚本放在`tests/`
   - 优化结果保存到`test_optimization_results/`

## 运行指南

### 基本运行命令
```bash
# 完整分析流程（包含牛熊市分析）
python scripts/run_full_analysis.py

# 单独运行策略
python scripts/run_strategy.py

# 牛熊市周期分析
python scripts/analyze_market_cycles.py

# 查看优化结果
python scripts/view_results.py

# 参数优化
python run_optimization.py
```

### 牛熊市分析功能

**新增功能：** 根据PE.xlsx数据自动识别牛熊市区间

**核心特性：**
- 基于股价走势和PE分位数识别市场周期
- 每个周期最少2年，确保可靠性
- 分析策略在不同市场环境下的表现
- 生成可视化图表和详细报告

**输出文件：**
- `report/market_cycles.json` - 周期数据（JSON格式）
- `report/market_cycles.xlsx` - 周期汇总表
- `report/market_cycles.png` - 牛熊市可视化图表
- `report/market_cycles_summary.xlsx` - 周期统计汇总
- `report/strategy_by_cycle.xlsx` - 策略在各周期的表现

**识别结果示例：**
```
识别出 6 个市场周期:
- 牛市: 5 个，平均持续 2.6 年
- 熊市: 1 个，平均持续 3.8 年
```

### 关键性能指标
- 期初现金：60,000元
- 目标收益率：> 500%
- 最大可接受回撤：< 5%
- 当前策略收益率：655.03%

## 注意事项
- 所有新创建的文件必须遵循上述目录结构
- 提交代码前运行 lint 和测试
- 重要修改需要更新工作日志
- 牛熊市区间最少2年，确保周期识别的可靠性