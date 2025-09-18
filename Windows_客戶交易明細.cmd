@echo off
chcp 65001 >nul 2>&1

rem 建立完整路徑
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%PowerShell_客戶交易明細.ps1"

rem 優先用 Windows Terminal
where wt >nul 2>&1
if %errorlevel%==0 (
  wt -w 0 -p "PowerShell" "pwsh" -NoExit -ExecutionPolicy Bypass -Command "Set-Location '%SCRIPT_DIR%'; & '%SCRIPT_PATH%'" %*
  exit /b
)

rem 如果沒裝 Windows Terminal，直接用 pwsh
where pwsh >nul 2>&1
if %errorlevel%==0 (
  start "" pwsh -NoExit -ExecutionPolicy Bypass -Command "Set-Location '%SCRIPT_DIR%'; & '%SCRIPT_PATH%'" %*
  exit /b
)

rem 備援舊版 PowerShell
start "" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location '%SCRIPT_DIR%'; & '%SCRIPT_PATH%'" %*
