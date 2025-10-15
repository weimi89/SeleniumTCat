# Project Context

## Purpose

SeleniumTCat 是一個專為黑貓宅急便（統一速達）設計的現代化自動化工具套件。專案目標是：

- **自動化數據下載**: 自動登入黑貓宅急便系統並下載各種業務資料
- **提升工作效率**: 減少手動操作，支援批次處理多個帳號
- **數據標準化**: 統一檔案命名和組織方式，便於後續處理
- **跨平台相容**: 支援 Windows、macOS、Linux 多平台使用

主要功能包括：
- 貨到付款匯款明細查詢（客樂得對帳單）
- 運費查詢（發票明細）  
- 交易明細表下載
- 智能驗證碼識別
- 多帳號批次處理

## Tech Stack

### 核心技術
- **Python >= 3.9**: 主要開發語言
- **Selenium >= 4.15.0**: Web 自動化框架
- **ddddocr == 1.4.7**: 驗證碼自動識別 
- **webdriver-manager >= 4.0.1**: Chrome WebDriver 自動管理
- **uv**: 現代 Python 套件管理器

### 數據處理
- **openpyxl >= 3.1.2**: Excel 檔案處理
- **requests >= 2.31.0**: HTTP 請求處理
- **beautifulsoup4 >= 4.12.2**: HTML 解析

### 系統整合
- **python-dotenv >= 1.0.0**: 環境變數管理
- **onnxruntime >= 1.16.0**: ddddocr 運行時依賴
- **pillow < 10.0.0**: 圖像處理（驗證碼）
- **numpy >= 1.26.0, < 2.0.0**: 數值計算

## Project Conventions

### Code Style
- **語言**: 使用繁體中文註解和文檔
- **編碼**: UTF-8 編碼，支援跨平台中文顯示
- **命名規則**: 
  - 類別名稱: PascalCase (例：PaymentScraper)
  - 函數和變數: snake_case (例：get_payment_data)
  - 檔案名稱: snake_case (例：payment_scraper.py)
  - 常數: UPPER_CASE (例：DEFAULT_TIMEOUT)

### Architecture Patterns
- **抽象基礎類別**: BaseScraper 提供所有爬蟲的共用功能
- **依賴注入**: MultiAccountManager 支援不同 scraper 類別的注入
- **工廠模式**: browser_utils.py 統一處理瀏覽器初始化
- **策略模式**: 不同 scraper 實現各自的抓取策略
- **模組化設計**: 清晰的 src/ 目錄結構分離核心、實作和工具

### Testing Strategy
- **測試位置**: 所有測試檔案必須放在 `tests/` 目錄
- **不在根目錄**: 絕對禁止在專案根目錄創建測試檔案
- **測試類型**: 
  - 單元測試：核心模組功能測試
  - 整合測試：多帳號管理器測試
  - 端到端測試：完整流程驗證

### Git Workflow
- **主分支**: `main` 為主要開發分支
- **功能分支**: 使用 `feature/功能名稱` 命名
- **提交規範**: 使用繁體中文描述，格式：`類型: 簡短描述`
  - 例：`功能: 新增交易明細表查詢`
  - 例：`修復: 解決驗證碼識別失敗問題`
  - 例：`重構: 優化基礎爬蟲架構`

## Domain Context

### 黑貓宅急便系統特性
- **契約客戶專區**: 專為企業客戶設計的 B2B 系統
- **驗證碼機制**: 登入頁面包含圖形驗證碼，需要 OCR 識別
- **多種查詢功能**: 
  - 客樂得對帳單：貨到付款相關
  - 發票明細：運費和對帳單
  - 交易明細表：週期性交易記錄
- **結算週期**: 系統有固定的結算期間概念
- **AJAX 介面**: 部分查詢功能使用 AJAX 非同步載入

### 業務邏輯
- **客代系統**: 每個企業客戶有唯一的客戶代號
- **多帳號需求**: 企業通常需要管理多個子帳號
- **檔案命名**: 依據帳號、日期、類型自動命名
- **日期範圍**: 支援不同的日期格式和查詢週期

## Important Constraints

### 技術限制
- **Chrome 依賴**: 必須安裝 Google Chrome 瀏覽器
- **網路連線**: 需要穩定的網際網路連線
- **系統權限**: 需要檔案寫入權限創建下載目錄
- **Python 版本**: 最低支援 Python 3.9

### 平台特殊性
- **Windows 編碼**: 特別處理 Windows 命令提示字元的 Unicode 顯示
- **路徑分隔符**: 跨平台路徑處理使用 pathlib
- **執行腳本**: 提供 .sh、.cmd、.ps1 多種格式

### 安全考量
- **憑證保護**: accounts.json 不納入版本控制
- **自動登出**: 操作完成後自動關閉瀏覽器
- **錯誤處理**: 登入失敗自動重試機制

### 業務限制
- **存取權限**: 僅限有效的契約客戶帳號
- **查詢頻率**: 避免過於頻繁的查詢請求
- **資料範圍**: 只能查詢帳號權限內的資料

## External Dependencies

### 必要服務
- **黑貓宅急便官網**: `https://www.takkyubin.com.tw/`
- **契約客戶登入系統**: 企業客戶專用的 B2B 入口
- **Chrome WebDriver**: 自動下載和管理

### 第三方函式庫
- **ddddocr**: 用於驗證碼自動識別
- **Selenium**: Web 自動化核心引擎  
- **webdriver-manager**: 自動管理 ChromeDriver 版本

### 系統需求
- **Google Chrome**: 瀏覽器引擎
- **chromedriver**: 由 webdriver-manager 自動管理
- **uv**: Python 套件管理器

### 檔案系統
- **下載目錄**: downloads/ 用於存放 Excel 檔案
- **日誌目錄**: logs/ 用於存放執行記錄  
- **設定檔案**: accounts.json, .env 環境設定
- **暫存目錄**: temp/ 用於處理過程檔案
