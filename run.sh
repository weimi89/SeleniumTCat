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

# 檢查 requirements.txt 是否存在並安裝依賴
if [ -f "requirements.txt" ]; then
    echo "📦 安裝依賴套件..."
    uv pip install -r requirements.txt
fi

# 檢查參數並執行
if [ "$1" = "download" ] || [ -z "$1" ]; then
    echo "📥 執行黑貓宅急便自動下載貨到付款匯款明細表"
    uv run python takkyubin_selenium_scraper.py "${@:2}"  # 傳遞除了第一個參數外的所有參數
else
    echo "使用方式："
    echo "  ./run.sh                      - 執行自動下載貨到付款匯款明細表"
    echo "  ./run.sh --headless          - 背景模式執行"
    echo ""
    echo "或直接使用："
    echo "  uv run python takkyubin_selenium_scraper.py [選項]"
fi