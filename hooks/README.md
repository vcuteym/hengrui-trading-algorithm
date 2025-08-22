# 📦 策略版本控制 Hook 系统

自动化的交易策略文件备份和版本管理系统，专为 Claude Code 设计。

## ✨ 功能特性

### 🔄 自动备份 (pre-edit-backup.sh)
- 编辑策略文件前自动创建备份
- 智能识别策略相关文件（strategy, algo, trading, backtest等）
- 基于内容哈希的去重机制，避免重复备份
- 自动清理旧备份（保留最近50个版本）
- 完整的元数据记录

### 📝 版本控制 (post-edit-version.sh)
- 自动生成语义化版本号（major.minor.patch）
- 智能分析变更类型（重大修改/功能更新/小修复）
- 生成详细的差异报告
- 自动维护 CHANGELOG.md
- Git 集成支持

### 🛠️ 备份管理工具 (backup-manager.sh)
- 列出和搜索备份文件
- 一键恢复任意版本
- 备份文件对比
- 统计和清理功能
- 批量导出备份

## 🚀 快速开始

### 1. 安装配置

```bash
# 运行安装脚本
./hooks/setup-hooks.sh
```

这将自动：
- 配置 Claude Code 的 settings.json
- 设置必要的文件权限
- 创建备份目录结构

### 2. 使用方法

安装后，hooks 会自动工作：

- **编辑文件时**：自动创建备份并记录版本
- **查看备份**：`./hooks/backup-manager.sh list`
- **恢复文件**：`./hooks/backup-manager.sh restore <备份文件名>`

## 📂 目录结构

```
hooks/
├── pre-edit-backup.sh      # 编辑前备份脚本
├── post-edit-version.sh    # 编辑后版本记录脚本
├── backup-manager.sh       # 备份管理工具
├── setup-hooks.sh         # 安装配置脚本
├── backups/               # 备份存储目录
│   ├── *.bak             # 备份文件
│   ├── versions/         # 版本记录
│   └── diffs/           # 差异文件
├── logs/                  # 操作日志
│   ├── backup.log       # 备份日志
│   └── version.log      # 版本日志
└── CHANGELOG.md          # 自动生成的变更日志
```

## 🎯 支持的文件类型

自动备份以下类型的文件：
- `*strategy*.py` - 策略文件
- `*algo*.py` - 算法文件
- `*trading*.py` - 交易逻辑
- `*backtest*.py` - 回测代码
- `*indicator*.py` - 技术指标
- `*signal*.py` - 信号生成
- `config/*.json` - 配置文件
- `config/*.yaml` - YAML配置

## 💡 备份管理命令

```bash
# 列出所有备份
./hooks/backup-manager.sh list

# 列出特定文件的备份
./hooks/backup-manager.sh list strategy.py

# 恢复备份
./hooks/backup-manager.sh restore strategy_py.20240101_120000.abc12345.bak

# 比较两个备份
./hooks/backup-manager.sh diff file1.bak file2.bak

# 清理30天前的备份
./hooks/backup-manager.sh clean 30

# 查看版本信息
./hooks/backup-manager.sh info strategy.py

# 显示备份统计
./hooks/backup-manager.sh stats

# 搜索备份内容
./hooks/backup-manager.sh search "关键词"

# 导出所有备份
./hooks/backup-manager.sh export ./my_backups
```

## 🔧 高级配置

### 修改备份策略

编辑 `pre-edit-backup.sh` 中的配置：

```bash
MAX_BACKUPS=50  # 每个文件最多保留的备份数量

# 添加自定义文件模式
STRATEGY_PATTERNS=(
    "*custom*.py"
    # 添加更多模式...
)
```

### 版本号策略

版本号自动根据变更程度分配：
- **Major (x.0.0)**: 变更超过50%的内容
- **Minor (1.x.0)**: 变更20-50%的内容  
- **Patch (1.0.x)**: 变更少于20%的内容

## 📊 示例输出

### 备份创建
```
✅ 已创建策略文件备份: strategy.py
   📁 备份位置: backups/strategy_py.20240101_120000.abc12345.bak
   📊 该文件共有 5 个备份版本
```

### 版本记录
```
🔖 版本控制记录已创建
   📄 文件: strategy.py
   🏷️  版本: 1.2.0 (minor)
   📊 差异报告: backups/diffs/strategy_py.1.2.0.20240101_120000.diff
   📝 变更日志已更新
```

## ⚠️ 注意事项

1. **首次使用**：运行 `setup-hooks.sh` 进行配置
2. **权限问题**：确保脚本有执行权限 (`chmod +x`)
3. **磁盘空间**：定期清理旧备份避免占用过多空间
4. **敏感信息**：备份不会自动加密，注意保护敏感数据

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可

MIT License