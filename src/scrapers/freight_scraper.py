#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time

# 導入共用模組
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from src.utils.windows_encoding_utils import safe_print, check_pythonunbuffered
from src.core.base_scraper import BaseScraper
from src.core.multi_account_manager import MultiAccountManager

# 檢查環境變數
check_pythonunbuffered()

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
import requests
import io

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FreightScraper(BaseScraper):
    """
    黑貓宅急便運費查詢自動下載工具
    繼承自 BaseScraper，複用登入和驗證碼處理功能
    """

    # 設定環境變數 key
    DOWNLOAD_DIR_ENV_KEY = "FREIGHT_DOWNLOAD_WORK_DIR"
    DOWNLOAD_OK_DIR_ENV_KEY = "FREIGHT_DOWNLOAD_OK_DIR"

    def __init__(
        self, username, password, headless=None, start_date=None, end_date=None, quiet_init=False
    ):
        # 呼叫父類建構子
        super().__init__(username, password, headless)

        # FreightScraper 特有的屬性
        # 日期範圍設定（格式：YYYYMMDD）
        self.start_date = start_date
        self.end_date = end_date

        # 如果沒有指定日期，預設使用上個月的完整範圍
        if not self.start_date:
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            self.start_date = last_month.replace(day=1).strftime("%Y%m%d")

        if not self.end_date:
            # 如果只指定了開始日期，預設結束日期為同月最後一天
            if self.start_date:
                start_dt = datetime.strptime(self.start_date, "%Y%m%d")
                if start_dt.month == 12:
                    last_day = start_dt.replace(year=start_dt.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    last_day = start_dt.replace(month=start_dt.month + 1, day=1) - timedelta(days=1)
                self.end_date = last_day.strftime("%Y%m%d")
            else:
                # 取得上個月的最後一天
                last_month = datetime.now().replace(day=1) - timedelta(days=1)
                self.end_date = last_month.strftime("%Y%m%d")

        # 只在非靜默模式下顯示（多帳號模式已在開頭統一顯示）
        if not quiet_init:
            safe_print(f"📅 查詢日期範圍: {self.start_date} - {self.end_date}")

    def navigate_to_freight_query(self):
        """導航到對帳單明細頁面 - 包含完整重試機制和 session timeout 處理"""
        safe_print("🧭 導航到對帳單明細頁面...")

        max_attempts = 3  # 最多嘗試 3 次

        for attempt in range(max_attempts):
            if attempt > 0:
                safe_print(f"🔄 第 {attempt + 1} 次嘗試導航...")
                # 移除固定等待，後續的智慧等待已足夠

            try:
                # 智慧等待登入完成
                safe_print("⏳ 等待登入完成...")
                self.smart_wait_for_url_change(timeout=10)

                # 檢查當前會話狀態
                if self._check_session_timeout():
                    safe_print("⏰ 檢測到會話超時，嘗試重新登入...")
                    if not self._handle_session_timeout():
                        safe_print("❌ 重新登入失敗，跳過本次嘗試")
                        continue

                # 方法1: 嘗試直接使用 URL
                safe_print("🎯 使用直接 URL 訪問對帳單明細頁面...")
                direct_success = self._try_direct_freight_url()

                # 檢查是否遇到安全警告
                if self.security_warning_encountered:
                    safe_print("🚨 檢測到密碼安全警告，終止當前帳號處理")
                    return False

                if direct_success:
                    safe_print("✅ 直接 URL 導航成功")
                    return True

                # 如果直接 URL 失敗，再次檢查是否為會話超時
                if self._check_session_timeout():
                    safe_print("⏰ 直接 URL 失敗後檢測到會話超時")
                    if self._handle_session_timeout():
                        safe_print("✅ 重新登入成功，重試直接 URL...")
                        # 重新嘗試直接 URL
                        direct_success = self._try_direct_freight_url()

                        # 檢查是否遇到安全警告
                        if self.security_warning_encountered:
                            safe_print("🚨 檢測到密碼安全警告，終止當前帳號處理")
                            return False

                        if direct_success:
                            safe_print("✅ 重新登入後直接 URL 導航成功")
                            return True

                # 方法2: 嘗試框架導航
                safe_print("⚠️ 直接 URL 失敗，嘗試框架導航...")
                frame_success = self._navigate_through_menu()
                if frame_success:
                    safe_print("✅ 框架導航成功")
                    return True
                else:
                    safe_print("❌ 框架導航失敗")

                # 如果所有方法都失敗，嘗試回到主頁重新開始
                if attempt < max_attempts - 1:  # 不是最後一次嘗試
                    safe_print("🏠 所有導航方法失敗，回到主頁重新開始...")
                    try:
                        # 回到合約客戶專區首頁
                        home_url = "https://www.takkyubin.com.tw/YMTContract/default.aspx"
                        self.driver.get(home_url)
                        self.smart_wait_for_url_change(timeout=5)

                        # 檢查是否需要重新登入
                        if "Login.aspx" in self.driver.current_url:
                            safe_print("🔑 需要重新登入...")
                            self.login()
                            self.smart_wait_for_url_change(timeout=10)
                    except Exception as reset_e:
                        safe_print(f"❌ 重置會話失敗: {reset_e}")

            except Exception as e:
                safe_print(f"❌ 第 {attempt + 1} 次導航嘗試失敗: {e}")
                if attempt < max_attempts - 1:
                    continue

        safe_print("❌ 所有導航嘗試都失敗了")
        return False

    def _try_direct_freight_url(self):
        """嘗試直接訪問對帳單明細頁面 - 包含重試機制和 session timeout 處理"""
        try:
            # 基於用戶提供的正確 URL 格式，參考 PaymentScraper 的成功模式
            direct_urls = [
                # 使用 RedirectFunc 的正確方式（基於用戶提供的 FuncNo=166）
                "https://www.takkyubin.com.tw/YMTContract/aspx/RedirectFunc.aspx?FuncNo=166",
                # 其他可能的直接 URL
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentList.aspx?SudaType=01&TimeOut=N",
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentList.aspx",
                # 添加更多後備 URL
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentList.aspx?SudaType=02",
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentList.aspx?SudaType=03",
            ]

            max_retries = 2  # 每個 URL 最多重試 2 次

            for url_index, full_url in enumerate(direct_urls):
                safe_print(f"🎯 嘗試 URL {url_index + 1}/{len(direct_urls)}: {full_url}")

                for retry in range(max_retries + 1):
                    if retry > 0:
                        print(f"      重試 {retry}/{max_retries}...")

                    try:
                        self.driver.get(full_url)
                        # 短暫等待以檢測 alert（保留此處固定等待，因 alert 檢測需要）
                        time.sleep(0.5)

                        # 處理可能的 alert 彈窗
                        alert_result = self._handle_alerts()
                        if alert_result == "SECURITY_WARNING":
                            print("   🚨 檢測到密碼安全警告，終止當前帳號處理")
                            return False  # 終止當前帳號處理
                        elif alert_result:
                            print("   🔔 處理了安全提示或其他彈窗")

                        # 智慧等待頁面完全載入（document.readyState == 'complete'）
                        self.smart_wait(
                            lambda d: d.execute_script("return document.readyState") == "complete",
                            timeout=10,
                            error_message="頁面載入完成",
                        )

                        current_url = self.driver.current_url
                        print(f"   導航後 URL: {current_url}")

                        # 檢查是否為會話超時
                        if self._check_session_timeout():
                            print("   ⏰ 檢測到會話超時，嘗試重新登入...")
                            if self._handle_session_timeout():
                                print("   ✅ 重新登入成功，重試導航...")
                                # 重新嘗試當前 URL
                                self.driver.get(full_url)
                                self.smart_wait(1)  # 等待頁面穩定
                            else:
                                print("   ❌ 重新登入失敗")
                                continue

                        current_url = self.driver.current_url

                        # 檢查是否成功到達對帳單明細頁面
                        if self._is_freight_page():
                            safe_print("✅ 直接 URL 訪問成功")
                            return True
                        else:
                            print("   ❌ 未能到達對帳單明細頁面")

                        # 如果這次嘗試失敗，但還有重試機會，則稍等片刻再重試
                        if retry < max_retries:
                            time.sleep(2)
                        else:
                            break  # 跳出重試循環，嘗試下一個 URL

                    except Exception as e:
                        print(f"   ❌ URL 導航失敗 (嘗試 {retry + 1}): {e}")

                        # 檢查是否為 alert 相關的異常
                        if "alert" in str(e).lower() or "unexpected alert" in str(e).lower():
                            # 嘗試處理 alert
                            alert_result = self._handle_alerts()
                            if alert_result == "SECURITY_WARNING":
                                print("   🚨 檢測到密碼安全警告，終止當前帳號處理")
                                return False  # 終止當前帳號處理

                        if retry < max_retries:
                            time.sleep(2)
                        continue

            print("   ❌ 所有直接 URL 嘗試都失敗")
            return False

        except Exception as e:
            safe_print(f"❌ 直接 URL 方法失敗: {e}")
            return False

    def _navigate_through_menu(self):
        """通過選單導航到對帳單明細"""
        try:
            # 等待並尋找框架
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            if not iframes:
                safe_print("❌ 找不到 iframe")
                return False

            # 切換到主框架
            self.driver.switch_to.frame(iframes[0])
            safe_print("✅ 已切換到主框架")

            # 步驟1: 尋找並點擊「帳務」選單
            accounting_success = self._click_accounting_menu()
            if not accounting_success:
                safe_print("❌ 找不到帳務選單")
                self.driver.switch_to.default_content()
                return False

            self.smart_wait(2)  # 等待選單展開

            # 步驟2: 尋找並點擊「對帳單明細」
            statement_success = self._click_statement_detail_menu()
            if not statement_success:
                safe_print("❌ 找不到對帳單明細選項")
                self.driver.switch_to.default_content()
                return False

            # 智慧等待頁面載入
            self.smart_wait(2)

            self.driver.switch_to.default_content()
            return self._is_freight_page()

        except Exception as e:
            safe_print(f"❌ 選單導航失敗: {e}")
            self.driver.switch_to.default_content()
            return False

    def _click_accounting_menu(self):
        """點擊帳務選單"""
        try:
            accounting_keywords = ["帳務", "財務", "會計"]

            # 尋找所有可能的帳務選單元素
            all_elements = (
                self.driver.find_elements(By.TAG_NAME, "a")
                + self.driver.find_elements(By.TAG_NAME, "div")
                + self.driver.find_elements(By.TAG_NAME, "span")
                + self.driver.find_elements(By.TAG_NAME, "td")
                + self.driver.find_elements(By.TAG_NAME, "li")
            )

            for element in all_elements:
                try:
                    element_text = element.text or element.get_attribute("title") or ""
                    element_text = element_text.strip()

                    if any(keyword in element_text for keyword in accounting_keywords):
                        if element.is_displayed() and element.is_enabled():
                            safe_print(f"✅ 找到帳務選單: '{element_text}'")
                            element.click()
                            return True
                except:
                    continue

            return False

        except Exception as e:
            safe_print(f"❌ 點擊帳務選單失敗: {e}")
            return False

    def _click_statement_detail_menu(self):
        """點擊對帳單明細選項"""
        try:
            # 基於用戶提供的連結特徵
            statement_keywords = ["對帳單明細", "對帳單", "明細"]

            # 特別尋找包含 RedirectFunc.aspx?FuncNo=166 的連結
            links = self.driver.find_elements(By.TAG_NAME, "a")

            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    text = link.text or ""

                    # 優先匹配特定的 URL 模式
                    if "RedirectFunc.aspx?FuncNo=166" in href:
                        if link.is_displayed() and link.is_enabled():
                            safe_print(f"✅ 找到對帳單明細連結: '{text}' ({href})")
                            link.click()
                            return True

                    # 備用匹配文字內容
                    elif any(keyword in text for keyword in statement_keywords):
                        if link.is_displayed() and link.is_enabled():
                            safe_print(f"✅ 找到對帳單明細選項: '{text}'")
                            link.click()
                            return True

                except:
                    continue

            return False

        except Exception as e:
            safe_print(f"❌ 點擊對帳單明細選項失敗: {e}")
            return False

    def _is_freight_page(self):
        """檢查是否成功到達對帳單明細頁面"""
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source

            # 檢查 URL 是否包含預期的頁面標識
            url_indicators = ["SudaPaymentList.aspx", "SudaType=01"]

            # 基於真實 HTML 結構的精確內容檢查
            content_indicators = [
                "速達應付帳款查詢",  # 基於 HTML 中的 lblSudaType
                "發票日期區間",  # 基於表格標題
                "txtDateS",  # 開始日期輸入框 ID
                "txtDateE",  # 結束日期輸入框 ID
                "btnSearch",  # 搜尋按鈕 ID
                "客戶帳號",  # 基於表格標題
                "查詢種類",  # 基於表格標題
            ]

            url_match = any(indicator in current_url for indicator in url_indicators)
            content_match = any(indicator in page_source for indicator in content_indicators)

            # 更精確的元素檢查
            element_check = False
            try:
                # 檢查關鍵元素是否存在
                key_elements = [("ID", "txtDateS"), ("ID", "txtDateE"), ("ID", "btnSearch")]

                found_elements = 0
                for method, selector in key_elements:
                    try:
                        if method == "ID":
                            element = self.driver.find_element(By.ID, selector)
                            if element:
                                found_elements += 1
                    except:
                        continue

                element_check = found_elements >= 2  # 至少找到 2 個關鍵元素

            except Exception as e:
                pass

            safe_print(f"📍 URL 檢查: {'✅' if url_match else '❌'}")
            safe_print(f"📄 內容檢查: {'✅' if content_match else '❌'}")
            safe_print(f"🎯 元素檢查: {'✅' if element_check else '❌'}")

            return url_match or content_match or element_check

        except Exception as e:
            safe_print(f"❌ 頁面檢查失敗: {e}")
            return False

    def set_invoice_date_range(self):
        """設定發票日期區間為指定的日期範圍"""
        safe_print("📅 設定發票日期區間...")

        try:
            # 直接使用 YYYYMMDD 格式的日期
            start_date_str = self.start_date
            end_date_str = self.end_date

            safe_print(f"📅 設定日期範圍: {start_date_str} - {end_date_str}")

            # 基於真實 HTML 結構的精確選擇器
            start_date_input = None
            end_date_input = None

            # 方法1: 使用確切的 name 和 id
            try:
                start_date_input = self.driver.find_element(By.ID, "txtDateS")
                end_date_input = self.driver.find_element(By.ID, "txtDateE")
                safe_print("✅ 找到確切的日期輸入框 (txtDateS, txtDateE)")
            except:
                safe_print("⚠️ 未找到確切的日期輸入框，嘗試備用方法")

                # 方法2: 使用 name 屬性
                try:
                    start_date_input = self.driver.find_element(By.NAME, "txtDateS")
                    end_date_input = self.driver.find_element(By.NAME, "txtDateE")
                    safe_print("✅ 通過 name 屬性找到日期輸入框")
                except:
                    # 方法3: 通用搜索
                    date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    if len(date_inputs) >= 2:
                        start_date_input = date_inputs[0]
                        end_date_input = date_inputs[1]
                        safe_print(f"✅ 通過通用搜索找到 {len(date_inputs)} 個輸入框")

            # 填入日期範圍
            if start_date_input and end_date_input:
                try:
                    # 清空並填入開始日期
                    start_date_input.clear()
                    start_date_input.send_keys(start_date_str)
                    safe_print(f"✅ 已設定開始日期: {start_date_str}")

                    # 清空並填入結束日期
                    end_date_input.clear()
                    end_date_input.send_keys(end_date_str)
                    safe_print(f"✅ 已設定結束日期: {end_date_str}")

                    return True

                except Exception as e:
                    safe_print(f"⚠️ 填入日期失敗: {e}")
                    return False

            else:
                safe_print("❌ 未找到日期輸入框")
                return False

        except Exception as e:
            safe_print(f"❌ 日期設定失敗: {e}")
            return False

    def search_and_download_statement(self):
        """搜尋並下載對帳單明細"""
        safe_print("🔍 開始搜尋並下載對帳單明細...")

        try:
            # 步驟1: 點擊搜尋按鈕
            search_success = self._click_search_button()
            if not search_success:
                safe_print("❌ 搜尋失敗")
                return []

            # 步驟2: 等待 AJAX 搜尋結果載入
            download_button_ready = self._wait_for_ajax_results()
            if not download_button_ready:
                safe_print("⚠️ AJAX 搜尋結果載入超時或無資料")
                return []

            # 步驟3: 尋找並點擊下載按鈕
            downloaded_files = self._download_results()

            return downloaded_files

        except Exception as e:
            safe_print(f"❌ 搜尋和下載失敗: {e}")
            return []

    def _wait_for_ajax_results(self, timeout=30):
        """等待 AJAX 搜尋結果載入並檢查下載按鈕是否出現"""
        safe_print("⏳ 等待 AJAX 搜尋結果載入...")

        try:
            # 使用智慧等待檢查下載按鈕
            download_button = self.smart_wait_for_element(By.ID, "btnDownload", timeout=timeout, visible=True)

            if download_button:
                safe_print("✅ AJAX 載入完成，下載按鈕已準備就緒")
                return True
            else:
                safe_print("⚠️ AJAX 結果載入超時，可能沒有符合條件的資料")
                return False

        except Exception as e:
            safe_print(f"⚠️ AJAX 結果載入失敗: {e}")
            return False

    def _click_search_button(self):
        """點擊搜尋按鈕並處理 AJAX 請求"""
        safe_print("🔍 點擊搜尋按鈕...")

        try:
            # 使用確切的 btnSearch ID（基於真實 HTML）
            search_button = None
            try:
                search_button = self.driver.find_element(By.ID, "btnSearch")
                if search_button and search_button.is_displayed() and search_button.is_enabled():
                    safe_print("✅ 找到搜尋按鈕: btnSearch (ID)")
                else:
                    safe_print("⚠️ btnSearch 按鈕存在但不可用")
                    return False
            except Exception as e:
                safe_print(f"❌ 找不到 btnSearch 按鈕: {e}")

                # 備用方法
                backup_selectors = [
                    ("NAME", "btnSearch"),
                    ("VALUE", " 搜尋 "),
                    ("CSS", "input[type='submit'][value*='搜尋']"),
                ]

                for method, selector in backup_selectors:
                    try:
                        if method == "NAME":
                            search_button = self.driver.find_element(By.NAME, selector)
                        elif method == "VALUE":
                            search_button = self.driver.find_element(By.CSS_SELECTOR, f"input[value='{selector}']")
                        elif method == "CSS":
                            search_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                        if search_button and search_button.is_displayed() and search_button.is_enabled():
                            safe_print(f"✅ 找到備用搜尋按鈕: {method}={selector}")
                            break

                    except Exception:
                        continue

            if not search_button:
                safe_print("❌ 找不到搜尋按鈕")
                return False

            # 點擊搜尋按鈕觸發 AJAX 請求
            safe_print("🖱️ 點擊搜尋按鈕 (將觸發 AJAX 請求)...")
            self.driver.execute_script("arguments[0].click();", search_button)
            safe_print("✅ 已點擊搜尋按鈕，AJAX 請求已發送")

            # 智慧等待 AJAX 開始
            self.smart_wait_for_ajax(timeout=15)
            return True

        except Exception as e:
            safe_print(f"❌ 點擊搜尋按鈕失敗: {e}")
            return False

    def _download_results(self):
        """下載搜尋結果 - 修正版：先點擊發票編號進入詳細頁面"""
        safe_print("📥 開始下載搜尋結果...")

        # 設定本次下載的 UUID 臨時目錄
        self.setup_temp_download_dir()

        try:
            # 首先解析表格資料以獲取發票資訊
            invoice_data = self._parse_invoice_table()

            # 如果沒有發票資料，直接返回，不執行下載
            if not invoice_data:
                safe_print("⚠️ 沒有找到發票資料，跳過下載")
                return []

            safe_print(f"✅ 找到 {len(invoice_data)} 筆發票資料，準備進入詳細頁面下載")

            all_downloaded_files = []

            # 對每一筆發票資料進行處理
            for idx, invoice_info in enumerate(invoice_data, 1):
                safe_print(f"📄 處理第 {idx}/{len(invoice_data)} 筆發票: {invoice_info['invoice_number']}")

                try:
                    # 步驟 1: 點擊發票編號進入詳細頁面
                    detail_page_success = self._click_invoice_number(invoice_info["invoice_number"])
                    if not detail_page_success:
                        safe_print(f"⚠️ 無法進入發票 {invoice_info['invoice_number']} 的詳細頁面，跳過")
                        continue

                    # 步驟 2: 智慧等待詳細頁面載入
                    self.smart_wait_for_element(By.ID, "lnkbtnDownloadInvoice", timeout=10, visible=False)

                    # 步驟 3: 在詳細頁面點擊下載表格按鈕
                    downloaded_file = self._download_invoice_detail(invoice_info)

                    if downloaded_file:
                        all_downloaded_files.extend(downloaded_file)
                        safe_print(f"✅ 成功下載發票 {invoice_info['invoice_number']}")
                    else:
                        safe_print(f"⚠️ 發票 {invoice_info['invoice_number']} 下載失敗")

                    # 步驟 4: 返回列表頁面
                    self._return_to_list_page()
                    # 智慧等待列表頁面載入
                    self.smart_wait_for_element(By.ID, "grdList", timeout=10, visible=False)

                except Exception as e:
                    safe_print(f"❌ 處理發票 {invoice_info['invoice_number']} 時發生錯誤: {e}")
                    # 嘗試返回列表頁面
                    try:
                        self._return_to_list_page()
                    except:
                        pass
                    continue

            if all_downloaded_files:
                safe_print(f"✅ 成功下載並重命名 {len(all_downloaded_files)} 個檔案")
                return all_downloaded_files
            else:
                safe_print("⚠️ 沒有檢測到新的下載檔案")
                return []

        except Exception as e:
            safe_print(f"❌ 下載失敗: {e}")
            return []

    def _click_invoice_number(self, invoice_number):
        """點擊發票編號進入詳細頁面"""
        safe_print(f"🖱️ 點擊發票編號: {invoice_number}")

        try:
            # 在表格中尋找對應的發票編號連結
            table = self.driver.find_element(By.ID, "grdList")
            rows = table.find_elements(By.TAG_NAME, "tr")

            for row in rows[1:]:  # 跳過標題行
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        # 檢查發票編號欄位（第3欄）
                        invoice_cell = cells[3]

                        # 尋找連結
                        try:
                            invoice_link = invoice_cell.find_element(By.TAG_NAME, "a")
                            link_text = invoice_link.text.strip()

                            if link_text == invoice_number:
                                safe_print(f"✅ 找到發票編號連結: {invoice_number}")
                                # 使用 JavaScript 點擊以避免元素被遮擋
                                self.driver.execute_script("arguments[0].click();", invoice_link)
                                self.smart_wait(1)  # 等待頁面跳轉
                                return True
                        except:
                            continue

                except Exception as e:
                    continue

            safe_print(f"❌ 找不到發票編號 {invoice_number} 的連結")
            return False

        except Exception as e:
            safe_print(f"❌ 點擊發票編號失敗: {e}")
            return False

    def _download_invoice_detail(self, invoice_info):
        """在詳細頁面下載發票表格"""
        safe_print("📥 在詳細頁面下載發票表格...")

        # 檢查檔案是否已下載過（在 OK_DIR 中）
        if invoice_info:
            target_filename = f"發票明細_{self.username}_{invoice_info['invoice_date']}_{invoice_info['invoice_number']}.xlsx"
            if self.is_file_already_downloaded(target_filename):
                return []  # 跳過已下載的檔案

        try:
            # 記錄下載前的檔案
            files_before = set(self.download_dir.glob("*"))

            # 尋找 lnkbtnDownloadInvoice 下載按鈕
            download_button = None

            try:
                # 方法 1: 直接使用 ID
                download_button = self.driver.find_element(By.ID, "lnkbtnDownloadInvoice")
                if download_button and download_button.is_displayed():
                    safe_print("✅ 找到下載表格按鈕: lnkbtnDownloadInvoice")
                else:
                    safe_print("⚠️ lnkbtnDownloadInvoice 按鈕不可見")
                    download_button = None

            except Exception as e:
                safe_print(f"⚠️ 找不到 lnkbtnDownloadInvoice: {e}")

                # 方法 2: 使用文字內容尋找
                try:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        if "下載表格" in link.text:
                            download_button = link
                            safe_print("✅ 透過文字找到下載表格按鈕")
                            break
                except:
                    pass

            if not download_button:
                safe_print("❌ 找不到下載表格按鈕")
                return []

            # 點擊下載按鈕
            safe_print("🖱️ 點擊下載表格按鈕...")

            try:
                # 如果是 JavaScript 連結，需要執行 JavaScript
                href = download_button.get_attribute("href")
                if href and "javascript:" in href:
                    # 提取 __doPostBack 參數並執行
                    self.driver.execute_script("arguments[0].click();", download_button)
                else:
                    download_button.click()

                safe_print("✅ 已點擊下載表格按鈕")

                # 檢查是否有確認對話框
                self.smart_wait(0.5)
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    safe_print(f"🔔 發現確認對話框: {alert_text}")
                    alert.accept()
                except:
                    pass

            except Exception as e:
                safe_print(f"❌ 點擊下載按鈕失敗: {e}")
                return []

            # 等待檔案下載
            safe_print("⏳ 等待檔案下載...")
            downloaded_files = self._wait_for_download(files_before)

            if downloaded_files:
                # 重命名檔案
                renamed_files = self._rename_downloaded_files_with_invoice_info(downloaded_files, [invoice_info])
                # 使用新的檔案移動機制
                final_files = self.move_and_cleanup_files(renamed_files, renamed_files)
                safe_print(f"✅ 成功下載並重命名檔案")
                return final_files
            else:
                safe_print("⚠️ 沒有檢測到新的下載檔案")
                return []

        except Exception as e:
            safe_print(f"❌ 下載發票詳細頁面失敗: {e}")
            return []

    def _return_to_list_page(self):
        """返回發票列表頁面"""
        safe_print("🔙 返回發票列表頁面...")

        try:
            # 方法 1: 使用瀏覽器的返回按鈕
            old_url = self.driver.current_url
            self.driver.back()
            self.smart_wait_for_url_change(old_url, timeout=5)
            safe_print("✅ 已返回列表頁面")
            return True

        except Exception as e:
            safe_print(f"⚠️ 返回列表頁面失敗: {e}")

            # 方法 2: 重新導航到對帳單明細頁面
            try:
                safe_print("🔄 嘗試重新導航到對帳單明細頁面...")
                nav_success = self.navigate_to_freight_query()
                if nav_success:
                    # 重新設定日期並搜尋
                    self.set_invoice_date_range()
                    self.smart_wait(0.5)
                    self._click_search_button()
                    self.smart_wait_for_ajax(timeout=15)
                    safe_print("✅ 重新導航並搜尋成功")
                    return True
            except Exception as nav_e:
                safe_print(f"❌ 重新導航失敗: {nav_e}")

            return False

    def _wait_for_download(self, files_before, timeout=60):
        """等待檔案下載完成 - 使用智慧等待"""
        safe_print(f"⏳ 等待檔案下載完成（最多 {timeout} 秒）...")

        # 使用智慧檔案下載等待
        downloaded_files = self.smart_wait_for_file_download(
            expected_extension=".xlsx", timeout=timeout, check_interval=0.5
        )

        if downloaded_files:
            safe_print(f"✅ 檔案下載完成: {len(downloaded_files)} 個檔案")
        else:
            safe_print("⚠️ 檔案下載超時")

        return downloaded_files

    def _parse_invoice_table(self):
        """解析發票明細表格以獲取發票資訊"""
        safe_print("📋 解析發票明細表格...")

        try:
            # 基於提供的 HTML 結構，尋找 grdList 表格
            table = self.driver.find_element(By.ID, "grdList")
            if not table:
                safe_print("❌ 找不到發票明細表格")
                return []

            # 獲取所有資料行（跳過標題行）
            rows = table.find_elements(By.TAG_NAME, "tr")
            invoice_data = []

            for row in rows[1:]:  # 跳過第一行（標題行）
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 10:  # 確保有足夠的欄位
                        # 根據 HTML 結構解析：
                        # cells[1] = 客戶代號
                        # cells[2] = 發票日期
                        # cells[3] = 發票號碼
                        customer_code = cells[1].text.strip()
                        invoice_date = cells[2].text.strip()

                        # 發票號碼可能在連結中
                        invoice_number = ""
                        try:
                            invoice_link = cells[3].find_element(By.TAG_NAME, "a")
                            invoice_number = invoice_link.text.strip()
                        except:
                            invoice_number = cells[3].text.strip()

                        if customer_code and invoice_date and invoice_number:
                            # 轉換日期格式從 2025/08/31 to 20250831
                            try:
                                date_parts = invoice_date.split("/")
                                if len(date_parts) == 3:
                                    formatted_date = f"{date_parts[0]}{date_parts[1].zfill(2)}{date_parts[2].zfill(2)}"
                                else:
                                    formatted_date = invoice_date.replace("/", "")
                            except:
                                formatted_date = invoice_date.replace("/", "")

                            invoice_info = {
                                "customer_code": customer_code,
                                "invoice_date": formatted_date,
                                "invoice_number": invoice_number,
                            }
                            invoice_data.append(invoice_info)
                            safe_print(f"✅ 解析發票: {customer_code} | {formatted_date} | {invoice_number}")

                except Exception as e:
                    safe_print(f"⚠️ 解析資料行失敗: {e}")
                    continue

            safe_print(f"📊 總共解析到 {len(invoice_data)} 筆發票資料")
            return invoice_data

        except Exception as e:
            safe_print(f"❌ 解析發票表格失敗: {e}")
            return []

    def _rename_downloaded_files_with_invoice_info(self, downloaded_files, invoice_data):
        """使用發票資訊重命名下載的檔案"""
        renamed_files = []

        for file_path in downloaded_files:
            try:
                original_name = file_path.stem
                extension = file_path.suffix

                # 如果有發票資料，使用第一筆資料來命名
                if invoice_data:
                    first_invoice = invoice_data[0]
                    # 格式：{帳號}_{發票日期}_{發票號碼}
                    new_name = f"發票明細_{self.username}_{first_invoice['invoice_date']}_{first_invoice['invoice_number']}{extension}"
                else:
                    # 備用格式：使用日期範圍
                    new_name = f"發票明細_{self.username}_{self.start_date}-{self.end_date}_{original_name}{extension}"

                new_path = file_path.parent / new_name

                # 如果目標檔案已存在，直接覆蓋
                if new_path.exists():
                    safe_print(f"⚠️ 目標檔案已存在，將覆蓋: {new_path.name}")
                    new_path.unlink()  # 刪除現有檔案

                file_path.rename(new_path)
                renamed_files.append(new_path)
                safe_print(f"✅ 檔案重命名: {file_path.name} → {new_path.name}")

            except Exception as e:
                safe_print(f"⚠️ 檔案重命名失敗 {file_path.name}: {e}")
                # 即使重命名失敗，也要確保檔案有唯一名稱
                try:
                    import uuid

                    backup_filename = f"發票明細_{self.username}_{uuid.uuid4().hex[:8]}.xlsx"
                    backup_file_path = file_path.parent / backup_filename
                    file_path.rename(backup_file_path)
                    renamed_files.append(backup_file_path)
                    safe_print(f"🔄 使用備用檔案名: {backup_filename}")
                except Exception as backup_e:
                    safe_print(f"❌ 備用重命名也失敗: {backup_e}")
                    renamed_files.append(file_path)  # 最後手段：保留原始檔案

        return renamed_files

    def run_full_process(self):
        """執行完整的運費查詢自動化流程"""
        downloaded_files = []

        # 開始執行時間計時
        self.start_execution_timer()

        try:
            print("=" * 60)
            safe_print(f"🚛 開始執行黑貓宅急便運費查詢流程 (帳號: {self.username})")
            print("=" * 60)

            # 1. 初始化瀏覽器
            self.init_browser()

            # 2. 登入
            login_success = self.login()
            if not login_success:
                safe_print(f"❌ 帳號 {self.username} 登入失敗")
                return {"success": False, "username": self.username, "error": "登入失敗", "downloads": []}

            # 3. 導航到對帳單明細頁面
            nav_success = self.navigate_to_freight_query()
            if not nav_success:
                # 檢查是否為密碼安全警告
                if self.security_warning_encountered:
                    safe_print(f"🚨 帳號 {self.username} 密碼安全警告")
                    return {
                        "success": False,
                        "username": self.username,
                        "error": "密碼安全警告",
                        "error_type": "security_warning",
                        "downloads": [],
                    }
                else:
                    safe_print(f"❌ 帳號 {self.username} 導航失敗")
                    return {"success": False, "username": self.username, "error": "導航失敗", "downloads": []}

            # 4. 設定發票日期區間
            date_success = self.set_invoice_date_range()
            if not date_success:
                safe_print(f"⚠️ 帳號 {self.username} 日期設定失敗，但繼續執行")

            # 5. 搜尋並下載對帳單明細
            downloaded_files = self.search_and_download_statement()

            if downloaded_files:
                safe_print(f"🎉 帳號 {self.username} 運費查詢流程完成！下載了 {len(downloaded_files)} 個檔案")
                return {"success": True, "username": self.username, "downloads": [str(f) for f in downloaded_files]}
            else:
                safe_print(f"⚠️ 帳號 {self.username} 沒有下載到檔案")
                return {"success": True, "username": self.username, "message": "無資料可下載", "downloads": []}

        except Exception as e:
            safe_print(f"💥 帳號 {self.username} 流程執行失敗: {e}")
            return {
                "success": False,
                "username": self.username,
                "error": str(e),
                "downloads": [str(f) for f in downloaded_files],
            }
        finally:
            # 結束執行時間計時
            self.end_execution_timer()
            self.close()


def main():
    """主程式入口"""
    import argparse

    parser = argparse.ArgumentParser(description="黑貓宅急便運費查詢自動下載工具")
    parser.add_argument("--headless", action="store_true", help="使用無頭模式")
    parser.add_argument("--start-date", type=str, help="開始日期 (格式: YYYYMMDD)")
    parser.add_argument("--end-date", type=str, help="結束日期 (格式: YYYYMMDD)")

    args = parser.parse_args()

    try:
        safe_print("🚛 黑貓宅急便運費查詢自動下載工具")

        manager = MultiAccountManager("accounts.json")
        # 只有在使用者明確指定 --headless 時才覆蓋設定檔
        headless_arg = True if "--headless" in sys.argv else None
        manager.run_all_accounts(
            FreightScraper, headless_override=headless_arg, start_date=args.start_date, end_date=args.end_date
        )

        return 0

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        safe_print(f"⛔ 錯誤: {e}")
        return 1
    except KeyboardInterrupt:
        safe_print("\n⛔ 使用者中斷執行")
        return 1
    except Exception as e:
        safe_print(f"⛔ 未知錯誤: {e}")
        return 1


if __name__ == "__main__":
    main()
