#!/bin/bash

# 黑貓宅急便運費查詢自動下載工具執行腳本 (macOS/Linux)
echo "🚛 黑貓宅急便運費查詢自動下載工具"
echo "================================="

# 載入共用檢查函數
source "$(dirname "$0")/scripts/common_checks.sh"

# 執行環境檢查
check_environment

# 執行運費查詢程式，並傳遞所有命令列參數
echo "🚀 啟動運費查詢功能"
echo

# 詢問使用者是否要自訂月份範圍（如果沒有命令列參數）
final_args=("$@")

# 檢查是否沒有日期相關參數
has_date_params=false
for arg in "$@"; do
    if [[ "$arg" == "--start-date" || "$arg" == "--end-date" ]]; then
        has_date_params=true
        break
    fi
done

if [[ $# -eq 0 || "$has_date_params" == false ]]; then
    # 計算預設日期範圍（上個月）
    start_date=$(date -d "last month" "+%Y%m01" 2>/dev/null || date -v-1m "+%Y%m01" 2>/dev/null || echo "")
    end_date=$(date -d "$(date -d 'last month' '+%Y-%m-01') +1 month -1 day" "+%Y%m%d" 2>/dev/null || \
               date -v-1m -v1d -v+1m -v-1d "+%Y%m%d" 2>/dev/null || echo "")

    echo ""
    echo "📅 查詢日期設定"
    if [[ -n "$start_date" && -n "$end_date" ]]; then
        echo "預設查詢範圍：${start_date} - ${end_date} (上個月)"
    else
        echo "預設查詢範圍：上個月完整範圍"
    fi
    echo ""

    read -p "是否要自訂日期範圍？(y/N): " custom_date

    if [[ "$custom_date" == "y" || "$custom_date" == "Y" ]]; then
        echo ""
        read -p "請輸入開始日期 (格式: YYYYMMDD，例如: 20250801): " start_date_str
        read -p "請輸入結束日期 (格式: YYYYMMDD，例如: 20250831): " end_date_str

        # 驗證並添加日期參數
        if [[ "$start_date_str" =~ ^[0-9]{8}$ ]]; then
            final_args+=("--start-date" "$start_date_str")
        fi

        if [[ "$end_date_str" =~ ^[0-9]{8}$ ]]; then
            final_args+=("--end-date" "$end_date_str")
        fi

        echo ""
        if [[ ${#final_args[@]} -gt $# ]]; then
            echo "✅ 將使用自訂日期範圍"
        else
            echo "⚠️ 未設定有效日期，將使用預設範圍"
        fi
    else
        if [[ -n "$start_date" && -n "$end_date" ]]; then
            echo "✅ 使用預設日期範圍：${start_date} - ${end_date} (上個月)"
        else
            echo "✅ 使用預設日期範圍：上個月"
        fi
    fi
fi

# 顯示執行命令
command_str="uv run python -u src/scrapers/freight_scraper.py"
if [[ ${#final_args[@]} -gt 0 ]]; then
    command_str="$command_str ${final_args[*]}"
fi
echo ""
echo "🚀 執行命令: $command_str"
echo ""

# 使用 uv 執行 Python 程式
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/freight_scraper.py "${final_args[@]}"

# 檢查執行結果
check_execution_result