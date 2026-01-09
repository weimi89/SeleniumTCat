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
├── core/           # 核心模組
│   ├── base_scraper.py         # 基礎抓取器 (登入、驗證碼、智慧等待)
│   ├── multi_account_manager.py # 多帳號管理 (批次處理、報告、Discord/Email 通知)
│   └── browser_utils.py         # Chrome WebDriver 初始化
├── scrapers/       # 實作模組
│   ├── payment_scraper.py      # 貨到付款匯款明細
│   ├── freight_scraper.py      # 運費對帳單
│   └── unpaid_scraper.py       # 交易明細表
└── utils/          # 工具模組
    ├── windows_encoding_utils.py # Unicode 顯示相容
    ├── discord_notifier.py       # Discord Webhook 通知
    ├── email_notifier.py         # Email SMTP 通知
    └── test_browser.py           # 瀏覽器環境測試

執行腳本: {Linux|Windows}_{客樂得對帳單|發票明細|客戶交易明細|安裝|更新}.{sh|cmd}
設定檔: accounts.json, pyproject.toml, .env
輸出目錄: downloads/, reports/, logs/, temp/
```

## 核心架構

### src/core/
- **BaseScraper**: 基礎抓取器類別
  - Chrome WebDriver 管理、登入流程 (ddddocr 驗證碼識別)
  - 智慧等待方法: `smart_wait()`, `smart_wait_for_element()`, `smart_wait_for_ajax()`
  - 會話管理: 超時處理、密碼安全警告檢測
  - 檔案下載: UUID 臨時目錄、自動清理機制
- **MultiAccountManager**: 多帳號管理器
  - 讀取 accounts.json、批次處理多帳號
  - 功能名稱識別 (`SCRAPER_NAMES` 映射)
  - 執行報告生成 (JSON 格式)
  - Discord 通知整合 (執行摘要、密碼警告)
  - Email 通知整合 (執行摘要、密碼警告)
- **browser_utils**: ChromeDriver 初始化
  - 跨平台 Chrome 設定、無頭/視窗模式
  - WebDriver Manager 自動版本匹配 (優先使用)
  - 系統 ChromeDriver 後備方案

### src/utils/
- **windows_encoding_utils**: `safe_print()` 函數處理 Unicode 顯示相容性
- **discord_notifier**: Discord Webhook 通知器
  - 執行摘要通知 (進度條、狀態顏色、下載檔案清單)
  - 密碼安全警告通知 (含處理步驟)
- **email_notifier**: Email SMTP 通知器
  - 執行摘要通知 (純文字格式)
  - 密碼安全警告通知 (含處理步驟)
  - 支援 TLS/SSL 加密
- **test_browser**: 瀏覽器環境測試工具

### src/scrapers/

| 爬蟲 | 功能 | 參數 | 檔案命名 |
|------|------|------|----------|
| **PaymentScraper** | 貨到付款匯款明細 | `--period N` (預設 2) | 客樂得對帳單_{帳號}_{結算期間}.xlsx |
| **FreightScraper** | 運費對帳單 | `--start-date` `--end-date` (預設上月) | 發票明細_{帳號}_{發票日期}_{發票號碼}.xlsx |
| **UnpaidScraper** | 交易明細表 | `--days N` (預設 14 天) | 交易明細表_{帳號}_{開始日期}-{結束日期}.xlsx |

所有 Scraper 支援 `quiet_init` 參數，用於多帳號模式下抑制重複的初始化訊息。

### 關鍵技術

- **ChromeDriver 自動匹配** (2026-01): WebDriver Manager 優先自動下載匹配版本 ✅
- **智慧等待機制** (2025-10): 31 處 time.sleep() → smart_wait 系列方法，效能提升 45-62% ✅
- **ddddocr 驗證碼**: 自動識別黑貓登入驗證碼
- **AJAX 處理**: FreightScraper, UnpaidScraper 支援 AJAX 搜尋
- **跨平台**: .env 設定 Chrome 路徑、uv 依賴管理
- **多帳號**: MultiAccountManager 3 秒間隔（避免速率限制）
- **Discord 通知** (2026-01 優化):
  - 執行摘要: 進度條視覺化、動態狀態顏色、下載檔案清單
  - 密碼安全警告: 含處理步驟指引、@here 標記
- **Email 通知** (2026-01 新增):
  - 執行摘要: 純文字格式、進度條視覺化
  - 密碼安全警告: 含處理步驟指引
  - 支援 TLS/SSL 加密、常見 SMTP 伺服器

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
  - PAYMENT_DOWNLOAD_WORK_DIR: 貨到付款檔案下載目錄 (預設 downloads)
  - FREIGHT_DOWNLOAD_WORK_DIR: 運費發票檔案下載目錄 (預設 downloads)
  - UNPAID_DOWNLOAD_WORK_DIR: 交易明細檔案下載目錄 (預設 downloads)
  - PAYMENT_DOWNLOAD_OK_DIR: 貨到付款已完成目錄（設定後跳過重複下載）
  - FREIGHT_DOWNLOAD_OK_DIR: 運費發票已完成目錄（設定後跳過重複下載）
  - UNPAID_DOWNLOAD_OK_DIR: 交易明細已完成目錄（設定後跳過重複下載）
  - DISCORD_WEBHOOK_URL: Discord Webhook URL，設定後會在執行完成時發送通知（可選）
  - MAIL_HOST/MAIL_PORT/MAIL_USERNAME/MAIL_PASSWORD: Email SMTP 設定（可選）
  - MAIL_ENCRYPTION: 加密方式 tls/ssl/none（預設 tls）
  - MAIL_FROM_ADDRESS/MAIL_TO_ADDRESS: 寄件人/收件人地址
  - 配置優先級: 命令列參數 > 環境變數 > 預設值
- **pyproject.toml**: Python 專案設定、依賴管理

### Discord 通知（可選功能）

設定 DISCORD_WEBHOOK_URL 後，系統會在所有帳號處理完成時自動發送通知到 Discord 頻道：

- **執行摘要通知**:
  - 視覺化進度條 (🟩⬜ 格式)
  - 動態狀態顏色 (綠色成功/紅色失敗/橘色警告)
  - 帳號統計、下載統計
  - 下載檔案清單 (按帳號分組)
  - 總執行時間
- **密碼安全警告**: 當有帳號需要更新密碼時，發送詳細警告通知
  - 使用 @here 標記提醒
  - 含處理步驟指引

取得 Webhook URL：Discord 伺服器設定 → 整合 → Webhook → 建立 Webhook

測試通知功能：
```bash
PYTHONPATH="$(pwd)" uv run python tests/test_discord_notifier.py
```

### Email 通知（可選功能）

設定 SMTP 相關環境變數後，系統會在所有帳號處理完成時自動發送 Email 通知（與 Discord 並行）：

- **執行摘要通知**:
  - 純文字格式，視覺化進度條
  - 帳號統計、下載統計、總執行時間
  - 下載檔案清單
- **密碼安全警告**: 當有帳號需要更新密碼時，發送詳細警告郵件

**常見 SMTP 設定**：
- Gmail: `MAIL_HOST=smtp.gmail.com`, `MAIL_PORT=587`, `MAIL_ENCRYPTION=tls`
- Outlook: `MAIL_HOST=smtp.office365.com`, `MAIL_PORT=587`, `MAIL_ENCRYPTION=tls`

測試通知功能：
```bash
PYTHONPATH="$(pwd)" uv run python tests/test_email_notifier.py
```

## 輸出

- **downloads/**: Excel 檔案（客樂得對帳單、發票明細、交易明細表）
- **reports/**: 執行報告 JSON 檔案（{timestamp}.json，含功能名稱、帳號統計、執行時間）
- **logs/**: 執行日誌和除錯資訊
- **temp/**: 暫存處理檔案（UUID 臨時下載目錄，完成後自動清理）

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
- **跨平台**: 執行腳本 (.sh/.cmd)、safe_print() Unicode 相容、自動設定環境變數
- **ChromeDriver**: WebDriver Manager 自動匹配版本，系統 ChromeDriver 後備
- **多帳號輸出優化**: 全域設定只顯示一次，quiet_init 抑制重複訊息
- **執行報告**: JSON 格式報告，含功能名稱識別、執行時間統計
- **Discord 整合**: 可選通知功能，視覺化執行摘要和密碼警告
- **Email 整合**: 可選 SMTP 通知，支援 TLS/SSL 加密