#!/bin/bash

# 啟動腳本 - 使用 uv 管理 Python 環境 (黑貓宅急便版本)
echo "🐱 啟動黑貓宅急便自動下載工具"
echo "======================================"

# 檢查 uv 是否安裝
if ! command -v uv &> /dev/null; then
    echo "❌ 找不到 uv，請先安裝："
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   或參考 https://github.com/astral-sh/uv#installation"
    exit 1
fi

# 檢查是否有 .venv 目錄，如果沒有就建立
if [ ! -d ".venv" ]; then
    echo "🔧 建立虛擬環境..."
    uv venv
fi

# 同步依賴套件
echo "📦 同步依賴套件..."
uv sync

# 直接執行下載功能
echo "📥 執行黑貓宅急便自動下載貨到付款匯款明細表"
# 設定環境變數確保即時輸出
export PYTHONUNBUFFERED=1
echo ""
echo "📅 請輸入要下載的期數 (例如: 1 表示下載最新1期, 3 表示下載最新3期)"
echo "   直接按 Enter 使用預設值 (最新一期)"
read -p "期數: " period_number

# 如果使用者沒有輸入，使用預設值
if [ -z "$period_number" ]; then
    echo "📅 使用預設值 (下載最新1期)"
    uv run python -u takkyubin_selenium_scraper.py "$@"  # 傳遞所有參數
else
    echo "📅 使用指定期數: 下載最新 $period_number 期"
    uv run python -u takkyubin_selenium_scraper.py --period "$period_number" "$@"  # 傳遞所有參數
fi