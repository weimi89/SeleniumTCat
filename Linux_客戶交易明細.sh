#!/bin/bash

# 啟動腳本 - 使用 uv 管理 Python 環境 (黑貓宅急便交易明細表版本)
echo "🐱 黑貓宅急便交易明細表自動下載工具"
echo "======================================"

# 載入共用檢查函數
source "$(dirname "$0")/scripts/common_checks.sh"

# 執行環境檢查
check_environment

# 直接執行交易明細表查詢功能
echo "📥 啟動交易明細表查詢功能"
echo ""

# 設定參數陣列
final_args=("$@")

# 檢查是否沒有 --periods 參數
has_periods=false
for arg in "$@"; do
    if [[ "$arg" == "--periods" ]]; then
        has_periods=true
        break
    fi
done

# 詢問下載週期數（如果命令列沒有指定）
if [[ "$has_periods" == false ]]; then
    echo "📅 下載範圍設定"
    echo "請輸入要下載的週期數："
    echo "• 1 = 下載最新 1 週期"
    echo "• 2 = 下載最新 2 週期（預設）"
    echo "• 3 = 下載最新 3 週期"
    echo "• 0 或空白 = 下載最新 2 週期（預設）"
    echo ""
    
    read -p "週期數: " periods_input
    
    if [[ "$periods_input" =~ ^[0-9]+$ && "$periods_input" -gt 0 ]]; then
        final_args+=("--periods" "$periods_input")
        echo "✅ 將下載最新 $periods_input 個週期"
    else
        echo "✅ 使用預設值：下載最新 2 個週期"
    fi
    echo ""
fi

# 顯示執行命令
command_str="uv run python -u src/scrapers/unpaid_scraper.py"
if [[ ${#final_args[@]} -gt 0 ]]; then
    command_str="$command_str ${final_args[*]}"
fi
echo "🚀 執行命令: $command_str"
echo ""

# 執行交易明細表查詢程式
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/unpaid_scraper.py "${final_args[@]}"

# 檢查執行結果
check_execution_result