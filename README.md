# 黑貓宅急便自動下載工具 🐱

一個使用 Python + Selenium + ddddocr 建立的自動化工具，專門用於自動登入黑貓宅急便系統並下載貨到付款匯款明細表。

## 功能特色

✨ **自動登入**: 自動填入帳號和密碼
🤖 **自動驗證碼識別**: 使用 ddddocr 自動識別驗證碼
📥 **精準下載**: 專門下載貨到付款匯款明細表 Excel 檔案
👥 **多帳號支援**: 批次處理多個帳號，自動產生總結報告
📅 **智能日期選擇**: 自動選擇最新的結算期間
📝 **智能檔案命名**: 檔案自動命名為 `帳號_結算期間.xlsx` 格式
🔄 **檔案覆蓋**: 重複執行會直接覆蓋同名檔案，保持目錄整潔
🌐 **跨平台**: 支援 macOS、Windows、Linux 系統

## 快速開始 🚀

### Windows 新手用戶 🪟

**完全沒有程式經驗？請先安裝基礎環境：**

1. **安裝 Python**
   - 前往：https://www.python.org/downloads/
   - 點擊黃色 "Download Python" 按鈕
   - **重要**：安裝時勾選 "Add Python to PATH"

2. **安裝 Chrome**
   - 前往：https://www.google.com/chrome/
   - 下載並安裝

3. **執行安裝**
   - 雙擊專案中的 `setup.cmd`
   - 等待安裝完成

### 方法一：一鍵自動安裝 (推薦) ⚡

**macOS/Linux**：
```bash
# 下載並執行自動安裝
chmod +x setup.sh && ./setup.sh
```

**Windows**：
```cmd
# 雙擊執行
setup.cmd
```

安裝腳本會自動：
- ✅ 檢測並安裝 Python
- ✅ 安裝 uv 套件管理工具
- ✅ 自動偵測 Chrome 路徑
- ✅ 建立虛擬環境並安裝依賴

### 方法二：手動安裝

如果您偏好手動控制安裝過程：

#### 1. 安裝 Python
- **Windows**: 從 [python.org](https://www.python.org/downloads/) 下載安裝
- **macOS**: `brew install python3` 或從官網下載
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

#### 2. 安裝 uv (Python 套件管理工具)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 3. 建立環境並安裝依賴
```bash
# 自動建立虛擬環境並安裝依賴
uv sync

# 或手動建立
uv venv
uv pip install -r requirements.txt
```

#### 4. 環境設定
```bash
# 複製環境設定範例檔案
cp .env.example .env

# 編輯 .env 檔案，設定你的 Chrome 瀏覽器路徑
# macOS 範例: CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Windows 範例: CHROME_BINARY_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### 5. 快速執行

**macOS/Linux 系統**：
```bash
# 使用 shell script (推薦)
./run.sh

# 或直接使用 uv 執行
uv run python payment_scraper.py
```

**Windows 系統**：
```cmd
# 使用批次檔 (推薦)
run.cmd

# 或直接使用虛擬環境執行
.venv\Scripts\python.exe payment_scraper.py
```

## 使用方式

### 基本使用

**macOS/Linux**：
```bash
# 使用預設設定（自動選擇最新結算期間）
./run.sh

# 無頭模式（背景執行）
./run.sh --headless

# 或直接使用 uv
uv run python payment_scraper.py --headless
```

**Windows**：
```cmd
# 使用預設設定（自動選擇最新結算期間）
run.cmd

# 無頭模式（背景執行）
.venv\Scripts\python.exe payment_scraper.py --headless

# 或直接執行
python payment_scraper.py --headless
```

### 自動執行流程

程式會自動執行以下步驟：

1. 🔐 **自動登入系統** - 讀取 `accounts.json` 中的帳號資訊
2. 🤖 **自動驗證碼識別** - 使用 ddddocr 自動識別並填入驗證碼
3. 🧭 **智能導航** - 使用 RedirectFunc.aspx?FuncNo=165 導航到貨到付款匯款明細表
4. 📅 **智能日期選擇** - 自動選擇第一個（最新）結算期間
5. 🔍 **執行查詢** - 點擊搜尋按鈕並等待 AJAX 載入完成
6. 📥 **自動下載** - 點擊「對帳單下載」按鈕下載 Excel 檔案
7. 📝 **智能重命名** - 檔案重命名為 `帳號_YYYYMMDD-YYYYMMDD.xlsx` 格式
8. 👥 **多帳號處理** - 依序處理所有啟用的帳號
9. 📋 **生成報告** - 產生 JSON 格式的總結報告

## 檔案命名格式

下載的檔案會自動重命名為：
- **格式**: `帳號_YYYYMMDD-YYYYMMDD.xlsx`
- **範例**: `0000000063_20250904-20250907.xlsx`
- **覆蓋**: 重複執行會直接覆蓋同名檔案

## 輸出結構

```
downloads/              # 下載的 Excel 檔案
├── 0000000063_20250904-20250907.xlsx
├── 0000000013_20250904-20250907.xlsx
└── ...

reports/               # 執行報告
├── takkyubin_report_20250912_132926.json
└── ...
```

## 設定檔案

### accounts.json
設定要處理的帳號清單：
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

## 技術特色

### ddddocr 驗證碼識別
- 使用先進的 OCR 技術自動識別驗證碼
- 無需手動輸入，大幅提升自動化程度
- 識別失敗時會自動等待手動輸入

### 智能導航系統
- 使用 RedirectFunc.aspx?FuncNo=165 精準導航
- 自動處理 ASP.NET 框架結構
- 避免權限錯誤和頁面跳轉問題

### AJAX 處理
- 智能等待 AJAX 載入完成
- 動態檢測下載按鈕出現
- 確保操作在正確的時機執行

## 故障排除

### 🔧 常見問題

**Q: Chrome 瀏覽器啟動失敗**
A: 檢查 `.env` 檔案中的 `CHROME_BINARY_PATH` 是否正確

**Q: Windows 顯示「DLL load failed」或 ddddocr 錯誤**
A: 1) 安裝 Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
   2) 重新執行 `setup.cmd`（已內建修復機制）

**Q: Windows 顯示「No module named 'dotenv'」**
A: 虛擬環境未正確安裝，重新執行 `setup.cmd`

**Q: ddddocr 驗證碼識別失敗**
A: 程式會自動等待手動輸入，或檢查 ddddocr 套件是否正確安裝

**Q: 導航到貨到付款頁面失敗**
A: 檢查帳號是否有貨到付款匯款明細表的存取權限

**Q: 找不到下載按鈕**
A: 確認該結算期間是否有資料，或稍後再試

**Q: 只想處理特定帳號**
A: 在 `accounts.json` 中將不需要的帳號設為 `"enabled": false`

**Q: 想要背景執行**
A: 使用 `--headless` 參數或在 `accounts.json` 中設定 `"headless": true`

## 依賴套件

- `selenium` - 網頁自動化
- `ddddocr` - 驗證碼識別
- `webdriver-manager` - Chrome WebDriver 管理
- `python-dotenv` - 環境變數管理

## 注意事項

⚠️ **使用須知**:
- 請確保有權限存取黑貓宅急便系統
- 確認帳號有貨到付款匯款明細表的查詢權限
- 遵守網站的使用條款
- 適度使用，避免對伺服器造成過大負載
- 定期檢查腳本是否因網站更新而需要調整

📝 **法律聲明**: 此工具僅供學習和合法用途使用