#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
瀏覽器初始化共用函式
"""

import sys
import os
import time
import tempfile
import shutil
import subprocess
import signal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# 導入 Windows 編碼處理工具
from ..utils.windows_encoding_utils import safe_print

# 追蹤所有建立的臨時 user-data-dir，供清理使用
_temp_user_data_dirs = []


def _cleanup_headless_chrome():
    """
    清理 Selenium 相關的 Chrome 和 ChromeDriver 進程

    只清理帶有 --user-data-dir=.*selenium 參數的 Chrome 進程（由本工具啟動的），
    避免誤殺使用者正常開啟的 Chrome 瀏覽器。同時清理 chromedriver 進程。
    """
    is_windows = sys.platform == "win32"

    try:
        if is_windows:
            # Windows: 使用 WMIC 查找並終止 Selenium Chrome
            # 查找帶有 selenium 臨時目錄的 chrome.exe
            try:
                result = subprocess.run(
                    ['wmic', 'process', 'where',
                     "name='chrome.exe' and commandline like '%selenium_chrome_%'",
                     'get', 'processid'],
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.strip().split('\n')[1:]:
                    pid = line.strip()
                    if pid and pid.isdigit():
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                       capture_output=True, timeout=5)
            except Exception:
                pass

            # 終止所有 chromedriver.exe
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'],
                               capture_output=True, timeout=5)
            except Exception:
                pass
        else:
            # macOS/Linux: 使用 pgrep 和 pkill
            # 查找並終止 Selenium 啟動的 Chrome 進程（匹配 selenium_chrome_ 臨時目錄）
            selenium_pids = []
            try:
                result = subprocess.run(
                    ['pgrep', '-f', 'selenium_chrome_'],
                    capture_output=True, text=True, timeout=10
                )
                selenium_pids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip().isdigit()]

                for pid in selenium_pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except (ProcessLookupError, PermissionError):
                        pass

                # macOS 上等待 SIGTERM 生效，仍存在則 SIGKILL
                if selenium_pids:
                    time.sleep(1)
                    for pid in selenium_pids:
                        try:
                            os.kill(int(pid), 0)  # 檢查進程是否仍存在
                            os.kill(int(pid), signal.SIGKILL)
                        except (ProcessLookupError, PermissionError, OSError):
                            pass
            except Exception:
                pass

            # 終止 chromedriver 進程
            try:
                subprocess.run(['pkill', '-f', 'chromedriver'],
                               capture_output=True, timeout=5)
            except Exception:
                pass

            # 清理可能殘留的 Chrome Helper 子進程（無 selenium_chrome_ 關鍵字但為孤兒進程）
            # 只在有 Selenium Chrome 被清理時才執行，避免誤殺使用者正常的 Chrome
            if selenium_pids:
                try:
                    # 找出所有 Chrome Helper 進程，檢查其父進程是否已不存在（孤兒進程）
                    result = subprocess.run(
                        ['pgrep', '-f', 'Google Chrome Helper'],
                        capture_output=True, text=True, timeout=10
                    )
                    helper_pids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip().isdigit()]

                    for pid in helper_pids:
                        try:
                            # 檢查父進程是否存在，若父進程已死則為孤兒
                            ppid_result = subprocess.run(
                                ['ps', '-o', 'ppid=', '-p', pid],
                                capture_output=True, text=True, timeout=5
                            )
                            ppid = ppid_result.stdout.strip()
                            if ppid and ppid.isdigit():
                                try:
                                    os.kill(int(ppid), 0)  # 檢查父進程是否存在
                                except ProcessLookupError:
                                    # 父進程已死，這是孤兒 Helper，終止它
                                    os.kill(int(pid), signal.SIGKILL)
                        except (ProcessLookupError, PermissionError, OSError, subprocess.TimeoutExpired):
                            pass
                except Exception:
                    pass

        # 給進程一點時間完全終止
        time.sleep(0.5)

    except Exception as e:
        # 清理失敗不應阻止主流程
        safe_print(f"⚠️ 進程清理時發生錯誤（可忽略）: {e}")


def cleanup_temp_user_data_dirs():
    """清理所有建立的臨時 user-data-dir 目錄"""
    global _temp_user_data_dirs
    for dir_path in _temp_user_data_dirs:
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
        except Exception:
            pass
    _temp_user_data_dirs.clear()


def init_chrome_browser(headless=False, download_dir=None, max_retries=3, retry_delay=2):
    """
    初始化 Chrome 瀏覽器（帶重試機制）

    Args:
        headless (bool): 是否使用無頭模式
        download_dir (str): 下載目錄路徑
        max_retries (int): 最大重試次數（預設 3）
        retry_delay (int): 基礎重試延遲秒數（實際延遲 = retry_delay * attempt）

    Returns:
        tuple: (driver, wait) WebDriver 實例和 WebDriverWait 實例

    重試邏輯：
    - 每次嘗試前：清理殘留 Chrome 進程 + 使用獨立 user-data-dir
    - 輪次 1：嘗試所有方法（CHROMEDRIVER_PATH → WebDriver Manager → 系統）
    - 輪次 2+：增加等待延遲後重試
    """
    global _temp_user_data_dirs

    safe_print("🚀 啟動瀏覽器...")

    # 偵測作業系統平台
    is_linux = sys.platform.startswith('linux')
    is_windows = sys.platform == "win32"
    is_macos = sys.platform == "darwin"

    # 從環境變數讀取 Chrome 路徑（跨平台設定）
    chrome_binary_path = os.getenv("CHROME_BINARY_PATH")

    # 初始化 Chrome 瀏覽器（帶重試機制）
    # 優先使用 WebDriver Manager 以確保版本相容性
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    all_errors = []  # 收集所有嘗試的錯誤

    for attempt in range(1, max_retries + 1):
        driver = None
        attempt_errors = []

        # 每次嘗試前都清理殘留進程（包括第一次）
        if attempt == 1:
            safe_print("🧹 清理殘留的 Chrome/ChromeDriver 進程...")
        else:
            safe_print(f"\n🔄 第 {attempt}/{max_retries} 次重試...")
            safe_print("🧹 清理殘留的 Chrome/ChromeDriver 進程...")
        _cleanup_headless_chrome()

        if attempt > 1:
            delay = retry_delay * attempt
            safe_print(f"⏳ 等待 {delay} 秒後重試...")
            time.sleep(delay)

        # 為每次嘗試建立獨立的 user-data-dir，避免 profile lock 衝突
        temp_user_data_dir = tempfile.mkdtemp(prefix="selenium_chrome_")
        _temp_user_data_dirs.append(temp_user_data_dir)

        # 每次嘗試都重新建立 Chrome 選項（因為 user-data-dir 不同）
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,720")

        # 使用獨立的 user-data-dir，避免 Chrome profile lock 衝突
        chrome_options.add_argument(f"--user-data-dir={temp_user_data_dir}")

        # 隱藏 Chrome 警告訊息
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu-sandbox")
        chrome_options.add_argument("--remote-debugging-port=0")  # 隱藏 DevTools listening 訊息
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 設定自動下載權限，避免下載多個檔案時的權限提示
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-iframes-during-prerender")

        # 跨平台穩定性選項
        chrome_options.add_argument("--disable-gpu")              # 防止 GPU 相關崩潰
        chrome_options.add_argument("--disable-hang-monitor")     # 防止未回應偵測導致終止
        chrome_options.add_argument("--disable-sync")             # 禁用 Chrome 同步
        chrome_options.add_argument("--disable-popup-blocking")   # 防止彈出窗口干擾
        chrome_options.add_argument("--no-first-run")             # 跳過首次運行設定
        chrome_options.add_argument("--disable-component-update") # 防止背景更新干擾

        # Linux/Ubuntu 環境專屬優化（降低記憶體和 CPU 使用）
        if is_linux:
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")  # 節省記憶體 ~80MB
            chrome_options.add_argument("--disable-software-rasterizer")  # 節省 CPU ~15%
            if attempt == 1:
                safe_print("🐧 Ubuntu/Linux 環境偵測: 已套用記憶體優化參數")
        else:
            # 非 Linux 環境也禁用 VizDisplayCompositor
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")

        # 如果設定為無頭模式，添加 headless 參數
        if headless:
            chrome_options.add_argument("--headless")
            if attempt == 1:
                safe_print("🔇 使用無頭模式（不顯示瀏覽器視窗）")
        else:
            if attempt == 1:
                safe_print("🖥️ 使用視窗模式（顯示瀏覽器）")

        # 設定 Chrome 路徑
        if chrome_binary_path:
            if os.path.exists(chrome_binary_path):
                chrome_options.binary_location = chrome_binary_path
                if attempt == 1:
                    safe_print(f"🌐 使用指定 Chrome 路徑: {chrome_binary_path}")
            else:
                if attempt == 1:
                    safe_print(f"⚠️ 警告: CHROME_BINARY_PATH 指定的路徑不存在: {chrome_binary_path}")
                    safe_print("   將嘗試使用系統預設 Chrome")
        else:
            if attempt == 1:
                safe_print("⚠️ 未設定 CHROME_BINARY_PATH 環境變數，使用系統預設 Chrome")

        # 設定下載路徑
        if download_dir:
            prefs = {
                "download.default_directory": str(download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_setting_values.automatic_downloads": 1,  # 允許多個檔案自動下載
                "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,  # 允許自動下載
            }
            chrome_options.add_experimental_option("prefs", prefs)

        # 方法1: 嘗試使用 .env 中設定的 ChromeDriver 路徑
        if chromedriver_path and os.path.exists(chromedriver_path):
            try:
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                safe_print(f"✅ 使用指定 ChromeDriver 啟動: {chromedriver_path}")
            except Exception as env_error:
                error_msg = f"指定 ChromeDriver: {env_error}"
                safe_print(f"⚠️ {error_msg}")
                attempt_errors.append(error_msg)

        # 方法2: 使用 WebDriver Manager（自動下載匹配版本的 ChromeDriver）
        if not driver:
            try:
                # 抑制 ChromeDriverManager 的輸出
                import logging
                logging.getLogger("WDM").setLevel(logging.WARNING)

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                safe_print("✅ 使用 WebDriver Manager 啟動 Chrome（自動匹配版本）")
            except Exception as wdm_error:
                error_msg = f"WebDriver Manager: {wdm_error}"
                safe_print(f"⚠️ {error_msg}")
                attempt_errors.append(error_msg)

        # 方法3: 最後嘗試使用系統 ChromeDriver（可能有版本不匹配問題）
        if not driver:
            try:
                # 配置 Chrome Service 來隱藏輸出
                if sys.platform == "win32":
                    # Windows 上重導向 Chrome 輸出到 null
                    service = Service()
                    service.creation_flags = 0x08000000  # CREATE_NO_WINDOW
                else:
                    # Linux/macOS 使用 devnull
                    service = Service(log_path=os.devnull)

                driver = webdriver.Chrome(service=service, options=chrome_options)
                safe_print("✅ 使用系統 ChromeDriver 啟動")
            except Exception as system_error:
                error_msg = f"系統 ChromeDriver: {system_error}"
                safe_print(f"⚠️ {error_msg}")
                attempt_errors.append(error_msg)

        # 如果成功啟動，設定超時並返回 driver 和 wait
        if driver:
            # 設定 WebDriver 超時，防止 Chrome 無限期掛起後崩潰
            driver.set_page_load_timeout(60)   # 頁面載入超時 60 秒
            driver.set_script_timeout(30)      # 腳本執行超時 30 秒

            wait = WebDriverWait(driver, 10)
            safe_print("✅ 瀏覽器初始化完成")
            return driver, wait

        # 本次失敗，清理剛建立的臨時目錄
        try:
            if os.path.exists(temp_user_data_dir):
                shutil.rmtree(temp_user_data_dir, ignore_errors=True)
                _temp_user_data_dirs.remove(temp_user_data_dir)
        except (ValueError, Exception):
            pass

        # 記錄本次嘗試的錯誤
        all_errors.append(f"嘗試 {attempt}: {'; '.join(attempt_errors)}")

    # 所有重試都失敗，輸出詳細診斷資訊
    safe_print("\n" + "=" * 60)
    safe_print("❌ 所有 Chrome 啟動嘗試都失敗了！")
    safe_print("=" * 60)
    safe_print("\n📋 錯誤摘要:")
    for error in all_errors:
        safe_print(f"   • {error}")
    safe_print("")

    # 如果所有方法都失敗，拋出錯誤（平台特定的故障排除訊息）
    error_occurred = True
    if error_occurred:
        error_msg = "❌ 所有 Chrome 啟動方法都失敗了！請檢查 Chrome 安裝或環境設定"
        safe_print(error_msg)
        safe_print("\n請依據您的作業系統檢查以下項目:\n")

        if is_linux:
            # Ubuntu/Linux 特定的故障排除步驟
            print("🐧 Ubuntu/Linux 解決方案:")
            print("   1. 安裝 Chromium 和 ChromeDriver:")
            print("      sudo apt update")
            print("      sudo apt install -y chromium-browser chromium-chromedriver")
            print("")
            print("   2. 驗證安裝:")
            print("      chromium-browser --version")
            print("      chromedriver --version")
            print("")
            print("   3. 設定 .env 檔案:")
            print('      CHROME_BINARY_PATH="/usr/bin/chromium-browser"')
            print('      CHROMEDRIVER_PATH="/usr/bin/chromedriver"')
            print("")
            print("   4. 檢查執行權限:")
            print("      ls -la /usr/bin/chromium-browser")
            print("      ls -la /usr/bin/chromedriver")
            print("")
            print("   5. 使用快速部署腳本:")
            print("      bash scripts/ubuntu_quick_setup.sh")
            print("")
            print("   📖 完整指南: docs/technical/ubuntu-deployment-guide.md")

        elif is_windows:
            # Windows 特定的故障排除步驟
            print("🪟 Windows 解決方案:")
            print("   1. 確認已安裝 Google Chrome 瀏覽器")
            print("      預設路徑: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            print("")
            print("   2. 下載 ChromeDriver:")
            print("      https://chromedriver.chromium.org/downloads")
            print("")
            print("   3. 設定 .env 檔案:")
            print('      CHROME_BINARY_PATH="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"')
            print('      CHROMEDRIVER_PATH="C:\\path\\to\\chromedriver.exe"')
            print("")
            print("   4. 或將 ChromeDriver.exe 放入系統 PATH")

        elif is_macos:
            # macOS 特定的故障排除步驟
            print("🍎 macOS 解決方案:")
            print("   1. 確認已安裝 Google Chrome")
            print("      應用程式 > Google Chrome.app")
            print("")
            print("   2. 使用 Homebrew 安裝 ChromeDriver:")
            print("      brew install chromedriver")
            print("")
            print("   3. 設定 .env 檔案:")
            print('      CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"')
            print('      CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"')

        else:
            # 未知平台
            print("❓ 未知平台 - 通用解決方案:")
            print("   1. 確認已安裝 Chrome 或 Chromium 瀏覽器")
            print("   2. 下載對應的 ChromeDriver")
            print("   3. 設定 .env 檔案中的路徑")

        error_msg = f"❌ 所有 Chrome 啟動方法都失敗了（共嘗試 {max_retries} 輪）！請檢查 Chrome 安裝或環境設定"
        raise RuntimeError(error_msg)
