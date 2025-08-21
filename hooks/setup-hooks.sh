#!/bin/bash

# ====================================================================
# Hook 配置安装脚本
# 功能：配置Claude Code hooks到用户的settings.json
# ====================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_CONFIG_DIR="$HOME/.claude"
SETTINGS_FILE="$CLAUDE_CONFIG_DIR/settings.json"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}            Claude Code 版本控制 Hook 安装程序${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}\n"

# 检查Claude配置目录
if [[ ! -d "$CLAUDE_CONFIG_DIR" ]]; then
    echo -e "${YELLOW}创建 Claude 配置目录...${NC}"
    mkdir -p "$CLAUDE_CONFIG_DIR"
fi

# 设置脚本执行权限
echo -e "${GREEN}设置脚本执行权限...${NC}"
chmod +x "$SCRIPT_DIR"/*.sh

# 备份现有配置
if [[ -f "$SETTINGS_FILE" ]]; then
    BACKUP_FILE="$SETTINGS_FILE.backup_$(date +%Y%m%d_%H%M%S)"
    cp "$SETTINGS_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}已备份现有配置到: $BACKUP_FILE${NC}"
fi

# 创建settings.json配置
cat > "$SETTINGS_FILE" <<EOF
{
  "hooks": {
    "pre-edit": "$SCRIPT_DIR/pre-edit-backup.sh",
    "post-edit": "$SCRIPT_DIR/post-edit-version.sh"
  },
  "output-styles": {
    "trading": "$HOME/.claude/output-styles/trading-algorithm-analysis.md"
  }
}
EOF

echo -e "${GREEN}✅ Hook 配置已安装!${NC}\n"

echo -e "${CYAN}已配置的 Hooks:${NC}"
echo -e "  ${GREEN}pre-edit${NC}:  策略文件自动备份"
echo -e "  ${GREEN}post-edit${NC}: 版本记录和变更追踪\n"

echo -e "${CYAN}管理工具使用方法:${NC}"
echo -e "  ${YELLOW}查看备份:${NC} $SCRIPT_DIR/backup-manager.sh list"
echo -e "  ${YELLOW}恢复备份:${NC} $SCRIPT_DIR/backup-manager.sh restore <备份文件>"
echo -e "  ${YELLOW}查看统计:${NC} $SCRIPT_DIR/backup-manager.sh stats"
echo -e "  ${YELLOW}查看帮助:${NC} $SCRIPT_DIR/backup-manager.sh --help\n"

echo -e "${CYAN}备份文件位置:${NC}"
echo -e "  备份目录: $SCRIPT_DIR/backups/"
echo -e "  版本记录: $SCRIPT_DIR/backups/versions/"
echo -e "  差异文件: $SCRIPT_DIR/backups/diffs/"
echo -e "  操作日志: $SCRIPT_DIR/logs/\n"

echo -e "${GREEN}提示: Hooks 将在下次使用 Claude Code 编辑文件时自动生效${NC}"