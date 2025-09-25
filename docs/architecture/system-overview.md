# SeleniumTCat 系統總覽

## 專案概述

SeleniumTCat 是一個專為黑貓宅急便（統一速達）設計的自動化工具套件，使用 Selenium WebDriver 技術自動從黑貓宅急便網頁系統下載各種商務資料。本工具套件支援多種資料類型的自動化下載，包括貨到付款匯款明細、運費對帳單明細，以及交易明細表。

### 專案背景

原本針對 WEDI（宅配通）系統開發，現已完全改版支援黑貓宅急便系統。專案採用現代化的模組化架構設計，使用抽象基礎類別模式，易於擴展新功能和維護既有功能。

### 核心價值

- **自動化效率**：減少手動下載的重複性工作，提升工作效率
- **多帳號支援**：支援批次處理多個帳號，適合企業環境使用
- **智慧驗證碼處理**：整合 ddddocr 自動識別驗證碼，減少人工介入
- **跨平台相容**：支援 Windows、macOS、Linux 三大作業系統
- **可擴展架構**：模組化設計，易於新增其他資料類型的抓取功能

## 整體架構

```mermaid
graph TB
    subgraph "使用者介面層"
        CLI[命令列介面]
        Scripts[執行腳本<br/>(.sh/.cmd/.ps1)]
    end

    subgraph "業務邏輯層"
        MAM[MultiAccountManager<br/>多帳號管理器]
        PS[PaymentScraper<br/>客樂得對帳單]
        FS[FreightScraper<br/>運費查詢]
        US[UnpaidScraper<br/>交易明細表]
    end

    subgraph "核心服務層"
        BS[BaseScraper<br/>基礎抓取器]
        BU[browser_utils<br/>瀏覽器工具]
        WEU[windows_encoding_utils<br/>編碼工具]
    end

    subgraph "外部依賴"
        Selenium[Selenium WebDriver]
        Chrome[Chrome Browser]
        ddddocr[ddddocr 驗證碼識別]
        UV[uv 套件管理]
    end

    subgraph "配置與資料"
        Config[accounts.json<br/>帳號配置]
        Env[.env<br/>環境變數]
        Downloads[downloads/<br/>下載檔案]
        Reports[reports/<br/>執行報告]
    end

    CLI --> MAM
    Scripts --> MAM
    MAM --> PS
    MAM --> FS
    MAM --> US

    PS --> BS
    FS --> BS
    US --> BS

    BS --> BU
    BS --> WEU

    BU --> Selenium
    BU --> Chrome
    BS --> ddddocr

    MAM --> Config
    BS --> Env
    MAM --> Downloads
    MAM --> Reports

    UV -.-> PS
    UV -.-> FS
    UV -.-> US
```

## 主要功能模組

### 1. 多帳號管理系統
- **MultiAccountManager**：統一管理多個黑貓宅急便帳號
- **批次處理**：自動循環處理所有啟用的帳號
- **進度追蹤**：提供執行進度回報和統計資訊
- **錯誤處理**：個別帳號失敗不影響其他帳號處理

### 2. 智慧爬蟲引擎
- **BaseScraper**：提供統一的登入、驗證碼處理、會話管理功能
- **ddddocr 整合**：自動識別驗證碼，大幅提升自動化成功率
- **會話恢復**：自動檢測並處理會話超時問題
- **檔案管理**：智慧化的臨時檔案管理和最終檔案整理

### 3. 專業資料抓取器

#### PaymentScraper - 客樂得對帳單查詢工具
- 自動下載貨到付款匯款明細（客樂得對帳單）
- 支援多期數下載，可配置期數參數
- 自動選擇最新結算區間，無需手動指定日期

#### FreightScraper - 運費查詢工具
- 下載對帳單明細（運費相關資料）
- 支援日期範圍查詢和 AJAX 搜尋處理
- 檔案命名包含發票日期和發票號碼

#### UnpaidScraper - 交易明細表工具
- 下載交易明細表資料
- 支援週期搜尋，預設處理 2 個週期
- 每週期涵蓋 7 天，檔案名包含完整日期範圍

## 技術棧說明

### 核心技術
- **Python 3.9+**：主要開發語言
- **Selenium WebDriver**：網頁自動化框架
- **Chrome WebDriver**：瀏覽器驅動程式

### 關鍵技術特色

#### 1. ddddocr 驗證碼識別
```python
# 自動驗證碼識別
self.ocr = ddddocr.DdddOcr(show_ad=False)
result = self.ocr.classification(screenshot)
```

#### 2. 跨平台 Chrome 支援
```python
# 支援 macOS、Windows、Linux
CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

#### 3. 現代 Python 套件管理
```toml
# pyproject.toml - 使用 uv 進行快速依賴管理
[tool.uv]
dev-dependencies = []
```

#### 4. 多平台執行腳本
- **Windows**: `.cmd` 檔案自動啟動 PowerShell
- **Linux/macOS**: `.sh` 檔案支援 Bash
- **PowerShell**: `.ps1` 檔案提供最佳體驗

## 專案特色

### 1. 契約客戶專區設計
專為黑貓宅急便契約客戶設計，自動選擇正確的登入模式，確保能夠存取企業級功能。

### 2. 智慧錯誤恢復機制
- **會話超時恢復**：自動檢測會話超時並重新登入
- **驗證碼重試**：驗證碼識別失敗時自動重試
- **個別錯誤隔離**：單一帳號失敗不影響其他帳號處理

### 3. 檔案管理最佳化
- **UUID 臨時目錄**：每次下載使用唯一臨時目錄
- **智慧檔案命名**：根據資料類型和時間範圍自動命名
- **自動清理機制**：下載完成後自動清理臨時檔案

### 4. Windows 編碼相容性
提供 `safe_print()` 函數，確保 Unicode 字符在 Windows 命令提示字元中正常顯示。

## 系統需求

### 環境需求
- Python 3.9 或更高版本
- Google Chrome 瀏覽器
- uv 套件管理工具

### 作業系統支援
- Windows 10/11
- macOS 10.15+
- Ubuntu 18.04+ / CentOS 7+

### 依賴套件
```toml
dependencies = [
    "selenium>=4.15.0",
    "webdriver-manager>=4.0.1",
    "ddddocr==1.4.7",
    "python-dotenv>=1.0.0",
    "requests>=2.31.0",
    # ... 其他依賴
]
```

## 安全性考量

### 1. 帳號資訊保護
- `accounts.json` 已加入 `.gitignore`，不會被版本控制追蹤
- 支援環境變數方式管理敏感資訊

### 2. 會話安全
- 自動處理密碼安全警告
- 支援會話超時自動重新認證

### 3. 下載檔案安全
- 檔案下載到指定目錄，避免路徑穿越攻擊
- 臨時檔案使用 UUID 命名，避免檔名衝突

---

本文件提供 SeleniumTCat 系統的整體架構概述。如需了解更多技術細節，請參閱其他架構文檔。