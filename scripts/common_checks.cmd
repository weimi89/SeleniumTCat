@echo off
REM 黑貓宅急便工具共用檢查函數
REM 此腳本包含所有執行腳本需要的共用檢查邏輯

:check_environment
REM 檢查 uv 是否安裝
uv --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 系統元件遺失，請重新安裝程式
    pause
    exit /b 1
)

REM 檢查是否有 .venv 目錄，如果沒有就建立
if not exist ".venv" (
    echo 🔧 正在初始化...
    uv venv > nul
)

REM 同步依賴套件
echo 📦 檢查程式元件...
uv sync > nul

REM 設定環境變數確保即時輸出
set PYTHONUNBUFFERED=1

REM 檢查設定檔案
if not exist "accounts.json" (
    echo ❌ 找不到 accounts.json 設定檔案
    echo 請參考 accounts.json.example 建立設定檔案
    pause
    exit /b 1
)
goto :eof

:check_execution_result
REM 檢查執行結果
if %errorlevel% equ 0 (
    echo.
    echo ✅ 執行完成
) else (
    echo.
    echo ❌ 執行時發生錯誤
)
goto :eof