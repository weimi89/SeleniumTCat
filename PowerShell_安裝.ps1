# 黑貓宅急便自動下載工具 - PowerShell 7 安裝腳本
# 需要 PowerShell 7+ 支援

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 確保在正確的專案目錄
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "🔧 安裝黑貓宅急便自動下載工具 - PowerShell 版本" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "🔍 專案路徑: $scriptPath" -ForegroundColor Blue
Write-Host ""

try {
    Write-Host "📦 步驟 1: 安裝 uv..." -ForegroundColor Yellow

    # 檢查 uv 是否已安裝
    try {
        $uvVersion = & uv --version 2>$null
        Write-Host "✅ uv 已安裝: $uvVersion" -ForegroundColor Green
    } catch {
        Write-Host "⬇️ 下載並安裝 uv..." -ForegroundColor Blue
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression

        # 重新檢查
        try {
            $uvVersion = & uv --version 2>$null
            Write-Host "✅ uv 安裝成功: $uvVersion" -ForegroundColor Green
        } catch {
            throw "uv 安裝失敗，請手動安裝"
        }
    }

    Write-Host "🔧 步驟 2: 建立虛擬環境..." -ForegroundColor Yellow
    uv venv
    if ($LASTEXITCODE -ne 0) {
        throw "建立虛擬環境失敗"
    }
    Write-Host "✅ 虛擬環境建立成功" -ForegroundColor Green

    Write-Host "📦 步驟 3: 安裝依賴套件..." -ForegroundColor Yellow
    uv sync
    if ($LASTEXITCODE -ne 0) {
        throw "安裝依賴套件失敗"
    }
    Write-Host "✅ 依賴套件安裝成功" -ForegroundColor Green

    Write-Host "🌐 步驟 4: 設定 Chrome 路徑..." -ForegroundColor Yellow
    if (-not (Test-Path ".env")) {
        $chromePaths = @(
            "C:\Program Files\Google\Chrome\Application\chrome.exe",
            "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        )

        $chromeFound = $false
        foreach ($path in $chromePaths) {
            if (Test-Path $path) {
                "CHROME_BINARY_PATH=`"$path`"" | Out-File -FilePath ".env" -Encoding UTF8
                Write-Host "✅ Chrome 路徑已設定: $path" -ForegroundColor Green
                $chromeFound = $true
                break
            }
        }

        if (-not $chromeFound) {
            # 使用預設路徑
            "CHROME_BINARY_PATH=`"C:\Program Files\Google\Chrome\Application\chrome.exe`"" | Out-File -FilePath ".env" -Encoding UTF8
            Write-Host "⚠️ Chrome 未在標準位置找到，已設定預設路徑" -ForegroundColor Yellow
            Write-Host "💡 如果您的 Chrome 安裝在其他位置，請編輯 .env 檔案" -ForegroundColor Blue
        }
    } else {
        Write-Host "✅ .env 檔案已存在" -ForegroundColor Green
    }

    Write-Host "👤 步驟 5: 建立帳號設定範例..." -ForegroundColor Yellow
    if (-not (Test-Path "accounts.json")) {
        if (Test-Path "accounts.json.example") {
            Copy-Item "accounts.json.example" "accounts.json"
            Write-Host "✅ 已從範例建立 accounts.json 檔案" -ForegroundColor Green
        } else {
            Write-Host "⚠️ 未找到 accounts.json.example，請手動建立 accounts.json" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✅ accounts.json 檔案已存在" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "🎉 安裝完成！" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 後續步驟：" -ForegroundColor Cyan
    Write-Host "1. 編輯 accounts.json 檔案，新增您的黑貓宅急便登入憑證" -ForegroundColor White
    Write-Host "2. 執行程式：./run_payment.cmd 或 ./run_payment.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 如果遇到任何問題，請查看 CLAUDE.md 或 README.md" -ForegroundColor Blue

} catch {
    Write-Host ""
    Write-Host "❌ 安裝過程中發生錯誤：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host "請檢查錯誤訊息並重試" -ForegroundColor Red
    Write-Host ""
    Write-Host "📞 常見問題解決方案：" -ForegroundColor Yellow
    Write-Host "• 確保以管理員身分執行 PowerShell" -ForegroundColor White
    Write-Host "• 檢查網路連線是否正常" -ForegroundColor White
    Write-Host "• 嘗試手動安裝 uv：Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression" -ForegroundColor White
    exit 1
}

Write-Host ""
Read-Host "按 Enter 鍵繼續..."