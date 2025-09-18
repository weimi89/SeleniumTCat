@echo off
chcp 65001 >nul 2>&1

rem 切換到腳本目錄
pushd "%~dp0"

rem 檢查 PowerShell 腳本是否存在
if not exist "scripts\invoice_details.ps1" (
    echo ❌ 錯誤：找不到 scripts\invoice_details.ps1 檔案
    echo 📁 當前目錄：%CD%
    pause
    exit /b 1
)

rem 優先用 Windows Terminal
where wt >nul 2>&1
if %errorlevel%==0 (
    echo 🚀 使用 Windows Terminal 啟動...
    wt -w 0 -p "PowerShell" pwsh -NoExit -ExecutionPolicy Bypass -WorkingDirectory "%CD%" -File "%CD%\scripts\invoice_details.ps1" %*
    goto :end
)

rem 如果沒裝 Windows Terminal，直接用 pwsh
where pwsh >nul 2>&1
if %errorlevel%==0 (
    echo 🚀 使用 PowerShell 7 啟動...
    start "" pwsh -NoExit -ExecutionPolicy Bypass -WorkingDirectory "%CD%" -File "%CD%\scripts\invoice_details.ps1" %*
    goto :end
)

rem 備援舊版 PowerShell
echo 🚀 使用傳統 PowerShell 啟動...
start "" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location '%CD%'; & '.\scripts\invoice_details.ps1'" %*

:end
popd
