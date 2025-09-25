# SeleniumTCat 開發環境設置指南

## 開發環境需求

### 系統需求
- **Python**: 3.9 或更高版本
- **作業系統**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **記憶體**: 建議 4GB 以上
- **硬碟空間**: 500MB 以上

### 必要軟體
- **Google Chrome**: 最新版本
- **Git**: 版本控制
- **uv**: Python 套件管理器
- **程式碼編輯器**: VSCode、PyCharm 或其他

## 快速開始

### 1. 取得專案程式碼

```bash
# 複製儲存庫
git clone <repository-url>
cd SeleniumTCat

# 或者如果已經下載
cd SeleniumTCat
```

### 2. 安裝 uv 套件管理器

#### Windows
```powershell
# 使用 PowerShell
irm https://astral.sh/uv/install.ps1 | iex
```

#### macOS/Linux
```bash
# 使用 curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# 重新載入 shell 或執行
source ~/.bashrc  # 或 ~/.zshrc
```

### 3. 建立開發環境

```bash
# 建立虛擬環境並安裝相依性
uv sync

# 檢查安裝狀態
uv run python --version
```

### 4. 配置環境變數

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，設定 Chrome 路徑
nano .env  # Linux/macOS
notepad .env  # Windows
```

#### 各平台 Chrome 路徑設定

**Windows:**
```bash
CHROME_BINARY_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

**macOS:**
```bash
CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

**Linux:**
```bash
CHROME_BINARY_PATH="/usr/bin/google-chrome"
```

### 5. 設定帳號配置

```bash
# 複製帳號配置範本
cp accounts.json.example accounts.json

# 編輯配置檔案
nano accounts.json  # Linux/macOS
notepad accounts.json  # Windows
```

```json
{
  "accounts": [
    {
      "username": "你的測試帳號",
      "password": "你的測試密碼",
      "enabled": true
    }
  ],
  "settings": {
    "headless": false,
    "download_base_dir": "downloads"
  }
}
```

### 6. 驗證安裝

```bash
# 執行測試腳本
uv run python -c "import selenium; print('Selenium 安裝成功')"
uv run python -c "import ddddocr; print('ddddocr 安裝成功')"

# 執行簡單測試
uv run python -u src/scrapers/payment_scraper.py --help
```

## 開發工具設定

### VSCode 設定

#### 1. 安裝建議擴展
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.pylint",
    "ms-toolsai.jupyter"
  ]
}
```

#### 2. VSCode 設定檔 (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".venv": true
  }
}
```

#### 3. 偵錯設定 (.vscode/launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "PaymentScraper Debug",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/scrapers/payment_scraper.py",
      "args": ["--period", "1"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "PYTHONUNBUFFERED": "1"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "FreightScraper Debug",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/scrapers/freight_scraper.py",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "PYTHONUNBUFFERED": "1"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm 設定

#### 1. 專案解釋器設定
1. 開啟 PyCharm
2. File → Settings → Project → Python Interpreter
3. 選擇 Existing environment
4. 指向 `.venv/bin/python` (Linux/macOS) 或 `.venv\Scripts\python.exe` (Windows)

#### 2. 執行配置
1. Run → Edit Configurations
2. 新增 Python 配置:
   - **Name**: PaymentScraper
   - **Script path**: `src/scrapers/payment_scraper.py`
   - **Parameters**: `--period 1`
   - **Environment variables**: `PYTHONUNBUFFERED=1;PYTHONPATH=.`

## 專案結構理解

```
SeleniumTCat/
├── src/                     # 原始碼目錄
│   ├── core/               # 核心模組
│   │   ├── base_scraper.py # 基礎爬蟲類別
│   │   ├── multi_account_manager.py # 多帳號管理
│   │   └── browser_utils.py # 瀏覽器工具
│   ├── scrapers/           # 業務爬蟲
│   │   ├── payment_scraper.py # 貨到付款爬蟲
│   │   ├── freight_scraper.py # 運費爬蟲
│   │   └── unpaid_scraper.py  # 交易明細爬蟲
│   └── utils/              # 工具模組
│       └── windows_encoding_utils.py # 編碼工具
├── scripts/                # 共用腳本
├── docs/                  # 文檔目錄
├── downloads/             # 下載檔案目錄
├── reports/              # 執行報告目錄
├── temp/                 # 臨時檔案目錄
├── logs/                 # 日誌目錄
├── accounts.json         # 帳號配置 (不納入版本控制)
├── .env                  # 環境變數 (不納入版本控制)
├── pyproject.toml       # 專案配置
└── uv.lock             # 依賴鎖定檔案
```

## 開發流程

### 1. 程式碼風格

#### Python 風格指南
- 使用 **Black** 進行程式碼格式化
- 使用 **isort** 整理 import
- 遵循 **PEP 8** 風格指南
- 使用 **Type Hints** (Python 3.9+)

```python
# 好的例子
def process_account(username: str, password: str, headless: bool = False) -> Dict[str, Any]:
    """處理單一帳號的範例函數

    Args:
        username: 使用者帳號
        password: 使用者密碼
        headless: 是否使用無頭模式

    Returns:
        包含處理結果的字典
    """
    result = {"success": False, "message": ""}
    # ... 實作邏輯
    return result
```

#### 註解和文檔字串
```python
class NewScraper(BaseScraper):
    """新的爬蟲類別

    繼承自 BaseScraper，實作特定的資料抓取功能。

    Attributes:
        special_param: 特殊參數說明
    """

    def __init__(self, username: str, password: str, **kwargs):
        """初始化新爬蟲

        Args:
            username: 使用者帳號
            password: 使用者密碼
            **kwargs: 其他參數
        """
        super().__init__(username, password, **kwargs)
        self.special_param = kwargs.get('special_param', None)
```

### 2. Git 工作流程

#### 分支策略
```bash
# 建立功能分支
git checkout -b feature/new-scraper

# 提交變更
git add .
git commit -m "feat: 新增 NewScraper 爬蟲實作"

# 推送到遠端
git push origin feature/new-scraper

# 建立 Pull Request
```

#### 提交訊息格式
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**類型 (type):**
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文檔更新
- `style`: 程式碼格式調整
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置工具、輔助工具變動

**範例:**
```
feat(scrapers): 新增 UnpaidScraper 交易明細抓取功能

- 實作週期搜尋邏輯
- 支援多期間下載
- 新增 AJAX 搜尋處理

Closes #123
```

### 3. 測試驅動開發

#### 測試檔案結構
```
tests/
├── unit/                  # 單元測試
│   ├── test_base_scraper.py
│   ├── test_multi_account_manager.py
│   └── test_browser_utils.py
├── integration/          # 整合測試
│   ├── test_payment_scraper.py
│   ├── test_freight_scraper.py
│   └── test_unpaid_scraper.py
└── fixtures/            # 測試夾具
    ├── sample_accounts.json
    └── mock_responses/
```

#### 測試範例
```python
# tests/unit/test_base_scraper.py
import pytest
from unittest.mock import Mock, patch
from src.core.base_scraper import BaseScraper


class TestBaseScraper:
    """BaseScraper 單元測試"""

    @pytest.fixture
    def scraper(self):
        """測試夾具：建立 BaseScraper 實例"""
        return BaseScraper("test_user", "test_pass")

    def test_init_browser(self, scraper):
        """測試瀏覽器初始化"""
        with patch('src.core.browser_utils.init_chrome_browser') as mock_init:
            mock_init.return_value = (Mock(), Mock())

            scraper.init_browser()

            assert scraper.driver is not None
            assert scraper.wait is not None
            mock_init.assert_called_once()

    def test_solve_captcha_success(self, scraper):
        """測試驗證碼識別成功"""
        with patch.object(scraper.ocr, 'classification') as mock_ocr:
            mock_ocr.return_value = "1234"
            mock_element = Mock()
            mock_element.screenshot_as_png = b"fake_image_data"

            result = scraper.solve_captcha(mock_element)

            assert result == "1234"
            mock_ocr.assert_called_once_with(b"fake_image_data")
```

## 除錯技巧

### 1. 日誌除錯

#### 啟用詳細日誌
```python
import logging

# 設定日誌等級
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 在程式碼中使用
logger = logging.getLogger(__name__)
logger.debug("除錯訊息")
logger.info("一般資訊")
logger.error("錯誤訊息")
```

#### Selenium 除錯
```python
# 啟用 Selenium 詳細日誌
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.DEBUG)
```

### 2. 瀏覽器除錯

#### 非無頭模式除錯
```python
# 在 accounts.json 中設定
{
  "settings": {
    "headless": false  # 可以看到瀏覽器操作
  }
}
```

#### 儲存頁面截圖
```python
def debug_screenshot(driver, filename="debug.png"):
    """儲存除錯截圖"""
    driver.save_screenshot(filename)
    print(f"除錯截圖已儲存: {filename}")
```

#### 頁面原始碼檢查
```python
def debug_page_source(driver, filename="debug.html"):
    """儲存頁面原始碼"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"頁面原始碼已儲存: {filename}")
```

### 3. 常見問題排除

#### Chrome 路徑問題
```bash
# 檢查 Chrome 是否存在
ls -la "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # macOS
ls -la "C:\Program Files\Google\Chrome\Application\chrome.exe"        # Windows
which google-chrome                                                   # Linux
```

#### 相依性問題
```bash
# 重新安裝相依性
rm -rf .venv
uv sync

# 檢查特定套件
uv run pip show selenium
uv run pip show ddddocr
```

#### 權限問題
```bash
# Linux/macOS 設定執行權限
chmod +x *.sh

# 檢查檔案權限
ls -la accounts.json
```

## 效能最佳化

### 1. 開發環境最佳化

```python
# 開發專用的快速設定
DEVELOPMENT_CONFIG = {
    "headless": False,          # 開發時建議看到瀏覽器
    "implicit_wait": 5,         # 縮短等待時間
    "page_load_timeout": 15,    # 縮短頁面載入超時
    "download_timeout": 30      # 設定下載超時
}
```

### 2. 程式碼分析工具

```bash
# 安裝分析工具
uv add --dev pytest-cov pytest-benchmark

# 執行程式碼覆蓋率測試
uv run pytest --cov=src tests/

# 效能基準測試
uv run pytest --benchmark-only tests/
```

---

遵循本設置指南，您將能夠快速建立一個完整的 SeleniumTCat 開發環境，並具備高效開發和除錯的能力。