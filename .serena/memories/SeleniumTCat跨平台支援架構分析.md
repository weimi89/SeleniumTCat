# SeleniumTCat 跨平台支援架構分析

## 跨平台策略核心設計

### 1. 執行腳本系統
- **三種腳本格式**：.sh (Linux/macOS), .cmd (Windows CMD), .ps1 (PowerShell)
- **共用邏輯抽取**：scripts/common_checks.* 檔案實現邏輯復用
- **智慧啟動順序**：Windows Terminal > PowerShell 7 > 舊版 PowerShell

### 2. 環境變數統一管理
- **CHROME_BINARY_PATH**：跨平台 Chrome 路徑設定
- **CHROMEDRIVER_PATH**：ChromeDriver 路徑設定
- **PYTHONUNBUFFERED**：確保即時輸出

### 3. 編碼處理機制
- **windows_encoding_utils.py**：統一處理 Unicode 字符顯示問題
- **safe_print() 函數**：自動轉換 Unicode 符號為純文字
- **跨平台一致性**：確保所有平台都能正常顯示程式輸出

### 4. 檔案路徸管理
- **Path 物件**：使用 Python Path 類別處理跨平台路徑差異
- **環境變數驅動**：通過 .env 檔案管理平台特定設定

這個架構設計非常成熟，充分考慮了不同平台的差異和使用者體驗。