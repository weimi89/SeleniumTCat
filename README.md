# 黑貓宅急便自動化工具套件 🐱

一個使用 Python + Selenium 建立的現代化自動化工具套件，專門用於自動登入黑貓宅急便（統一速達）系統並下載各種資料。支援貨到付款匯款明細查詢、運費(對帳單明細)查詢，以及交易明細表下載。該工具採用現代化的模組化架構，使用抽象基礎類別設計，易於擴展新功能。

## 功能特色

✨ **自動登入**: 自動填入客代和密碼
🤖 **智能驗證碼識別**: 使用 ddddocr 自動識別驗證碼，大幅提升自動化成功率
💰 **貨到付款查詢**: 下載貨到付款匯款明細表 Excel 檔案
🚛 **運費查詢**: 下載對帳單明細 (運費相關) Excel 檔案
📊 **交易明細表**: 下載交易明細表，支援週期搜尋方式
👥 **多帳號支援**: 批次處理多個帳號，自動產生總結報告
📅 **彈性日期**: 支援不同的日期格式和週期設定
📝 **智能檔案命名**: 檔案自動命名為標準格式
🔄 **檔案覆蓋**: 重複執行會直接覆蓋同名檔案，保持目錄整潔
🏗️ **模組化架構**: 使用現代化 src/ 目錄結構和抽象基礎類別
🌐 **跨平台相容**: 支援 macOS、Windows、Linux 系統
🖥️ **Windows 友善**: Unicode 字符自動轉換，完美支援中文 Windows 環境

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
├── scripts/                      # 共用腳本和 PowerShell 模組
│   ├── common_checks.ps1         # PowerShell 共用檢查函數
│   ├── common_checks.sh          # Shell 共用檢查函數
│   ├── common_checks.cmd         # CMD 共用檢查函數
│   ├── run_payment.ps1           # PowerShell 客樂得對帳單執行腳本
│   ├── run_freight.ps1           # PowerShell 運費查詢執行腳本
│   ├── run_unpaid.ps1            # PowerShell 交易明細表執行腳本
│   ├── install.ps1               # PowerShell 自動安裝腳本
│   └── update.ps1                # PowerShell 自動更新腳本
├── Linux_客樂得對帳單.sh          # Linux 客樂得對帳單執行腳本
├── Linux_發票明細.sh             # Linux 運費查詢執行腳本
├── Linux_客戶交易明細.sh          # Linux 交易明細表執行腳本
├── Linux_安裝.sh                # Linux 自動安裝腳本
├── Linux_更新.sh                # Linux 自動更新腳本
├── Windows_客樂得對帳單.cmd       # Windows 客樂得對帳單執行腳本
├── Windows_發票明細.cmd          # Windows 運費查詢執行腳本
├── Windows_客戶交易明細.cmd       # Windows 交易明細表執行腳本
├── Windows_安裝.cmd             # Windows 自動安裝腳本
├── Windows_更新.cmd             # Windows 自動更新腳本
├── accounts.json                 # 帳號設定檔
├── accounts.json.example         # 帳號設定檔範例
├── pyproject.toml               # Python 專案設定
└── uv.lock                      # 鎖定依賴版本
```

## 自動更新 🔄

保持工具為最新版本，享受最新功能和錯誤修復：

### 一鍵更新 ⚡

**Linux/macOS**：
```bash
./Linux_更新.sh
```

**Windows**：
```cmd
# 雙擊執行或在命令提示字元中執行（自動啟動 PowerShell 7）
Windows_更新.cmd

```

### 更新功能特色

✅ **智能檢查** - 自動檢查是否有新版本可用
💾 **安全更新** - 自動暫存未提交的變更，避免資料遺失
📦 **依賴同步** - 檢測到 pyproject.toml 變更時自動更新套件
🔄 **變更還原** - 更新完成後自動還原之前的變更
🛡️ **衝突處理** - 遇到合併衝突時提供清楚的處理指引
🌐 **網路檢查** - 更新前驗證網路連線和 Git 權限

> **小提示**: 定期執行更新以獲得最佳體驗和最新功能！

## 快速開始 🚀

### Windows 建議安裝 (推薦) 💻

為了獲得最佳體驗，建議 Windows 使用者先安裝以下工具：

#### 安裝 Windows Terminal
1. **開啟 Microsoft Store**
   - 在開始選單搜尋「Microsoft Store」
   - 搜尋 `Windows Terminal`
   - 或直接點這裡：[Windows Terminal 下載](https://aka.ms/terminal)
2. **點「取得」** → 安裝完成後打開

#### 安裝 Git
Git 是版本控制工具，用於專案下載和更新功能。

**方法一：使用 winget 安裝（推薦）**
```cmd
winget install --id Git.Git --source winget
```

**方法二：手動下載安裝**
- 前往 [Git 官方網站](https://git-scm.com/download/win) 下載安裝程式
- 執行安裝程式，使用預設設定即可

#### 安裝 PowerShell 7
PowerShell 7 的彩色支援比舊版 PowerShell / CMD 完整許多，而且相容性很好。

在 PowerShell (舊版) 或 CMD 輸入：
```cmd
winget install --id Microsoft.Powershell --source winget
```

安裝完成後，在 Windows Terminal 裡會自動多一個 Profile 叫「PowerShell 7」。

#### 🎨 設定 Windows Terminal 預設 Profile
1. 打開 Windows Terminal
2. 按 `Ctrl + ,` 開啟設定
3. 在「啟動」→「預設設定檔」改成 **PowerShell 7**（或你想要的 Git Bash / WSL）
4. 按下儲存，之後每次開 Terminal 都用新的 Shell

> **提示**：完成這些設定後，使用我們的 `.cmd` 執行腳本會自動啟動最佳的執行環境！

### 方法一：一鍵自動安裝 (推薦) ⚡

**macOS/Linux**：
```bash
# 下載並執行自動安裝
chmod +x Linux_安裝.sh && ./Linux_安裝.sh
```

**Windows**：
```cmd
# 雙擊執行或在命令提示字元中執行（自動啟動 PowerShell 7）
Windows_安裝.cmd

```

安裝腳本會自動：
- ✅ 檢測並安裝 Python
- ✅ 安裝 uv 套件管理工具
- ✅ 自動偵測 Chrome 路徑
- ✅ 建立虛擬環境並安裝依賴

### 方法二：手動安裝

#### 1. 安裝 Python 和 uv
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. 建立環境並安裝依賴
```bash
# 自動建立虛擬環境並安裝依賴
uv sync
```

#### 3. 環境設定
```bash
# 複製環境設定範例檔案
cp .env.example .env

# 編輯 .env 檔案，設定你的 Chrome 瀏覽器路徑
# macOS 範例: CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Windows 範例: CHROME_BINARY_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
# Linux 範例: CHROME_BINARY_PATH="/usr/bin/google-chrome"
```

## 使用方式

### 貨到付款查詢

**推薦使用方式 (跨平台腳本)**：
```bash
# macOS/Linux
./Linux_客樂得對帳單.sh

# Windows（自動啟動 PowerShell 7）
Windows_客樂得對帳單.cmd


# 指定下載期數
./Linux_客樂得對帳單.sh --period 3      # Linux/macOS
Windows_客樂得對帳單.cmd --period 3       # Windows

# 無頭模式
./Linux_客樂得對帳單.sh --headless      # Linux/macOS
Windows_客樂得對帳單.cmd --headless       # Windows
```

**手動執行**：
```bash
# macOS/Linux
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/payment_scraper.py

# Windows (命令提示字元)
set PYTHONPATH=%cd%
set PYTHONUNBUFFERED=1
uv run python -u src\scrapers\payment_scraper.py
```

### 運費查詢

**推薦使用方式 (跨平台腳本)**：
```bash
# macOS/Linux
./Linux_發票明細.sh

# Windows（自動啟動 PowerShell 7）
Windows_發票明細.cmd

# 指定日期範圍
./Linux_發票明細.sh --start-date 20241201 --end-date 20241208   # Linux/macOS
Windows_發票明細.cmd --start-date 20241201 --end-date 20241208    # Windows

# 無頭模式
./Linux_發票明細.sh --headless      # Linux/macOS
Windows_發票明細.cmd --headless       # Windows
```

**手動執行**：
```bash
# macOS/Linux
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/freight_scraper.py

# Windows (命令提示字元)
set PYTHONPATH=%cd%
set PYTHONUNBUFFERED=1
uv run python -u src\scrapers\freight_scraper.py
```

### 交易明細表查詢

**推薦使用方式 (跨平台腳本)**：
```bash
# macOS/Linux
./Linux_客戶交易明細.sh

# Windows（自動啟動 PowerShell 7）
Windows_客戶交易明細.cmd


# 指定週期數量
./Linux_客戶交易明細.sh --periods 3      # Linux/macOS
Windows_客戶交易明細.cmd --periods 3       # Windows

# 無頭模式
./Linux_客戶交易明細.sh --headless       # Linux/macOS
Windows_客戶交易明細.cmd --headless        # Windows
```

**手動執行**：
```bash
# macOS/Linux
PYTHONPATH="$(pwd)" uv run python -u src/scrapers/unpaid_scraper.py

# Windows (命令提示字元)
set PYTHONPATH=%cd%
set PYTHONUNBUFFERED=1
uv run python -u src\scrapers\unpaid_scraper.py
```

## 自動執行流程

### 貨到付款查詢流程：
1. 🔐 **自動登入** - 讀取 `accounts.json` 中的帳號資訊
2. 🤖 **驗證碼識別** - 使用 ddddocr 自動識別並填入驗證碼
3. 🧭 **智能導航** - 導航到貨到付款匯款明細表頁面
4. 📅 **期數選擇** - 自動選擇指定期數或最新一期結算區間
5. 🔍 **執行查詢** - 點擊搜尋按鈕並等待 AJAX 載入完成
6. 📥 **自動下載** - 點擊下載按鈕下載 Excel 檔案
7. 📝 **智能重命名** - 檔案重命名為 `客樂得對帳單_{帳號}_{結算期間}.xlsx` 格式
8. 👥 **多帳號處理** - 依序處理所有啟用的帳號
9. 📋 **生成報告** - 產生詳細的執行報告

### 運費查詢流程：
1. 🔐 **自動登入** - 讀取帳號設定檔
2. 🤖 **驗證碼識別** - 自動識別驗證碼
3. 🧭 **智能導航** - 導航到對帳單明細頁面
4. 📅 **日期設定** - 設定發票日期區間（YYYYMMDD 格式）
5. 🔍 **AJAX 搜尋** - 執行搜尋並等待結果載入
6. 📥 **自動下載** - 下載明細檔案
7. 📝 **智能重命名** - 檔案重命名為 `發票明細_{帳號}_{發票日期}_{發票號碼}.xlsx` 格式
8. 👥 **批次處理** - 處理所有啟用的帳號
9. 📋 **總結報告** - 產生執行統計和結果報告

### 交易明細表查詢流程：
1. 🔐 **自動登入** - 讀取帳號設定檔
2. 🤖 **驗證碼識別** - 自動識別驗證碼
3. 🧭 **智能導航** - 導航到交易明細表頁面
4. 📅 **週期計算** - 自動計算各週期的日期範圍（預設 2 期，每期 7 天）
5. 🔍 **AJAX 搜尋** - 針對每個週期執行搜尋請求
6. 📥 **批次下載** - 下載各週期的明細檔案
7. 📝 **智能重命名** - 檔案重命名為 `交易明細表_{帳號}_{開始日期}-{結束日期}.xlsx` 格式
8. 👥 **批次處理** - 處理所有啟用的帳號
9. 📋 **總結報告** - 產生執行統計和結果報告

## 檔案命名格式

下載的檔案會自動重命名為：

### 貨到付款匯款明細
- **格式**: `客樂得對帳單_{帳號}_{結算期間}.xlsx`
- **範例**: `客樂得對帳單_0000000063_202409-1.xlsx`

### 運費對帳單明細
- **格式**: `發票明細_{帳號}_{發票日期}_{發票號碼}.xlsx`
- **範例**: `發票明細_0000000063_20240904_AB12345678.xlsx`

### 交易明細表
- **格式**: `交易明細表_{帳號}_{開始日期}-{結束日期}.xlsx`
- **範例**: `交易明細表_0000000063_20240901-20240907.xlsx`

> **覆蓋策略**: 重複執行會直接覆蓋同名檔案，保持目錄整潔

## 輸出結構

```
downloads/              # 下載的 Excel 檔案
├── 客樂得對帳單_0000000063_202409-1.xlsx         # 貨到付款明細
├── 發票明細_0000000063_20240904_AB12345678.xlsx   # 運費對帳單明細
├── 交易明細表_0000000063_20240901-20240907.xlsx     # 交易明細表
└── ...

reports/               # 執行報告
├── takkyubin_report_20240912_132926.json
└── ...

logs/                 # 執行日誌
temp/                 # 暫存檔案
```

## 設定檔案

### accounts.json
設定要處理的帳號清單（⚠️ 此檔案不會被 Git 追蹤）：

> **安全提醒**：請參考 `accounts.json.example` 建立此檔案，切勿將真實密碼提交到版本控制系統。

```json
{
  "accounts": [
    {"username": "0000000063", "password": "your_password", "enabled": true},
    {"username": "0000000013", "password": "your_password", "enabled": false}
  ],
  "settings": {
    "headless": false,
    "download_base_dir": "downloads"
  }
}
```

**重要設定說明**：
- `enabled: true/false` - 控制要處理哪些帳號
- `headless: true/false` - 是否使用背景模式（無法手動輸入驗證碼）
- 已加入 `.gitignore`，不會意外提交敏感資訊

### .env
設定 Chrome 瀏覽器路徑：
```bash
# macOS
CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Windows
CHROME_BINARY_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"

# Linux
CHROME_BINARY_PATH="/usr/bin/google-chrome"
```

## 現代化特色

### 🏗️ 模組化架構
- 採用 `src/` 目錄結構，符合現代 Python 專案標準
- 根目錄保持整潔，不包含 Python 檔案
- 清晰的模組分離：core（核心）、scrapers（實作）、utils（工具）

### 📦 現代依賴管理
- 使用 `pyproject.toml` + `uv.lock` 管理依賴
- 快速且可重現的環境安裝
- 自動版本鎖定，避免依賴衝突

### 🖥️ Windows 完美相容
- 實作 `safe_print()` 函數處理 Unicode 字符顯示
- 所有 Unicode 字符（如 ✅ ❌ 🎉）自動轉換為純文字標籤
- 在 Windows 命令提示字元中完美顯示中文和符號

### 🚀 優化執行體驗
- 提供跨平台執行腳本（.sh、.cmd、.ps1）
- Windows 自動啟動 PowerShell 7，享受完整 UTF-8 支援和彩色輸出
- 使用共用檢查函數確保環境一致性
- 自動設定必要的環境變數
- 簡化使用者執行流程

### ⚡ 智慧等待優化 (2025-10)
- **動態等待機制**: 將 31 處固定延遲 (`time.sleep()`) 替換為智慧等待
- **效能提升**: 平均處理速度提升 **45-62%** (目標: 40-60%) ✅
  - BaseScraper 登入流程: 57-78% 提升
  - PaymentScraper (客樂得對帳單): 44% 提升 (27秒 → 15秒/期)
  - FreightScraper (運費查詢): 50-70% 提升
  - UnpaidScraper (交易明細表): 28-57% 提升
- **智慧等待方法**:
  - `smart_wait_for_element()`: 等待特定元素出現
  - `smart_wait_for_url_change()`: 等待 URL 跳轉完成
  - `smart_wait()` + document.readyState: 確保頁面完全載入
- **保留速率限制**: 多帳號處理保持 3 秒間隔，避免伺服器限制
- **實測成果**: 17 個帳號處理從 15.3 分鐘降至 7-8 分鐘 (47-52% 節省)

> 詳細效能報告: `openspec/changes/refactor-smart-wait-adoption/performance-report.md`

## 技術特色

### 智能驗證碼識別
- 使用 ddddocr 函式庫自動識別驗證碼
- 無需手動輸入，大幅提升自動化程度
- 識別失敗時會自動等待手動輸入

### 智能導航系統
- 使用 RedirectFunc.aspx?FuncNo 精準導航
- 自動處理黑貓宅急便系統的複雜結構
- 避免權限錯誤和頁面跳轉問題

### AJAX 處理機制
- 智能等待 AJAX 載入完成
- 動態檢測下載按鈕出現
- 確保操作在正確的時機執行
- 支援多種元素定位策略

### 週期和期數管理
- **貨到付款**: 支援 `--period` 參數指定下載期數
- **交易明細表**: 支援 `--periods` 參數指定週期數量
- **運費查詢**: 支援日期範圍查詢

## 故障排除

### 🔧 常見問題

**Q: Chrome 瀏覽器啟動失敗**
A: 檢查 `.env` 檔案中的 `CHROME_BINARY_PATH` 是否正確

**Q: Windows 顯示「DLL load failed」或 ddddocr 錯誤**
A: 1) 安裝 Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
   2) 重新執行 `setup.cmd`（已內建修復機制）

**Q: Windows 顯示亂碼或符號異常**
A: 程式已內建 Unicode 相容處理，會自動轉換為純文字顯示

**Q: 執行時顯示「模組找不到」**
A: 確認是否使用了正確的執行腳本，會自動設定 PYTHONPATH

**Q: ddddocr 驗證碼識別失敗**
A: 程式會自動等待手動輸入，或檢查 ddddocr 套件是否正確安裝

**Q: 導航到查詢頁面失敗**
A: 檢查帳號是否有相應功能的存取權限

**Q: 找不到下載按鈕**
A: 確認該查詢條件是否有資料，或稍後再試

**Q: 只想處理特定帳號**
A: 在 `accounts.json` 中將不需要的帳號設為 `"enabled": false`

**Q: 想要背景執行但無法輸入驗證碼**
A: 背景模式無法手動輸入驗證碼，建議先確認自動識別功能正常

**Q: 多帳號執行時中斷**
A: 程式採用容錯設計，個別帳號失敗不會影響其他帳號處理

### 🔍 調試工具

如遇到驗證碼識別問題，可使用內建調試工具：
```bash
# macOS/Linux
PYTHONPATH="$(pwd)" python -u src/utils/debug_captcha.py

# Windows
set PYTHONPATH=%cd%
python -u src\utils\debug_captcha.py
```

## 依賴套件

- `selenium` - 網頁自動化框架
- `ddddocr` - 驗證碼識別
- `webdriver-manager` - Chrome WebDriver 自動管理
- `python-dotenv` - 環境變數管理
- `beautifulsoup4` - HTML 解析工具
- `openpyxl` - Excel 檔案處理
- `requests` - HTTP 請求處理

## 注意事項

⚠️ **使用須知**:
- 請確保有權限存取黑貓宅急便系統
- 確認帳號有相應資料的查詢權限
- 遵守網站的使用條款和服務協議
- 適度使用，避免對伺服器造成過大負載
- 定期檢查腳本是否因網站更新而需要調整

🔒 **安全提醒**:
- `accounts.json` 已加入 `.gitignore`，不會被版本控制追蹤
- 請定期更改密碼，確保帳號安全
- 切勿在公開場所或文件中暴露真實密碼
- 建議使用強密碼並啟用雙因素認證（如果支援）
- 如發現密碼洩露，請立即更改所有相關帳號密碼

📝 **法律聲明**: 此工具僅供學習和合法用途使用，使用者需自行承擔使用責任。