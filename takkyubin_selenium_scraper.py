#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time

# 設定 Windows 終端支援 UTF-8 輸出
if sys.platform == "win32":
    try:
        # 設定控制台輸出編碼為 UTF-8
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

        # 設定控制台代碼頁為 UTF-8
        os.system('chcp 65001 > nul')
    except Exception:
        # 如果設定失敗，使用替代方案
        pass

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import requests
import io
import ddddocr

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class TakkyubinSeleniumScraper:
    """
    使用 Selenium 的黑貓宅急便自動登入抓取工具
    """

    def __init__(self, username, password, headless=False, download_base_dir="downloads"):
        # 載入環境變數
        load_dotenv()

        self.url = "https://www.takkyubin.com.tw/YMTContract/aspx/Login.aspx"
        self.username = username
        self.password = password
        self.headless = headless

        self.driver = None
        self.wait = None

        # 儲存當前選擇的結算區間
        self.current_settlement_period = None

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
        print("🚀 啟動瀏覽器...")

        # Chrome 選項設定
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,720")

        # 如果設定為無頭模式，添加 headless 參數
        if self.headless:
            chrome_options.add_argument("--headless")
            print("🔇 使用無頭模式（不顯示瀏覽器視窗）")
        else:
            print("🖥️ 使用視窗模式（顯示瀏覽器）")

        # 從環境變數讀取 Chrome 路徑（跨平台設定）
        chrome_binary_path = os.getenv('CHROME_BINARY_PATH')
        if chrome_binary_path:
            chrome_options.binary_location = chrome_binary_path
            print(f"🌐 使用指定 Chrome 路徑: {chrome_binary_path}")
        else:
            print("⚠️ 未設定 CHROME_BINARY_PATH 環境變數，使用系統預設 Chrome")

        # 設定下載路徑
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # 使用 webdriver-manager 自動管理 ChromeDriver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ 使用 WebDriver Manager 啟動 Chrome")
        except Exception as e:
            print(f"⚠️ WebDriver Manager 失敗，嘗試使用系統 Chrome: {e}")
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✅ 使用系統 Chrome")
            except Exception as e2:
                print(f"❌ Chrome 啟動失敗: {e2}")
                raise e2

        self.wait = WebDriverWait(self.driver, 10)
        print("✅ 瀏覽器初始化完成")

    def solve_captcha(self, captcha_img_element):
        """使用 ddddocr 自動識別驗證碼"""
        try:
            print("🔍 使用 ddddocr 識別驗證碼...")

            # 截取驗證碼圖片
            screenshot = captcha_img_element.screenshot_as_png

            # 使用 ddddocr 識別
            result = self.ocr.classification(screenshot)

            print(f"✅ ddddocr 識別結果: {result}")
            return result
        except Exception as e:
            print(f"❌ ddddocr 識別失敗: {e}")
            return None

    def login(self):
        """執行登入流程"""
        print("🌐 開始登入流程...")

        # 前往登入頁面
        self.driver.get(self.url)
        time.sleep(2)
        print("✅ 登入頁面載入完成")

        # 填寫表單
        self.fill_login_form()
        submit_success = self.submit_login()

        if not submit_success:
            print("❌ 登入失敗 - 表單提交有誤")
            return False

        # 檢查登入結果
        success = self.check_login_success()
        if success:
            print("✅ 登入成功！")
            return True
        else:
            print("❌ 登入失敗")
            return False

    def fill_login_form(self):
        """填寫登入表單"""
        print("📝 填寫登入表單...")

        try:
            # 填入使用者帳號
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "txtUserID"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            print(f"✅ 已填入使用者帳號: {self.username}")

            # 填入密碼
            password_field = self.driver.find_element(By.ID, "txtUserPW")
            password_field.clear()
            password_field.send_keys(self.password)
            print("✅ 已填入密碼")

            # 處理驗證碼
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
                        print(f"✅ 已填入驗證碼: {captcha_text}")
                    else:
                        print("⚠️ 找不到驗證碼輸入框")
                else:
                    print("⚠️ 無法自動識別驗證碼，等待手動輸入...")
                    time.sleep(10)  # 給用戶10秒手動輸入驗證碼

            except Exception as captcha_e:
                print(f"⚠️ 處理驗證碼時發生錯誤: {captcha_e}")
                time.sleep(10)  # 給用戶手動處理的時間

            # 確保選擇「契約客戶專區 登入」
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
                    print("✅ 已選擇契約客戶專區登入")
                elif contract_radio:
                    print("✅ 契約客戶專區已預先選中")
                else:
                    print("⚠️ 無法找到契約客戶專區選項，使用預設值")
            except Exception as e:
                print(f"⚠️ 處理契約客戶專區選項時發生錯誤: {e}")

        except Exception as e:
            print(f"❌ 填寫表單失敗: {e}")

    def submit_login(self):
        """提交登入表單"""
        print("📤 提交登入表單...")

        try:
            # 找到登入按鈕並點擊
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
            login_button.click()

            # 等待頁面載入並處理可能的Alert
            time.sleep(5)  # 增加等待時間

            # 檢查是否有錯誤訊息在頁面上
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
                    print(f"⚠️ 頁面錯誤訊息: {'; '.join(set(error_messages))}")

            except Exception as msg_e:
                print(f"⚠️ 檢查錯誤訊息失敗: {msg_e}")

            # 檢查是否有Alert彈窗
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                print(f"⚠️ 出現警告彈窗: {alert_text}")
                alert.accept()  # 點擊確定
                return False  # 登入失敗
            except:
                pass  # 沒有Alert彈窗

            print("✅ 表單已提交")
            return True

        except Exception as e:
            print(f"❌ 提交表單失敗: {e}")
            return False

    def check_login_success(self):
        """檢查登入是否成功"""
        print("🔐 檢查登入狀態...")

        current_url = self.driver.current_url
        current_title = self.driver.title
        print(f"📍 當前 URL: {current_url}")
        print(f"📄 當前標題: {current_title}")

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
            print(f"⚠️ 發現登入失敗訊息: {', '.join(found_failures)}")
            return False

        # 檢查成功指標
        found_success = []
        for indicator in success_indicators:
            if indicator in page_source:
                found_success.append(indicator)

        # 檢查 URL 變化
        url_changed = current_url != self.url

        print(f"🔍 登入檢查結果:")
        print(f"   URL 是否改變: {'✅' if url_changed else '❌'}")
        print(f"   成功指標: {found_success if found_success else '無'}")
        print(f"   失敗指標: {found_failures if found_failures else '無'}")

        # 如果 URL 改變或找到成功指標，認為登入成功
        if url_changed or found_success:
            print("✅ 登入成功，已進入系統")
            return True
        else:
            # 截取部分頁面內容用於分析
            page_snippet = page_source[:1000] if len(page_source) > 1000 else page_source
            print(f"⚠️ 頁面內容片段: ...{page_snippet[-200:] if len(page_snippet) > 200 else page_snippet}")
            print("❌ 登入失敗或頁面異常")
            return False

    def navigate_to_payment_query(self):
        """導航到貨到付款查詢頁面 - 優先使用直接 URL"""
        print("🧭 導航到貨到付款查詢頁面...")

        try:
            # 等待登入完成
            print("⏳ 等待登入完成...")
            time.sleep(5)

            # 直接使用已知的正確 URL
            print("🎯 使用直接 URL 訪問貨到付款匯款明細表...")
            direct_success = self._try_direct_urls()

            if direct_success:
                return True

            # 如果直接 URL 失敗，嘗試框架導航
            print("⚠️ 直接 URL 失敗，嘗試框架導航...")
            frame_success = self._wait_for_frame_content()
            if frame_success:
                return self._navigate_in_frame()

            print("❌ 所有導航方法都失敗了")
            return False

        except Exception as e:
            print(f"❌ 導航失敗: {e}")
            return False

    def _wait_for_frame_content(self):
        """等待框架內容載入並尋找導航元素"""
        print("🔍 等待框架內容載入...")

        for attempt in range(30):  # 等待最多 30 秒
            try:
                # 檢查 iframe
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                if not iframes:
                    time.sleep(1)
                    continue

                # 切換到第一個 iframe
                main_iframe = iframes[0]
                self.driver.switch_to.frame(main_iframe)

                # 檢查框架內容
                frame_source = self.driver.page_source

                # 尋找導航相關的關鍵字
                navigation_keywords = [
                    "貨到付款", "匯款明細", "結算", "查詢", "報表", "COD",
                    "代收貨款", "財務報表", "統計分析"
                ]

                found_keywords = [kw for kw in navigation_keywords if kw in frame_source]

                if found_keywords:
                    print(f"   第 {attempt+1} 秒: 框架中發現關鍵字 {', '.join(found_keywords)}")

                    # 尋找可點擊元素
                    clickable_elements = self._find_payment_elements()

                    if clickable_elements:
                        print(f"   找到 {len(clickable_elements)} 個相關可點擊元素")
                        self.driver.switch_to.default_content()
                        return True

                self.driver.switch_to.default_content()
                time.sleep(1)

            except Exception as e:
                self.driver.switch_to.default_content()
                time.sleep(1)
                continue

        print("❌ 框架內容載入超時")
        return False

    def _find_payment_elements(self):
        """在當前框架中尋找支付相關元素 - 專門搜尋帳務選單"""
        payment_elements = []

        try:
            # 尋找所有可點擊元素
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
            all_divs = self.driver.find_elements(By.TAG_NAME, "div")
            all_spans = self.driver.find_elements(By.TAG_NAME, "span")
            all_tds = self.driver.find_elements(By.TAG_NAME, "td")
            all_lis = self.driver.find_elements(By.TAG_NAME, "li")

            all_clickables = all_links + all_buttons + all_inputs + all_divs + all_spans + all_tds + all_lis

            # 優先搜尋帳務相關的關鍵字
            accounting_keywords = [
                "帳務選單", "帳務", "財務", "會計"
            ]

            payment_keywords = [
                "貨到付款匯款明細表", "貨到付款", "匯款明細", "COD",
                "代收貨款", "付款", "收款", "匯款"
            ]

            # 先尋找帳務選單
            for element in all_clickables:
                try:
                    element_text = element.text or element.get_attribute('value') or element.get_attribute('title') or ''
                    element_text = element_text.strip()

                    # 優先匹配帳務選單
                    if any(keyword in element_text for keyword in accounting_keywords):
                        payment_elements.append({
                            'element': element,
                            'text': element_text,
                            'tag': element.tag_name,
                            'priority': 1  # 最高優先級
                        })
                        print(f"      找到帳務選單元素: '{element_text}' ({element.tag_name})")

                    # 然後匹配貨到付款相關
                    elif any(keyword in element_text for keyword in payment_keywords):
                        payment_elements.append({
                            'element': element,
                            'text': element_text,
                            'tag': element.tag_name,
                            'priority': 2  # 次要優先級
                        })
                        print(f"      找到支付相關元素: '{element_text}' ({element.tag_name})")

                except:
                    continue

            # 按優先級排序
            payment_elements.sort(key=lambda x: x.get('priority', 3))

        except Exception as e:
            print(f"   元素搜尋錯誤: {e}")

        return payment_elements

    def _navigate_in_frame(self):
        """在框架內執行導航 - 兩步驟：帳務選單 → 貨到付款匯款明細表"""
        print("🎯 在框架內執行兩步驟導航...")

        try:
            # 切換到 iframe
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if not iframes:
                return False

            self.driver.switch_to.frame(iframes[0])

            # 步驟1: 尋找並點擊帳務選單
            print("📋 步驟1: 尋找帳務選單...")
            accounting_success = self._click_accounting_menu()

            if not accounting_success:
                print("❌ 找不到帳務選單，嘗試直接尋找貨到付款選項...")
                payment_success = self._click_payment_option()
                self.driver.switch_to.default_content()
                return payment_success

            # 步驟2: 尋找並點擊貨到付款匯款明細表
            print("💰 步驟2: 尋找貨到付款匯款明細表...")
            time.sleep(3)  # 等待選單載入
            payment_success = self._click_payment_option()

            self.driver.switch_to.default_content()
            return payment_success

        except Exception as e:
            print(f"❌ 框架內導航失敗: {e}")
            self.driver.switch_to.default_content()
            return False

    def _click_accounting_menu(self):
        """點擊帳務選單"""
        try:
            accounting_keywords = ["帳務選單", "帳務", "財務", "會計"]

            # 尋找所有可能的元素類型
            all_elements = (
                self.driver.find_elements(By.TAG_NAME, "a") +
                self.driver.find_elements(By.TAG_NAME, "div") +
                self.driver.find_elements(By.TAG_NAME, "span") +
                self.driver.find_elements(By.TAG_NAME, "td") +
                self.driver.find_elements(By.TAG_NAME, "li") +
                self.driver.find_elements(By.TAG_NAME, "button")
            )

            for element in all_elements:
                try:
                    element_text = element.text or element.get_attribute('title') or ''
                    element_text = element_text.strip()

                    if any(keyword in element_text for keyword in accounting_keywords):
                        if element.is_displayed() and element.is_enabled():
                            print(f"   找到帳務選單: '{element_text}' ({element.tag_name})")
                            element.click()
                            print("   ✅ 已點擊帳務選單")
                            return True

                except Exception as e:
                    continue

            return False

        except Exception as e:
            print(f"   帳務選單點擊失敗: {e}")
            return False

    def _click_payment_option(self):
        """點擊貨到付款匯款明細表選項 - 專門尋找特定的 JavaScript 連結"""
        try:
            print("   🔍 尋找貨到付款匯款明細表的特殊連結...")

            # 專門尋找包含 JavaScript:replaceUrl 的連結
            javascript_links = self.driver.find_elements(By.XPATH,
                "//a[contains(@href, 'JavaScript:replaceUrl') or contains(@href, 'javascript:replaceUrl')]")

            print(f"   找到 {len(javascript_links)} 個 JavaScript 連結")

            for i, link in enumerate(javascript_links):
                try:
                    link_text = link.text or link.get_attribute('title') or ''
                    link_href = link.get_attribute('href') or ''
                    link_class = link.get_attribute('class') or ''

                    print(f"      連結 {i+1}: '{link_text.strip()}'")
                    print(f"         href: {link_href}")
                    print(f"         class: {link_class}")

                    # 檢查是否是貨到付款匯款明細表
                    if "貨到付款匯款明細表" in link_text:
                        print(f"   🎯 找到目標連結: '{link_text.strip()}'")

                        if link.is_displayed() and link.is_enabled():
                            print("   點擊 JavaScript 連結...")
                            link.click()
                            time.sleep(5)

                            current_url = self.driver.current_url
                            print(f"   📍 點擊後 URL: {current_url}")

                            # 檢查是否成功導航
                            if 'MsgCenter.aspx' not in current_url and 'ErrorMsg.aspx' not in current_url:
                                print("   ✅ 成功點擊貨到付款匯款明細表連結")
                                return True
                            else:
                                print("   ❌ 點擊後仍有權限或錯誤問題")

                        else:
                            print("   ❌ 連結不可見或不可點擊")

                except Exception as link_e:
                    print(f"      連結 {i+1} 處理失敗: {link_e}")
                    continue

            # 如果沒有找到 JavaScript 連結，嘗試尋找包含 FuncNo=165 的連結
            print("   🔍 尋找包含 FuncNo=165 的連結...")
            funcno_links = self.driver.find_elements(By.XPATH,
                "//a[contains(@href, 'FuncNo=165')]")

            if funcno_links:
                print(f"   找到 {len(funcno_links)} 個 FuncNo=165 連結")
                for i, link in enumerate(funcno_links):
                    try:
                        link_text = link.text or ''
                        print(f"      FuncNo 連結 {i+1}: '{link_text.strip()}'")

                        if link.is_displayed() and link.is_enabled():
                            print("   點擊 FuncNo=165 連結...")
                            link.click()
                            time.sleep(5)

                            current_url = self.driver.current_url
                            print(f"   📍 點擊後 URL: {current_url}")

                            if 'MsgCenter.aspx' not in current_url and 'ErrorMsg.aspx' not in current_url:
                                print("   ✅ 成功點擊 FuncNo=165 連結")
                                return True

                    except Exception as funcno_e:
                        print(f"      FuncNo 連結 {i+1} 處理失敗: {funcno_e}")
                        continue

            # 最後嘗試通用搜尋
            print("   🔍 執行通用搜尋...")
            all_links = self.driver.find_elements(By.TAG_NAME, "a")

            for link in all_links:
                try:
                    link_text = link.text or ''
                    if "貨到付款匯款明細表" in link_text or "貨到付款" in link_text:
                        if link.is_displayed() and link.is_enabled():
                            print(f"   找到通用連結: '{link_text.strip()}'")
                            link.click()
                            time.sleep(5)

                            current_url = self.driver.current_url
                            print(f"   📍 點擊後 URL: {current_url}")

                            if 'MsgCenter.aspx' not in current_url and 'ErrorMsg.aspx' not in current_url:
                                return True

                except Exception as e:
                    continue

            return False

        except Exception as e:
            print(f"   ❌ 貨到付款選項點擊失敗: {e}")
            return False

    def _try_direct_urls(self):
        """嘗試直接 URL 訪問 - 使用 RedirectFunc 和已知的 URL"""
        print("🔄 嘗試直接 URL 訪問...")

        # 使用 RedirectFunc 方式和直接 URL
        direct_urls = [
            # 使用 RedirectFunc 的正確方式
            'https://www.takkyubin.com.tw/YMTContract/aspx/RedirectFunc.aspx?FuncNo=165',
            # 其他可能的直接 URL
            'https://www.takkyubin.com.tw/YMTContract/aspx/CollectPaymentList3200T.aspx?Settlement=02&TimeOut=N',
            'https://www.takkyubin.com.tw/YMTContract/aspx/CollectPaymentList3200T.aspx',
        ]

        for url in direct_urls:
            try:
                print(f"   嘗試 URL: {url}")
                self.driver.get(url)
                time.sleep(5)  # 增加等待時間

                current_url = self.driver.current_url
                page_source = self.driver.page_source

                print(f"   導航後 URL: {current_url}")

                # 檢查是否成功（不是錯誤頁面）
                if ('ErrorMsg.aspx' not in current_url and
                    'Login.aspx' not in current_url and
                    'MsgCenter.aspx' not in current_url and  # 加入權限錯誤檢查
                    current_url != self.url):

                    # 檢查頁面內容是否包含相關關鍵字
                    success_keywords = ['匯款明細', '貨到付款', '結算', '代收貨款', 'COD', '明細表']
                    found_keywords = [kw for kw in success_keywords if kw in page_source]

                    if found_keywords:
                        print(f"✅ 成功導航到: {current_url}")
                        print(f"   找到關鍵字: {', '.join(found_keywords)}")
                        return True
                    else:
                        print(f"   頁面載入但未找到預期內容")

                elif 'MsgCenter.aspx' in current_url:
                    print(f"   ❌ 權限不足 - 無法存取此功能")

                else:
                    print(f"   導航失敗或重導向到錯誤頁面")

            except Exception as url_e:
                print(f"   ❌ URL 導航失敗: {url_e}")
                continue

        return False

    def get_latest_settlement_period(self):
        """獲取最新一期的結算區間 - 專門處理 ddlDate 選單"""
        print("📅 查找最新結算區間...")

        try:
            # 等待頁面載入
            time.sleep(3)

            # 專門尋找 ddlDate 選單
            date_selects = self.driver.find_elements(By.NAME, "ddlDate")

            if not date_selects:
                # 如果找不到 ddlDate，嘗試其他可能的名稱
                date_selects = self.driver.find_elements(By.CSS_SELECTOR,
                    "select[name*='date'], select[name*='Date'], select[id*='date'], select[id*='Date']")

            if not date_selects:
                # 最後嘗試所有 select 元素
                date_selects = self.driver.find_elements(By.TAG_NAME, "select")

            selected_period = False

            for i, select_element in enumerate(date_selects):
                try:
                    select_name = select_element.get_attribute('name') or f'select_{i}'
                    select_id = select_element.get_attribute('id') or 'no-id'

                    # 使用 Selenium 的 Select 類
                    from selenium.webdriver.support.ui import Select
                    select_obj = Select(select_element)
                    options = select_obj.options

                    if len(options) > 1:  # 確保有選項
                        print(f"   檢查選單: {select_name} (id: {select_id}) - {len(options)} 個選項")

                        # 顯示前幾個和最後幾個選項
                        print("      前3個選項:")
                        for j, option in enumerate(options[:3]):
                            option_text = option.text.strip()
                            option_value = option.get_attribute('value')
                            print(f"         {j+1}. {option_text} (value: {option_value})")

                        if len(options) > 6:
                            print("      最後3個選項:")
                            for j, option in enumerate(options[-3:], len(options)-2):
                                option_text = option.text.strip()
                                option_value = option.get_attribute('value')
                                print(f"         {j}. {option_text} (value: {option_value})")

                        # 檢查選項是否包含日期相關內容
                        option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
                        date_keywords = ['202', '2025', '2024', '結算', '期間', '月']

                        if any(keyword in ' '.join(option_texts) for keyword in date_keywords):
                            # 根據用戶指示：結算區間必須選擇第一個（非空選項）
                            valid_options = [opt for opt in options if opt.text.strip()]

                            if valid_options:
                                first_valid_option = valid_options[0]
                                period_text = first_valid_option.text.strip()
                                print(f"   🎯 選擇第一個結算區間: {period_text}")

                                try:
                                    # 找到第一個有效選項的索引
                                    first_valid_index = None
                                    for idx, opt in enumerate(options):
                                        if opt.text.strip():
                                            first_valid_index = idx
                                            break

                                    if first_valid_index is not None:
                                        select_obj.select_by_index(first_valid_index)
                                        time.sleep(2)
                                        selected_period = True
                                        # 儲存選中的結算區間
                                        self.current_settlement_period = period_text
                                        print("   ✅ 第一個結算區間選擇成功")
                                        break

                                except Exception as select_e:
                                    print(f"   ❌ 選擇失敗: {select_e}")
                                    # 嘗試直接點擊
                                    try:
                                        first_valid_option.click()
                                        time.sleep(2)
                                        selected_period = True
                                        # 儲存選中的結算區間
                                        self.current_settlement_period = period_text
                                        print("   ✅ 第一個結算區間點擊成功")
                                        break
                                    except Exception as click_e:
                                        print(f"   ❌ 點擊也失敗: {click_e}")
                        else:
                            print("   ⚠️ 選項不包含日期相關內容，跳過此選單")

                except Exception as e:
                    print(f"   處理選單 {i} 失敗: {e}")
                    continue

            if not selected_period:
                print("⚠️ 未能自動選擇結算期間，使用預設值繼續")

            return selected_period

        except Exception as e:
            print(f"❌ 獲取結算區間失敗: {e}")
            return False

    def format_settlement_period_for_filename(self, period_text):
        """將結算期間轉換為檔案名格式"""
        if not period_text:
            return "unknown_period"

        try:
            # 例如: "2025/09/04~2025/09/07" -> "20250904-20250907"
            # 使用正則表達式提取日期
            import re
            date_pattern = r'(\d{4})/(\d{2})/(\d{2})~(\d{4})/(\d{2})/(\d{2})'
            match = re.search(date_pattern, period_text)

            if match:
                start_year, start_month, start_day = match.group(1), match.group(2), match.group(3)
                end_year, end_month, end_day = match.group(4), match.group(5), match.group(6)

                # 格式化為: YYYYMMDD-YYYYMMDD
                start_date = f"{start_year}{start_month}{start_day}"
                end_date = f"{end_year}{end_month}{end_day}"

                return f"{start_date}-{end_date}"
            else:
                # 如果無法解析，嘗試其他格式或返回原始文字（去除特殊字符）
                safe_text = re.sub(r'[^\w\-]', '_', period_text)
                return safe_text
        except Exception as e:
            print(f"⚠️ 格式化結算期間失敗: {e}")
            # 返回安全的檔案名
            safe_text = re.sub(r'[^\w\-]', '_', period_text)
            return safe_text

    def download_cod_statement(self):
        """下載貨到付款匯款明細表"""
        print("📥 開始下載貨到付款匯款明細表...")

        try:
            # 等待頁面載入
            time.sleep(3)

            # 首先嘗試執行查詢（有些頁面需要先查詢才會顯示下載按鈕）
            print("🔍 執行查詢...")

            # 尋找並點擊查詢按鈕
            query_buttons_found = []

            # 方法1：尋找包含查詢文字的按鈕
            query_selectors = [
                "//button[contains(text(), '查詢')]",
                "//input[@type='button' and contains(@value, '查詢')]",
                "//input[@type='submit' and contains(@value, '查詢')]",
                "//a[contains(text(), '查詢')]",
                "//button[contains(text(), '搜尋')]",
                "//input[@type='button' and contains(@value, '搜尋')]"
            ]

            for selector in query_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            query_buttons_found.append({
                                'element': elem,
                                'text': elem.text or elem.get_attribute('value'),
                                'selector': selector
                            })
                except:
                    continue

            # 方法2：尋找所有按鈕，檢查文字內容
            if not query_buttons_found:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button") + \
                             self.driver.find_elements(By.CSS_SELECTOR, "input[type='button'], input[type='submit']")

                for button in all_buttons:
                    try:
                        button_text = button.text or button.get_attribute('value') or ''
                        if '查詢' in button_text or '搜尋' in button_text or 'query' in button_text.lower():
                            if button.is_displayed() and button.is_enabled():
                                query_buttons_found.append({
                                    'element': button,
                                    'text': button_text,
                                    'selector': 'all_buttons_scan'
                                })
                    except:
                        continue

            # 嘗試點擊搜尋按鈕（專門尋找「搜尋」而不是「查詢」）
            query_executed = False
            search_buttons_found = []

            # 專門尋找「搜尋」按鈕
            search_selectors = [
                "//button[contains(text(), '搜尋')]",
                "//input[@type='button' and contains(@value, '搜尋')]",
                "//input[@type='submit' and contains(@value, '搜尋')]",
                "//a[contains(text(), '搜尋')]"
            ]

            for selector in search_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            search_buttons_found.append({
                                'element': elem,
                                'text': elem.text or elem.get_attribute('value'),
                                'selector': selector
                            })
                except:
                    continue

            # 如果沒找到「搜尋」，再找「查詢」
            if not search_buttons_found:
                for i, btn_info in enumerate(query_buttons_found):
                    if '搜尋' in btn_info['text']:
                        search_buttons_found.append(btn_info)

            # 執行搜尋
            if search_buttons_found:
                print(f"   找到 {len(search_buttons_found)} 個搜尋按鈕")
                for i, btn_info in enumerate(search_buttons_found):
                    try:
                        print(f"   點擊搜尋按鈕: '{btn_info['text']}'")
                        # 使用 JavaScript 點擊以確保成功
                        self.driver.execute_script("arguments[0].click();", btn_info['element'])
                        print("   ✅ 搜尋按鈕已點擊，等待 AJAX 載入...")
                        time.sleep(10)  # 等待 AJAX 完成載入
                        query_executed = True
                        break
                    except Exception as click_e:
                        print(f"   ❌ 搜尋按鈕點擊失敗: {click_e}")
                        continue
            elif query_buttons_found:
                # 如果沒有搜尋按鈕，嘗試查詢按鈕
                print(f"   未找到搜尋按鈕，嘗試 {len(query_buttons_found)} 個查詢按鈕")
                for i, btn_info in enumerate(query_buttons_found):
                    try:
                        print(f"   點擊查詢按鈕: '{btn_info['text']}'")
                        self.driver.execute_script("arguments[0].click();", btn_info['element'])
                        print("   ✅ 查詢按鈕已點擊，等待 AJAX 載入...")
                        time.sleep(10)
                        query_executed = True
                        break
                    except Exception as click_e:
                        print(f"   ❌ 查詢按鈕點擊失敗: {click_e}")
                        continue
            else:
                print("   ❌ 未找到搜尋或查詢按鈕")

            # AJAX 載入完成後，尋找「對帳單下載」按鈕
            print("🔍 尋找對帳單下載按鈕...")

            # 專門尋找對帳單下載按鈕（基於用戶提供的確切元素）
            download_selectors = [
                # 優先使用 ID 選擇器
                ("id", "lnkbtnDownload"),
                # 備選：XPath 選擇器
                ("xpath", "//a[@id='lnkbtnDownload']"),
                ("xpath", "//a[contains(text(), '對帳單下載')]"),
                # 其他可能的下載按鈕
                ("xpath", "//button[contains(text(), '對帳單下載')]"),
                ("xpath", "//input[contains(@value, '對帳單下載')]"),
                ("xpath", "//a[contains(text(), '下載')]"),
                ("xpath", "//button[contains(text(), '下載')]"),
                ("xpath", "//input[contains(@value, '下載')]")
            ]

            download_buttons_found = []

            # 等待一段時間確保 AJAX 完全載入
            if query_executed:
                print("   等待 AJAX 內容完全載入...")
                time.sleep(5)

            for selector_type, selector_value in download_selectors:
                try:
                    if selector_type == "id":
                        elements = [self.driver.find_element(By.ID, selector_value)]
                    elif selector_type == "xpath":
                        elements = self.driver.find_elements(By.XPATH, selector_value)
                    else:
                        continue

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text or element.get_attribute('value') or ''
                            element_id = element.get_attribute('id') or ''
                            download_buttons_found.append({
                                'element': element,
                                'text': element_text,
                                'id': element_id,
                                'selector': f"{selector_type}:{selector_value}"
                            })
                            print(f"   找到下載按鈕: '{element_text}' (id: {element_id})")
                except:
                    continue

            # 如果沒找到明確的下載按鈕，掃描所有可點擊元素
            if not download_buttons_found:
                print("   未找到明確的下載按鈕，掃描所有可點擊元素...")
                all_clickable = (
                    self.driver.find_elements(By.TAG_NAME, "button") +
                    self.driver.find_elements(By.TAG_NAME, "a") +
                    self.driver.find_elements(By.CSS_SELECTOR, "input[type='button'], input[type='submit']")
                )

                for element in all_clickable:
                    try:
                        element_text = element.text or element.get_attribute('value') or ''
                        download_keywords = ['對帳單', '下載', '匯出', 'Excel', 'download', 'export']

                        if any(kw in element_text for kw in download_keywords):
                            if element.is_displayed() and element.is_enabled():
                                download_buttons_found.append({
                                    'element': element,
                                    'text': element_text,
                                    'selector': 'scan_all'
                                })
                                print(f"   掃描找到相關按鈕: '{element_text}'")
                    except:
                        continue

            # 嘗試點擊下載按鈕
            download_success = False
            if download_buttons_found:
                print(f"📥 找到 {len(download_buttons_found)} 個可能的下載按鈕")

                # 優先點擊包含「對帳單」的按鈕
                priority_buttons = [btn for btn in download_buttons_found if '對帳單' in btn['text']]
                other_buttons = [btn for btn in download_buttons_found if '對帳單' not in btn['text']]

                all_download_buttons = priority_buttons + other_buttons

                for i, btn_info in enumerate(all_download_buttons):
                    try:
                        print(f"   嘗試點擊下載按鈕 {i+1}: '{btn_info['text']}'")

                        # 記錄下載前的檔案
                        files_before = set(self.download_dir.glob("*"))

                        # 點擊下載按鈕
                        self.driver.execute_script("arguments[0].click();", btn_info['element'])
                        print("   ✅ 下載按鈕已點擊，等待檔案下載...")

                        # 等待下載完成
                        max_wait_time = 30  # 最多等待30秒
                        downloaded_files = []
                        for wait_time in range(max_wait_time):
                            time.sleep(1)
                            files_after = set(self.download_dir.glob("*"))
                            new_files = files_after - files_before

                            if new_files:
                                for new_file in new_files:
                                    if new_file.suffix.lower() in ['.xls', '.xlsx', '.csv']:
                                        print(f"   🎉 下載成功: {new_file.name}")
                                        downloaded_files.append(new_file)
                                        download_success = True
                                        break

                            if download_success:
                                break

                        if download_success:
                            break
                        else:
                            print(f"   ⚠️ 按鈕 {i+1} 點擊後 {max_wait_time} 秒內未檢測到新檔案")

                    except Exception as click_e:
                        print(f"   ❌ 下載按鈕 {i+1} 點擊失敗: {click_e}")
                        continue
            else:
                print("   ❌ 未找到任何下載按鈕")

            if download_success:
                # 生成目標檔案名
                period_suffix = self.format_settlement_period_for_filename(self.current_settlement_period)
                target_filename = f"{self.username}_{period_suffix}.xlsx"
                target_file_path = self.download_dir / target_filename

                # 如果目標檔案已存在，先刪除它
                if target_file_path.exists():
                    print(f"   📝 覆蓋現有檔案: {target_filename}")
                    target_file_path.unlink()

                # 處理當前下載的檔案
                if downloaded_files:
                    # 取最新下載的檔案
                    latest_file = downloaded_files[0]  # 通常只有一個檔案

                    try:
                        # 重新命名為目標檔案名
                        latest_file.rename(target_file_path)
                        print(f"   📝 檔案已重新命名: {latest_file.name} -> {target_filename}")
                        return [target_file_path]

                    except Exception as rename_e:
                        print(f"   ⚠️ 檔案重新命名失敗: {rename_e}")
                        return [latest_file]

                return []
            else:
                return []

        except Exception as e:
            print(f"❌ 下載失敗: {e}")
            return []

    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            print("🔚 瀏覽器已關閉")

    def run_full_process(self):
        """執行完整的自動化流程"""
        success = False
        downloaded_files = []

        try:
            print("=" * 60)
            print(f"🤖 開始執行黑貓宅急便自動下載流程 (帳號: {self.username})")
            print("=" * 60)

            # 1. 初始化瀏覽器
            self.init_browser()

            # 2. 登入
            login_success = self.login()
            if not login_success:
                print(f"❌ 帳號 {self.username} 登入失敗")
                return {
                    "success": False,
                    "username": self.username,
                    "error": "登入失敗",
                    "downloads": []
                }

            # 3. 導航到貨到付款查詢頁面
            nav_success = self.navigate_to_payment_query()
            if not nav_success:
                print(f"❌ 帳號 {self.username} 導航失敗")
                return {
                    "success": False,
                    "username": self.username,
                    "error": "導航失敗",
                    "downloads": []
                }

            # 4. 獲取最新結算期間
            period_success = self.get_latest_settlement_period()
            if not period_success:
                print(f"⚠️ 帳號 {self.username} 未能選擇結算期間，但繼續執行")

            # 5. 下載貨到付款匯款明細表
            downloaded_files = self.download_cod_statement()

            if downloaded_files:
                print(f"🎉 帳號 {self.username} 自動化流程完成！下載了 {len(downloaded_files)} 個檔案")
                success = True
            else:
                print(f"⚠️ 帳號 {self.username} 沒有下載到任何檔案")

            return {
                "success": success,
                "username": self.username,
                "downloads": [str(f) for f in downloaded_files]  # 轉換 PosixPath 為字串
            }

        except Exception as e:
            print(f"💥 帳號 {self.username} 流程執行失敗: {e}")
            return {
                "success": False,
                "username": self.username,
                "error": str(e),
                "downloads": [str(f) for f in downloaded_files]  # 轉換 PosixPath 為字串
            }
        finally:
            self.close()


class MultiAccountManager:
    """多帳號管理器"""

    def __init__(self, config_file="accounts.json"):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        """載入設定檔"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"⛔ 設定檔 '{self.config_file}' 不存在！\n"
                "📝 請建立 accounts.json 檔案，包含 accounts 和 settings 設定"
            )

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            if "accounts" not in self.config or not self.config["accounts"]:
                raise ValueError("⛔ 設定檔中沒有找到帳號資訊！")

            print(f"✅ 已載入設定檔: {self.config_file}")

        except json.JSONDecodeError as e:
            raise ValueError(f"⛔ 設定檔格式錯誤: {e}")
        except Exception as e:
            raise RuntimeError(f"⛔ 載入設定檔失敗: {e}")

    def get_enabled_accounts(self):
        """取得啟用的帳號列表"""
        return [acc for acc in self.config["accounts"] if acc.get("enabled", True)]

    def run_all_accounts(self, headless_override=None):
        """執行所有啟用的帳號"""
        accounts = self.get_enabled_accounts()
        results = []
        settings = self.config.get("settings", {})

        print("\n" + "=" * 80)
        print(f"🚀 開始執行多帳號黑貓宅急便自動下載 (共 {len(accounts)} 個帳號)")
        print("=" * 80)

        for i, account in enumerate(accounts, 1):
            username = account["username"]
            password = account["password"]

            print(f"\n📊 [{i}/{len(accounts)}] 處理帳號: {username}")
            print("-" * 50)

            try:
                # 如果有命令列參數覆寫，則使用該設定
                use_headless = headless_override if headless_override is not None else settings.get("headless", False)

                scraper = TakkyubinSeleniumScraper(
                    username=username,
                    password=password,
                    headless=use_headless,
                    download_base_dir=settings.get("download_base_dir", "downloads")
                )

                result = scraper.run_full_process()
                results.append(result)

                # 帳號間暫停一下避免過於頻繁
                if i < len(accounts):
                    print("⏳ 等待 3 秒後處理下一個帳號...")
                    time.sleep(3)

            except Exception as e:
                print(f"💥 帳號 {username} 處理失敗: {e}")
                results.append({
                    "success": False,
                    "username": username,
                    "error": str(e),
                    "downloads": []
                })
                continue

        # 生成總報告
        self.generate_summary_report(results)
        return results

    def generate_summary_report(self, results):
        """生成總體執行報告"""
        print("\n" + "=" * 80)
        print("📋 多帳號執行總結報告")
        print("=" * 80)

        successful_accounts = [r for r in results if r["success"]]
        failed_accounts = [r for r in results if not r["success"]]
        total_downloads = sum(len(r["downloads"]) for r in results)

        print(f"📊 執行統計:")
        print(f"   總帳號數: {len(results)}")
        print(f"   成功帳號: {len(successful_accounts)}")
        print(f"   失敗帳號: {len(failed_accounts)}")
        print(f"   總下載檔案: {total_downloads}")

        if successful_accounts:
            print(f"\n✅ 成功帳號詳情:")
            for result in successful_accounts:
                username = result["username"]
                download_count = len(result["downloads"])
                print(f"   🔸 {username}: 成功下載 {download_count} 個檔案")

        if failed_accounts:
            print(f"\n❌ 失敗帳號詳情:")
            for result in failed_accounts:
                username = result["username"]
                error = result.get("error", "未知錯誤")
                print(f"   🔸 {username}: {error}")

        # 保存詳細報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"takkyubin_report_{timestamp}.json"
        report_file = Path("reports") / report_filename

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_accounts": len(results),
                "successful_accounts": len(successful_accounts),
                "failed_accounts": len(failed_accounts),
                "total_downloads": total_downloads,
                "details": results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 詳細報告已保存: {report_file}")
        print("=" * 80)


def main():
    """主程式入口"""
    import argparse

    parser = argparse.ArgumentParser(description='黑貓宅急便自動下載工具')
    parser.add_argument('--headless', action='store_true', help='使用無頭模式')

    args = parser.parse_args()

    try:
        print("🐱 黑貓宅急便自動下載工具")

        manager = MultiAccountManager("accounts.json")
        manager.run_all_accounts(headless_override=args.headless)

        return 0

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"⛔ 錯誤: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⛔ 使用者中斷執行")
        return 1
    except Exception as e:
        print(f"⛔ 未知錯誤: {e}")
        return 1


if __name__ == "__main__":
    main()