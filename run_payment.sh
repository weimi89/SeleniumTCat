#!/bin/bash

# 啟動腳本 - 使用 uv 管理 Python 環境 (黑貓宅急便版本)
echo "🐱 黑貓宅急便自動下載工具"
echo "======================================"

# 載入共用檢查函數
source "$(dirname "$0")/scripts/common_checks.sh"

# 執行環境檢查
check_environment

# 直接執行貨到付款查詢功能
echo "📥 啟動貨到付款查詢功能"
echo ""

# 檢查是否有 --headless 參數
has_headless=false
has_window=false
for arg in "$@"; do
    if [[ "$arg" == "--headless" ]]; then
        has_headless=true
    elif [[ "$arg" == "--window" ]]; then
        has_window=true
    fi
done

# 詢問是否要使用無頭模式（如果命令列沒有指定）
final_args=("$@")
if [[ "$has_headless" == false && "$has_window" == false ]]; then
    echo "📋 執行模式選擇"
    echo "1. 視窗模式 - 可看到瀏覽器操作過程"
    echo "2. 無頭模式 - 後台執行，速度較快"
    echo ""
    
    read -p "請選擇執行模式 (1/2，預設: 1): " mode_choice
    
    if [[ "$mode_choice" == "2" ]]; then
        final_args+=("--headless")
        echo "✅ 將使用無頭模式執行"
    else
        echo "✅ 將使用視窗模式執行"
    fi
    echo ""
fi

# 檢查是否沒有 --period 參數
has_period=false
for arg in "$@"; do
    if [[ "$arg" == "--period" ]]; then
        has_period=true
        break
    fi
done

# 詢問下載期數（如果命令列沒有指定）
if [[ "$has_period" == false ]]; then
    echo "📅 下載範圍設定"
    echo "請輸入要下載的期數："
    echo "• 1 = 下載最新 1 期"
    echo "• 3 = 下載最新 3 期"
    echo "• 0 或空白 = 下載最新 1 期（預設）"
    echo ""
    
    read -p "期數: " period_input
    
    if [[ "$period_input" =~ ^[0-9]+$ && "$period_input" -gt 0 ]]; then
        final_args+=("--period" "$period_input")
        echo "✅ 將下載最新 $period_input 期"
    else
        echo "✅ 使用預設值：下載最新 1 期"
    fi
    echo ""
fi

# 顯示執行命令
command_str="uv run python -u payment_scraper.py"
if [[ ${#final_args[@]} -gt 0 ]]; then
    command_str="$command_str ${final_args[*]}"
fi
echo "🚀 執行命令: $command_str"
echo ""

# 執行貨到付款查詢程式
PYTHONPATH="$(pwd)" uv run python -u payment_scraper.py "${final_args[@]}"

# 檢查執行結果
check_execution_result