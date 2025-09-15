# 黑貓宅急便自動下載工具 - PowerShell 7 版本

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 確保在正確的專案目錄
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "🐱 黑貓宅急便自動下載工具" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 載入共用檢查函數
$commonChecksPath = Join-Path $PSScriptRoot "scripts\common_checks.ps1"
if (Test-Path $commonChecksPath) {
    . $commonChecksPath
} else {
    Write-Host "❌ 找不到 common_checks.ps1，請確認檔案存在" -ForegroundColor Red
    exit 1
}

# 執行共用檢查
Test-Environment

# 直接執行貨到付款查詢功能
Write-Host "📥 啟動貨到付款查詢功能" -ForegroundColor Green
Write-Host ""

try {
    # 設定 PYTHONPATH 並執行 Python 程式
    $env:PYTHONPATH = $PWD.Path
    
    # 檢查是否有 --headless 參數
    $isHeadless = $args -contains "--headless"
    
    # 詢問是否要使用無頭模式（如果命令列沒有指定）
    if (-not $isHeadless -and -not ($args -contains "--window")) {
        Write-Host "📋 執行模式選擇" -ForegroundColor Yellow
        Write-Host "1. 視窗模式 - 可看到瀏覽器操作過程"
        Write-Host "2. 無頭模式 - 後台執行，速度較快"
        Write-Host ""
        
        $modeChoice = Read-Host "請選擇執行模式 (1/2，預設: 1)"
        
        if ($modeChoice -eq "2") {
            $args += "--headless"
            Write-Host "✅ 將使用無頭模式執行" -ForegroundColor Green
        } else {
            Write-Host "✅ 將使用視窗模式執行" -ForegroundColor Green
        }
        Write-Host ""
    }
    
    # 詢問下載期數（如果命令列沒有指定）
    if (-not ($args -contains "--period")) {
        Write-Host "📅 下載範圍設定" -ForegroundColor Yellow
        Write-Host "請輸入要下載的期數："
        Write-Host "• 1 = 下載最新 1 期"
        Write-Host "• 3 = 下載最新 3 期"
        Write-Host "• 0 或空白 = 下載最新 1 期（預設）"
        Write-Host ""
        
        $periodInput = Read-Host "期數"
        
        if ($periodInput -and $periodInput -match '^\d+$' -and [int]$periodInput -gt 0) {
            $args += "--period"
            $args += $periodInput
            Write-Host "✅ 將下載最新 $periodInput 期" -ForegroundColor Green
        } else {
            Write-Host "✅ 使用預設值：下載最新 1 期" -ForegroundColor Green
        }
        Write-Host ""
    }
    
    # 顯示執行命令
    $commandStr = "uv run python -u payment_scraper.py"
    if ($args.Count -gt 0) {
        $commandStr += " " + ($args -join " ")
    }
    Write-Host "🚀 執行命令: $commandStr" -ForegroundColor Blue
    Write-Host ""
    
    # 執行 Python 程式
    & uv run python -u payment_scraper.py @args
    
    # 檢查執行結果
    Test-ExecutionResult -ExitCode $LASTEXITCODE
    
} catch {
    Write-Host "❌ 執行過程中發生錯誤：$($_.Exception.Message)" -ForegroundColor Red
    Test-ExecutionResult -ExitCode 1
}

Write-Host ""
Read-Host "按 Enter 鍵繼續..."