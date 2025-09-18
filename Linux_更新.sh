#!/bin/bash

# WEDI 工具自動更新腳本 (Linux/macOS)
# 使用 git pull 更新專案到最新版本

set -e  # 遇到錯誤立即停止

echo "🔄 WEDI 工具自動更新程式"
echo "=================================="

# 檢查是否為 Git 儲存庫
if [ ! -d ".git" ]; then
    echo "❌ 錯誤: 這不是一個 Git 儲存庫"
    echo "💡 請確認您在正確的專案目錄中"
    exit 1
fi

# 檢查是否有未提交的變更
echo "🔍 檢查工作目錄狀態..."
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  警告: 發現未提交的變更"
    echo ""
    echo "未提交的檔案:"
    git status --porcelain
    echo ""
    read -p "是否要繼續更新? 這可能會覆蓋您的變更 [y/N]: " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 更新已取消"
        exit 1
    fi

    echo "💾 儲存當前變更到暫存區..."
    git stash push -m "Auto-stash before update $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ 變更已暫存"
fi

# 檢查網路連線
echo "🌐 檢查網路連線..."
if ! git ls-remote origin HEAD > /dev/null 2>&1; then
    echo "❌ 錯誤: 無法連接到遠端儲存庫"
    echo "💡 請檢查您的網路連線和 Git 權限"
    exit 1
fi

# 獲取當前分支
current_branch=$(git branch --show-current)
echo "📍 當前分支: $current_branch"

# 獲取當前版本
current_commit=$(git rev-parse HEAD)
current_commit_short=$(git rev-parse --short HEAD)
echo "📌 當前版本: $current_commit_short"

# 檢查遠端更新
echo "🔍 檢查遠端更新..."
git fetch origin

# 比較本地和遠端版本
remote_commit=$(git rev-parse origin/$current_branch)
remote_commit_short=$(git rev-parse --short origin/$current_branch)

if [ "$current_commit" = "$remote_commit" ]; then
    echo "✅ 專案已是最新版本 ($current_commit_short)"
    echo "🎉 無需更新!"
    exit 0
fi

echo "🆕 發現新版本: $remote_commit_short"
echo ""

# 顯示更新內容
echo "📋 更新內容預覽:"
echo "=================================="
git log --oneline --graph --decorate $current_commit..$remote_commit
echo "=================================="
echo ""

# 確認更新
read -p "是否要更新到最新版本? [Y/n]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "❌ 更新已取消"
    exit 1
fi

# 執行更新
echo "⬇️  正在下載更新..."
if git pull origin $current_branch; then
    new_commit_short=$(git rev-parse --short HEAD)
    echo ""
    echo "✅ 更新成功!"
    echo "📌 新版本: $new_commit_short"

    # 檢查是否需要更新依賴
    if git diff --name-only $current_commit HEAD | grep -q "pyproject.toml\|uv.lock"; then
        echo ""
        echo "📦 偵測到依賴變更，正在更新套件..."
        if command -v uv >/dev/null 2>&1; then
            uv sync
            echo "✅ 依賴更新完成"
        else
            echo "⚠️  請手動執行: uv sync"
        fi
    fi

    # 檢查是否有暫存的變更需要還原
    if git stash list | grep -q "Auto-stash before update"; then
        echo ""
        echo "🔄 還原之前暫存的變更..."
        if git stash pop; then
            echo "✅ 變更已還原"
        else
            echo "⚠️  變更還原時發生衝突，請手動處理"
            echo "💡 使用 'git stash list' 查看暫存清單"
        fi
    fi

    echo ""
    echo "🎉 WEDI 工具更新完成!"
    echo "💡 如果遇到問題，請參考 README.md 或重新安裝依賴"

else
    echo ""
    echo "❌ 更新失敗"
    echo "💡 請檢查網路連線或手動執行: git pull"
    exit 1
fi