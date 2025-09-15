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
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 設定自動下載權限，避免下載多個檔案時的權限提示
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-iframes-during-prerender")

    # 如果設定為無頭模式，添加 headless 參數
    if headless:
        chrome_options.add_argument("--headless")
        safe_print("🔇 使用無頭模式（不顯示瀏覽器視窗）")
    else:
        safe_print("🖥️ 使用視窗模式（顯示瀏覽器）")

    # 從環境變數讀取 Chrome 路徑（跨平台設定）
    chrome_binary_path = os.getenv('CHROME_BINARY_PATH')
    if chrome_binary_path:
        chrome_options.binary_location = chrome_binary_path
        safe_print(f"🌐 使用指定 Chrome 路徑: {chrome_binary_path}")
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
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1  # 允許自動下載
        }
        chrome_options.add_experimental_option("prefs", prefs)

    # 初始化 Chrome 瀏覽器 (優先使用系統 Chrome)
    driver = None

    # 方法1: 嘗試使用 .env 中設定的 ChromeDriver 路徑
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
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
            logging.getLogger('WDM').setLevel(logging.WARNING)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            safe_print("✅ 使用 WebDriver Manager 啟動 Chrome")
        except Exception as wdm_error:
            safe_print(f"⚠️ WebDriver Manager 失敗: {wdm_error}")

    # 如果所有方法都失敗，拋出錯誤
    if not driver:
        error_msg = "❌ 所有 Chrome 啟動方法都失敗了！請檢查 Chrome 安裝或環境設定"
        safe_print(error_msg)
        safe_print("請檢查以下項目:")
        print("   1. 確認已安裝 Google Chrome 瀏覽器")
        print("   2. 手動下載 ChromeDriver 並設定到 .env 檔案:")
        if sys.platform == "win32":
            print('      CHROMEDRIVER_PATH="C:\\path\\to\\chromedriver.exe"')
        else:
            print('      CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"')
        print("   3. 或將 ChromeDriver 放入系統 PATH")
        raise RuntimeError(error_msg)

    # 創建 WebDriverWait 實例
    wait = WebDriverWait(driver, 10)
    safe_print("✅ 瀏覽器初始化完成")

    return driver, wait