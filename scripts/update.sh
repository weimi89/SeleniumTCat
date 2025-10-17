#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# SeleniumTCat 自動更新腳本 - 統一更新邏輯
# ═══════════════════════════════════════════════════════════════════════════
# 用途: 使用 git pull 更新專案到最新版本並同步依賴
# 支援: Linux, macOS
# 執行: bash scripts/update.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e  # 遇到錯誤立即停止

# ───────────────────────────────────────────────────────────────────────────
# 顏色定義
# ───────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ───────────────────────────────────────────────────────────────────────────
# 輔助函數
# ───────────────────────────────────────────────────────────────────────────
print_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${BLUE}🔹 $1${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# 主更新流程
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🔄 SeleniumTCat 自動更新程式${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 1. 檢查 Git 儲存庫
# ───────────────────────────────────────────────────────────────────────────
print_step "檢查 Git 儲存庫..."

if [ ! -d ".git" ]; then
    print_error "這不是一個 Git 儲存庫"
    echo "💡 請確認您在正確的專案目錄中"
    exit 1
fi

print_info "Git 儲存庫檢查通過"

# ───────────────────────────────────────────────────────────────────────────
# 2. 檢查工作目錄狀態
# ───────────────────────────────────────────────────────────────────────────
print_step "檢查工作目錄狀態..."

if ! git diff-index --quiet HEAD --; then
    print_warning "發現未提交的變更"
    echo ""
    echo "未提交的檔案:"
    git status --porcelain
    echo ""
    read -p "是否要繼續更新? 這可能會覆蓋您的變更 [y/N]: " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "更新已取消"
        exit 1
    fi

    print_step "儲存當前變更到暫存區..."
    git stash push -m "Auto-stash before update $(date '+%Y-%m-%d %H:%M:%S')"
    print_info "變更已暫存"
fi

# ───────────────────────────────────────────────────────────────────────────
# 3. 檢查網路連線
# ───────────────────────────────────────────────────────────────────────────
print_step "檢查網路連線..."

if ! git ls-remote origin HEAD > /dev/null 2>&1; then
    print_error "無法連接到遠端儲存庫"
    echo "💡 請檢查您的網路連線和 Git 權限"
    exit 1
fi

print_info "網路連線正常"

# ───────────────────────────────────────────────────────────────────────────
# 4. 獲取當前狀態
# ───────────────────────────────────────────────────────────────────────────
current_branch=$(git branch --show-current)
current_commit=$(git rev-parse HEAD)
current_commit_short=$(git rev-parse --short HEAD)

echo ""
print_info "當前分支: $current_branch"
print_info "當前版本: $current_commit_short"

# ───────────────────────────────────────────────────────────────────────────
# 5. 檢查遠端更新
# ───────────────────────────────────────────────────────────────────────────
print_step "檢查遠端更新..."
git fetch origin

remote_commit=$(git rev-parse origin/$current_branch)
remote_commit_short=$(git rev-parse --short origin/$current_branch)

if [ "$current_commit" = "$remote_commit" ]; then
    echo ""
    print_info "專案已是最新版本 ($current_commit_short)"
    echo "🎉 無需更新!"
    exit 0
fi

echo ""
print_info "發現新版本: $remote_commit_short"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 6. 顯示更新內容
# ───────────────────────────────────────────────────────────────────────────
echo "📋 更新內容預覽:"
echo "=================================="
git log --oneline --graph --decorate $current_commit..$remote_commit
echo "=================================="
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 7. 確認更新
# ───────────────────────────────────────────────────────────────────────────
read -p "是否要更新到最新版本? [Y/n]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Nn]$ ]]; then
    print_error "更新已取消"
    exit 1
fi

# ───────────────────────────────────────────────────────────────────────────
# 8. 執行更新
# ───────────────────────────────────────────────────────────────────────────
print_step "正在下載更新..."

if git pull origin $current_branch; then
    new_commit_short=$(git rev-parse --short HEAD)
    echo ""
    print_info "更新成功!"
    print_info "新版本: $new_commit_short"

    # ───────────────────────────────────────────────────────────────────────
    # 9. 檢查並更新依賴
    # ───────────────────────────────────────────────────────────────────────
    if git diff --name-only $current_commit HEAD | grep -q "pyproject.toml\|uv.lock"; then
        echo ""
        print_step "偵測到依賴變更，正在更新套件..."
        if command -v uv >/dev/null 2>&1; then
            uv sync
            print_info "依賴更新完成"
        else
            print_warning "請手動執行: uv sync"
        fi
    fi

    # ───────────────────────────────────────────────────────────────────────
    # 10. 還原暫存的變更
    # ───────────────────────────────────────────────────────────────────────
    if git stash list | grep -q "Auto-stash before update"; then
        echo ""
        print_step "還原之前暫存的變更..."
        if git stash pop; then
            print_info "變更已還原"
        else
            print_warning "變更還原時發生衝突，請手動處理"
            echo "💡 使用 'git stash list' 查看暫存清單"
        fi
    fi

    echo ""
    echo -e "${GREEN}🎉 SeleniumTCat 更新完成！${NC}"
    echo "💡 如果遇到問題，請參考 CLAUDE.md 或重新安裝依賴"

else
    echo ""
    print_error "更新失敗"
    echo "💡 請檢查網路連線或手動執行: git pull"
    exit 1
fi
