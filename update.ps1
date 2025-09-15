# WEDI 工具自動更新腳本 (PowerShell)
# 使用 git pull 更新專案到最新版本

# 設定 UTF-8 編碼
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

# 錯誤時停止執行
$ErrorActionPreference = "Stop"

try {
    Write-Host "🔄 WEDI 工具自動更新程式" -ForegroundColor Cyan
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host ""

    # 檢查是否為 Git 儲存庫
    if (-not (Test-Path ".git" -PathType Container)) {
        Write-Host "❌ 錯誤: 這不是一個 Git 儲存庫" -ForegroundColor Red
        Write-Host "💡 請確認您在正確的專案目錄中" -ForegroundColor Yellow
        exit 1
    }

    # 檢查 Git 是否安裝
    try {
        $null = git --version
    } catch {
        Write-Host "❌ 錯誤: 找不到 Git" -ForegroundColor Red
        Write-Host "💡 請先安裝 Git: https://git-scm.com/download/windows" -ForegroundColor Yellow
        exit 1
    }

    # 檢查是否有未提交的變更
    Write-Host "🔍 檢查工作目錄狀態..." -ForegroundColor Blue
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "⚠️  警告: 發現未提交的變更" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "未提交的檔案:" -ForegroundColor Yellow
        git status --porcelain
        Write-Host ""
        
        $response = Read-Host "是否要繼續更新? 這可能會覆蓋您的變更 [y/N]"
        if ($response -notmatch '^[Yy]$') {
            Write-Host "❌ 更新已取消" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "💾 儲存當前變更到暫存區..." -ForegroundColor Blue
        $stashMessage = "Auto-stash before update $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git stash push -m $stashMessage
        Write-Host "✅ 變更已暫存" -ForegroundColor Green
    }

    # 檢查網路連線
    Write-Host "🌐 檢查網路連線..." -ForegroundColor Blue
    try {
        $null = git ls-remote origin HEAD 2>$null
    } catch {
        Write-Host "❌ 錯誤: 無法連接到遠端儲存庫" -ForegroundColor Red
        Write-Host "💡 請檢查您的網路連線和 Git 權限" -ForegroundColor Yellow
        exit 1
    }

    # 獲取當前分支
    $currentBranch = git branch --show-current
    Write-Host "📍 當前分支: $currentBranch" -ForegroundColor Cyan

    # 獲取當前版本
    $currentCommit = git rev-parse HEAD
    $currentCommitShort = git rev-parse --short HEAD
    Write-Host "📌 當前版本: $currentCommitShort" -ForegroundColor Cyan

    # 檢查遠端更新
    Write-Host "🔍 檢查遠端更新..." -ForegroundColor Blue
    git fetch origin

    # 比較本地和遠端版本
    $remoteCommit = git rev-parse "origin/$currentBranch"
    $remoteCommitShort = git rev-parse --short "origin/$currentBranch"

    if ($currentCommit -eq $remoteCommit) {
        Write-Host "✅ 專案已是最新版本 ($currentCommitShort)" -ForegroundColor Green
        Write-Host "🎉 無需更新!" -ForegroundColor Green
        exit 0
    }

    Write-Host "🆕 發現新版本: $remoteCommitShort" -ForegroundColor Yellow
    Write-Host ""

    # 顯示更新內容
    Write-Host "📋 更新內容預覽:" -ForegroundColor Cyan
    Write-Host "==================================" -ForegroundColor Cyan
    git log --oneline --graph --decorate "$currentCommit..$remoteCommit"
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host ""

    # 確認更新
    $response = Read-Host "是否要更新到最新版本? [Y/n]"
    if ($response -match '^[Nn]$') {
        Write-Host "❌ 更新已取消" -ForegroundColor Red
        exit 1
    }

    # 執行更新
    Write-Host "⬇️  正在下載更新..." -ForegroundColor Blue
    $pullResult = git pull origin $currentBranch
    
    if ($LASTEXITCODE -eq 0) {
        $newCommitShort = git rev-parse --short HEAD
        Write-Host ""
        Write-Host "✅ 更新成功!" -ForegroundColor Green
        Write-Host "📌 新版本: $newCommitShort" -ForegroundColor Cyan
        
        # 檢查是否需要更新依賴
        $changedFiles = git diff --name-only $currentCommit HEAD
        if ($changedFiles -match "(pyproject\.toml|uv\.lock)") {
            Write-Host ""
            Write-Host "📦 偵測到依賴變更，正在更新套件..." -ForegroundColor Blue
            
            if (Get-Command uv -ErrorAction SilentlyContinue) {
                uv sync
                Write-Host "✅ 依賴更新完成" -ForegroundColor Green
            } else {
                Write-Host "⚠️  請手動執行: uv sync" -ForegroundColor Yellow
            }
        }
        
        # 檢查是否有暫存的變更需要還原
        $stashList = git stash list
        if ($stashList -match "Auto-stash before update") {
            Write-Host ""
            Write-Host "🔄 還原之前暫存的變更..." -ForegroundColor Blue
            try {
                git stash pop
                Write-Host "✅ 變更已還原" -ForegroundColor Green
            } catch {
                Write-Host "⚠️  變更還原時發生衝突，請手動處理" -ForegroundColor Yellow
                Write-Host "💡 使用 'git stash list' 查看暫存清單" -ForegroundColor Yellow
            }
        }
        
        Write-Host ""
        Write-Host "🎉 WEDI 工具更新完成!" -ForegroundColor Green
        Write-Host "💡 如果遇到問題，請參考 README.md 或重新安裝依賴" -ForegroundColor Yellow
        
    } else {
        Write-Host ""
        Write-Host "❌ 更新失敗" -ForegroundColor Red
        Write-Host "💡 請檢查網路連線或手動執行: git pull" -ForegroundColor Yellow
        exit 1
    }

} catch {
    Write-Host ""
    Write-Host "❌ 發生未預期的錯誤: $_" -ForegroundColor Red
    Write-Host "💡 請檢查 Git 設定或網路連線" -ForegroundColor Yellow
    exit 1
}

# 只有在直接執行時才暫停
if ($MyInvocation.InvocationName -ne "&") {
    Write-Host ""
    Write-Host "按任意鍵繼續..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}