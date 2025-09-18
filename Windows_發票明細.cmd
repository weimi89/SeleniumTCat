@echo off
chcp 65001 >nul 2>&1
set "SCRIPT=%~dp0PowerShell_發票明細.ps1"

rem 使用相對路徑避免中文路徑問題
cd /d "%~dp0"

rem 優先用 Windows Terminal
where wt >nul 2>&1
if %errorlevel%==0 (
  wt -w 0 -p "PowerShell" "pwsh" -NoExit -ExecutionPolicy Bypass -File "PowerShell_發票明細.ps1" %*
  exit /b
)

rem 如果沒裝 Windows Terminal，直接用 pwsh
where pwsh >nul 2>&1
if %errorlevel%==0 (
  start "" pwsh -NoExit -ExecutionPolicy Bypass -File "PowerShell_發票明細.ps1" %*
  exit /b
)

rem 備援舊版 PowerShell
start "" powershell -NoExit -ExecutionPolicy Bypass -File "PowerShell_發票明細.ps1" %*
