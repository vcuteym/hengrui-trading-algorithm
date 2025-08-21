#!/bin/bash

# ====================================================================
# Post-Edit Version Control Hook for Trading Strategy Files
# 功能：在编辑策略文件后记录版本变更和差异
# ====================================================================

# 从环境变量获取文件路径和内容
FILE_PATH="${CLAUDE_EDIT_FILE_PATH}"
NEW_CONTENT="${CLAUDE_EDIT_NEW_STRING}"
OLD_CONTENT="${CLAUDE_EDIT_OLD_STRING}"

# 配置
VERSION_DIR="$(dirname "$0")/backups/versions"
DIFF_DIR="$(dirname "$0")/backups/diffs"
LOG_FILE="$(dirname "$0")/logs/version.log"
CHANGELOG="$(dirname "$0")/CHANGELOG.md"

# 创建必要的目录
mkdir -p "$VERSION_DIR" "$DIFF_DIR" "$(dirname "$LOG_FILE")"

# 日志函数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 生成版本号
generate_version() {
    local file_base="$1"
    local version_file="${VERSION_DIR}/.version_${file_base//\//_}"
    
    if [[ -f "$version_file" ]]; then
        local current_version=$(cat "$version_file")
        # 解析版本号 (major.minor.patch)
        IFS='.' read -r major minor patch <<< "$current_version"
        
        # 根据修改类型决定版本号增量
        if [[ "$2" == "major" ]]; then
            major=$((major + 1))
            minor=0
            patch=0
        elif [[ "$2" == "minor" ]]; then
            minor=$((minor + 1))
            patch=0
        else
            patch=$((patch + 1))
        fi
        
        echo "${major}.${minor}.${patch}"
    else
        echo "1.0.0"
    fi
}

# 分析修改类型
analyze_change_type() {
    local old="$1"
    local new="$2"
    
    # 计算变更行数
    local added_lines=$(echo "$new" | wc -l)
    local removed_lines=$(echo "$old" | wc -l)
    local change_ratio=$(echo "scale=2; abs($added_lines - $removed_lines) / ($removed_lines + 1)" | bc -l 2>/dev/null || echo "0")
    
    # 根据变更程度判断版本类型
    if [[ $(echo "$change_ratio > 0.5" | bc -l 2>/dev/null) == "1" ]]; then
        echo "major"  # 重大修改
    elif [[ $(echo "$change_ratio > 0.2" | bc -l 2>/dev/null) == "1" ]]; then
        echo "minor"  # 功能修改
    else
        echo "patch"  # 小修复
    fi
}

# 生成差异报告
generate_diff_report() {
    local file_path="$1"
    local old_content="$2"
    local new_content="$3"
    local version="$4"
    local timestamp="$5"
    
    local file_base="${file_path#*/}"
    local diff_file="${DIFF_DIR}/${file_base//\//_}.${version}.${timestamp}.diff"
    
    # 创建临时文件
    local tmp_old="/tmp/old_${timestamp}.tmp"
    local tmp_new="/tmp/new_${timestamp}.tmp"
    
    echo "$old_content" > "$tmp_old"
    echo "$new_content" > "$tmp_new"
    
    # 生成差异文件
    cat > "$diff_file" <<EOF
================================================================================
文件: $file_path
版本: $version
时间: $(date '+%Y-%m-%d %H:%M:%S')
================================================================================

变更摘要:
EOF
    
    # 统计变更
    local stats=$(diff --brief "$tmp_old" "$tmp_new" 2>/dev/null)
    if [[ -n "$stats" ]]; then
        local added=$(diff "$tmp_old" "$tmp_new" | grep "^>" | wc -l)
        local removed=$(diff "$tmp_old" "$tmp_new" | grep "^<" | wc -l)
        echo "  - 新增行数: $added" >> "$diff_file"
        echo "  - 删除行数: $removed" >> "$diff_file"
        echo "  - 总变更行数: $((added + removed))" >> "$diff_file"
    fi
    
    echo -e "\n详细差异:\n" >> "$diff_file"
    diff -u "$tmp_old" "$tmp_new" >> "$diff_file" 2>/dev/null
    
    # 清理临时文件
    rm -f "$tmp_old" "$tmp_new"
    
    echo "$diff_file"
}

# 更新变更日志
update_changelog() {
    local file_path="$1"
    local version="$2"
    local change_type="$3"
    local summary="$4"
    
    # 如果CHANGELOG不存在，创建header
    if [[ ! -f "$CHANGELOG" ]]; then
        cat > "$CHANGELOG" <<EOF
# 策略版本变更日志

所有策略文件的重要变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

EOF
    fi
    
    # 添加新的变更记录
    local temp_file="/tmp/changelog_temp.md"
    local date_str=$(date '+%Y-%m-%d')
    local time_str=$(date '+%H:%M:%S')
    
    # 创建新条目
    cat > "$temp_file" <<EOF

## [$version] - $date_str $time_str

### ${change_type^}
- **文件**: \`$(basename "$file_path")\`
- **路径**: \`$file_path\`
- **摘要**: $summary

EOF
    
    # 将新条目插入到文件开头（在header之后）
    if [[ -f "$CHANGELOG" ]]; then
        # 保存header（前6行）
        head -n 7 "$CHANGELOG" > "/tmp/changelog_header.md"
        # 保存其余内容
        tail -n +8 "$CHANGELOG" > "/tmp/changelog_body.md"
        # 重新组合
        cat "/tmp/changelog_header.md" "$temp_file" "/tmp/changelog_body.md" > "$CHANGELOG"
        rm -f "/tmp/changelog_header.md" "/tmp/changelog_body.md"
    fi
    
    rm -f "$temp_file"
}

# 主版本控制逻辑
if [[ -n "$FILE_PATH" ]] && [[ -f "$FILE_PATH" ]]; then
    FILE_NAME=$(basename "$FILE_PATH")
    FILE_BASE="${FILE_PATH#*/}"
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    
    # 分析变更类型
    CHANGE_TYPE=$(analyze_change_type "$OLD_CONTENT" "$NEW_CONTENT")
    
    # 生成版本号
    VERSION=$(generate_version "$FILE_BASE" "$CHANGE_TYPE")
    VERSION_FILE="${VERSION_DIR}/.version_${FILE_BASE//\//_}"
    echo "$VERSION" > "$VERSION_FILE"
    
    # 生成差异报告
    DIFF_FILE=$(generate_diff_report "$FILE_PATH" "$OLD_CONTENT" "$NEW_CONTENT" "$VERSION" "$TIMESTAMP")
    
    # 记录版本信息
    VERSION_RECORD="${VERSION_DIR}/${FILE_BASE//\//_}.${VERSION}.json"
    cat > "$VERSION_RECORD" <<EOF
{
  "file": "$FILE_PATH",
  "version": "$VERSION",
  "change_type": "$CHANGE_TYPE",
  "timestamp": "$(date '+%Y-%m-%d %H:%M:%S')",
  "diff_file": "$DIFF_FILE",
  "author": "Claude Code",
  "hash_before": "$(echo -n "$OLD_CONTENT" | md5sum | cut -d' ' -f1)",
  "hash_after": "$(echo -n "$NEW_CONTENT" | md5sum | cut -d' ' -f1)"
}
EOF
    
    # 生成变更摘要
    SUMMARY="更新了策略逻辑"
    if echo "$FILE_PATH" | grep -q "indicator"; then
        SUMMARY="修改了技术指标计算"
    elif echo "$FILE_PATH" | grep -q "signal"; then
        SUMMARY="调整了交易信号生成"
    elif echo "$FILE_PATH" | grep -q "backtest"; then
        SUMMARY="优化了回测逻辑"
    elif echo "$FILE_PATH" | grep -q "config"; then
        SUMMARY="更新了配置参数"
    fi
    
    # 更新CHANGELOG
    update_changelog "$FILE_PATH" "$VERSION" "$CHANGE_TYPE" "$SUMMARY"
    
    # 输出版本信息
    echo "🔖 版本控制记录已创建"
    echo "   📄 文件: $FILE_NAME"
    echo "   🏷️  版本: $VERSION ($CHANGE_TYPE)"
    echo "   📊 差异报告: $DIFF_FILE"
    echo "   📝 变更日志已更新"
    
    # 写入日志
    log_message "版本更新: $FILE_PATH -> v$VERSION ($CHANGE_TYPE)"
    
    # Git集成（如果在git仓库中）
    if git rev-parse --git-dir > /dev/null 2>&1; then
        # 创建自动提交消息
        COMMIT_MSG="[Auto-Version] $FILE_NAME v$VERSION - $SUMMARY"
        echo "   🔗 Git提交消息: $COMMIT_MSG"
        
        # 保存提交消息供后续使用
        echo "$COMMIT_MSG" > "${VERSION_DIR}/.last_commit_msg"
    fi
else
    echo "ℹ️ 文件路径无效或文件不存在: $FILE_PATH"
fi

exit 0