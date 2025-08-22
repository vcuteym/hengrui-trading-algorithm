# 📊 交易策略参数优化模块

自动化优化交易策略的关键参数：买入PE阈值、卖出PE阈值和回撤比例。

## ✨ 核心功能

### 1. **网格搜索优化** (Grid Search)
- 系统遍历所有参数组合
- 适合参数空间较小的情况
- 保证找到全局最优解

### 2. **贝叶斯优化** (Bayesian Optimization)
- 智能搜索参数空间
- 使用高斯过程建模
- 效率更高，适合大参数空间

### 3. **优化结果分析**
- 自动生成优化报告
- 参数敏感性分析
- 可视化图表输出

## 🚀 快速开始

### 安装依赖

```bash
pip install scikit-optimize pandas numpy matplotlib tqdm
```

### 基本使用

#### 1. 使用测试脚本（推荐）

```bash
# 运行完整测试
python scripts/test_optimization.py
```

#### 2. 使用真实数据优化

```bash
# 网格搜索优化
python run_optimization.py --method grid --n_trials 50

# 贝叶斯优化
python run_optimization.py --method bayesian --n_trials 100

# 同时运行两种方法
python run_optimization.py --method both --n_trials 50
```

### 命令行参数

```bash
python run_optimization.py [选项]

选项:
  --method {grid,bayesian,both}  优化方法
  --config CONFIG                配置文件路径 (默认: config/optimization_config.json)
  --data DATA                    数据文件路径
  --n_trials N                   试验次数
  --objective {total_return,sharpe_ratio,max_drawdown,profit_factor}
                                 优化目标
  --output OUTPUT                输出目录 (默认: ./optimization_results)
```

## 📝 配置文件

编辑 `config/optimization_config.json` 来自定义优化设置：

```json
{
  "optimization_settings": {
    "objective": "sharpe_ratio",    // 优化目标
    "n_trials": 100,                // 试验次数
    "n_jobs": 1,                     // 并行任务数
    "early_stopping": true,          // 是否启用早停
    "early_stopping_rounds": 20     // 早停轮数
  },
  
  "parameter_ranges": {
    "buy_pe_threshold": {
      "min": 30,        // 最小值
      "max": 70,        // 最大值
      "step": 5         // 步长（网格搜索用）
    },
    "sell_pe_threshold": {
      "min": 60,
      "max": 100,
      "step": 5
    },
    "drawdown_threshold": {
      "min": -0.40,     // -40%
      "max": -0.10,     // -10%
      "step": 0.05
    }
  }
}
```

## 📊 优化目标

可选择的优化目标：

- **total_return**: 总收益率
- **sharpe_ratio**: 夏普比率（风险调整收益）
- **max_drawdown**: 最大回撤（负值，越小越好）
- **profit_factor**: 盈利因子

## 📈 输出结果

优化完成后会生成：

### 1. **优化报告** (`optimization_report_*.txt`)
```
最优参数组合:
  buy_pe_threshold: 45.00
  sell_pe_threshold: 85.00
  drawdown_threshold: -20.00%

最优性能指标:
  总收益率: 150.23%
  年化收益率: 12.34%
  最大回撤: -15.67%
  夏普比率: 1.23
```

### 2. **可视化图表**
- **优化历史图**: 显示优化收敛过程
- **参数敏感性图**: 分析各参数对结果的影响
- **参数空间探索图**: 展示参数组合与性能的关系

### 3. **数据文件**
- **CSV摘要**: 所有试验结果的详细数据
- **JSON配置**: 最优参数组合，可直接用于策略

## 🔧 高级用法

### 自定义优化

```python
from optimization.grid_search import GridSearchOptimizer
from optimization.optimizer import OptimizationConfig, ParameterRange

# 定义参数范围
parameter_ranges = {
    'buy_pe_threshold': ParameterRange('buy_pe_threshold', 40, 60, 5),
    'sell_pe_threshold': ParameterRange('sell_pe_threshold', 70, 90, 5),
    'drawdown_threshold': ParameterRange('drawdown_threshold', -0.30, -0.15, 0.05)
}

# 创建配置
config = OptimizationConfig(
    parameter_ranges=parameter_ranges,
    objective='sharpe_ratio',
    n_trials=100,
    verbose=True
)

# 运行优化
optimizer = GridSearchOptimizer(data, config)
best_trial = optimizer.optimize()

# 获取最优参数
print(f"最优参数: {best_trial.parameters}")
print(f"最优性能: {best_trial.metrics}")
```

### 批量优化不同股票

```python
for stock_file in stock_files:
    data = pd.read_excel(stock_file)
    optimizer = BayesianOptimizer(data, config)
    best = optimizer.optimize()
    optimizer.save_results(f'results/{stock_name}.json')
```

## 📊 性能指标说明

| 指标 | 说明 | 理想值 |
|------|------|--------|
| 总收益率 | 策略的总回报率 | 越高越好 |
| 年化收益率 | 年化后的收益率 | > 15% |
| 最大回撤 | 最大亏损幅度 | > -20% |
| 夏普比率 | 风险调整后收益 | > 1.0 |
| 盈利因子 | 总盈利/总亏损 | > 1.5 |
| 交易次数 | 总交易次数 | 适中 |
| 胜率 | 盈利交易占比 | > 50% |

## ⚠️ 注意事项

1. **数据格式**: 确保数据包含`日期`、`收盘`/`股价`、`PE`、`回撤`列
2. **计算资源**: 贝叶斯优化需要安装scikit-optimize
3. **并行计算**: 设置n_jobs>1可加速网格搜索
4. **过拟合风险**: 避免过度优化，建议使用交叉验证

## 🤝 贡献

欢迎提交Issue和Pull Request来改进优化算法！

## 📄 许可

MIT License