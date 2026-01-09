#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
黑貓宅急便基礎抓取器共用模組
包含登入、驗證碼處理等核心功能
"""

import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import ddddocr

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .browser_utils import init_chrome_browser
from ..utils.windows_encoding_utils import safe_print


class BaseScraper:
    """黑貓宅急便基礎抓取器類別"""

    # 子類別必須覆寫此類別變數，指定環境變數名稱
    DOWNLOAD_DIR_ENV_KEY = None
    # 子類別必須覆寫此類別變數，指定已完成下載目錄的環境變數名稱
    DOWNLOAD_OK_DIR_ENV_KEY = None

    def __init__(self, username, password, headless=None):
        # 載入環境變數
        load_dotenv()

        self.url = "https://www.takkyubin.com.tw/YMTContract/aspx/Login.aspx"
        self.username = username
        self.password = password

        # headless 優先級: CLI 參數 > 環境變數 > 預設值 (true)
        if headless is not None:
            self.headless = headless
        else:
            env_headless = os.getenv("HEADLESS", "true").lower()
            self.headless = env_headless == "true"

        self.driver = None
        self.wait = None

        # 安全警告標記 - 用於跟蹤是否遇到密碼安全警告
        self.security_warning_encountered = False

        # 執行時間統計
        self.start_time = None
        self.end_time = None
        self.execution_duration_minutes = 0

        # 初始化 ddddocr
        self.ocr = ddddocr.DdddOcr(show_ad=False)

        # 從環境變數讀取下載目錄
        if self.DOWNLOAD_DIR_ENV_KEY is None:
            raise NotImplementedError("子類別必須設定 DOWNLOAD_DIR_ENV_KEY")
        if self.DOWNLOAD_OK_DIR_ENV_KEY is None:
            raise NotImplementedError("子類別必須設定 DOWNLOAD_OK_DIR_ENV_KEY")

        download_base_dir = os.getenv(self.DOWNLOAD_DIR_ENV_KEY, "downloads")

        # 所有檔案都放在同一層的下載目錄
        self.final_download_dir = Path(download_base_dir)
        self.final_download_dir.mkdir(parents=True, exist_ok=True)

        # 從環境變數讀取已完成下載目錄（用於檢查是否已下載過）
        ok_dir = os.getenv(self.DOWNLOAD_OK_DIR_ENV_KEY)
        self.ok_download_dir = Path(ok_dir) if ok_dir else None

        # download_dir 將在每次下載時動態設定為 UUID 臨時目錄
        self.download_dir = None

        # 建立專屬資料夾
        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")
        self.temp_dir = Path("temp")

        # 確保資料夾存在
        for dir_path in [self.reports_dir, self.logs_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    # ==================== 檔案檢查方法 ====================

    def is_file_already_downloaded(self, filename):
        """
        檢查檔案是否已存在於 WORK_DIR 或 OK_DIR 中（已下載過）

        Args:
            filename: 要檢查的檔案名稱

        Returns:
            bool: 如果檔案已存在返回 True，否則返回 False
        """
        # 檢查 WORK_DIR
        if self.final_download_dir and self.final_download_dir.exists():
            work_file = self.final_download_dir / filename
            if work_file.exists():
                safe_print(f"⏭️ 檔案已存在於 WORK_DIR，跳過下載: {filename}")
                return True

        # 檢查 OK_DIR
        if self.ok_download_dir and self.ok_download_dir.exists():
            ok_file = self.ok_download_dir / filename
            if ok_file.exists():
                safe_print(f"⏭️ 檔案已存在於 OK_DIR，跳過下載: {filename}")
                return True

        return False

    # ==================== 智慧等待方法 ====================
    # 以下方法用於替代固定 time.sleep()，提升執行效率

    def smart_wait(self, condition, timeout=10, poll_frequency=0.5, error_message="等待條件超時"):
        """
        智慧等待 - 條件滿足立即返回，替代固定 time.sleep()

        Args:
            condition: WebDriverWait 條件或 lambda 函數
            timeout: 最長等待時間（秒），預設 10 秒
            poll_frequency: 輪詢頻率（秒），預設 0.5 秒
            error_message: 超時錯誤訊息

        Returns:
            條件滿足時的元素或布林值

        Example:
            # 等待元素出現
            element = self.smart_wait(
                EC.presence_of_element_located((By.ID, "myElement"))
            )

            # 等待 URL 變化
            self.smart_wait(
                lambda d: 'Login.aspx' not in d.current_url,
                timeout=15
            )
        """
        try:
            return WebDriverWait(self.driver, timeout, poll_frequency=poll_frequency).until(condition)
        except Exception as e:
            safe_print(f"⚠️ {error_message}: {e}")
            return None

    def smart_wait_for_url_change(self, old_url=None, timeout=10):
        """
        智慧等待 URL 變化

        Args:
            old_url: 舊 URL，若為 None 則使用當前 URL
            timeout: 最長等待時間（秒）

        Returns:
            是否成功變化
        """
        if old_url is None:
            old_url = self.driver.current_url

        try:
            WebDriverWait(self.driver, timeout).until(lambda d: d.current_url != old_url)
            safe_print(f"✅ URL 已變化: {old_url} → {self.driver.current_url}")
            return True
        except:
            safe_print(f"⚠️ URL 在 {timeout} 秒內未變化")
            return False

    def smart_wait_for_element(self, by, value, timeout=10, visible=True):
        """
        智慧等待元素出現

        Args:
            by: 定位方式 (By.ID, By.XPATH, 等)
            value: 定位值
            timeout: 最長等待時間（秒）
            visible: 是否需要可見，預設 True

        Returns:
            找到的元素或 None
        """
        try:
            if visible:
                element = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((by, value)))
            else:
                element = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            return element
        except:
            safe_print(f"⚠️ 在 {timeout} 秒內未找到元素: {by}={value}")
            return None

    def smart_wait_for_clickable(self, by, value, timeout=10):
        """
        智慧等待元素可點擊

        Args:
            by: 定位方式
            value: 定位值
            timeout: 最長等待時間（秒）

        Returns:
            可點擊的元素或 None
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
            return element
        except:
            safe_print(f"⚠️ 在 {timeout} 秒內元素未變為可點擊: {by}={value}")
            return None

    def smart_wait_for_ajax(self, timeout=15):
        """
        智慧等待 AJAX 請求完成（jQuery 或原生 fetch）

        Args:
            timeout: 最長等待時間（秒）

        Returns:
            是否完成
        """
        try:
            # 等待 jQuery AJAX 完成
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return typeof jQuery !== 'undefined' ? jQuery.active === 0 : true")
            )
            safe_print("✅ AJAX 請求已完成")
            return True
        except:
            safe_print(f"⚠️ AJAX 在 {timeout} 秒內未完成")
            return False

    def smart_wait_for_file_download(self, expected_extension=None, timeout=30, check_interval=0.5):
        """
        智慧等待檔案下載完成

        Args:
            expected_extension: 預期的檔案副檔名（如 '.xlsx'），None 表示任何檔案
            timeout: 最長等待時間（秒）
            check_interval: 檢查間隔（秒）

        Returns:
            下載的檔案清單
        """
        if not self.download_dir:
            safe_print("⚠️ 下載目錄未設定")
            return []

        safe_print(f"⏳ 等待檔案下載... (最多 {timeout} 秒)")
        start_time = time.time()
        downloaded_files = []

        while time.time() - start_time < timeout:
            # 檢查下載目錄中的檔案
            files = list(self.download_dir.glob("*"))

            # 排除臨時檔案（.crdownload, .tmp）
            valid_files = [f for f in files if f.suffix.lower() not in [".crdownload", ".tmp", ".part"]]

            # 如果指定了副檔名，進一步過濾
            if expected_extension:
                valid_files = [f for f in valid_files if f.suffix.lower() == expected_extension.lower()]

            if valid_files:
                # 找到新檔案
                new_files = [f for f in valid_files if f not in downloaded_files]
                if new_files:
                    for new_file in new_files:
                        safe_print(f"✅ 檢測到下載檔案: {new_file.name}")
                        downloaded_files.append(new_file)

                    # 等待一小段時間確保檔案完全寫入
                    time.sleep(1)
                    return downloaded_files

            time.sleep(check_interval)

        safe_print(f"⚠️ 在 {timeout} 秒內未檢測到下載檔案")
        return downloaded_files

    # ==================== 原有方法 ====================

    def init_browser(self):
        """初始化瀏覽器"""
        # 使用預設的 downloads 目錄初始化瀏覽器
        # 實際的 UUID 臨時目錄將在需要下載時才建立
        default_download_dir = self.final_download_dir

        self.driver, self.wait = init_chrome_browser(
            headless=self.headless, download_dir=str(default_download_dir.absolute())
        )

    def solve_captcha(self, captcha_img_element):
        """使用 ddddocr 自動識別驗證碼"""
        try:
            safe_print("🔍 使用 ddddocr 識別驗證碼...")

            # 截取驗證碼圖片
            screenshot = captcha_img_element.screenshot_as_png

            # 使用 ddddocr 識別
            result = self.ocr.classification(screenshot)

            safe_print(f"✅ ddddocr 識別結果: {result}")
            return result
        except Exception as e:
            safe_print(f"❌ ddddocr 識別失敗: {e}")
            return None

    def login(self, max_attempts=3):
        """執行登入流程，支援多次重試"""
        safe_print("🌐 開始登入流程...")

        for attempt in range(1, max_attempts + 1):
            safe_print(f"🔄 第 {attempt}/{max_attempts} 次登入嘗試")

            # 前往登入頁面
            self.driver.get(self.url)
            # 智慧等待登入表單載入完成
            self.smart_wait_for_element(By.ID, "txtUserID", timeout=10, visible=True)
            safe_print("✅ 登入頁面載入完成")

            # 填寫表單
            form_success = self.fill_login_form()
            if not form_success:
                safe_print(f"❌ 第 {attempt} 次嘗試 - 表單填寫失敗")
                if attempt < max_attempts:
                    safe_print("🔄 準備重試...")
                    time.sleep(2)
                continue

            submit_success = self.submit_login()
            if not submit_success:
                safe_print(f"❌ 第 {attempt} 次嘗試 - 表單提交失敗")
                if attempt < max_attempts:
                    safe_print("🔄 準備重試...")
                    time.sleep(2)
                continue

            # 檢查登入結果
            success = self.check_login_success()
            if success:
                safe_print(f"✅ 第 {attempt} 次嘗試成功登入！")
                return True
            else:
                safe_print(f"❌ 第 {attempt} 次嘗試登入失敗")
                if attempt < max_attempts:
                    safe_print("🔄 準備重試...")
                    time.sleep(3)  # 稍微增加重試間隔

        safe_print(f"❌ 經過 {max_attempts} 次嘗試後仍然登入失敗")
        return False

    def fill_login_form(self):
        """填寫登入表單"""
        safe_print("📝 填寫登入表單...")

        try:
            # 填入使用者帳號
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "txtUserID")))
            username_field.clear()
            username_field.send_keys(self.username)
            safe_print(f"✅ 已填入使用者帳號: {self.username}")

            # 填入密碼
            password_field = self.driver.find_element(By.ID, "txtUserPW")
            password_field.clear()
            password_field.send_keys(self.password)
            safe_print("✅ 已填入密碼")

            # 處理驗證碼
            captcha_success = self._handle_captcha()
            if not captcha_success:
                safe_print("❌ 驗證碼處理失敗")
                return False

            # 確保選擇「契約客戶專區 登入」
            self._select_contract_customer_login()
            return True

        except Exception as e:
            safe_print(f"❌ 填寫表單失敗: {e}")
            return False

    def _handle_captcha(self):
        """處理驗證碼輸入"""
        try:
            # 找到驗證碼圖片
            captcha_img = self.driver.find_element(By.ID, "captcha")

            # 使用 ddddocr 識別驗證碼
            captcha_text = self.solve_captcha(captcha_img)

            if captcha_text:
                # 填入驗證碼 - 尋找驗證碼輸入框
                captcha_selectors = [
                    (By.ID, "txtValidate"),
                    (By.NAME, "txtValidate"),
                    (By.ID, "txtCaptcha"),
                    (By.NAME, "txtCaptcha"),
                    (By.CSS_SELECTOR, "input[placeholder*='驗證']"),
                    (By.CSS_SELECTOR, "input[type='text']:nth-of-type(2)"),
                ]

                captcha_field = None
                for by_method, selector in captcha_selectors:
                    try:
                        captcha_field = self.driver.find_element(by_method, selector)
                        break
                    except:
                        continue

                if captcha_field:
                    captcha_field.clear()
                    captcha_field.send_keys(captcha_text)
                    safe_print(f"✅ 已填入驗證碼: {captcha_text}")
                    return True
                else:
                    safe_print("⚠️ 找不到驗證碼輸入框")
                    return False
            else:
                safe_print("⚠️ ddddocr 無法識別驗證碼")
                return False

        except Exception as captcha_e:
            safe_print(f"⚠️ 處理驗證碼時發生錯誤: {captcha_e}")
            return False

    def _select_contract_customer_login(self):
        """選擇契約客戶專區登入"""
        try:
            # 嘗試多種可能的選擇器
            contract_selectors = [
                (By.ID, "IsCustService_1"),  # 契約客戶專區
                (By.ID, "rdoLoginType_1"),
                (By.NAME, "IsCustService"),
                (By.CSS_SELECTOR, "input[type='radio'][value='1']"),
                (By.CSS_SELECTOR, "input[type='radio']:nth-of-type(2)"),
            ]

            contract_radio = None
            for by_method, selector in contract_selectors:
                try:
                    if by_method == By.NAME:
                        radios = self.driver.find_elements(by_method, selector)
                        if len(radios) > 1:
                            contract_radio = radios[1]  # 選擇第二個選項
                    else:
                        contract_radio = self.driver.find_element(by_method, selector)
                    break
                except:
                    continue

            if contract_radio and not contract_radio.is_selected():
                contract_radio.click()
                safe_print("✅ 已選擇契約客戶專區登入")
            elif contract_radio:
                safe_print("✅ 契約客戶專區已預先選中")
            else:
                safe_print("⚠️ 無法找到契約客戶專區選項，使用預設值")
        except Exception as e:
            safe_print(f"⚠️ 處理契約客戶專區選項時發生錯誤: {e}")

    def submit_login(self):
        """提交登入表單"""
        safe_print("📤 提交登入表單...")

        try:
            # 找到登入按鈕並點擊
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
            old_url = self.driver.current_url
            login_button.click()

            # 智慧等待頁面響應（URL變化或頁面載入完成）
            self.smart_wait_for_url_change(old_url=old_url, timeout=10)

            # 檢查是否有錯誤訊息在頁面上
            self._check_error_messages()

            # 檢查是否有Alert彈窗 - 使用統一的處理方式
            try:
                # 如果子類別有 _handle_alerts 方法，使用它
                if hasattr(self, "_handle_alerts"):
                    alert_result = self._handle_alerts()
                    if alert_result == "SECURITY_WARNING":
                        safe_print("🚨 登入後遇到密碼安全警告，終止當前帳號處理")
                        return False  # 返回 False 表示登入失敗，讓上層處理
                    elif alert_result:
                        safe_print("🔔 登入後處理了彈窗")
                else:
                    # fallback 到舊的處理方式
                    try:
                        alert = self.driver.switch_to.alert
                        alert_text = alert.text
                        safe_print(f"⚠️ 出現警告彈窗: {alert_text}")
                        alert.accept()  # 點擊確定
                        return False  # 登入失敗
                    except:
                        pass  # 沒有Alert彈窗
            except Exception as e:
                safe_print(f"⚠️ 處理登入後彈窗時發生錯誤: {e}")
                pass

            safe_print("✅ 表單已提交")
            return True

        except Exception as e:
            safe_print(f"❌ 提交表單失敗: {e}")
            return False

    def _check_error_messages(self):
        """檢查頁面上的錯誤訊息"""
        try:
            error_messages = []
            # 尋找可能的錯誤訊息
            error_selectors = [
                "//div[contains(@class, 'error')]",
                "//span[contains(@class, 'error')]",
                "//div[contains(text(), '錯誤')]",
                "//span[contains(text(), '錯誤')]",
                "//div[contains(text(), '失敗')]",
                "//span[contains(text(), '失敗')]",
                "//div[contains(text(), '驗證碼')]",
                "//span[contains(text(), '驗證碼')]",
            ]

            for selector in error_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.text.strip():
                            error_messages.append(element.text.strip())
                except:
                    continue

            if error_messages:
                safe_print(f"⚠️ 頁面錯誤訊息: {'; '.join(set(error_messages))}")

        except Exception as msg_e:
            safe_print(f"⚠️ 檢查錯誤訊息失敗: {msg_e}")

    def check_login_success(self):
        """檢查登入是否成功"""
        safe_print("🔐 檢查登入狀態...")

        current_url = self.driver.current_url
        current_title = self.driver.title
        safe_print(f"📍 當前 URL: {current_url}")
        safe_print(f"📄 當前標題: {current_title}")

        # 檢查頁面內容是否包含登入成功的跡象
        page_source = self.driver.page_source
        success_indicators = [
            "登出",
            "系統主選單",
            "歡迎",
            "功能選單",
            "查詢",
            "報表",
            "主頁",
            "首頁",
            "logout",
            "menu",
            "welcome",
            "main",
            "dashboard",
        ]

        failure_indicators = [
            "帳號或密碼錯誤",
            "驗證碼錯誤",
            "登入失敗",
            "帳號不存在",
            "密碼錯誤",
            "驗證失敗",
            "請重新登入",
        ]

        # 檢查失敗指標
        found_failures = []
        for indicator in failure_indicators:
            if indicator in page_source:
                found_failures.append(indicator)

        if found_failures:
            safe_print(f"⚠️ 發現登入失敗訊息: {', '.join(found_failures)}")
            return False

        # 檢查成功指標
        found_success = []
        for indicator in success_indicators:
            if indicator in page_source:
                found_success.append(indicator)

        # 檢查 URL 變化
        url_changed = current_url != self.url

        safe_print(f"🔍 登入檢查結果:")
        safe_print(f"   URL 是否改變: {'✅' if url_changed else '❌'}")
        safe_print(f"   成功指標: {found_success if found_success else '無'}")
        safe_print(f"   失敗指標: {found_failures if found_failures else '無'}")

        # 如果 URL 改變或找到成功指標，認為登入成功
        if url_changed or found_success:
            safe_print("✅ 登入成功，已進入系統")
            return True
        else:
            # 截取部分頁面內容用於分析
            page_snippet = page_source[:1000] if len(page_source) > 1000 else page_source
            safe_print(f"⚠️ 頁面內容片段: ...{page_snippet[-200:] if len(page_snippet) > 200 else page_snippet}")
            safe_print("❌ 登入失敗或頁面異常")
            return False

    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            safe_print("🔚 瀏覽器已關閉")

    def start_execution_timer(self):
        """開始執行時間計時"""
        self.start_time = datetime.now()
        safe_print(f"⏱️ 開始執行時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def end_execution_timer(self):
        """結束執行時間計時並計算總時長"""
        self.end_time = datetime.now()
        if self.start_time:
            duration = self.end_time - self.start_time
            self.execution_duration_minutes = duration.total_seconds() / 60
            safe_print(f"⏱️ 結束執行時間: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            safe_print(f"📊 執行時長: {self.execution_duration_minutes:.2f} 分鐘")
        else:
            safe_print("⚠️ 未找到開始時間，無法計算執行時長")

    def get_execution_summary(self):
        """獲取執行時間摘要"""
        if self.start_time and self.end_time:
            return {
                "username": self.username,
                "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_minutes": round(self.execution_duration_minutes, 2),
                "security_warning": self.security_warning_encountered,
            }
        else:
            return {
                "username": self.username,
                "start_time": None,
                "end_time": None,
                "duration_minutes": 0,
                "security_warning": self.security_warning_encountered,
            }

    def set_download_directory(self, download_path):
        """動態設定 Chrome 下載目錄"""
        try:
            self.driver.execute_cdp_cmd(
                "Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(download_path.absolute())}
            )
            safe_print(f"✅ 已設定下載目錄: {download_path}")
            return True
        except Exception as e:
            safe_print(f"⚠️ 設定下載目錄失敗: {e}")
            return False

    def setup_temp_download_dir(self):
        """
        建立並設定新的 UUID 臨時下載目錄
        如果瀏覽器已啟動，會動態設定下載目錄
        """
        import uuid

        temp_uuid = str(uuid.uuid4())
        self.download_dir = Path("temp") / temp_uuid
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # 如果瀏覽器已經啟動，動態設定下載目錄
        if hasattr(self, "driver") and self.driver:
            self.set_download_directory(self.download_dir)

        safe_print(f"📁 建立臨時下載目錄: {self.download_dir}")

    def create_temp_download_dir(self):
        """
        為本次下載建立唯一的 UUID 臨時目錄 (向後相容方法)
        Returns:
            臨時下載目錄的 Path 物件
        """
        self.setup_temp_download_dir()
        return self.download_dir

    def move_and_cleanup_files(self, downloaded_files, renamed_files):
        """
        將重命名後的檔案從臨時目錄移動到最終下載目錄，並清理臨時目錄

        Args:
            downloaded_files: 原始下載的檔案清單
            renamed_files: 重命名後的檔案清單

        Returns:
            最終目錄中的檔案清單
        """
        final_files = []

        try:
            import shutil

            safe_print(f"📁 移動檔案從臨時目錄 {self.download_dir} 到 {self.final_download_dir}")

            for renamed_file in renamed_files:
                if isinstance(renamed_file, Path):
                    source_file = renamed_file
                else:
                    source_file = Path(renamed_file)

                # 目標檔案路徑
                target_file = self.final_download_dir / source_file.name

                # 如果目標檔案存在，先刪除（覆蓋）
                if target_file.exists():
                    safe_print(f"⚠️ 目標檔案已存在，將覆蓋: {target_file.name}")
                    target_file.unlink()

                # 移動檔案
                shutil.move(str(source_file), str(target_file))
                final_files.append(target_file)
                safe_print(f"✅ 檔案已移動: {source_file.name} → {target_file}")

            # 清理臨時目錄
            self._cleanup_temp_directory(self.download_dir)

        except Exception as e:
            safe_print(f"❌ 檔案移動失敗: {e}")
            # 即使移動失敗，也嘗試清理臨時目錄
            self._cleanup_temp_directory(self.download_dir)

        return final_files

    def _cleanup_temp_directory(self, temp_dir):
        """清理臨時下載目錄"""
        try:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir)
                safe_print(f"🗑️ 已清理臨時目錄: {temp_dir}")
        except Exception as e:
            safe_print(f"⚠️ 清理臨時目錄失敗: {e}")

    # ==================== 元素搜尋輔助方法 ====================
    # 以下方法用於通用的元素搜尋，減少子類中的重複程式碼

    def find_date_inputs(self):
        """
        尋找頁面上的日期輸入欄位

        使用多種策略尋找開始日期和結束日期輸入框。

        Returns:
            tuple: (start_date_input, end_date_input) 或 (None, None) 如果找不到
        """
        start_date_input = None
        end_date_input = None

        # 策略1: 使用確切的 ID (txtDateS, txtDateE)
        try:
            start_date_input = self.driver.find_element(By.ID, "txtDateS")
            end_date_input = self.driver.find_element(By.ID, "txtDateE")
            return (start_date_input, end_date_input)
        except:
            pass

        # 策略2: 使用 NAME 屬性
        try:
            start_date_input = self.driver.find_element(By.NAME, "txtDateS")
            end_date_input = self.driver.find_element(By.NAME, "txtDateE")
            return (start_date_input, end_date_input)
        except:
            pass

        # 策略3: 嘗試交易明細表特有的 ID
        try:
            start_date_input = self.driver.find_element(By.ID, "txtStartDate")
            end_date_input = self.driver.find_element(By.ID, "txtEndDate")
            return (start_date_input, end_date_input)
        except:
            pass

        # 策略4: 通用搜索 - 尋找前兩個文字輸入框
        try:
            date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if len(date_inputs) >= 2:
                return (date_inputs[0], date_inputs[1])
        except:
            pass

        return (None, None)

    def fill_date_range(self, start_date, end_date):
        """
        填入日期範圍到輸入欄位

        Args:
            start_date: 開始日期字串 (YYYYMMDD 格式)
            end_date: 結束日期字串 (YYYYMMDD 格式)

        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        start_input, end_input = self.find_date_inputs()

        if not start_input or not end_input:
            safe_print("❌ 未找到日期輸入框")
            return False

        try:
            start_input.clear()
            start_input.send_keys(start_date)
            safe_print(f"✅ 已設定開始日期: {start_date}")

            end_input.clear()
            end_input.send_keys(end_date)
            safe_print(f"✅ 已設定結束日期: {end_date}")

            return True
        except Exception as e:
            safe_print(f"⚠️ 填入日期失敗: {e}")
            return False

    def find_search_button(self):
        """
        尋找頁面上的搜尋按鈕

        Returns:
            搜尋按鈕元素或 None
        """
        # 嘗試多種搜尋按鈕 ID
        button_ids = ["btnSearch", "btnQuery", "lnkbtnSearch"]

        for button_id in button_ids:
            try:
                button = self.driver.find_element(By.ID, button_id)
                if button and button.is_displayed() and button.is_enabled():
                    return button
            except:
                continue

        # 備用方法: 通用 CSS 選擇器
        try:
            buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "input[type='submit'][value*='搜'], input[type='button'][value*='搜'], button[value*='搜']"
            )
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    return button
        except:
            pass

        return None

    def click_search_button(self):
        """
        點擊搜尋按鈕

        Returns:
            bool: 成功點擊返回 True，失敗返回 False
        """
        button = self.find_search_button()
        if button:
            try:
                self.driver.execute_script("arguments[0].click();", button)
                safe_print("✅ 已點擊搜尋按鈕")
                return True
            except Exception as e:
                safe_print(f"❌ 點擊搜尋按鈕失敗: {e}")
                return False
        else:
            safe_print("❌ 找不到搜尋按鈕")
            return False

    # ==================== 會話管理方法 ====================
    # 以下方法用於處理會話超時和彈窗，在子類中共用

    def _check_session_timeout(self):
        """檢查當前頁面是否為會話超時"""
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source

            # 檢查 URL 是否包含會話超時相關的訊息
            timeout_indicators = ["MsgCenter.aspx", "系統閒置過久", "請重新登入"]

            # 檢查 URL - 使用更精確的檢查
            if any(indicator in current_url for indicator in timeout_indicators):
                return True

            # 特別檢查 TimeOut 參數，只有 TimeOut=Y 才算超時
            if "TimeOut=Y" in current_url:
                return True

            # 檢查其他 Session 相關但排除正常情況
            if "Session" in current_url and "SessionExpired" in current_url:
                return True

            # 檢查頁面內容
            timeout_messages = ["系統閒置過久", "請重新登入", "Session timeout", "Session expired", "會話超時"]

            if any(message in page_source for message in timeout_messages):
                return True

            return False

        except Exception as e:
            safe_print(f"❌ 檢查會話狀態時發生錯誤: {e}")
            return False

    def _handle_session_timeout(self):
        """處理會話超時，嘗試重新登入，包含完整的錯誤恢復機制"""
        try:
            safe_print("🔄 處理會話超時，嘗試重新登入...")

            # 清除可能的彈窗或alert
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
                safe_print("   清除了一個 alert 彈窗")
            except:
                pass

            # 確保回到主框架
            try:
                self.driver.switch_to.default_content()
            except:
                pass

            # 嘗試多個登入 URL，以防某些 URL 無法存取
            login_urls = [
                "https://www.takkyubin.com.tw/YMTContract/Login.aspx",
                "https://www.takkyubin.com.tw/YMTContract/",
                "https://www.takkyubin.com.tw/YMTContract/default.aspx",
            ]

            login_success = False

            for login_url in login_urls:
                try:
                    safe_print(f"   嘗試登入 URL: {login_url}")
                    self.driver.get(login_url)
                    self.smart_wait_for_url_change(timeout=5)

                    current_url = self.driver.current_url
                    safe_print(f"   導航後 URL: {current_url}")

                    # 檢查是否成功到達登入頁面
                    if "Login.aspx" in current_url or "登入" in self.driver.page_source:
                        safe_print("   ✅ 成功到達登入頁面")

                        # 重新執行登入流程
                        login_success = self.login()
                        if login_success:
                            safe_print("✅ 會話超時後重新登入成功")

                            # 智慧等待登入完成並驗證
                            self.smart_wait_for_url_change(timeout=10)

                            # 驗證登入是否真的成功
                            if not self._check_session_timeout():
                                safe_print("   ✅ 登入驗證成功，會話有效")
                                return True
                            else:
                                safe_print("   ❌ 登入驗證失敗，會話仍然無效")
                                continue
                        else:
                            safe_print("   ❌ 登入過程失敗")
                            continue
                    else:
                        safe_print("   ❌ 未能到達登入頁面")
                        continue

                except Exception as url_e:
                    safe_print(f"   ❌ 嘗試登入 URL 失敗: {url_e}")
                    continue

            if not login_success:
                safe_print("❌ 所有重新登入嘗試都失敗")

                # 最後嘗試：重新初始化瀏覽器會話
                try:
                    safe_print("🔄 嘗試重新初始化瀏覽器會話...")

                    # 刪除所有 cookies
                    self.driver.delete_all_cookies()

                    # 回到首頁
                    old_url = self.driver.current_url
                    self.driver.get("https://www.takkyubin.com.tw/YMTContract/")
                    self.smart_wait_for_url_change(old_url, timeout=5)

                    # 再次嘗試登入
                    final_login_success = self.login()
                    if final_login_success:
                        safe_print("✅ 重新初始化後登入成功")
                        return True

                except Exception as reinit_e:
                    safe_print(f"❌ 重新初始化失敗: {reinit_e}")

            return False

        except Exception as e:
            safe_print(f"❌ 處理會話超時時發生錯誤: {e}")
            return False

    def _handle_alerts(self):
        """處理各種類型的 alert 彈窗 - 密碼安全提示會終止當前帳號"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            safe_print(f"🔔 檢測到彈窗: {alert_text}")

            # 檢查是否為密碼安全相關的嚴重警告
            critical_keywords = ["密碼", "安全", "更新您的密碼", "為維護資訊安全"]

            if any(keyword in alert_text for keyword in critical_keywords):
                safe_print("🚨 檢測到密碼安全警告 - 終止當前帳號處理！")
                safe_print("⛔ 請先更新此帳號密碼後再使用本工具")
                alert.accept()  # 先關閉彈窗
                # 設置安全警告標記
                self.security_warning_encountered = True
                # 返回特殊值表示需要終止當前帳號
                return "SECURITY_WARNING"

            # 對於其他非關鍵性提示，可以繼續
            elif "系統" in alert_text:
                safe_print("ℹ️ 系統提示 - 點擊確定繼續")
                alert.accept()
                return True
            else:
                # 對於其他類型的 alert，謹慎處理
                safe_print(f"⚠️ 其他提示: {alert_text} - 點擊確定繼續")
                alert.accept()
                return True

        except Exception:
            # 沒有 alert 或其他處理失敗
            return False
