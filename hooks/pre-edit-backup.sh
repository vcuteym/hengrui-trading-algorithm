#!/bin/bash

# ====================================================================
# Pre-Edit Backup Hook for Trading Strategy Files
# 功能：在编辑策略文件前自动创建备份
# ====================================================================

# 从环境变量获取文件路径
FILE_PATH="${CLAUDE_EDIT_FILE_PATH}"
OLD_CONTENT="${CLAUDE_EDIT_OLD_STRING}"

# 配置
BACKUP_DIR="$(dirname "$0")/backups"
LOG_FILE="$(dirname "$0")/logs/backup.log"
MAX_BACKUPS=50  # 每个文件最多保留的备份数量

# 定义需要备份的文件模式
STRATEGY_PATTERNS=(
    "*strategy*.py"
    "*algo*.py"
    "*trading*.py"
    "*backtest*.py"
    "*indicator*.py"
    "*signal*.py"
    "config/*.json"
    "config/*.yaml"
    "params/*.json"
)

# 创建必要的目录
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

# 日志函数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查文件是否需要备份
should_backup() {
    local file="$1"
    
    # 检查文件是否匹配策略文件模式
    for pattern in "${STRATEGY_PATTERNS[@]}"; do
        if [[ "$file" == $pattern ]]; then
            return 0
        fi
    done
    
    # 检查文件名是否包含策略相关关键词
    if echo "$file" | grep -qE "(strategy|trading|algo|backtest|indicator|signal)"; then
        return 0
    fi
    
    return 1
}

# 计算文件内容的哈希值
get_file_hash() {
    local file="$1"
    if [[ -f "$file" ]]; then
        md5sum "$file" | cut -d' ' -f1
    else
        echo "none"
    fi
}

# 清理旧备份
cleanup_old_backups() {
    local file_base="$1"
    local backup_pattern="${BACKUP_DIR}/${file_base//\//_}.*.bak"
    
    # 获取备份文件列表并按时间排序
    local backups=($(ls -t $backup_pattern 2>/dev/null))
    local count=${#backups[@]}
    
    # 如果备份数量超过限制，删除最旧的
    if [[ $count -gt $MAX_BACKUPS ]]; then
        for ((i=$MAX_BACKUPS; i<$count; i++)); do
            rm -f "${backups[$i]}"
            log_message "清理旧备份: ${backups[$i]}"
        done
    fi
}

# 主备份逻辑
if [[ -n "$FILE_PATH" ]] && [[ -f "$FILE_PATH" ]]; then
    # 获取文件基本信息
    FILE_NAME=$(basename "$FILE_PATH")
    FILE_DIR=$(dirname "$FILE_PATH")
    FILE_BASE="${FILE_PATH#*/}"  # 相对路径
    
    # 检查是否需要备份
    if should_backup "$FILE_PATH"; then
        # 生成备份文件名
        TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
        HASH=$(get_file_hash "$FILE_PATH")
        BACKUP_FILE="${BACKUP_DIR}/${FILE_BASE//\//_}.${TIMESTAMP}.${HASH:0:8}.bak"
        
        # 检查最后一次备份的哈希值
        LAST_BACKUP=$(ls -t "${BACKUP_DIR}/${FILE_BASE//\//_}".*.bak 2>/dev/null | head -1)
        if [[ -n "$LAST_BACKUP" ]]; then
            LAST_HASH=$(echo "$LAST_BACKUP" | sed -E 's/.*\.([a-f0-9]{8})\.bak$/\1/')
            CURRENT_HASH="${HASH:0:8}"
            
            # 如果内容没有变化，跳过备份
            if [[ "$LAST_HASH" == "$CURRENT_HASH" ]]; then
                echo "📝 文件内容未变化，跳过备份: $FILE_NAME"
                log_message "跳过备份 (内容未变化): $FILE_PATH"
                exit 0
            fi
        fi
        
        # 创建备份
        cp "$FILE_PATH" "$BACKUP_FILE"
        
        if [[ $? -eq 0 ]]; then
            # 记录备份信息
            echo "✅ 已创建策略文件备份: $FILE_NAME"
            echo "   📁 备份位置: $BACKUP_FILE"
            
            # 写入日志
            log_message "备份成功: $FILE_PATH -> $BACKUP_FILE"
            
            # 记录备份元数据
            cat >> "${BACKUP_FILE}.meta" <<EOF
{
  "original_path": "$FILE_PATH",
  "backup_time": "$(date '+%Y-%m-%d %H:%M:%S')",
  "file_size": $(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH" 2>/dev/null),
  "file_hash": "$HASH",
  "modification": "pre-edit"
}
EOF
            
            # 清理旧备份
            cleanup_old_backups "$FILE_BASE"
            
            # 显示备份统计
            BACKUP_COUNT=$(ls "${BACKUP_DIR}/${FILE_BASE//\//_}".*.bak 2>/dev/null | wc -l)
            echo "   📊 该文件共有 $BACKUP_COUNT 个备份版本"
        else
            echo "⚠️ 备份失败: $FILE_PATH"
            log_message "备份失败: $FILE_PATH"
            exit 1
        fi
    else
        echo "ℹ️ 非策略文件，跳过备份: $FILE_NAME"
    fi
fi

exit 0