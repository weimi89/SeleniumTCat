# SeleniumTCat 開發最佳實務

## 程式碼品質原則

### 1. 程式碼風格標準

#### 1.1 Python 風格指南

**遵循 PEP 8**：
```python
# ✅ 好的命名慣例
class PaymentScraper(BaseScraper):
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def get_settlement_periods(self) -> List[Dict[str, str]]:
        """取得結算期間清單"""
        return self._fetch_periods_from_dropdown()

# ❌ 不好的命名慣例
class payment_scraper:
    def __init__(self, usr, pwd):
        self.usr = usr
        self.pwd = pwd

    def getPeriods(self):
        return self.fetchData()
```

**函數設計原則**：
```python
# ✅ 單一職責、清晰命名
def validate_account_credentials(username: str, password: str) -> bool:
    """驗證帳號憑證的有效性"""
    if not username or not password:
        return False

    return len(username) >= 3 and len(password) >= 6

def format_filename_for_download(account: str, period: str, date: str) -> str:
    """格式化下載檔案的名稱"""
    safe_account = re.sub(r'[^\w\-_]', '_', account)
    return f"客樂得對帳單_{safe_account}_{period}_{date}.xlsx"

# ❌ 職責不清、命名模糊
def check_stuff(data):
    # 混合了驗證、格式化、處理邏輯
    if not data:
        return None
    # ... 複雜的混合邏輯
```

#### 1.2 類型提示應用

```python
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path

class BaseScraper:
    def __init__(self,
                 username: str,
                 password: str,
                 headless: bool = False,
                 download_base_dir: Union[str, Path] = "downloads") -> None:
        self.username = username
        self.password = password
        self.headless = headless
        self.download_dir: Optional[Path] = None

    def run_full_process(self) -> Dict[str, Union[bool, str, List[str]]]:
        """執行完整流程

        Returns:
            包含執行結果的字典：
            - success: 執行是否成功
            - username: 使用者帳號
            - downloads: 下載檔案清單
            - error: 錯誤訊息（如果有的話）
        """
        return {
            "success": True,
            "username": self.username,
            "downloads": [],
            "error": None
        }
```

### 2. 文檔和註解規範

#### 2.1 文檔字串標準

```python
class PaymentScraper(BaseScraper):
    """黑貓宅急便貨到付款匯款明細抓取器

    這個類別專門處理黑貓宅急便的客樂得對帳單下載功能，
    支援多期數下載和自動期間選擇。

    Attributes:
        period_number (int): 要下載的期數，1 表示最新一期
        current_settlement_period (str): 當前選中的結算期間
        periods_to_download (List[Dict]): 待下載的期間資訊清單

    Example:
        >>> scraper = PaymentScraper("username", "password", period_number=2)
        >>> result = scraper.run_full_process()
        >>> print(f"下載了 {len(result['downloads'])} 個檔案")
    """

    def get_settlement_periods_for_download(self) -> Union[bool, str]:
        """獲取要下載的結算期間資訊

        根據設定的期數從下拉選單中提取可用的結算期間，
        並準備下載清單。

        Returns:
            bool: 成功時返回 True
            str: 當沒有可用資料時返回 "NO_DATA_AVAILABLE"
            bool: 發生錯誤時返回 False

        Raises:
            WebDriverException: 當頁面元素無法找到時

        Note:
            此方法會修改 self.periods_to_download 清單
        """
        # 實作邏輯...
```

#### 2.2 程式碼註解最佳實務

```python
def navigate_to_payment_query(self) -> bool:
    """導航到貨到付款查詢頁面"""

    # 重試機制：最多嘗試 3 次，每次間隔 3 秒
    max_attempts = 3
    for attempt in range(max_attempts):
        if attempt > 0:
            safe_print(f"🔄 第 {attempt + 1} 次嘗試導航...")
            time.sleep(3)

        try:
            # 步驟 1：檢查當前會話狀態
            if self._check_session_timeout():
                safe_print("⏰ 檢測到會話超時，嘗試重新登入...")
                if not self._handle_session_timeout():
                    continue  # 重新登入失敗，繼續重試

            # 步驟 2：優先使用直接 URL 方式（效率最高）
            if self._try_direct_urls():
                return True

            # 步驟 3：回退到框架導航方式
            if self._navigate_through_frames():
                return True

        except Exception as e:
            safe_print(f"❌ 第 {attempt + 1} 次導航嘗試失敗: {e}")
            continue

    return False
```

## 錯誤處理策略

### 1. 分層錯誤處理

```python
class SeleniumTCatError(Exception):
    """SeleniumTCat 基礎異常類別"""
    pass

class LoginError(SeleniumTCatError):
    """登入相關錯誤"""
    pass

class NavigationError(SeleniumTCatError):
    """導航相關錯誤"""
    pass

class DownloadError(SeleniumTCatError):
    """下載相關錯誤"""
    pass

class ConfigurationError(SeleniumTCatError):
    """配置相關錯誤"""
    pass


def login(self, max_attempts: int = 3) -> bool:
    """登入系統，包含完整的錯誤處理"""

    for attempt in range(1, max_attempts + 1):
        try:
            # 執行登入邏輯
            if self._attempt_login():
                return True

        except LoginError as e:
            safe_print(f"❌ 登入錯誤 (嘗試 {attempt}/{max_attempts}): {e}")
            if attempt == max_attempts:
                raise  # 最後一次嘗試仍失敗，向上拋出

        except Exception as e:
            # 未預期的錯誤，記錄並轉換為已知錯誤類型
            safe_print(f"⚠️ 未預期的登入錯誤: {e}")
            if attempt == max_attempts:
                raise LoginError(f"登入失敗，未預期錯誤: {e}")

    return False
```

### 2. 優雅降級機制

```python
def download_cod_statement(self) -> List[Path]:
    """下載對帳單，包含多種備用方案"""

    downloaded_files = []

    # 方案 1：標準 AJAX 下載
    try:
        files = self._download_via_ajax()
        if files:
            safe_print("✅ AJAX 下載成功")
            return files
    except Exception as e:
        safe_print(f"⚠️ AJAX 下載失敗，嘗試備用方案: {e}")

    # 方案 2：直接連結下載
    try:
        files = self._download_via_direct_link()
        if files:
            safe_print("✅ 直接連結下載成功")
            return files
    except Exception as e:
        safe_print(f"⚠️ 直接連結下載失敗，嘗試最後方案: {e}")

    # 方案 3：表單提交下載
    try:
        files = self._download_via_form_submission()
        if files:
            safe_print("✅ 表單提交下載成功")
            return files
    except Exception as e:
        safe_print(f"❌ 所有下載方案都失敗: {e}")

    # 所有方案都失敗
    return []
```

### 3. 資源清理保證

```python
import contextlib
from typing import Generator

@contextlib.contextmanager
def browser_session(scraper_instance) -> Generator[None, None, None]:
    """瀏覽器會話上下文管理器，確保資源正確清理"""

    try:
        scraper_instance.init_browser()
        safe_print("🌐 瀏覽器會話已建立")
        yield

    except Exception as e:
        safe_print(f"❌ 瀏覽器會話錯誤: {e}")
        raise

    finally:
        # 無論是否發生錯誤，都確保清理
        try:
            if scraper_instance.driver:
                scraper_instance.driver.quit()
                safe_print("🔚 瀏覽器已關閉")
        except Exception as cleanup_error:
            safe_print(f"⚠️ 瀏覽器清理時發生錯誤: {cleanup_error}")

        # 清理臨時檔案
        if hasattr(scraper_instance, 'download_dir') and scraper_instance.download_dir:
            scraper_instance._cleanup_temp_directory(scraper_instance.download_dir)

# 使用方式
def run_full_process(self) -> Dict[str, Any]:
    """使用上下文管理器的完整流程"""

    with browser_session(self):
        if not self.login():
            return self._create_error_result("登入失敗")

        if not self.navigate_to_query_page():
            return self._create_error_result("導航失敗")

        downloaded_files = self.download_data()
        return self._create_success_result(downloaded_files)
```

## 效能最佳化

### 1. 智慧等待策略

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class SmartWaiter:
    """智慧等待工具類別"""

    def __init__(self, driver, default_timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, default_timeout)
        self.short_wait = WebDriverWait(driver, 3)
        self.long_wait = WebDriverWait(driver, 30)

    def wait_for_element_clickable(self, selector: str, timeout: Optional[int] = None) -> WebElement:
        """等待元素可點擊"""
        wait_instance = WebDriverWait(self.driver, timeout) if timeout else self.wait
        return wait_instance.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )

    def wait_for_ajax_complete(self, timeout: int = 15) -> bool:
        """等待 AJAX 請求完成"""
        try:
            self.wait.until(
                lambda driver: driver.execute_script("return jQuery.active == 0")
            )
            return True
        except Exception:
            # jQuery 可能不存在，嘗試其他方法
            return self._wait_for_network_idle(timeout)

    def _wait_for_network_idle(self, timeout: int) -> bool:
        """等待網路活動靜止"""
        try:
            # 使用 Chrome DevTools Protocol
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    let requestCount = 0;
                    const originalFetch = window.fetch;
                    const originalXHR = window.XMLHttpRequest;

                    // 監控 fetch 請求
                    window.fetch = function(...args) {
                        requestCount++;
                        return originalFetch.apply(this, args).finally(() => {
                            requestCount--;
                        });
                    };

                    // 等待請求完成
                    const checkIdle = () => {
                        if (requestCount === 0) {
                            resolve(true);
                        } else {
                            setTimeout(checkIdle, 100);
                        }
                    };

                    setTimeout(checkIdle, 1000);
                });
            """)
            return True
        except Exception:
            return False
```

### 2. 記憶體管理

```python
import gc
import psutil
import os

class ResourceMonitor:
    """資源監控器"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.get_memory_usage()

    def get_memory_usage(self) -> float:
        """取得目前記憶體使用量 (MB)"""
        return self.process.memory_info().rss / 1024 / 1024

    def check_memory_limit(self, limit_mb: int = 500) -> bool:
        """檢查記憶體使用是否超過限制"""
        current_memory = self.get_memory_usage()
        return current_memory > limit_mb

    def force_garbage_collection(self):
        """強制垃圾回收"""
        collected = gc.collect()
        safe_print(f"🗑️ 垃圾回收完成，清理了 {collected} 個物件")

    def log_memory_status(self):
        """記錄記憶體狀態"""
        current = self.get_memory_usage()
        increase = current - self.initial_memory
        safe_print(f"📊 記憶體使用: {current:.1f}MB (增加: +{increase:.1f}MB)")


# 在長時間執行的操作中使用
def process_multiple_accounts(self, accounts):
    """處理多個帳號，包含資源監控"""

    monitor = ResourceMonitor()

    for i, account in enumerate(accounts):
        try:
            # 處理帳號
            result = self._process_single_account(account)

            # 每處理 5 個帳號檢查一次資源
            if (i + 1) % 5 == 0:
                monitor.log_memory_status()

                if monitor.check_memory_limit(800):  # 800MB 限制
                    safe_print("⚠️ 記憶體使用過高，執行垃圾回收...")
                    monitor.force_garbage_collection()

        except Exception as e:
            safe_print(f"❌ 處理帳號 {account['username']} 失敗: {e}")
            continue
```

### 3. 並行處理最佳化

```python
import asyncio
import concurrent.futures
from typing import List, Callable, Any

class ParallelProcessor:
    """並行處理器"""

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers

    async def process_accounts_async(self,
                                   accounts: List[Dict],
                                   processor_func: Callable,
                                   **kwargs) -> List[Any]:
        """非同步處理多個帳號"""

        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_semaphore(account):
            async with semaphore:
                # 在執行緒池中執行同步程式碼
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, processor_func, account, **kwargs
                )

        # 建立所有任務
        tasks = [process_with_semaphore(account) for account in accounts]

        # 等待所有任務完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                safe_print(f"❌ 帳號 {accounts[i]['username']} 處理失敗: {result}")
                processed_results.append({
                    "success": False,
                    "username": accounts[i]['username'],
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    def process_with_thread_pool(self,
                                accounts: List[Dict],
                                processor_func: Callable,
                                **kwargs) -> List[Any]:
        """使用執行緒池處理帳號"""

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任務
            future_to_account = {
                executor.submit(processor_func, account, **kwargs): account
                for account in accounts
            }

            results = []
            for future in concurrent.futures.as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    result = future.result()
                    results.append(result)
                    safe_print(f"✅ 帳號 {account['username']} 處理完成")
                except Exception as e:
                    safe_print(f"❌ 帳號 {account['username']} 處理失敗: {e}")
                    results.append({
                        "success": False,
                        "username": account['username'],
                        "error": str(e)
                    })

            return results
```

## 測試策略

### 1. 測試架構設計

```python
# tests/conftest.py
import pytest
from pathlib import Path
import json
from unittest.mock import Mock
from src.core.base_scraper import BaseScraper

@pytest.fixture
def mock_driver():
    """模擬 WebDriver"""
    driver = Mock()
    driver.current_url = "https://example.com"
    driver.page_source = "<html><body>Test</body></html>"
    return driver

@pytest.fixture
def mock_config(tmp_path):
    """建立測試用配置檔"""
    config_data = {
        "accounts": [
            {"username": "test_user", "password": "test_pass", "enabled": True}
        ],
        "settings": {
            "headless": True,
            "download_base_dir": str(tmp_path / "downloads")
        }
    }

    config_file = tmp_path / "test_accounts.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)

    return str(config_file)

@pytest.fixture
def base_scraper(mock_driver):
    """建立測試用 BaseScraper 實例"""
    scraper = BaseScraper("test_user", "test_pass")
    scraper.driver = mock_driver
    scraper.wait = Mock()
    return scraper
```

### 2. 模擬和存根模式

```python
# tests/unit/test_payment_scraper.py
import pytest
from unittest.mock import patch, Mock, call
from src.scrapers.payment_scraper import PaymentScraper

class TestPaymentScraper:
    """PaymentScraper 單元測試"""

    @patch('src.scrapers.payment_scraper.init_chrome_browser')
    def test_navigate_success_with_direct_url(self, mock_init_browser):
        """測試直接 URL 導航成功"""

        # 設定模擬環境
        mock_driver = Mock()
        mock_driver.current_url = "https://www.takkyubin.com.tw/success"
        mock_driver.page_source = "匯款明細 貨到付款"
        mock_init_browser.return_value = (mock_driver, Mock())

        scraper = PaymentScraper("test_user", "test_pass")
        scraper.driver = mock_driver

        # 模擬 _try_direct_urls 方法
        with patch.object(scraper, '_try_direct_urls', return_value=True) as mock_direct:
            result = scraper.navigate_to_payment_query()

            assert result is True
            mock_direct.assert_called_once()

    def test_download_with_multiple_periods(self):
        """測試多期數下載"""

        scraper = PaymentScraper("test_user", "test_pass", period_number=3)
        scraper.driver = Mock()

        # 模擬期間資料
        scraper.periods_to_download = [
            {'index': 1, 'text': '2024/09/01~2024/09/07'},
            {'index': 2, 'text': '2024/08/25~2024/08/31'},
            {'index': 3, 'text': '2024/08/18~2024/08/24'}
        ]

        with patch.object(scraper, 'download_cod_statement') as mock_download:
            mock_download.return_value = [Path("test_file.xlsx")]

            result = scraper.download_data()

            # 驗證每個期間都被處理
            assert mock_download.call_count == 3
            assert len(result) == 3  # 每期一個檔案
```

### 3. 整合測試策略

```python
# tests/integration/test_full_workflow.py
import pytest
from pathlib import Path
from src.core.multi_account_manager import MultiAccountManager
from src.scrapers.payment_scraper import PaymentScraper

class TestFullWorkflow:
    """完整工作流程整合測試"""

    @pytest.mark.integration
    def test_end_to_end_payment_scraper(self, mock_config, tmp_path):
        """端到端測試支付爬蟲"""

        # 使用真實的管理器但模擬網路部分
        manager = MultiAccountManager(mock_config)

        with patch('src.scrapers.payment_scraper.init_chrome_browser') as mock_init:
            mock_driver = Mock()
            mock_init.return_value = (mock_driver, Mock())

            # 模擬成功的登入和導航
            with patch.object(PaymentScraper, 'login', return_value=True), \
                 patch.object(PaymentScraper, 'navigate_to_payment_query', return_value=True), \
                 patch.object(PaymentScraper, 'get_settlement_periods_for_download', return_value=True):

                # 模擬檔案下載
                test_file = tmp_path / "downloads" / "test_download.xlsx"
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text("test content")

                with patch.object(PaymentScraper, 'download_cod_statement', return_value=[test_file]):
                    results = manager.run_all_accounts(PaymentScraper)

                    # 驗證結果
                    assert len(results) == 1
                    assert results[0]['success'] is True
                    assert results[0]['username'] == 'test_user'
                    assert len(results[0]['downloads']) == 1

    @pytest.mark.slow
    @pytest.mark.requires_browser
    def test_browser_initialization_real(self):
        """測試真實瀏覽器初始化（需要實際瀏覽器）"""

        scraper = PaymentScraper("dummy", "dummy", headless=True)

        try:
            scraper.init_browser()
            assert scraper.driver is not None
            assert scraper.wait is not None

            # 測試基本瀏覽器功能
            scraper.driver.get("https://www.google.com")
            assert "google" in scraper.driver.current_url.lower()

        finally:
            if scraper.driver:
                scraper.driver.quit()
```

## 安全性最佳實務

### 1. 密碼和憑證處理

```python
import os
import base64
from cryptography.fernet import Fernet
from typing import Optional

class SecureCredentialManager:
    """安全憑證管理器"""

    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def _get_or_create_key(self) -> bytes:
        """取得或建立加密金鑰"""
        key_file = Path(".encryption_key")

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # 建立新金鑰
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)

            # 設定檔案權限
            key_file.chmod(0o600)  # 只有擁有者可讀寫
            return key

    def encrypt_password(self, password: str) -> str:
        """加密密碼"""
        encrypted = self.cipher.encrypt(password.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_password(self, encrypted_password: str) -> str:
        """解密密碼"""
        encrypted_bytes = base64.b64decode(encrypted_password.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

    def get_password_from_env(self, account: str) -> Optional[str]:
        """從環境變數取得密碼"""
        env_var = f"TCAT_PASSWORD_{account.upper()}"
        return os.getenv(env_var)

# 使用範例
def load_secure_config(config_file: str) -> dict:
    """載入安全配置"""

    credential_manager = SecureCredentialManager()

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 處理帳號密碼
    for account in config.get('accounts', []):
        username = account['username']

        # 優先順序：環境變數 > 加密密碼 > 明文密碼
        env_password = credential_manager.get_password_from_env(username)
        if env_password:
            account['password'] = env_password
        elif account.get('encrypted_password'):
            account['password'] = credential_manager.decrypt_password(
                account['encrypted_password']
            )
        # 如果都沒有，使用明文密碼（開發環境）

        # 清除敏感資訊
        account.pop('encrypted_password', None)

    return config
```

### 2. 日誌安全處理

```python
import logging
import re
from typing import Any

class SecureFormatter(logging.Formatter):
    """安全的日誌格式器，會遮蔽敏感資訊"""

    SENSITIVE_PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'，\s]+)', re.IGNORECASE), 'password=***'),
        (re.compile(r'帳號["\']?\s*[:=]\s*["\']?([^"\'，\s]+)', re.IGNORECASE), '帳號=***'),
        (re.compile(r'密碼["\']?\s*[:=]\s*["\']?([^"\'，\s]+)', re.IGNORECASE), '密碼=***'),
        (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'，\s]+)', re.IGNORECASE), 'token=***'),
    ]

    def format(self, record: logging.LogRecord) -> str:
        """格式化日誌記錄，遮蔽敏感資訊"""

        # 先進行標準格式化
        formatted = super().format(record)

        # 遮蔽敏感資訊
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            formatted = pattern.sub(replacement, formatted)

        return formatted

def setup_secure_logging():
    """設定安全的日誌系統"""

    # 建立日誌目錄
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 設定日誌等級
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "seleniumtcat.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 使用安全格式器
    for handler in logging.getLogger().handlers:
        handler.setFormatter(SecureFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

def safe_log_account_info(logger: logging.Logger, username: str):
    """安全地記錄帳號資訊"""

    # 只記錄使用者名稱的前3個字元
    masked_username = username[:3] + '*' * (len(username) - 3) if len(username) > 3 else '***'
    logger.info(f"處理帳號: {masked_username}")
```

### 3. 輸入驗證和清理

```python
import re
import html
from typing import Any, Dict, List

class InputValidator:
    """輸入驗證器"""

    @staticmethod
    def validate_username(username: str) -> bool:
        """驗證使用者名稱格式"""
        if not username or len(username) < 3:
            return False

        # 只允許字母、數字、底線、連字號
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, username))

    @staticmethod
    def validate_period_number(period: Any) -> bool:
        """驗證期數參數"""
        try:
            period_int = int(period)
            return 1 <= period_int <= 12  # 合理的期數範圍
        except (ValueError, TypeError):
            return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理檔案名稱，移除危險字元"""

        # 移除危險字元
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
        clean_name = re.sub(dangerous_chars, '_', filename)

        # 移除開頭結尾的空白和點
        clean_name = clean_name.strip(' .')

        # 限制長度
        if len(clean_name) > 200:
            clean_name = clean_name[:200]

        return clean_name

    @staticmethod
    def validate_config_data(config: Dict[str, Any]) -> List[str]:
        """驗證配置資料"""
        errors = []

        # 檢查必要欄位
        if 'accounts' not in config:
            errors.append("缺少 accounts 欄位")
            return errors

        if not isinstance(config['accounts'], list):
            errors.append("accounts 必須是陣列")
            return errors

        # 驗證每個帳號
        for i, account in enumerate(config['accounts']):
            account_errors = []

            if 'username' not in account:
                account_errors.append("缺少 username")
            elif not InputValidator.validate_username(account['username']):
                account_errors.append("username 格式無效")

            if 'password' not in account:
                account_errors.append("缺少 password")
            elif len(account['password']) < 6:
                account_errors.append("password 長度不足")

            if account_errors:
                errors.append(f"帳號 {i+1}: {', '.join(account_errors)}")

        return errors

# 使用範例
def safe_process_user_input(username: str, period: str) -> Dict[str, Any]:
    """安全處理使用者輸入"""

    result = {"valid": True, "errors": []}

    # 驗證使用者名稱
    if not InputValidator.validate_username(username):
        result["errors"].append("使用者名稱格式無效")
        result["valid"] = False

    # 驗證期數
    if not InputValidator.validate_period_number(period):
        result["errors"].append("期數參數無效")
        result["valid"] = False

    return result
```

---

遵循這些最佳實務將幫助您開發出高品質、安全且可維護的 SeleniumTCat 擴展功能。記住，良好的程式碼不僅要能正常運作，更要易於理解、測試和維護。