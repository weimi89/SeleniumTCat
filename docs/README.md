# SeleniumTCat 專案文檔

這裡包含 SeleniumTCat 專案的完整技術文檔，涵蓋系統架構、開發指南和最佳實務。

## 🏗️ 架構文檔

深入了解 SeleniumTCat 的系統設計和技術架構。

### [系統總覽](architecture/system-overview.md)
- 專案概述和核心價值
- 整體架構圖解
- 主要功能模組介紹
- 技術棧說明
- 系統需求和安全考量

### [模組設計](architecture/module-design.md)
- 核心模組 (`src/core/`) 詳解
- 業務模組 (`src/scrapers/`) 設計
- 工具模組 (`src/utils/`) 功能
- 模組間依賴關係
- 設計模式應用

### [類別階層](architecture/class-hierarchy.md)
- BaseScraper 抽象基類設計
- 各 Scraper 子類別實作
- 繼承關係和多型應用
- SOLID 原則實踐
- 類別擴展指南

### [資料流程](architecture/data-flow.md)
- 配置載入和驗證流程
- 多帳號批次處理流程
- 登入和驗證碼處理
- 資料抓取和下載流程
- 錯誤處理和恢復機制

### [配置架構](architecture/configuration.md)
- accounts.json 主配置檔
- .env 環境變數配置
- pyproject.toml 專案配置
- 配置優先級系統
- 安全性配置

### [平台支援](architecture/platform-support.md)
- Windows、macOS、Linux 支援
- 跨平台瀏覽器適配
- 執行腳本系統設計
- 編碼處理機制
- 平台特定最佳化

## 🛠️ 開發指南

開發者必備的設置、擴展和最佳實務指南。

### [開發環境設置](development/setup-guide.md)
- 快速開始指南
- 開發工具設定 (VSCode, PyCharm)
- 專案結構理解
- 除錯技巧和故障排除
- 效能最佳化

### [擴展開發指南](development/extension-guide.md)
- 新增 Scraper 爬蟲
- 新增功能模組
- 新增平台支援
- 新增配置選項
- 測試和驗證

### [最佳實務](development/best-practices.md)
- 程式碼品質原則
- 錯誤處理策略
- 效能最佳化技巧
- 測試策略
- 安全性最佳實務

## 📚 快速參考

### 常用連結
- [專案 README](../README.md) - 使用者指南
- [CLAUDE.md](../CLAUDE.md) - Claude Code 專案指導
- [pyproject.toml](../pyproject.toml) - 專案配置
- [accounts.json.example](../accounts.json.example) - 配置範本

### 核心類別參考

#### BaseScraper - 基礎抓取器
```python
from src.core.base_scraper import BaseScraper

class MyCustomScraper(BaseScraper):
    def __init__(self, username, password, **kwargs):
        super().__init__(username, password, **kwargs)

    def navigate_to_query_page(self):
        # 實作導航邏輯
        pass

    def download_data(self):
        # 實作下載邏輯
        return []
```

#### MultiAccountManager - 多帳號管理器
```python
from src.core.multi_account_manager import MultiAccountManager
from src.scrapers.payment_scraper import PaymentScraper

manager = MultiAccountManager("accounts.json")
results = manager.run_all_accounts(
    PaymentScraper,
    headless_override=True,
    period_number=2
)
```

### 執行命令參考

#### 基本執行
```bash
# Windows
Windows_客樂得對帳單.cmd
Windows_發票明細.cmd
Windows_客戶交易明細.cmd

# Linux/macOS
./Linux_客樂得對帳單.sh
./Linux_發票明細.sh
./Linux_客戶交易明細.sh
```

#### 進階參數
```bash
# 指定期數
Windows_客樂得對帳單.cmd --period 3

# 指定日期範圍
Linux_發票明細.sh --start-date 20241201 --end-date 20241208

# 無頭模式
Windows_客戶交易明細.cmd --headless

# 指定週期數
Linux_客戶交易明細.sh --periods 3
```

## 🎯 關鍵概念

### 核心設計原則
- **模組化架構**：清晰的責任分離和介面定義
- **跨平台相容**：統一 API，多平台適配
- **可擴展性**：基於繼承的插件式架構
- **錯誤處理**：優雅降級和資源清理
- **安全性**：憑證保護和輸入驗證

### 主要組件
- **BaseScraper**：所有爬蟲的基礎類別
- **MultiAccountManager**：多帳號批次處理管理器
- **ddddocr 整合**：自動驗證碼識別
- **智慧等待**：動態頁面載入處理
- **檔案管理**：臨時檔案和最終檔案處理

### 支援的功能
- 🏪 **客樂得對帳單**：貨到付款匯款明細下載
- 🚚 **運費查詢**：對帳單明細（運費相關）下載
- 📊 **交易明細表**：客戶交易明細下載
- 👥 **多帳號支援**：批次處理多個帳號
- 🔄 **會話管理**：自動會話超時恢復
- 🖥️ **跨平台**：Windows、macOS、Linux 支援

## 🔧 故障排除

### 常見問題
1. **Chrome 瀏覽器路徑問題** → 檢查 [平台支援文檔](architecture/platform-support.md#瀏覽器路徑設定)
2. **驗證碼識別失敗** → 參考 [資料流程文檔](architecture/data-flow.md#驗證碼處理流程)
3. **配置檔案錯誤** → 查看 [配置架構文檔](architecture/configuration.md#配置驗證機制)
4. **會話超時問題** → 查閱 [資料流程文檔](architecture/data-flow.md#錯誤處理和恢復機制)

### 除錯模式
```bash
# 啟用詳細日誌
export PYTHONUNBUFFERED=1
uv run python -u src/scrapers/payment_scraper.py --verbose

# 非無頭模式（可觀察瀏覽器操作）
# 在 accounts.json 中設定 "headless": false
```

### 獲取幫助
- 查看相關架構文檔了解技術細節
- 參考開發指南進行擴展開發
- 遵循最佳實務確保程式碼品質

## 📝 貢獻指南

### 文檔貢獻
1. 遵循既有的 Markdown 格式
2. 使用 Mermaid 繪製圖表
3. 提供實用的程式碼範例
4. 保持繁體中文撰寫

### 程式碼貢獻
1. 遵循 [最佳實務](development/best-practices.md)
2. 參考 [擴展開發指南](development/extension-guide.md)
3. 編寫完整的測試用例
4. 更新相關文檔

---

## 📄 文檔版本

**版本**: 1.0.0
**最後更新**: 2024年12月
**維護者**: SeleniumTCat 開發團隊

這些文檔與專案程式碼同步維護，確保資訊的準確性和時效性。如有任何問題或建議，歡迎提出 issue 或提交 pull request。

---

*本文檔使用 [Claude Code](https://claude.ai/code) 輔助生成和維護。*