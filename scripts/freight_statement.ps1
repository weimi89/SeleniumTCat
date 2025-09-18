# 黑貓宅急便自動下載工具 - PowerShell 7 版本

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 確保在正確的專案目錄
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath
Set-Location $projectPath

Write-Host "🐱 黑貓宅急便自動下載工具" -ForegroundColor Cyan
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

# 直接執行貨到付款查詢功能
Write-Host "📥 啟動貨到付款查詢功能" -ForegroundColor Green
Write-Host ""

try {
    # 設定 PYTHONPATH 並執行 Python 程式
    $env:PYTHONPATH = $PWD.Path


    # 詢問日期範圍（如果命令列沒有指定）
    if (-not ($args -contains "--start-date") -and -not ($args -contains "--end-date")) {
        Write-Host "📅 查詢日期設定" -ForegroundColor Yellow

        # 取得上個月的範圍 - 使用最直接的計算方式
        $today = Get-Date

        # 計算上個月
        if ($today.Month -eq 1) {
            $lastMonthYear = $today.Year - 1
            $lastMonthNum = 12
        } else {
            $lastMonthYear = $today.Year
            $lastMonthNum = $today.Month - 1
        }

        # 上個月第一天
        $startDate = Get-Date -Year $lastMonthYear -Month $lastMonthNum -Day 1

        # 上個月最後一天（本月第一天減1天）
        $thisMonthFirst = Get-Date -Year $today.Year -Month $today.Month -Day 1
        $endDate = $thisMonthFirst.AddDays(-1)

        $defaultStart = $startDate.ToString("yyyyMMdd")
        $defaultEnd = $endDate.ToString("yyyyMMdd")

        Write-Host "預設查詢範圍：$defaultStart - $defaultEnd (上個月)"
        Write-Host ""

        $customDate = Read-Host "是否要自訂日期範圍？(y/N)"

        if ($customDate -eq 'y' -or $customDate -eq 'Y') {
            $startInput = Read-Host "開始日期 (YYYYMMDD)"
            $endInput = Read-Host "結束日期 (YYYYMMDD)"

            if ($startInput -match '^\d{8}$') {
                $args += "--start-date"
                $args += $startInput
            }
            if ($endInput -match '^\d{8}$') {
                $args += "--end-date"
                $args += $endInput
            }

            Write-Host "✅ 將查詢日期範圍：$startInput - $endInput" -ForegroundColor Green
        } else {
            # 使用預設範圍，將預設日期加入參數
            $args += "--start-date"
            $args += $defaultStart
            $args += "--end-date"
            $args += $defaultEnd
            Write-Host "✅ 使用預設範圍：$defaultStart - $defaultEnd" -ForegroundColor Green
        }
        Write-Host ""
    }

    # 顯示執行命令
    $commandStr = "uv run python -u src/scrapers/freight_scraper.py"
    if ($args.Count -gt 0) {
        $commandStr += " " + ($args -join " ")
    }
    Write-Host "🚀 執行命令: $commandStr" -ForegroundColor Blue
    Write-Host ""

    # 執行 Python 程式
    & uv run python -u src/scrapers/freight_scraper.py @args

    # 檢查執行結果
    Test-ExecutionResult -ExitCode $LASTEXITCODE

} catch {
    Write-Host "❌ 執行過程中發生錯誤：$($_.Exception.Message)" -ForegroundColor Red
    Test-ExecutionResult -ExitCode 1
}

Write-Host ""
Read-Host "按 Enter 鍵繼續..."