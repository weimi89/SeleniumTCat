@echo off
set "SCRIPT=%~dp0setup.ps1"

rem 優先用 Windows Terminal
where wt >nul 2>&1
if %errorlevel%==0 (
  wt -w 0 -p "PowerShell" "pwsh" -NoExit -ExecutionPolicy Bypass -File "%SCRIPT%"
  exit /b
)

rem 如果沒裝 Windows Terminal，直接用 pwsh
where pwsh >nul 2>&1
if %errorlevel%==0 (
  start "" pwsh -NoExit -ExecutionPolicy Bypass -File "%SCRIPT%"
  exit /b
)

rem 備援舊版 PowerShell
start "" powershell -NoExit -ExecutionPolicy Bypass -File "%SCRIPT%"