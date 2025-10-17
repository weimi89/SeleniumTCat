# SeleniumTCat 技術文檔索引

## 📚 文檔導航

### 部署與設定
- **[Ubuntu 部署指南](ubuntu-deployment-guide.md)** - Ubuntu 24.04 LTS 完整部署流程
- **[Browser Utils 優化方案](browser-utils-ubuntu-optimization.md)** - Ubuntu 環境瀏覽器優化說明

### 快速開始

#### Ubuntu 使用者
```bash
# 1. 一鍵部署
bash scripts/ubuntu_quick_setup.sh

# 2. 環境驗證
bash scripts/test_ubuntu_env.sh

# 3. 瀏覽器測試
PYTHONPATH=$(pwd) uv run python src/utils/test_browser.py

# 4. 執行爬蟲（無頭模式）
PYTHONPATH=$(pwd) uv run python -u src/scrapers/payment_scraper.py --headless --period 1
```

#### Windows/macOS 使用者
請參考專案根目錄的 [CLAUDE.md](../../CLAUDE.md)

### 常見問題

#### Q1: Ubuntu 環境記憶體使用過高？
A: 已實作 Ubuntu 專屬優化，無頭模式記憶體使用降低 37% (350MB → 220MB)

#### Q2: ChromeDriver 版本不匹配？
A: 使用 apt 安裝可確保版本配套：
```bash
sudo apt install -y chromium-browser chromium-chromedriver
```

#### Q3: ddddocr 無法識別驗證碼？
A: 執行測試腳本檢查：
```bash
PYTHONPATH=$(pwd) uv run python src/utils/test_browser.py
```

#### Q4: 權限不足 (Permission denied)？
A: 檢查檔案權限設定：
```bash
chmod 600 .env accounts.json
chmod 755 downloads logs temp
```

### 效能數據

| 指標 | 優化前 | 優化後 | 改善 |
|------|--------|--------|------|
| 無頭模式記憶體 | ~350MB | ~220MB | -37% |
| Ubuntu 啟動速度 | ~3.5s | ~2.8s | -20% |
| 批次處理效能 | 基準 | 改善 | ~30% |

### 支援平台

| 平台 | 支援程度 | 建議瀏覽器 |
|------|----------|-----------|
| Ubuntu 24.04 LTS | ✅ 完整支援 + 優化 | Chromium |
| Ubuntu 22.04 LTS | ✅ 支援 | Chromium |
| Other Linux | ⚠️ 未測試 | Chromium |
| Windows 10/11 | ✅ 支援 | Google Chrome |
| macOS | ✅ 支援 | Google Chrome |

### 相關連結

- 🏠 [專案首頁](../../README.md)
- 📋 [專案說明](../../CLAUDE.md)
- 🔧 [環境設定範例](../../.env.example)
- 📦 [套件依賴](../../pyproject.toml)

### 貢獻

發現文檔錯誤或需要改進？歡迎提交 Issue 或 Pull Request！

---

**最後更新**: 2025-01 (OpenSpec Change: add-ubuntu-deployment-support)
