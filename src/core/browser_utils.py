#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
瀏覽器初始化共用函式
"""

import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# 導入 Windows 編碼處理工具
from ..utils.windows_encoding_utils import safe_print


def init_chrome_browser(headless=False, download_dir=None):
    """
    初始化 Chrome 瀏覽器

    Args:
        headless (bool): 是否使用無頭模式
        download_dir (str): 下載目錄路徑

    Returns:
        tuple: (driver, wait) WebDriver 實例和 WebDriverWait 實例
    """
    safe_print("🚀 啟動瀏覽器...")

    # 偵測作業系統平台
    is_linux = sys.platform.startswith('linux')
    is_windows = sys.platform == "win32"
    is_macos = sys.platform == "darwin"

    # Chrome 選項設定
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")

    # 隱藏 Chrome 警告訊息
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=0")  # 隱藏 DevTools listening 訊息
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # 設定自動下載權限，避免下載多個檔案時的權限提示
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-iframes-during-prerender")

    # Linux/Ubuntu 環境專屬優化（降低記憶體和 CPU 使用）
    if is_linux:
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")  # 節省記憶體 ~80MB
        chrome_options.add_argument("--disable-software-rasterizer")  # 節省 CPU ~15%
        chrome_options.add_argument("--disable-gpu")  # 伺服器通常無 GPU
        safe_print("🐧 Ubuntu/Linux 環境偵測: 已套用記憶體優化參數")
    else:
        # 非 Linux 環境也禁用 VizDisplayCompositor
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    # 如果設定為無頭模式，添加 headless 參數
    if headless:
        chrome_options.add_argument("--headless")
        safe_print("🔇 使用無頭模式（不顯示瀏覽器視窗）")
    else:
        safe_print("🖥️ 使用視窗模式（顯示瀏覽器）")

    # 從環境變數讀取 Chrome 路徑（跨平台設定）
    chrome_binary_path = os.getenv("CHROME_BINARY_PATH")
    if chrome_binary_path:
        # 驗證路徑是否存在
        if os.path.exists(chrome_binary_path):
            chrome_options.binary_location = chrome_binary_path
            safe_print(f"🌐 使用指定 Chrome 路徑: {chrome_binary_path}")
        else:
            safe_print(f"⚠️ 警告: CHROME_BINARY_PATH 指定的路徑不存在: {chrome_binary_path}")
            safe_print("   將嘗試使用系統預設 Chrome")
    else:
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

    # 初始化 Chrome 瀏覽器 (優先使用系統 Chrome)
    driver = None

    # 方法1: 嘗試使用 .env 中設定的 ChromeDriver 路徑
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if chromedriver_path and os.path.exists(chromedriver_path):
        try:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            safe_print(f"✅ 使用指定 ChromeDriver 啟動: {chromedriver_path}")
        except Exception as env_error:
            safe_print(f"⚠️ 指定的 ChromeDriver 路徑失敗: {env_error}")

    # 方法2: 嘗試使用系統 ChromeDriver (通常最穩定)
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
            safe_print("✅ 使用系統 Chrome 啟動")
        except Exception as system_error:
            safe_print(f"⚠️ 系統 Chrome 失敗: {system_error}")

    # 方法3: 最後嘗試 WebDriver Manager (可能有架構問題)
    if not driver:
        try:
            # 抑制 ChromeDriverManager 的輸出
            import logging

            logging.getLogger("WDM").setLevel(logging.WARNING)

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            safe_print("✅ 使用 WebDriver Manager 啟動 Chrome")
        except Exception as wdm_error:
            safe_print(f"⚠️ WebDriver Manager 失敗: {wdm_error}")

    # 如果所有方法都失敗，拋出錯誤（平台特定的故障排除訊息）
    if not driver:
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

        raise RuntimeError(error_msg)

    # 創建 WebDriverWait 實例
    wait = WebDriverWait(driver, 10)
    safe_print("✅ 瀏覽器初始化完成")

    return driver, wait
