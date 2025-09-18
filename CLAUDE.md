# CLAUDE.md

這個檔案為 Claude Code (claude.ai/code) 在此儲存庫工作時提供指導。

## 專案概述

這是一個黑貓宅急便 (統一速達) 自動化工具套件，使用 Selenium 自動從黑貓宅急便網頁系統下載各種資料。支援貨到付款匯款明細查詢、運費(對帳單明細)查詢，以及交易明細表下載。該工具採用現代化的模組化架構，使用抽象基礎類別設計，易於擴展新功能。

**原本是 WEDI (宅配通) 系統，現已改為黑貓宅急便系統。**

## 專案結構

```
SeleniumTCat/
├── src/                          # 所有 Python 原始碼
│   ├── core/                     # 核心模組
│   │   ├── base_scraper.py       # 基礎爬蟲類別
│   │   ├── multi_account_manager.py  # 多帳號管理器
│   │   └── browser_utils.py      # 瀏覽器初始化工具
│   ├── scrapers/                 # 具體實作的爬蟲
│   │   ├── payment_scraper.py    # 貨到付款查詢工具
│   │   ├── freight_scraper.py    # 運費查詢工具
│   │   └── unpaid_scraper.py     # 交易明細表工具
│   └── utils/                    # 工具模組
│       └── windows_encoding_utils.py  # Windows 相容性工具
├── scripts/                      # 共用腳本
│   ├── common_checks.ps1         # PowerShell 共用檢查函數
│   ├── common_checks.sh          # Shell 共用檢查函數
│   └── common_checks.cmd         # CMD 共用檢查函數
├── Linux_客樂得對帳單.sh          # Linux 貨到付款執行腳本
├── Linux_發票明細.sh             # Linux 運費查詢執行腳本
├── Linux_客戶交易明細.sh          # Linux 交易明細表執行腳本
├── Linux_安裝.sh                # Linux 自動安裝腳本
├── Linux_更新.sh                # Linux 自動更新腳本
├── Windows_客樂得對帳單.cmd       # Windows 貨到付款執行腳本
├── Windows_發票明細.cmd          # Windows 運費查詢執行腳本
├── Windows_客戶交易明細.cmd       # Windows 交易明細表執行腳本
├── Windows_安裝.cmd             # Windows 自動安裝腳本
├── Windows_更新.cmd             # Windows 自動更新腳本
├── PowerShell_客樂得對帳單.ps1    # PowerShell 貨到付款執行腳本
├── PowerShell_發票明細.ps1       # PowerShell 運費查詢執行腳本
├── PowerShell_客戶交易明細.ps1    # PowerShell 交易明細表執行腳本
├── PowerShell_安裝.ps1          # PowerShell 自動安裝腳本
├── PowerShell_更新.ps1          # PowerShell 自動更新腳本
├── accounts.json                 # 帳號設定檔
├── accounts.json.example         # 帳號設定檔範例
├── pyproject.toml               # Python 專案設定
└── uv.lock                      # 鎖定依賴版本
```

## 核心架構

### 基礎模組 (src/core/)

1. **BaseScraper** (`src/core/base_scraper.py`): 核心基礎類別
   - 處理 Chrome WebDriver 瀏覽器初始化和管理
   - 管理登入流程，整合 ddddocr 自動驗證碼識別
   - 實作基本的導航流程（契約客戶專區 → 查詢頁面）
   - 提供共用的瀏覽器管理和連接管理功能

2. **MultiAccountManager** (`src/core/multi_account_manager.py`): 多帳號管理器
   - 讀取和解析 `accounts.json` 設定檔
   - 支援多帳號批次處理
   - 產生整合的總結報告
   - 提供依賴注入模式支援不同的抓取器類別

3. **browser_utils.py** (`src/core/browser_utils.py`): Chrome 瀏覽器初始化工具
   - 跨平台 Chrome WebDriver 設定和啟動
   - 支援無頭模式和視窗模式
   - 自動處理 ChromeDriver 版本和路徑問題

### 工具模組 (src/utils/)

1. **windows_encoding_utils.py**: Windows 編碼相容性處理
   - 提供 `safe_print()` 函數，將 Unicode 字符轉換為純文字
   - 支援跨平台 Unicode 字符顯示
   - 自動檢查和提醒 PYTHONUNBUFFERED 環境變數設定

### 爬蟲實作 (src/scrapers/)

本專案包含三個專門的爬蟲工具，各自針對不同的黑貓宅急便功能進行優化：

1. **PaymentScraper** (`src/scrapers/payment_scraper.py`): 客樂得對帳單查詢工具
   - **功能**: 下載貨到付款匯款明細（客樂得對帳單）
   - **繼承**: BaseScraper 實作貨到付款匯款明細查詢
   - **特色**: 自動選擇最新一期結算區間，無需手動指定日期範圍
   - **週期設定**: 支援命令列 `--period` 參數指定下載期數，預設 2 期
   - **檔案命名**: `{帳號}_{payment_no}.xlsx`
   - **下載方式**: 點擊連結下載 Excel 檔案

2. **FreightScraper** (`src/scrapers/freight_scraper.py`): 運費查詢工具
   - **功能**: 下載對帳單明細 (運費相關)
   - **繼承**: BaseScraper 實作對帳單明細查詢
   - **日期格式**: 支援日期範圍查詢（YYYYMMDD 格式）
   - **預設範圍**: 上個月
   - **搜尋目標**: 速達應付帳款查詢相關項目
   - **檔案命名**: `{帳號}_{發票日期}_{發票號碼}.xlsx`
   - **下載方式**: 使用 AJAX 搜尋後下載明細

3. **UnpaidScraper** (`src/scrapers/unpaid_scraper.py`): 交易明細表工具
   - **功能**: 下載交易明細表
   - **繼承**: BaseScraper 實作交易明細表查詢
   - **週期搜尋**: 支援週期搜尋方式，預設 2 期（1週1個檔案）
   - **檔案命名**: `{帳號}_{開始日期}_{結束日期}.xlsx`
   - **下載方式**: 執行 AJAX 搜尋請求後下載
   - **特色**: 支援 `--periods` 參數指定要下載的週期數量

### 關鍵技術細節

- **ddddocr 驗證碼識別**: 整合 ddddocr 函式庫自動識別黑貓宅急便登入頁面的驗證碼，大幅提升自動化成功率。
- **最新結算期間**: PaymentScraper 自動選擇最新一期的結算區間，UnpaidScraper 支援多週期搜尋。
- **AJAX 處理**: FreightScraper 和 UnpaidScraper 支援 AJAX 搜尋請求處理。
- **跨平台 Chrome 支援**: 使用 `.env` 檔案設定 Chrome 在 macOS、Windows 和 Linux 系統的執行檔路徑。
- **現代 Python 管理**: 使用 uv 進行快速依賴管理和虛擬環境處理。
- **契約客戶專區**: 專為黑貓宅急便契約客戶設計，自動選擇正確的登入模式。

### 舊版 WEDI 系統特點（參考用）
- **iframe 導航**: 工具在 WEDI 系統的巢狀 iframe 中導航。
- **過濾邏輯**: 只下載同時包含「代收貨款」和「匯款明細」關鍵字的項目。
- **日期範圍彈性**: 支援命令列日期參數（`--start-date`、`--end-date`）。

## 開發指令

### 設定和安裝
```bash
# 安裝 uv（如果尚未安裝）
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# 建立並啟動虛擬環境及安裝依賴
uv sync

# 或手動建立環境並安裝依賴
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
uv sync  # 使用 pyproject.toml 管理依賴
```

### 執行黑貓宅急便工具

#### 客樂得對帳單（貨到付款查詢）
```bash
# Windows 使用者（推薦）：
Windows_客樂得對帳單.cmd

# Linux/macOS 使用者：
./Linux_客樂得對帳單.sh

# 指定下載期數
Windows_客樂得對帳單.cmd --period 3  # Windows
./Linux_客樂得對帳單.sh --period 3  # Linux/macOS

# 無頭模式
Windows_客樂得對帳單.cmd --headless  # Windows
./Linux_客樂得對帳單.sh --headless  # Linux/macOS
```

#### 運費查詢（發票明細）
```bash
# Windows 使用者：
Windows_發票明細.cmd

# Linux/macOS 使用者：
./Linux_發票明細.sh

# 指定日期範圍
Windows_發票明細.cmd --start-date 20241201 --end-date 20241208  # Windows
./Linux_發票明細.sh --start-date 20241201 --end-date 20241208  # Linux/macOS
```

#### 交易明細表查詢
```bash
# Windows 使用者：
Windows_客戶交易明細.cmd

# Linux/macOS 使用者：
./Linux_客戶交易明細.sh

# 指定週期數量
Windows_客戶交易明細.cmd --periods 3  # Windows
./Linux_客戶交易明細.sh --periods 3  # Linux/macOS
```

### 手動執行（需要先設定環境變數）
```bash
# 客樂得對帳單（貨到付款查詢）
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/payment_scraper.py

# 運費查詢（發票明細）
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/freight_scraper.py

# 交易明細表查詢
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/unpaid_scraper.py

# Windows 使用者設定：
# set PYTHONPATH=%cd%
# uv run python -u src\scrapers\payment_scraper.py
# uv run python -u src\scrapers\freight_scraper.py
# uv run python -u src\scrapers\unpaid_scraper.py
```

### 設定檔案

- **pyproject.toml**: 現代 Python 專案設定，包含依賴和 uv 設定
- **accounts.json**: 包含帳號憑證和設定（⚠️ 不會被 Git 追蹤）
  - `enabled: true/false` 控制要處理哪些帳號
  - `settings.headless` 和 `settings.download_base_dir` 為全域設定
  - **重要**：請參考 `accounts.json.example` 建立此檔案
  - **安全提醒**：切勿將真實密碼提交到 Git

- **.env**: Chrome 執行檔路徑設定（從 `.env.example` 建立）
  ```
  CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  ```

### 安全注意事項

- `accounts.json` 已加入 `.gitignore`，不會被 Git 追蹤
- 請定期更改密碼，確保帳號安全
- 切勿在公開場所或文件中暴露真實密碼
- 建議使用強密碼並啟用雙因素認證（如果支援）

## 輸出結構

- **downloads/**: 按帳號下載的 Excel 檔案
  - 貨到付款：`客樂得對帳單_{帳號}_{結算期間}.xlsx`
  - 運費對帳單：`發票明細_{帳號}_{發票日期}_{發票號碼}.xlsx`
  - 交易明細表：`交易明細表_{帳號}_{開始日期}-{結束日期}.xlsx`
- **reports/**: 個別帳號執行報告（目前版本已停用）
- **logs/**: 執行日誌和除錯資訊
- **temp/**: 暫存處理檔案

## 重要實作說明

### 驗證碼處理

**自動識別機制**：
- 程式使用 ddddocr 函式庫自動識別黑貓宅急便登入頁面的驗證碼
- 成功識別後會自動填入並登入

**手動輸入模式**：
- 無法自動識別時，程式會等待使用者手動輸入
- **重要**：背景模式（--headless）無法手動輸入，建議使用視窗模式

**重試機制**：
- 登入失敗會自動重試最多3次
- 每次重試會重新載入頁面和重新識別驗證碼

### 週期和期數管理

**PaymentScraper (貨到付款)**：
- 使用 `--period` 參數指定下載期數
- 自動選擇最新一期或指定期數的結算區間

**UnpaidScraper (交易明細表)**：
- 使用 `--periods` 參數指定下載週期數
- 預設 2 個週期，每週期 7 天
- 檔案命名包含開始和結束日期

**FreightScraper (運費查詢)**：
- 使用日期範圍查詢（YYYYMMDD 格式）
- 支援 `--start-date` 和 `--end-date` 參數

### AJAX 處理

UnpaidScraper 和 FreightScraper 支援 AJAX 搜尋：
- 自動填入日期欄位（txtDateS, txtDateE）
- 點擊搜尋按鈕觸發 AJAX 請求
- 等待搜尋結果載入後執行下載

### 錯誤處理哲學
工具採用「繼續執行」方式，個別失敗不會停止整個流程：
- 日期設定失敗會記錄但不會中斷執行
- 找不到查詢按鈕時會跳過並顯示警告
- 個別帳號失敗不會影響其他帳號

### 多帳號處理
`MultiAccountManager` 依序處理帳號，並產生單一整合報告而非每個帳號的個別報告，以減少輸出雜亂。

### 現代化改進

**模組化架構**：
- 採用 `src/` 目錄結構，符合現代 Python 專案標準
- 根目錄不包含 Python 檔案，保持整潔
- 清晰的模組分離：core（核心）、scrapers（實作）、utils（工具）

**依賴管理**：
- 移除舊的 `requirements.txt`，統一使用 `pyproject.toml` + `uv.lock`
- 避免版本衝突和重複安裝問題
- 使用 `uv sync` 確保依賴版本一致性

**Windows 相容性**：
- 實作 `safe_print()` 函數處理 Unicode 字符顯示問題
- 所有 Unicode 字符（如 ✅ ❌ 🎉）自動轉換為純文字標籤
- 確保在 Windows 命令提示字元中正常顯示

**執行腳本優化**：
- 提供跨平台執行腳本（.sh、.cmd、.ps1）
- .cmd 檔案自動啟動 PowerShell，享受最佳體驗
- 智慧執行順序：Windows Terminal > PowerShell 7 > 舊版 PowerShell
- 完整 UTF-8 支援和彩色輸出
- 使用共用檢查函數 (scripts/common_checks.ps1, scripts/common_checks.sh)
- 自動設定必要的環境變數（PYTHONUNBUFFERED、PYTHONPATH）
- 簡化使用者執行流程