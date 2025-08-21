# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
恒瑞医药（600276）PE回撤量化交易策略回测系统。主数据文件：`PE.xlsx`

## 核心架构

### 模块结构
- `data/reader.py` - 数据读取和预处理（处理PE.xlsx，计算回撤）
- `strategy/trading_strategy.py` - 交易策略实现（买卖信号、持仓管理）
- `visualization/plotter.py` - 图表绘制功能
- `calculate_returns.py` - 收益率和资产曲线计算
- `evaluate_strategy.py` - 策略评估（夏普比率、最大回撤等）
- `strategy_comparison.py` - 策略对比分析（vs买入持有）

### 策略核心参数
```python
StrategyConfig(
    drawdown_threshold=-0.25,      # 回撤阈值 -25%
    buy_pe_threshold=55,            # 买入PE阈值
    sell_pe_threshold=75,           # 卖出PE阈值
    start_date='2010-07-22',        # 起始日期
    buy_amount=10000,               # 每次买入金额
    sell_ratio=0.5                  # 每次卖出比例
)
```

## 常用命令

### 运行策略
```bash
# 完整分析流程（推荐）
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

### 测试命令
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_reader.py
pytest tests/test_visualization.py
```

## Git 工作流程

### 分支规范
- 功能分支：`feature/功能名称`
- 算法分支：`algorithm/算法名称`
- 修复分支：`fix/问题描述`
- 优化分支：`optimize/优化内容`

### 提交信息格式
- `feat:` 新功能
- `fix:` 修复问题
- `refactor:` 重构代码
- `test:` 添加测试
- `docs:` 更新文档
- `style:` 代码格式

### 每次修改后的工作流
```bash
# 1. 查看状态
git status

# 2. 添加修改
git add 文件名  # 或 git add .

# 3. 提交（每个功能单独提交）
git commit -m "feat: 功能描述"

# 4. 推送到远程
git push origin 分支名
```

## 数据处理注意事项

### PE.xlsx 数据结构
- 日期、代码、股票名称
- PE-TTM-S（重命名为PE）
- 危险值、中位值、机会值（PE分位）
- 投数网前复权（重命名为股价）
- 分位点（重命名为PE分位数）

### 回撤计算
- 基于一年滚动窗口最高价
- 回撤 = (当前价 - 最高价) / 最高价

## 输出文件位置
所有结果保存在 `report/` 目录：
- `strategy_trades.xlsx` - 交易记录
- `strategy_trades_enhanced.xlsx` - 增强版记录（含资产曲线）
- `asset_curve.png` - 资产曲线图
- `strategy_evaluation.png` - 评估图表
- `strategy_comparison.png` - 对比图表

## 重要规则
1. 不要直接修改 PE.xlsx 原始数据
2. 每次买入固定金额（默认10000元）
3. 卖出按比例（默认50%）
4. 最小交易间隔30天
5. 现金流计算：总收益 = 当前市值 - 现金流出 + 现金流入