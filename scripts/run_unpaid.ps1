# 黑貓宅急便交易明細表自動下載工具 - PowerShell 7 版本

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 確保在正確的專案目錄
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath
Set-Location $projectPath

Write-Host "🐱 黑貓宅急便交易明細表自動下載工具" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 載入共用檢查函數
$commonChecksPath = Join-Path $PSScriptRoot "common_checks.ps1"
if (Test-Path $commonChecksPath) {
    . $commonChecksPath
} else {
    Write-Host "❌ 找不到 common_checks.ps1，請確認檔案存在" -ForegroundColor Red
    exit 1
}

# 執行共用檢查
Test-Environment

# 直接執行交易明細表查詢功能
Write-Host "📥 啟動交易明細表查詢功能" -ForegroundColor Green
Write-Host ""

try {
    # 設定 PYTHONPATH 並執行 Python 程式
    $env:PYTHONPATH = $PWD.Path


    # 詢問下載天數（如果命令列沒有指定）
    if (-not ($args -contains "--days")) {
        Write-Host "📅 下載範圍設定" -ForegroundColor Yellow
        Write-Host "請輸入要下載的天數："
        Write-Host "• 例如：30 = 前 30 天"
        Write-Host "• 例如：7 = 前 7 天"
        Write-Host "• 空白 = 使用預設 30 天"
        Write-Host ""

        $daysInput = Read-Host "天數"

        # 驗證天數格式
        if ($daysInput -and $daysInput -match '^[0-9]+$') {
            $days = [int]$daysInput
            
            # 檢查天數的合理性（1-365天）
            if ($days -gt 0 -and $days -le 365) {
                $args += "--days"
                $args += $daysInput
                Write-Host "✅ 將下載前 ${days} 天的交易明細" -ForegroundColor Green
            } else {
                Write-Host "⚠️ 天數必須在 1-365 之間，使用預設 30 天" -ForegroundColor Yellow
            }
        } elseif ($daysInput) {
            Write-Host "⚠️ 天數格式錯誤，使用預設 30 天" -ForegroundColor Yellow
        } else {
            Write-Host "✅ 使用預設 30 天" -ForegroundColor Green
        }
        Write-Host ""
    }

    # 顯示執行命令
    $commandStr = "uv run python -u src/scrapers/unpaid_scraper.py"
    if ($args.Count -gt 0) {
        $commandStr += " " + ($args -join " ")
    }
    Write-Host "🚀 執行命令: $commandStr" -ForegroundColor Blue
    Write-Host ""

    # 執行 Python 程式
    & uv run python -u src/scrapers/unpaid_scraper.py @args

    # 檢查執行結果
    Test-ExecutionResult -ExitCode $LASTEXITCODE

} catch {
    Write-Host "❌ 執行過程中發生錯誤：$($_.Exception.Message)" -ForegroundColor Red
    Test-ExecutionResult -ExitCode 1
}

Write-Host ""
Read-Host "按 Enter 鍵繼續..."