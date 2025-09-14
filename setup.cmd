@echo off
chcp 65001 >nul
echo 安裝宅急便工具 - Windows 相容版本...

echo 步驟 1：檢查是否已安裝 uv...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo 找不到 uv。正在安裝 uv...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    echo 請重新啟動命令提示字元並再次執行此腳本。
    pause
    exit /b 1
)

echo 步驟 2：使用 uv 同步專案相依性...
uv sync

echo 步驟 3：檢查安裝是否成功...
uv run python --version

echo.
echo 安裝完成！
echo.
echo 執行工具：
echo   uv run takkyubin_selenium_scraper.py
echo   或
echo   uv run takkyubin_selenium_scraper.py --headless
echo.
echo 如果遇到 DLL 錯誤，請安裝：
echo Microsoft Visual C++ 可轉散發套件：https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
pause