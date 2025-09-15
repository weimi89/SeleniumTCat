#!/bin/bash

# 黑貓宅急便工具共用檢查函數
# 此腳本包含所有執行腳本需要的共用檢查邏輯

check_environment() {
    # 檢查 uv 是否安裝
    if ! command -v uv &> /dev/null; then
        echo "❌ 系統元件遺失，請重新安裝程式"
        exit 1
    fi

    # 檢查是否有 .venv 目錄，如果沒有就建立
    if [ ! -d ".venv" ]; then
        echo "🔧 正在初始化..."
        uv venv > /dev/null
    fi

    # 同步依賴套件
    echo "📦 檢查程式元件..."
    uv sync > /dev/null

    # 設定環境變數確保即時輸出
    export PYTHONUNBUFFERED=1

    # 檢查設定檔案
    if [ ! -f "accounts.json" ]; then
        echo "❌ 找不到 accounts.json 設定檔案"
        echo "請參考 accounts.json.example 建立設定檔案"
        exit 1
    fi
}

check_execution_result() {
    # 檢查執行結果
    if [ $? -eq 0 ]; then
        echo
        echo "✅ 執行完成"
    else
        echo
        echo "❌ 執行時發生錯誤"
    fi
}