# 黑貓宅急便工具共用檢查函數 - PowerShell 7 版本
# 此腳本包含所有執行腳本需要的共用檢查邏輯

function Test-Environment {
    Write-Host "🔍 專案路徑: $(Get-Location)" -ForegroundColor Blue

    # 檢查是否在正確的專案目錄（應該有 pyproject.toml）
    if (-not (Test-Path "pyproject.toml")) {
        Write-Host "❌ 找不到 pyproject.toml，請確認您在正確的專案目錄" -ForegroundColor Red
        Write-Host "目前路徑: $(Get-Location)" -ForegroundColor Yellow
        Read-Host "按 Enter 鍵繼續..."
        exit 1
    }

    # 檢查 uv 是否安裝
    try {
        $null = uv --version
    } catch {
        Write-Host "❌ 系統元件遺失，請重新安裝程式" -ForegroundColor Red
        Read-Host "按 Enter 鍵繼續..."
        exit 1
    }

    # 檢查是否有 .venv 目錄，如果沒有就建立
    if (-not (Test-Path ".venv")) {
        Write-Host "🔧 正在初始化..." -ForegroundColor Yellow
        uv venv | Out-Null
    }

    # 同步依賴套件
    Write-Host "📦 檢查程式元件..." -ForegroundColor Yellow
    uv sync | Out-Null

    # 設定環境變數確保即時輸出
    $env:PYTHONUNBUFFERED = "1"

    # 檢查設定檔案
    if (-not (Test-Path "accounts.json")) {
        Write-Host "❌ 找不到 accounts.json 設定檔案" -ForegroundColor Red
        Write-Host "請參考 accounts.json.example 建立設定檔案" -ForegroundColor Yellow

        # 如果有 example 檔案，詢問是否自動建立
        if (Test-Path "accounts.json.example") {
            $response = Read-Host "是否要複製 accounts.json.example 為 accounts.json？(y/N)"
            if ($response -eq 'y' -or $response -eq 'Y') {
                Copy-Item "accounts.json.example" "accounts.json"
                Write-Host "✅ 已建立 accounts.json，請編輯此檔案添加您的登入憑證" -ForegroundColor Green
                return
            }
        }

        Read-Host "按 Enter 鍵繼續..."
        exit 1
    }
}

function Test-ExecutionResult {
    param(
        [int]$ExitCode
    )

    Write-Host ""
    if ($ExitCode -eq 0) {
        Write-Host "✅ 執行完成" -ForegroundColor Green
    } else {
        Write-Host "❌ 執行時發生錯誤" -ForegroundColor Red
    }
}