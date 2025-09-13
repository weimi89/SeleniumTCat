# CLAUDE.md

這個檔案為 Claude Code (claude.ai/code) 在此儲存庫工作時提供指導。

## 專案概述

這是一個黑貓宅急便 (統一速達) 自動化工具，使用 Selenium 自動從黑貓宅急便網頁系統下載貨到付款匯款明細表。該工具支援多帳號處理，並整合 ddddocr 進行驗證碼自動識別。

**原本是 WEDI (宅配通) 系統，現已改為黑貓宅急便系統。**

## 核心架構

### 主要元件

1. **TakkyubinSeleniumScraper** (`takkyubin_selenium_scraper.py`): 核心自動化類別
   - 處理 Chrome WebDriver 瀏覽器初始化
   - 管理登入流程，整合 ddddocr 自動驗證碼識別
   - 導航到貨到付款查詢頁面
   - 自動選擇最新一期結算區間
   - 下載貨到付款匯款明細表 Excel 檔案

2. **MultiAccountManager** (`takkyubin_selenium_scraper.py`): 批次處理管理器
   - 處理 `accounts.json` 中的多個帳號
   - 產生整合的總結報告
   - 管理順序執行和錯誤處理

3. **舊版 WEDI 工具**: 
   - `wedi_selenium_scraper.py`: 原本的宅配通系統工具（保留作為參考）

### 關鍵技術細節

- **ddddocr 驗證碼識別**: 整合 ddddocr 函式庫自動識別黑貓宅急便登入頁面的驗證碼，大幅提升自動化成功率。
- **最新結算期間**: 自動選擇最新一期的結算區間，無需手動指定日期範圍。
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
uv pip install -r requirements.txt
```

### 執行黑貓宅急便工具
```bash
# 使用 shell 腳本執行（推薦）
./run_takkyubin.sh download           # 視窗模式
./run_takkyubin.sh download-headless  # 無頭模式

# 直接使用 uv 執行 Python
uv run takkyubin_selenium_scraper.py

# 無頭模式
uv run takkyubin_selenium_scraper.py --headless

# 傳統 Python 執行（如果環境已啟動）
python takkyubin_selenium_scraper.py
```

### 執行舊版 WEDI 工具（參考用）
```bash
# 使用舊版腳本
./run.sh download

# 直接執行
uv run wedi_selenium_scraper.py --start-date 20241201 --end-date 20241208
```

### 設定檔案

- **pyproject.toml**: 現代 Python 專案設定，包含依賴和 uv 設定
- **accounts.json**: 包含帳號憑證和設定
  - `enabled: true/false` 控制要處理哪些帳號
  - `settings.headless` 和 `settings.download_base_dir` 為全域設定

- **.env**: Chrome 執行檔路徑設定（從 `.env.example` 建立）
  ```
  CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  ```

## 輸出結構

- **downloads/**: 按帳號下載的 Excel 檔案（格式：`{username}_{payment_no}.xlsx`）
- **reports/**: 個別帳號執行報告（目前版本已停用）
- **logs/**: 執行日誌和除錯資訊
- **temp/**: 暫存處理檔案

## 重要實作說明

### iframe 管理
工具在整個過程中維持 iframe 上下文以避免 Chrome 崩潰：
- `navigate_to_payment_query()`: 進入 iframe 並保持
- `set_date_range()`: 在現有 iframe 上下文中工作
- `get_payment_records()`: 在 iframe 內搜尋
- `download_excel_for_record()`: 在 iframe 內下載

### 錯誤處理哲學
工具採用「繼續執行」方式，個別失敗不會停止整個流程：
- 日期設定失敗會記錄但不會中斷執行
- 找不到查詢按鈕時會跳過並顯示警告
- 個別帳號失敗不會影響其他帳號

### 多帳號處理
`MultiAccountManager` 依序處理帳號，並產生單一整合報告而非每個帳號的個別報告，以減少輸出雜亂。