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

# 檢查是否沒有 --days 參數
has_days=false
for arg in "$@"; do
    if [[ "$arg" == "--days" ]]; then
        has_days=true
        break
    fi
done

# 詢問下載天數（如果命令列沒有指定）
if [[ "$has_days" == false ]]; then
    echo "📅 下載範圍設定"
    echo "請輸入要下載的天數："
    echo "• 例如：30 = 前 30 天"
    echo "• 例如：7 = 前 7 天"
    echo "• 空白 = 使用預設 30 天"
    echo ""

    read -p "天數: " days_input

    # 驗證天數格式
    if [[ "$days_input" =~ ^[0-9]+$ ]]; then
        if [[ $days_input -gt 0 && $days_input -le 365 ]]; then
            final_args+=("--days" "$days_input")
            echo "✅ 將下載前 ${days_input} 天的交易明細"
        else
            echo "⚠️ 天數必須在 1-365 之間，使用預設 30 天"
        fi
    elif [[ -n "$days_input" ]]; then
        echo "⚠️ 天數格式錯誤，使用預設 30 天"
    else
        echo "✅ 使用預設 30 天"
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