# 恒瑞交易算法测试项目

PE数据分析与交易策略开发平台

## 项目简介

本项目用于恒瑞医药(600276)的PE数据分析和交易策略开发。通过读取和分析历史PE数据，开发量化交易策略。

## 主要功能

- ✅ **数据读取模块**：从Excel文件读取PE数据，自动处理缺失值
- 🚧 交易策略开发（开发中）
- 🚧 回测系统（规划中）
- 🚧 风险管理（规划中）

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from data.reader import DataReader

# 创建数据读取器
reader = DataReader('PE.xlsx')

# 读取并处理数据
processed_data = reader.process_data()

# 获取数据摘要
summary = reader.get_summary()
```

### 运行示例

```bash
python example_usage.py
```

### 运行测试

```bash
python tests/test_reader.py
```

## 项目结构

```
.
├── PE.xlsx              # 原始数据文件
├── data/               # 数据处理模块
│   ├── __init__.py
│   └── reader.py       # 数据读取器
├── tests/              # 测试文件
│   └── test_reader.py  # 数据读取器测试
├── example_usage.py    # 使用示例
├── requirements.txt    # 项目依赖
├── CLAUDE.md          # 开发指南
└── README.md          # 本文件
```

## 数据说明

- **PE-TTM-S**：市盈率（PE）
- **投数网前复权**：股价
- **分位点**：PE所处历史分位数
- **危险值**：PE危险值阈值
- **中位值**：PE中位值
- **机会值**：PE机会值阈值

## 开发规范

详细的开发规范请参考 [CLAUDE.md](CLAUDE.md)

### 分支管理

- `main`：主分支，保持稳定
- `feature/*`：功能开发分支
- `fix/*`：修复分支

### 提交规范

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 代码重构

## 依赖要求

- Python 3.7+
- pandas >= 1.3.0
- numpy >= 1.21.0
- openpyxl >= 3.0.0
- pytest >= 7.0.0

## 许可证

MIT License

## 联系方式

如有问题，请提交 [Issue](https://github.com/vcuteym/hengrui-trading-algorithm/issues)