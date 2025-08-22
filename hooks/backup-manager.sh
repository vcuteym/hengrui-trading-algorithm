#!/bin/bash

# ====================================================================
# 备份管理工具 - 用于管理和恢复策略文件备份
# ====================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
VERSION_DIR="$BACKUP_DIR/versions"
DIFF_DIR="$BACKUP_DIR/diffs"
LOG_DIR="$SCRIPT_DIR/logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    cat <<EOF
═══════════════════════════════════════════════════════════════════
                    策略备份管理工具 v1.0
═══════════════════════════════════════════════════════════════════

用法: $(basename "$0") [命令] [选项]

命令:
  list [文件名]           列出备份文件
  restore <备份文件>      恢复备份文件
  diff <文件1> <文件2>    比较两个备份文件
  clean [天数]            清理指定天数前的备份（默认30天）
  info <文件名>           显示文件的版本信息
  stats                   显示备份统计信息
  search <关键词>         搜索备份中的内容
  export <输出目录>       导出所有备份
  
选项:
  -h, --help             显示此帮助信息
  -v, --verbose          显示详细信息
  -f, --force            强制执行操作
  
示例:
  $(basename "$0") list                    # 列出所有备份
  $(basename "$0") list strategy.py        # 列出strategy.py的备份
  $(basename "$0") restore backup.bak      # 恢复指定备份
  $(basename "$0") clean 7                 # 清理7天前的备份
  $(basename "$0") info strategy.py        # 查看strategy.py的版本信息
  
═══════════════════════════════════════════════════════════════════
EOF
}

# 列出备份文件
list_backups() {
    local filter="$1"
    
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                         备份文件列表${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}\n"
    
    if [[ -n "$filter" ]]; then
        local pattern="${BACKUP_DIR}/*${filter}*.bak"
    else
        local pattern="${BACKUP_DIR}/*.bak"
    fi
    
    local count=0
    for backup in $(ls -t $pattern 2>/dev/null); do
        ((count++))
        local filename=$(basename "$backup")
        local size=$(du -h "$backup" | cut -f1)
        local date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup" 2>/dev/null || \
                    stat -c "%y" "$backup" 2>/dev/null | cut -d' ' -f1,2)
        
        # 解析文件名获取原始文件
        local original=$(echo "$filename" | sed -E 's/\.([0-9]{8}_[0-9]{6})\..*\.bak$//')
        original=${original//_/\/}
        
        # 获取元数据
        local meta_file="${backup}.meta"
        local version="N/A"
        if [[ -f "$meta_file" ]]; then
            version=$(grep '"file_hash"' "$meta_file" | cut -d'"' -f4 | cut -c1-8)
        fi
        
        printf "${GREEN}[%02d]${NC} %-40s ${YELLOW}%8s${NC} ${BLUE}%s${NC} ${PURPLE}[%s]${NC}\n" \
               "$count" "$filename" "$size" "$date" "$version"
        
        if [[ $count -eq 1 ]]; then
            echo -e "     ${CYAN}原始文件: $original${NC}"
        fi
    done
    
    if [[ $count -eq 0 ]]; then
        echo -e "${YELLOW}没有找到备份文件${NC}"
    else
        echo -e "\n${GREEN}共找到 $count 个备份文件${NC}"
    fi
}

# 恢复备份
restore_backup() {
    local backup_file="$1"
    
    if [[ ! -f "$BACKUP_DIR/$backup_file" ]]; then
        echo -e "${RED}错误: 备份文件不存在: $backup_file${NC}"
        return 1
    fi
    
    # 读取元数据获取原始路径
    local meta_file="$BACKUP_DIR/${backup_file}.meta"
    if [[ ! -f "$meta_file" ]]; then
        echo -e "${YELLOW}警告: 找不到元数据文件${NC}"
        echo -n "请输入要恢复到的目标路径: "
        read target_path
    else
        target_path=$(grep '"original_path"' "$meta_file" | cut -d'"' -f4)
    fi
    
    # 确认恢复操作
    echo -e "${YELLOW}准备恢复备份:${NC}"
    echo -e "  备份文件: ${CYAN}$backup_file${NC}"
    echo -e "  目标路径: ${CYAN}$target_path${NC}"
    echo -n -e "${YELLOW}确认恢复? (y/n): ${NC}"
    read -r confirm
    
    if [[ "$confirm" != "y" ]]; then
        echo -e "${RED}取消恢复操作${NC}"
        return 1
    fi
    
    # 备份当前文件（如果存在）
    if [[ -f "$target_path" ]]; then
        local temp_backup="${target_path}.temp_$(date +%Y%m%d_%H%M%S)"
        cp "$target_path" "$temp_backup"
        echo -e "${GREEN}已备份当前文件到: $temp_backup${NC}"
    fi
    
    # 恢复文件
    cp "$BACKUP_DIR/$backup_file" "$target_path"
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ 文件恢复成功!${NC}"
        
        # 记录恢复操作
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 恢复: $backup_file -> $target_path" >> "$LOG_DIR/restore.log"
    else
        echo -e "${RED}❌ 文件恢复失败!${NC}"
        return 1
    fi
}

# 比较两个备份
diff_backups() {
    local file1="$1"
    local file2="$2"
    
    if [[ ! -f "$BACKUP_DIR/$file1" ]]; then
        echo -e "${RED}错误: 文件不存在: $file1${NC}"
        return 1
    fi
    
    if [[ ! -f "$BACKUP_DIR/$file2" ]]; then
        echo -e "${RED}错误: 文件不存在: $file2${NC}"
        return 1
    fi
    
    echo -e "${CYAN}比较备份文件:${NC}"
    echo -e "  文件1: $file1"
    echo -e "  文件2: $file2"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}\n"
    
    diff -u "$BACKUP_DIR/$file1" "$BACKUP_DIR/$file2" | head -100
}

# 清理旧备份
clean_old_backups() {
    local days="${1:-30}"
    
    echo -e "${YELLOW}准备清理 $days 天前的备份...${NC}"
    
    # 查找并统计要删除的文件
    local files_to_delete=$(find "$BACKUP_DIR" -name "*.bak" -mtime +$days 2>/dev/null)
    local count=$(echo "$files_to_delete" | grep -c "\.bak" 2>/dev/null || echo "0")
    
    if [[ $count -eq 0 ]]; then
        echo -e "${GREEN}没有需要清理的备份文件${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}找到 $count 个旧备份文件${NC}"
    echo -n -e "${YELLOW}确认删除? (y/n): ${NC}"
    read -r confirm
    
    if [[ "$confirm" != "y" ]]; then
        echo -e "${RED}取消清理操作${NC}"
        return 1
    fi
    
    # 删除旧文件
    echo "$files_to_delete" | while read -r file; do
        if [[ -f "$file" ]]; then
            rm -f "$file" "${file}.meta"
            echo -e "${GREEN}已删除: $(basename "$file")${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ 清理完成，已删除 $count 个备份文件${NC}"
}

# 显示版本信息
show_version_info() {
    local file_pattern="$1"
    
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                      版本信息: $file_pattern${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}\n"
    
    # 查找版本文件
    local version_files=$(find "$VERSION_DIR" -name "*${file_pattern}*.json" 2>/dev/null | sort -V)
    
    if [[ -z "$version_files" ]]; then
        echo -e "${YELLOW}没有找到版本信息${NC}"
        return 1
    fi
    
    echo "$version_files" | while read -r vfile; do
        if [[ -f "$vfile" ]]; then
            local version=$(grep '"version"' "$vfile" | cut -d'"' -f4)
            local timestamp=$(grep '"timestamp"' "$vfile" | cut -d'"' -f4)
            local change_type=$(grep '"change_type"' "$vfile" | cut -d'"' -f4)
            
            echo -e "${GREEN}版本 $version${NC} [$change_type] - $timestamp"
        fi
    done
}

# 显示统计信息
show_stats() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                        备份统计信息${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}\n"
    
    # 统计备份文件
    local total_backups=$(find "$BACKUP_DIR" -name "*.bak" 2>/dev/null | wc -l)
    local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    local today_backups=$(find "$BACKUP_DIR" -name "*.bak" -mtime -1 2>/dev/null | wc -l)
    local week_backups=$(find "$BACKUP_DIR" -name "*.bak" -mtime -7 2>/dev/null | wc -l)
    
    echo -e "  ${GREEN}总备份数量:${NC} $total_backups"
    echo -e "  ${GREEN}总占用空间:${NC} $total_size"
    echo -e "  ${GREEN}今日备份:${NC} $today_backups"
    echo -e "  ${GREEN}本周备份:${NC} $week_backups"
    
    # 统计各文件的备份数
    echo -e "\n${CYAN}各文件备份统计:${NC}"
    
    # 获取所有唯一的原始文件名
    local files=$(ls "$BACKUP_DIR"/*.bak 2>/dev/null | \
                 sed -E 's/.*\/(.*)\.([0-9]{8}_[0-9]{6})\..*\.bak$/\1/' | \
                 sort -u)
    
    echo "$files" | while read -r file; do
        if [[ -n "$file" ]]; then
            local count=$(ls "$BACKUP_DIR"/${file}.*.bak 2>/dev/null | wc -l)
            printf "  %-40s: %3d 个备份\n" "${file//_/\/}" "$count"
        fi
    done
}

# 搜索备份内容
search_in_backups() {
    local keyword="$1"
    
    echo -e "${CYAN}在备份中搜索: '$keyword'${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}\n"
    
    local found=0
    for backup in "$BACKUP_DIR"/*.bak; do
        if [[ -f "$backup" ]]; then
            if grep -l "$keyword" "$backup" >/dev/null 2>&1; then
                ((found++))
                echo -e "${GREEN}找到匹配:${NC} $(basename "$backup")"
                grep -n "$keyword" "$backup" | head -3
                echo ""
            fi
        fi
    done
    
    if [[ $found -eq 0 ]]; then
        echo -e "${YELLOW}没有找到匹配的内容${NC}"
    else
        echo -e "${GREEN}共在 $found 个备份文件中找到匹配${NC}"
    fi
}

# 导出备份
export_backups() {
    local export_dir="$1"
    
    if [[ -z "$export_dir" ]]; then
        export_dir="./strategy_backups_$(date +%Y%m%d_%H%M%S)"
    fi
    
    echo -e "${CYAN}导出备份到: $export_dir${NC}"
    
    # 创建导出目录
    mkdir -p "$export_dir"
    
    # 复制所有备份文件
    cp -r "$BACKUP_DIR"/* "$export_dir/" 2>/dev/null
    
    # 创建导出报告
    cat > "$export_dir/export_report.txt" <<EOF
策略备份导出报告
导出时间: $(date '+%Y-%m-%d %H:%M:%S')
备份数量: $(find "$BACKUP_DIR" -name "*.bak" | wc -l)
总大小: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF
    
    echo -e "${GREEN}✅ 备份导出完成${NC}"
    echo -e "  导出位置: $export_dir"
    echo -e "  文件数量: $(find "$export_dir" -type f | wc -l)"
}

# 主程序
case "$1" in
    list)
        list_backups "$2"
        ;;
    restore)
        restore_backup "$2"
        ;;
    diff)
        diff_backups "$2" "$3"
        ;;
    clean)
        clean_old_backups "$2"
        ;;
    info)
        show_version_info "$2"
        ;;
    stats)
        show_stats
        ;;
    search)
        search_in_backups "$2"
        ;;
    export)
        export_backups "$2"
        ;;
    -h|--help|help)
        show_help
        ;;
    *)
        echo -e "${RED}无效命令: $1${NC}"
        echo "使用 '$(basename "$0") --help' 查看帮助信息"
        exit 1
        ;;
esac