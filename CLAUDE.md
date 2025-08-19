# 恒瑞交易算法测试项目 - 开发指南

## 项目概述
本项目用于恒瑞交易算法的开发和测试，主要数据文件为 `PE.xlsx`。

## Git 版本控制规范

### 分支管理策略

1. **主分支 (main/master)**
   - 保持稳定，只包含经过测试的代码
   - 不直接在主分支上开发

2. **功能分支命名规范**
   - 新算法：`algorithm/算法名称` (例：`algorithm/momentum-strategy`)
   - 新功能：`feature/功能名称` (例：`feature/data-preprocessing`)
   - 修复：`fix/问题描述` (例：`fix/calculation-error`)
   - 优化：`optimize/优化内容` (例：`optimize/performance`)

### 开发流程

1. **创建新分支**
   ```bash
   git checkout -b feature/新功能名称
   ```

2. **提交规范**
   - 每修改一个文件或完成一个小功能就要提交
   - 提交信息格式：
     - `feat: 添加新功能`
     - `fix: 修复问题`
     - `refactor: 重构代码`
     - `test: 添加测试`
     - `docs: 更新文档`
     - `style: 代码格式调整`

3. **示例提交流程**
   ```bash
   git add 修改的文件
   git commit -m "feat: 添加数据清洗功能"
   ```

### 测试要求

1. **每个新功能必须测试**
   - 单元测试：测试单个函数/方法
   - 集成测试：测试功能模块
   - 回测：验证算法效果

2. **测试文件组织**
   ```
   tests/
   ├── test_algorithms/    # 算法测试
   ├── test_data/          # 数据处理测试
   └── test_utils/         # 工具函数测试
   ```

3. **运行测试**
   ```bash
   # 运行所有测试
   pytest
   
   # 运行特定测试
   pytest tests/test_algorithms/
   ```

### 合并流程

1. **功能完成后**
   ```bash
   # 切换到主分支
   git checkout main
   
   # 更新主分支
   git pull origin main
   
   # 合并功能分支
   git merge feature/新功能名称
   ```

2. **推送到 GitHub**
   ```bash
   git push origin main
   ```

## 项目结构建议

```
.
├── PE.xlsx              # 主数据文件
├── algorithms/          # 算法实现
│   ├── __init__.py
│   └── strategy.py
├── data/               # 数据处理
│   ├── __init__.py
│   └── preprocessing.py
├── tests/              # 测试文件
│   └── test_*.py
├── results/            # 结果输出
├── logs/               # 日志文件
├── requirements.txt    # 依赖包
├── .gitignore         # Git忽略文件
├── README.md          # 项目说明
└── CLAUDE.md          # 本文件

```

## 常用命令速查

### Git 基础命令
```bash
# 查看状态
git status

# 查看分支
git branch -a

# 创建并切换分支
git checkout -b 分支名

# 添加文件
git add 文件名
git add .  # 添加所有修改

# 提交
git commit -m "提交信息"

# 查看提交历史
git log --oneline

# 推送到远程
git push origin 分支名
```

### 测试命令
```bash
# 运行测试
pytest

# 运行测试并显示覆盖率
pytest --cov=.

# 运行特定测试文件
pytest tests/test_specific.py
```

## 开发检查清单

- [ ] 新功能在独立分支开发
- [ ] 每个文件修改都有对应的 commit
- [ ] 提交信息清晰明确
- [ ] 新功能有对应的测试
- [ ] 测试全部通过
- [ ] 代码符合规范
- [ ] 合并前更新主分支
- [ ] 推送到 GitHub 远程仓库

## 注意事项

1. **不要直接修改 PE.xlsx 原始数据文件**
   - 创建副本进行测试
   - 使用代码读取和处理数据

2. **敏感信息处理**
   - 不要提交包含密码、API密钥的文件
   - 使用环境变量管理敏感配置

3. **定期备份**
   - 定期推送到 GitHub
   - 重要版本打标签 (tag)

## 联系与支持

如有问题，请查看项目 README.md 或提交 Issue。