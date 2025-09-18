@echo off
chcp 65001 >nul

REM WEDI 工具自動更新腳本 (Windows)
REM 自動啟動 PowerShell 7 以獲得最佳體驗

echo 🔄 WEDI 工具自動更新程式
echo ==================================

REM 檢查是否為 Git 儲存庫
if not exist ".git" (
    echo ❌ 錯誤: 這不是一個 Git 儲存庫
    echo 💡 請確認您在正確的專案目錄中
    pause
    exit /b 1
)

echo 🔧 正在啟動 PowerShell 進行更新...
echo.

REM 建立完整路徑
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%PowerShell_更新.ps1"

REM 優先順序：PowerShell 7 > 舊版 PowerShell
where /q pwsh
if %ERRORLEVEL% == 0 (
    pwsh -NoProfile -Command "Set-Location '%SCRIPT_DIR%'; & '%SCRIPT_PATH%'"
) else (
    powershell -NoProfile -Command "Set-Location '%SCRIPT_DIR%'; & '%SCRIPT_PATH%'"
)

REM 檢查更新結果
if %ERRORLEVEL% == 0 (
    echo.
    echo ✅ 更新程序完成
) else (
    echo.
    echo ❌ 更新過程中發生錯誤
)

echo.
echo 按任意鍵退出...
pause >nul