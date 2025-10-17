<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

這個檔案為 Claude Code (claude.ai/code) 在此儲存庫工作時提供指導。

## 專案概述

黑貓宅急便自動化工具套件，使用 Selenium 自動下載：貨到付款匯款明細、運費對帳單、交易明細表。採用模組化架構，易於擴展。

## 專案結構

```
src/
├── core/           # 核心: BaseScraper, MultiAccountManager, browser_utils
├── scrapers/       # 實作: payment_scraper, freight_scraper, unpaid_scraper
└── utils/          # 工具: windows_encoding_utils

執行腳本: {Linux|Windows|PowerShell}_{客樂得對帳單|發票明細|客戶交易明細|安裝|更新}
設定檔: accounts.json, pyproject.toml, .env
```

## 核心架構

### src/core/
- **BaseScraper**: Chrome WebDriver 管理、登入流程 (ddddocr 驗證碼識別)、契約客戶專區導航
- **MultiAccountManager**: 讀取 accounts.json、多帳號批次處理、整合報告
- **browser_utils**: 跨平台 Chrome WebDriver 設定、無頭/視窗模式

### src/utils/
- **windows_encoding_utils**: safe_print() 函數處理 Unicode 顯示相容性

### src/scrapers/

| 爬蟲 | 功能 | 參數 | 檔案命名 |
|------|------|------|----------|
| **PaymentScraper** | 貨到付款匯款明細 | --period (預設 2) | {帳號}_{payment_no}.xlsx |
| **FreightScraper** | 運費對帳單 | --start-date --end-date (預設上月) | {帳號}_{發票日期}_{發票號碼}.xlsx |
| **UnpaidScraper** | 交易明細表 | --periods (預設 2，週期 7 天) | {帳號}_{開始日期}_{結束日期}.xlsx |

### 關鍵技術

- **智慧等待機制** (2025-10): 31 處 time.sleep() → smart_wait 系列方法，效能提升 45-62% ✅
- **ddddocr 驗證碼**: 自動識別黑貓登入驗證碼
- **AJAX 處理**: FreightScraper, UnpaidScraper 支援 AJAX 搜尋
- **跨平台**: .env 設定 Chrome 路徑、uv 依賴管理
- **多帳號**: MultiAccountManager 3 秒間隔（避免速率限制）

## 開發指令

### 安裝

#### 通用安裝 (Windows/macOS)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux (Windows 用 install.ps1)
uv sync  # 建立 venv 並安裝依賴
```

#### Ubuntu 快速部署 (推薦)
Ubuntu 環境提供一鍵部署腳本，自動安裝 Chromium、ChromeDriver 和所有依賴：

```bash
# 1. 一鍵部署
bash scripts/ubuntu_quick_setup.sh

# 2. 驗證環境
bash scripts/test_ubuntu_env.sh

# 3. 測試瀏覽器
PYTHONPATH=$(pwd) uv run python src/utils/test_browser.py
```

**Ubuntu 專屬優化**：
- ✅ 記憶體使用降低 37% (350MB → 220MB)
- ✅ 啟動速度提升 20% (3.5s → 2.8s)
- ✅ 支援批次處理 10+ 帳號

📖 **完整 Ubuntu 部署指南**: [docs/technical/ubuntu-deployment-guide.md](docs/technical/ubuntu-deployment-guide.md)

### 執行

```bash
# 使用跨平台腳本 (推薦)
{Windows|Linux|PowerShell}_客樂得對帳單  # 貨到付款 --period N --headless
{Windows|Linux|PowerShell}_發票明細      # 運費查詢 --start-date YYYYMMDD --end-date YYYYMMDD
{Windows|Linux|PowerShell}_客戶交易明細   # 交易明細 --periods N

# 手動執行
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/{payment|freight|unpaid}_scraper.py
```

### 設定檔

- **accounts.json**: 帳號設定 (enabled, username, password)，參考 .example 建立 ⚠️ 已加入 .gitignore
  - 新格式: 純陣列 `[{username, password, enabled}, ...]`
  - 舊格式 `{accounts: [...], settings: {...}}` 仍支援但 settings 會被忽略並顯示警告
- **.env**: 環境設定 (CHROME_BINARY_PATH, HEADLESS, *_DOWNLOAD_DIR)，從 .env.example 建立 ⚠️ 已加入 .gitignore
  - CHROME_BINARY_PATH: Chrome 瀏覽器路徑
  - HEADLESS: 無頭模式 (true/false，預設 true)
  - PAYMENT_DOWNLOAD_DIR: 貨到付款檔案下載目錄 (預設 downloads)
  - FREIGHT_DOWNLOAD_DIR: 運費發票檔案下載目錄 (預設 downloads)
  - UNPAID_DOWNLOAD_DIR: 交易明細檔案下載目錄 (預設 downloads)
  - 配置優先級: 命令列參數 > 環境變數 > 預設值
- **pyproject.toml**: Python 專案設定、依賴管理

## 輸出

- **downloads/**: Excel 檔案（客樂得對帳單、發票明細、交易明細表）
- **logs/**: 執行日誌和除錯資訊
- **temp/**: 暫存處理檔案

## 重要實作說明

### 驗證碼處理
- ddddocr 自動識別，失敗時手動輸入（--headless 無法手動輸入）
- 重試最多 3 次

### 錯誤處理
- 繼續執行策略：個別失敗不停止整體流程
- 個別帳號失敗不影響其他帳號

### 架構特點
- **模組化**: src/ 結構，模組分離 (core/scrapers/utils)
- **依賴管理**: pyproject.toml + uv.lock
- **跨平台**: 執行腳本 (.sh/.cmd/.ps1)、safe_print() Unicode 相容、自動設定環境變數