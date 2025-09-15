#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
黑貓宅急便基礎抓取器共用模組
包含登入、驗證碼處理等核心功能
"""

import os
import time
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

    def __init__(self, username, password, headless=False, download_base_dir="downloads"):
        # 載入環境變數
        load_dotenv()

        self.url = "https://www.takkyubin.com.tw/YMTContract/aspx/Login.aspx"
        self.username = username
        self.password = password
        self.headless = headless

        self.driver = None
        self.wait = None

        # 初始化 ddddocr
        self.ocr = ddddocr.DdddOcr(show_ad=False)

        # 所有帳號使用同一個下載目錄
        self.download_dir = Path(download_base_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # 建立專屬資料夾
        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")
        self.temp_dir = Path("temp")

        # 確保資料夾存在
        for dir_path in [self.reports_dir, self.logs_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def init_browser(self):
        """初始化瀏覽器"""
        self.driver, self.wait = init_chrome_browser(
            headless=self.headless,
            download_dir=str(self.download_dir.absolute())
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
            time.sleep(2)
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
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "txtUserID"))
            )
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
                    (By.CSS_SELECTOR, "input[type='text']:nth-of-type(2)")
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
                (By.CSS_SELECTOR, "input[type='radio']:nth-of-type(2)")
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
            login_button.click()

            # 等待頁面載入並處理可能的Alert
            time.sleep(5)  # 增加等待時間

            # 檢查是否有錯誤訊息在頁面上
            self._check_error_messages()

            # 檢查是否有Alert彈窗
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                safe_print(f"⚠️ 出現警告彈窗: {alert_text}")
                alert.accept()  # 點擊確定
                return False  # 登入失敗
            except:
                pass  # 沒有Alert彈窗

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
                "//span[contains(text(), '驗證碼')]"
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
            "登出", "系統主選單", "歡迎", "功能選單", "查詢", "報表", "主頁", "首頁",
            "logout", "menu", "welcome", "main", "dashboard"
        ]

        failure_indicators = [
            "帳號或密碼錯誤", "驗證碼錯誤", "登入失敗", "帳號不存在",
            "密碼錯誤", "驗證失敗", "請重新登入"
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