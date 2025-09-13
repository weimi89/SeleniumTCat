@echo off
echo Starting Takkyubin download...

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please run setup.cmd first
    pause
    exit /b 1
)

.venv\Scripts\python.exe takkyubin_selenium_scraper.py %*

echo Process completed.
pause