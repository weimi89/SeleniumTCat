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


class UnpaidScraper(BaseScraper):
    """
    黑貓宅急便交易明細表自動下載工具
    繼承自 BaseScraper，複用登入和驗證碼處理功能
    """

    # 設定環境變數 key
    DOWNLOAD_DIR_ENV_KEY = "UNPAID_DOWNLOAD_WORK_DIR"
    DOWNLOAD_OK_DIR_ENV_KEY = "UNPAID_DOWNLOAD_OK_DIR"

    def __init__(self, username, password, headless=None, days=None, quiet_init=False):
        # 呼叫父類建構子
        super().__init__(username, password, headless)

        # UnpaidScraper 特有的屬性
        # 天數設定（預設為 30 天）
        if days is None:
            days = 30

        self.days = days

        # 驗證天數
        if not isinstance(self.days, int) or self.days <= 0:
            raise ValueError(f"天數必須為正整數: {self.days}")

        # 只在非靜默模式下顯示（多帳號模式已在開頭統一顯示）
        if not quiet_init:
            safe_print(f"📅 查詢範圍: 前 {self.days} 天")

    def navigate_to_transaction_detail(self):
        """導航到交易明細表頁面 - 包含完整重試機制和 session timeout 處理"""
        safe_print("🧭 導航到交易明細表頁面...")

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
                safe_print("🎯 使用直接 URL 訪問交易明細表頁面...")
                direct_success = self._try_direct_transaction_url()

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
                        direct_success = self._try_direct_transaction_url()

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

    def _try_direct_transaction_url(self):
        """嘗試直接訪問交易明細表頁面 - 包含重試機制和 session timeout 處理"""
        try:
            # 基於用戶提供的 URL 格式，使用 FuncNo=167 (交易明細表)
            direct_urls = [
                # 使用 RedirectFunc 的正確方式（基於用戶提供的 FuncNo=167）
                "https://www.takkyubin.com.tw/YMTContract/aspx/RedirectFunc.aspx?FuncNo=167",
                # 直接訪問交易明細頁面
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentDetail.aspx?TimeOut=N",
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentDetail.aspx",
                # 添加更多後備 URL
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentDetail.aspx?DetailType=01",
                "https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentDetail.aspx?DetailType=02",
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
                                # 智慧等待頁面完全載入
                                self.smart_wait(
                                    lambda d: d.execute_script("return document.readyState") == "complete",
                                    timeout=10,
                                    error_message="重新登入後頁面載入完成",
                                )
                                current_url = self.driver.current_url
                            else:
                                print("   ❌ 重新登入失敗")
                                continue

                        # 檢查是否成功到達交易明細表頁面
                        if self._is_transaction_detail_page():
                            safe_print("✅ 直接 URL 訪問成功")
                            return True
                        else:
                            print("   ❌ 未能到達交易明細表頁面")

                        # 如果這次嘗試失敗，但還有重試機會，則稍等片刻再重試
                        if retry < max_retries:
                            # 移除固定等待，直接重試
                            pass
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
                            # 短暫等待後重試（alert 處理後需要一些時間穩定）
                            time.sleep(0.5)
                        continue

            print("   ❌ 所有直接 URL 嘗試都失敗")
            return False

        except Exception as e:
            safe_print(f"❌ 直接 URL 方法失敗: {e}")
            return False

    def _navigate_through_menu(self):
        """通過選單導航到交易明細表"""
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

            # 步驟2: 尋找並點擊「交易明細表」
            transaction_success = self._click_transaction_detail_menu()
            if not transaction_success:
                safe_print("❌ 找不到交易明細表選項")
                self.driver.switch_to.default_content()
                return False

            # 智慧等待頁面載入
            self.smart_wait(2)

            self.driver.switch_to.default_content()
            return self._is_transaction_detail_page()

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

    def _click_transaction_detail_menu(self):
        """點擊交易明細表選項"""
        try:
            # 基於用戶提供的連結特徵
            transaction_keywords = ["交易明細表", "交易明細", "明細表"]

            # 特別尋找包含 RedirectFunc.aspx?FuncNo=167 的連結
            links = self.driver.find_elements(By.TAG_NAME, "a")

            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    text = link.text or ""

                    # 優先匹配特定的 URL 模式
                    if "RedirectFunc.aspx?FuncNo=167" in href:
                        if link.is_displayed() and link.is_enabled():
                            safe_print(f"✅ 找到交易明細表連結: '{text}' ({href})")
                            link.click()
                            return True

                    # 備用匹配文字內容
                    elif any(keyword in text for keyword in transaction_keywords):
                        if link.is_displayed() and link.is_enabled():
                            safe_print(f"✅ 找到交易明細表選項: '{text}'")
                            link.click()
                            return True

                except:
                    continue

            return False

        except Exception as e:
            safe_print(f"❌ 點擊交易明細表選項失敗: {e}")
            return False

    def _is_transaction_detail_page(self):
        """檢查是否成功到達交易明細表頁面"""
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source

            # 檢查 URL 是否包含預期的頁面標識
            url_indicators = ["SudaPaymentDetail.aspx", "TimeOut=N"]

            # 基於真實 HTML 結構的精確內容檢查
            content_indicators = [
                "交易明細表",  # 頁面標題
                "週期",  # 週期選擇
                "lnkbtnDownload",  # 下載按鈕 ID（基於用戶提供的）
                "交易明細下載",  # 下載按鈕文字（基於用戶提供的）
                "開始日期",  # 日期選擇欄位
                "結束日期",  # 日期選擇欄位
            ]

            url_match = any(indicator in current_url for indicator in url_indicators)
            content_match = any(indicator in page_source for indicator in content_indicators)

            # 更精確的元素檢查
            element_check = False
            try:
                # 檢查關鍵元素是否存在
                key_elements = [
                    ("ID", "lnkbtnDownload"),  # 下載按鈕
                ]

                found_elements = 0
                for method, selector in key_elements:
                    try:
                        if method == "ID":
                            element = self.driver.find_element(By.ID, selector)
                            if element:
                                found_elements += 1
                    except:
                        continue

                element_check = found_elements >= 1  # 至少找到 1 個關鍵元素

            except Exception as e:
                pass

            safe_print(f"📍 URL 檢查: {'✅' if url_match else '❌'}")
            safe_print(f"📄 內容檢查: {'✅' if content_match else '❌'}")
            safe_print(f"🎯 元素檢查: {'✅' if element_check else '❌'}")

            return url_match or content_match or element_check

        except Exception as e:
            safe_print(f"❌ 頁面檢查失敗: {e}")
            return False

    def search_and_download_days(self):
        """搜尋並下載指定天數範圍的交易明細"""
        safe_print(f"🔍 開始搜尋並下載前 {self.days} 天的交易明細...")

        downloaded_files = []
        days_details = {}

        try:
            # 設定本次下載的 UUID 臨時目錄
            self.setup_temp_download_dir()

            # 計算天數的日期範圍
            start_date, end_date = self._calculate_date_range()
            safe_print(f"📅 日期範圍: {start_date} - {end_date}")

            # 執行下載
            days_result = self._download_days_data_with_details(start_date, end_date)

            # 記錄天數範圍詳細情況
            days_details = days_result

            if days_result["files"]:
                downloaded_files.extend(days_result["files"])
                safe_print(f"✅ 前 {self.days} 天下載完成: {len(days_result['files'])} 個檔案")
            elif days_result["status"] == "no_records":
                safe_print(f"⚠️ 前 {self.days} 天無交易記錄 ({start_date} - {end_date})")
            else:
                safe_print(f"⚠️ 前 {self.days} 天下載失敗: {days_result.get('error', '未知錯誤')}")

            return downloaded_files, days_details

        except Exception as e:
            safe_print(f"❌ 搜尋和下載失敗: {e}")
            return downloaded_files, days_details


    def _download_days_data_with_details(self, start_date, end_date, max_retries=3):
        """下載指定天數範圍的資料並返回詳細信息，支援重試機制"""
        safe_print(f"📥 下載資料 ({start_date} - {end_date})...")

        # 檢查檔案是否已下載過（在 OK_DIR 中）
        target_filename = f"交易明細表_{self.username}_{start_date}-{end_date}.xlsx"
        if self.is_file_already_downloaded(target_filename):
            return [], {
                "days": self.days,
                "start_date": start_date,
                "end_date": end_date,
                "status": "skipped",
                "files": [],
                "error": None,
                "record_count": 0,
            }

        days_info = {
            "days": self.days,
            "start_date": start_date,
            "end_date": end_date,
            "status": "unknown",
            "files": [],
            "error": None,
            "record_count": 0,
        }

        for retry in range(max_retries):
            try:
                if retry > 0:
                    safe_print(f"🔄 下載第 {retry + 1} 次重試...")
                    # 重新載入頁面
                    transaction_url = "https://www.takkyubin.com.tw/YMTContract/aspx/RedirectFunc.aspx?FuncNo=167"
                    old_url = self.driver.current_url
                    self.driver.get(transaction_url)
                    self.smart_wait_for_url_change(old_url, timeout=5)

                # 記錄下載前的檔案
                files_before = set(self.download_dir.glob("*"))

                # 執行 AJAX 搜尋請求
                search_success = self._perform_ajax_search(start_date, end_date)
                if not search_success:
                    safe_print(f"⚠️ AJAX 搜尋失敗")
                    if retry < max_retries - 1:
                        continue
                    else:
                        days_info["status"] = "search_failed"
                        days_info["error"] = "AJAX 搜尋失敗"
                        return days_info

                # 等待搜尋結果載入
                download_ready = self._wait_for_search_results()
                if not download_ready:
                    safe_print(f"⚠️ 搜尋結果載入超時或無資料")
                    if retry < max_retries - 1:
                        continue
                    else:
                        days_info["status"] = "no_results"
                        days_info["error"] = "搜尋結果載入超時"
                        return days_info


                # 點擊下載按鈕
                download_success = self._click_download_button()
                if not download_success:
                    safe_print(f"⚠️ 下載按鈕點擊失敗")
                    if retry < max_retries - 1:
                        continue
                    else:
                        return []

                # 等待檔案下載（30秒超時）
                downloaded_files = self._wait_for_download(files_before, timeout=30)

                if downloaded_files:
                    # 重命名檔案（格式：{帳號}_{開始日期}_{結束日期}）
                    renamed_files = self._rename_period_files(downloaded_files, start_date, end_date)
                    # 使用新的檔案移動機制
                    final_files = self.move_and_cleanup_files(renamed_files, renamed_files)
                    safe_print(f"✅ 下載成功")
                    days_info["status"] = "success"
                    days_info["files"] = final_files
                    return days_info
                else:
                    if retry < max_retries - 1:
                        safe_print(f"⚠️ 下載超時，將重試...")
                        continue
                    else:
                        safe_print(f"❌ 下載失敗（所有重試完畢）")
                        days_info["status"] = "download_failed"
                        days_info["error"] = "下載超時"
                        return days_info

            except Exception as e:
                if retry < max_retries - 1:
                    safe_print(f"⚠️ 下載異常 (第 {retry + 1} 次): {e}")
                    safe_print("🔄 將重試...")
                else:
                    safe_print(f"❌ 資料下載失敗 (所有重試完畢): {e}")
                    days_info["status"] = "error"
                    days_info["error"] = str(e)
                    return days_info

        return days_info

    def _calculate_date_range(self):
        """計算從今天往前推指定天數的日期範圍"""
        try:
            from datetime import datetime, timedelta
            
            # 結束日期為今天
            end_date_obj = datetime.now()
            # 開始日期為今天往前推 N 天
            start_date_obj = end_date_obj - timedelta(days=self.days - 1)
            
            # 轉換為字串格式 YYYYMMDD
            start_date = start_date_obj.strftime("%Y%m%d")
            end_date = end_date_obj.strftime("%Y%m%d")
            
            safe_print(f"📅 日期範圍: {start_date} - {end_date} (前 {self.days} 天)")
            
            return start_date, end_date
            
        except Exception as e:
            safe_print(f"❌ 日期計算失敗: {e}")
            # 回傳預設值（前 30 天）
            from datetime import datetime, timedelta
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=29)
            start_date = start_date_obj.strftime("%Y%m%d")
            end_date = end_date_obj.strftime("%Y%m%d")
            return start_date, end_date

    def _perform_ajax_search(self, start_date, end_date):
        """執行 AJAX 搜尋請求"""
        safe_print("🔍 執行 AJAX 搜尋請求...")

        try:
            # 基於實際的 HTML 結構設定日期欄位
            start_date_input = None
            end_date_input = None

            # 方法1: 使用確切的 ID（基於 freight_scraper 的成功經驗）
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
                    # 方法3: 嘗試交易明細表特有的 ID
                    try:
                        start_date_input = self.driver.find_element(By.ID, "txtStartDate")
                        end_date_input = self.driver.find_element(By.ID, "txtEndDate")
                        safe_print("✅ 找到交易明細表日期輸入框")
                    except:
                        # 方法4: 通用搜索
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
                    start_date_input.send_keys(start_date)
                    safe_print(f"✅ 已設定開始日期: {start_date}")

                    # 清空並填入結束日期
                    end_date_input.clear()
                    end_date_input.send_keys(end_date)
                    safe_print(f"✅ 已設定結束日期: {end_date}")

                    # 觸發搜尋（嘗試多種搜尋按鈕 ID）
                    search_success = self._trigger_search_button()
                    if search_success:
                        safe_print("✅ AJAX 搜尋請求已發送")
                        return True
                    else:
                        safe_print("❌ 找不到搜尋按鈕")
                        return False

                except Exception as e:
                    safe_print(f"⚠️ 填入日期失敗: {e}")
                    return False
            else:
                safe_print("❌ 未找到日期輸入框")
                return False

        except Exception as e:
            safe_print(f"❌ AJAX 搜尋失敗: {e}")
            return False

    def _trigger_search_button(self):
        """嘗試觸發搜尋按鈕"""
        try:
            # 嘗試多種搜尋按鈕 ID
            search_button_ids = ["btnSearch", "btnQuery", "lnkbtnSearch"]

            for button_id in search_button_ids:
                try:
                    search_button = self.driver.find_element(By.ID, button_id)
                    if search_button and search_button.is_displayed() and search_button.is_enabled():
                        safe_print(f"✅ 找到搜尋按鈕: {button_id}")
                        self.driver.execute_script("arguments[0].click();", search_button)
                        return True
                except:
                    continue

            # 如果 ID 搜尋失敗，嘗試通用搜尋
            try:
                search_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='submit'][value*='搜'], input[type='button'][value*='搜'], button[value*='搜']",
                )
                for button in search_buttons:
                    if button.is_displayed() and button.is_enabled():
                        safe_print("✅ 找到通用搜尋按鈕")
                        self.driver.execute_script("arguments[0].click();", button)
                        return True
            except:
                pass

            return False

        except Exception as e:
            safe_print(f"❌ 觸發搜尋按鈕失敗: {e}")
            return False

    def _wait_for_search_results(self, timeout=30):
        """等待搜尋結果載入 - 使用智慧等待"""
        safe_print("⏳ 等待搜尋結果載入...")

        try:
            # 嘗試多種可能的下載按鈕 ID
            download_button_ids = ["lnkbtnDownload", "btnDownload", "lnkDownload"]

            for button_id in download_button_ids:
                download_button = self.smart_wait_for_element(
                    By.ID, button_id, timeout=timeout // len(download_button_ids), visible=True
                )

                if download_button:
                    safe_print(f"✅ 搜尋結果載入完成，下載按鈕已準備就緒: {button_id}")
                    return True

            # 如果沒找到特定 ID，嘗試 XPath 搜尋
            safe_print("⚠️ 嘗試使用 XPath 搜尋下載元素...")
            download_element = self.smart_wait_for_element(
                By.XPATH,
                "//*[contains(text(), '下載') or contains(text(), '明細下載') or contains(text(), '交易明細下載')]",
                timeout=10,
                visible=True,
            )

            if download_element:
                safe_print("✅ 搜尋結果載入完成，找到下載元素")
                return True

            safe_print("⚠️ 搜尋結果載入超時，可能沒有符合條件的資料")
            return False

        except Exception as e:
            safe_print(f"⚠️ 搜尋結果載入失敗: {e}")
            return False

    def _click_download_button(self, max_retries=3):
        """點擊交易明細下載按鈕，支援重試機制"""
        safe_print("🖱️ 點擊交易明細下載按鈕...")

        for retry in range(max_retries):
            try:
                if retry > 0:
                    safe_print(f"🔄 第 {retry + 1} 次重試點擊下載按鈕...")
                    self.smart_wait(1)  # 等待頁面穩定

                download_button = None

                # 方法1: 嘗試多種可能的下載按鈕 ID (重新查找)
                download_button_ids = ["lnkbtnDownload", "btnDownload", "lnkDownload"]

                for button_id in download_button_ids:
                    try:
                        # 每次都重新查找元素，避免 stale reference
                        download_button = self.driver.find_element(By.ID, button_id)
                        if download_button and download_button.is_displayed() and download_button.is_enabled():
                            safe_print(f"✅ 找到下載按鈕: {button_id} (ID)")
                            break
                    except:
                        continue

                # 方法2: 如果沒找到特定 ID，嘗試文字搜尋
                if not download_button:
                    backup_selectors = [
                        ("LINK_TEXT", "交易明細下載"),
                        ("PARTIAL_LINK_TEXT", "明細下載"),
                        ("PARTIAL_LINK_TEXT", "下載"),
                        ("XPATH", "//a[contains(text(), '交易明細下載')]"),
                        ("XPATH", "//a[contains(text(), '明細下載')]"),
                        ("XPATH", "//a[contains(text(), '下載')]"),
                        ("CSS", "a[href*='Download']"),
                        ("CSS", "input[value*='下載']"),
                        ("CSS", "button[value*='下載']"),
                    ]

                    for method, selector in backup_selectors:
                        try:
                            if method == "LINK_TEXT":
                                download_button = self.driver.find_element(By.LINK_TEXT, selector)
                            elif method == "PARTIAL_LINK_TEXT":
                                download_button = self.driver.find_element(By.PARTIAL_LINK_TEXT, selector)
                            elif method == "XPATH":
                                download_button = self.driver.find_element(By.XPATH, selector)
                            elif method == "CSS":
                                download_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                            if download_button and download_button.is_displayed() and download_button.is_enabled():
                                safe_print(f"✅ 找到備用下載按鈕: {method}={selector}")
                                break

                        except Exception:
                            continue

                if not download_button:
                    if retry < max_retries - 1:
                        safe_print("⚠️ 本次未找到下載按鈕，將重試...")
                        continue
                    else:
                        safe_print("❌ 找不到任何下載按鈕，可能沒有資料可下載")
                        return False

                # 點擊下載按鈕
                safe_print("🖱️ 執行下載點擊...")

                # 使用 JavaScript 點擊以避免攔截問題
                self.driver.execute_script("arguments[0].click();", download_button)

                # 處理可能的確認對話框
                self.smart_wait(0.5)
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    safe_print(f"🔔 發現確認對話框: {alert_text}")
                    alert.accept()
                    safe_print("✅ 已確認下載")
                except Exception:
                    pass  # 沒有對話框

                safe_print("✅ 下載按鈕點擊成功")
                return True

            except Exception as e:
                if retry < max_retries - 1:
                    safe_print(f"⚠️ 點擊下載按鈕失敗 (第 {retry + 1} 次): {e}")
                    safe_print("🔄 將重試...")
                else:
                    safe_print(f"❌ 點擊下載按鈕失敗 (所有重試完畢): {e}")
                    return False

        # 如果所有重試都失敗
        safe_print("❌ 下載按鈕點擊失敗，已用盡所有重試")
        return False

    def _check_records_count(self):
        """檢查交易記錄筆數，避免下載空資料"""
        try:
            safe_print("🔍 檢查交易記錄筆數...")

            # 查找包含筆數資訊的元素
            count_element = None

            # 方法1: 直接尋找 lblTotleCount ID
            try:
                count_element = self.driver.find_element(By.ID, "lblTotleCount")
                safe_print("✅ 找到筆數元素 (lblTotleCount)")
            except:
                # 方法2: 尋找包含 "交易共" 和 "筆" 的文字
                try:
                    count_elements = self.driver.find_elements(
                        By.XPATH, "//span[contains(@style, 'color:Red;') or contains(@style, 'color:red;')]"
                    )
                    for element in count_elements:
                        if element.text.isdigit():
                            count_element = element
                            safe_print("✅ 找到筆數元素 (通過紅色文字)")
                            break
                except:
                    pass

            if count_element:
                try:
                    count_text = count_element.text.strip()
                    record_count = int(count_text)
                    safe_print(f"📊 交易記錄筆數: {record_count} 筆")

                    if record_count > 0:
                        safe_print("✅ 有交易記錄，可以執行下載")
                        return True
                    else:
                        safe_print("⚠️ 交易記錄筆數為 0，跳過下載避免空轉")
                        return False

                except ValueError:
                    safe_print(f"⚠️ 無法解析筆數文字: {count_text}")
                    # 如果無法解析，謹慎起見還是允許下載
                    return True
            else:
                safe_print("⚠️ 未找到筆數元素，檢查頁面內容...")

                # 備用方法：檢查頁面源碼
                page_source = self.driver.page_source

                # 尋找 "交易共 X 筆" 的模式
                import re

                pattern = r"交易共.*?(\d+).*?筆"
                match = re.search(pattern, page_source)

                if match:
                    record_count = int(match.group(1))
                    safe_print(f"📊 通過頁面內容檢測到交易記錄筆數: {record_count} 筆")

                    if record_count > 0:
                        safe_print("✅ 有交易記錄，可以執行下載")
                        return True
                    else:
                        safe_print("⚠️ 交易記錄筆數為 0，跳過下載避免空轉")
                        return False
                else:
                    safe_print("⚠️ 無法檢測筆數，為安全起見允許下載")
                    return True

        except Exception as e:
            safe_print(f"❌ 檢查記錄筆數時發生錯誤: {e}")
            # 發生錯誤時謹慎起見還是允許下載
            return True

    def _wait_for_download(self, files_before, timeout=30):
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

    def _rename_period_files(self, downloaded_files, start_date, end_date):
        """重命名下載的檔案（格式：{帳號}_{開始日期}-{結束日期}）"""
        renamed_files = []

        for file_path in downloaded_files:
            try:
                original_name = file_path.stem
                extension = file_path.suffix

                # 新的檔案名稱格式：{帳號}_{開始日期}-{結束日期}
                new_name = f"交易明細表_{self.username}_{start_date}-{end_date}{extension}"
                new_path = file_path.parent / new_name

                # 如果目標檔案已存在，直接覆蓋
                if new_path.exists():
                    safe_print(f"⚠️ 檔案已存在，將覆蓋: {new_path.name}")

                file_path.rename(new_path)
                renamed_files.append(new_path)
                safe_print(f"✅ 檔案重命名: {file_path.name} → {new_path.name}")

            except Exception as e:
                safe_print(f"⚠️ 檔案重命名失敗 {file_path.name}: {e}")
                # 即使重命名失敗，也要確保檔案有唯一名稱
                try:
                    import uuid

                    backup_filename = f"交易明細_{self.username}_{uuid.uuid4().hex[:8]}.xlsx"
                    backup_file_path = file_path.parent / backup_filename
                    file_path.rename(backup_file_path)
                    renamed_files.append(backup_file_path)
                    safe_print(f"🔄 使用備用檔案名: {backup_filename}")
                except Exception as backup_e:
                    safe_print(f"❌ 備用重命名也失敗: {backup_e}")
                    renamed_files.append(file_path)  # 最後手段：保留原始檔案

        return renamed_files

    def run_full_process(self):
        """執行完整的交易明細查詢自動化流程"""
        downloaded_files = []

        # 開始執行時間計時
        self.start_execution_timer()

        try:
            print("=" * 60)
            safe_print(f"🚛 開始執行黑貓宅急便交易明細查詢流程 (帳號: {self.username})")
            print("=" * 60)

            # 1. 初始化瀏覽器
            self.init_browser()

            # 2. 登入
            login_success = self.login()
            if not login_success:
                safe_print(f"❌ 帳號 {self.username} 登入失敗")
                return {"success": False, "username": self.username, "error": "登入失敗", "downloads": []}

            # 3. 導航到交易明細表頁面
            nav_success = self.navigate_to_transaction_detail()
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

            # 4. 搜尋並下載指定天數範圍的交易明細
            downloaded_files, days_details = self.search_and_download_days()

            if downloaded_files:
                safe_print(f"🎉 帳號 {self.username} 交易明細查詢流程完成！下載了 {len(downloaded_files)} 個檔案")
                return {
                    "success": True,
                    "username": self.username,
                    "downloads": [str(f) for f in downloaded_files],
                    "days_details": days_details,
                }
            else:
                safe_print(f"⚠️ 帳號 {self.username} 沒有下載到檔案")
                return {
                    "success": True,
                    "username": self.username,
                    "message": "無資料可下載",
                    "downloads": [],
                    "days_details": days_details,
                }

        except Exception as e:
            safe_print(f"💥 帳號 {self.username} 流程執行失敗: {e}")
            return {
                "success": False,
                "username": self.username,
                "error": str(e),
                "downloads": [str(f) for f in downloaded_files],
                "days_details": getattr(locals(), "days_details", {}),
            }
        finally:
            # 結束執行時間計時
            self.end_execution_timer()
            self.close()


def main():
    """主程式入口"""
    import argparse

    parser = argparse.ArgumentParser(description="黑貓宅急便交易明細表自動下載工具")
    parser.add_argument("--headless", action="store_true", help="使用無頭模式")
    parser.add_argument("--days", type=int, default=30, help="要下載的天數範圍 (預設: 30 天)")

    args = parser.parse_args()

    try:
        safe_print("🚛 黑貓宅急便交易明細表自動下載工具")

        manager = MultiAccountManager("accounts.json")
        # 只有在使用者明確指定 --headless 時才覆蓋設定檔
        headless_arg = True if "--headless" in sys.argv else None
        manager.run_all_accounts(UnpaidScraper, headless_override=headless_arg, days=args.days)

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
