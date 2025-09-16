#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time

# 導入共用模組
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
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

    def __init__(self, username, password, headless=False, download_base_dir="downloads", periods=2):
        # 呼叫父類建構子
        super().__init__(username, password, headless, download_base_dir)

        # UnpaidScraper 特有的屬性
        # 週期設定（預設2期，1週1個檔案）
        self.periods = periods

        safe_print(f"📅 預設查詢 {self.periods} 個週期")

    def navigate_to_transaction_detail(self):
        """導航到交易明細表頁面"""
        safe_print("🧭 導航到交易明細表頁面...")

        try:
            # 等待登入完成
            safe_print("⏳ 等待登入完成...")
            time.sleep(5)

            # 方法1: 嘗試直接使用 URL
            direct_success = self._try_direct_transaction_url()
            if direct_success:
                return True

            # 方法2: 嘗試框架導航
            safe_print("⚠️ 直接 URL 失敗，嘗試框架導航...")
            frame_success = self._navigate_through_menu()
            if frame_success:
                return True

            safe_print("❌ 所有導航方法都失敗了")
            return False

        except Exception as e:
            safe_print(f"❌ 導航失敗: {e}")
            return False

    def _try_direct_transaction_url(self):
        """嘗試直接訪問交易明細表頁面"""
        try:
            # 基於用戶提供的 URL 格式，使用 FuncNo=167 (交易明細表)
            direct_urls = [
                # 使用 RedirectFunc 的正確方式（基於用戶提供的 FuncNo=167）
                'https://www.takkyubin.com.tw/YMTContract/aspx/RedirectFunc.aspx?FuncNo=167',
                # 直接訪問交易明細頁面
                'https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentDetail.aspx?TimeOut=N',
                'https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentDetail.aspx',
            ]

            for full_url in direct_urls:
                try:
                    safe_print(f"🎯 嘗試直接訪問: {full_url}")

                    self.driver.get(full_url)
                    time.sleep(5)  # 增加等待時間以確保頁面完全載入

                    # 檢查是否成功到達交易明細表頁面
                    if self._is_transaction_detail_page():
                        safe_print("✅ 直接 URL 訪問成功")
                        return True

                except Exception as e:
                    safe_print(f"⚠️ 直接 URL {full_url} 失敗: {e}")
                    continue

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

            time.sleep(3)  # 等待選單展開

            # 步驟2: 尋找並點擊「交易明細表」
            transaction_success = self._click_transaction_detail_menu()
            if not transaction_success:
                safe_print("❌ 找不到交易明細表選項")
                self.driver.switch_to.default_content()
                return False

            # 等待頁面載入
            time.sleep(5)

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
                self.driver.find_elements(By.TAG_NAME, "a") +
                self.driver.find_elements(By.TAG_NAME, "div") +
                self.driver.find_elements(By.TAG_NAME, "span") +
                self.driver.find_elements(By.TAG_NAME, "td") +
                self.driver.find_elements(By.TAG_NAME, "li")
            )

            for element in all_elements:
                try:
                    element_text = element.text or element.get_attribute('title') or ''
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
                    href = link.get_attribute('href') or ''
                    text = link.text or ''

                    # 優先匹配特定的 URL 模式
                    if 'RedirectFunc.aspx?FuncNo=167' in href:
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
            url_indicators = [
                "SudaPaymentDetail.aspx",
                "TimeOut=N"
            ]

            # 基於真實 HTML 結構的精確內容檢查
            content_indicators = [
                "交易明細表",            # 頁面標題
                "週期",                # 週期選擇
                "lnkbtnDownload",      # 下載按鈕 ID（基於用戶提供的）
                "交易明細下載",         # 下載按鈕文字（基於用戶提供的）
                "開始日期",            # 日期選擇欄位
                "結束日期"             # 日期選擇欄位
            ]

            url_match = any(indicator in current_url for indicator in url_indicators)
            content_match = any(indicator in page_source for indicator in content_indicators)

            # 更精確的元素檢查
            element_check = False
            try:
                # 檢查關鍵元素是否存在
                key_elements = [
                    ("ID", "lnkbtnDownload"),   # 下載按鈕
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

    def set_period_search(self):
        """設定週期搜尋方式，預設會抓2期(1週1個檔案)"""
        safe_print(f"📅 設定週期搜尋方式 ({self.periods} 期)...")

        try:
            # 這裡需要根據實際的週期選擇介面來實作
            # 目前作為佔位符，待有實際的 HTML 結構後再詳細實作

            # 檢查頁面是否有週期選擇功能
            page_source = self.driver.page_source

            if "週期" in page_source:
                safe_print("✅ 頁面支援週期選擇")
                # 這裡添加週期選擇的具體邏輯
                # 可能需要選擇下拉選單或填寫特定的週期數值
                return True
            else:
                safe_print("⚠️ 頁面不支援週期選擇，使用預設設定")
                return True

        except Exception as e:
            safe_print(f"❌ 週期設定失敗: {e}")
            return False

    def search_and_download_periods(self):
        """搜尋並下載指定週期的交易明細"""
        safe_print(f"🔍 開始搜尋並下載 {self.periods} 個週期的交易明細...")

        downloaded_files = []

        try:
            # 為每個週期執行下載
            for period in range(1, self.periods + 1):
                safe_print(f"\n📊 處理第 {period} 期...")

                # 設定該週期的日期範圍
                period_files = self._download_period_data(period)

                if period_files:
                    downloaded_files.extend(period_files)
                    safe_print(f"✅ 第 {period} 期下載完成: {len(period_files)} 個檔案")
                else:
                    safe_print(f"⚠️ 第 {period} 期沒有資料")

                # 週期間等待
                if period < self.periods:
                    time.sleep(2)

            return downloaded_files

        except Exception as e:
            safe_print(f"❌ 週期搜尋和下載失敗: {e}")
            return downloaded_files

    def _download_period_data(self, period):
        """下載特定週期的資料"""
        safe_print(f"📥 下載第 {period} 期資料...")

        try:
            # 計算週期的開始和結束日期
            start_date, end_date = self._calculate_period_dates(period)

            safe_print(f"📅 第 {period} 期日期範圍: {start_date} - {end_date}")

            # 記錄下載前的檔案
            files_before = set(self.download_dir.glob("*"))

            # 執行 AJAX 搜尋請求
            search_success = self._perform_ajax_search(start_date, end_date)
            if not search_success:
                safe_print(f"❌ 第 {period} 期 AJAX 搜尋失敗")
                return []

            # 等待搜尋結果載入
            download_ready = self._wait_for_search_results()
            if not download_ready:
                safe_print(f"⚠️ 第 {period} 期搜尋結果載入超時或無資料")
                return []

            # 點擊下載按鈕
            download_success = self._click_download_button()
            if not download_success:
                safe_print(f"❌ 第 {period} 期下載按鈕點擊失敗")
                return []

            # 等待檔案下載
            downloaded_files = self._wait_for_download(files_before)

            if downloaded_files:
                # 重命名檔案（格式：{帳號}_{開始日期}_{結束日期}）
                renamed_files = self._rename_period_files(downloaded_files, start_date, end_date)
                return renamed_files
            else:
                return []

        except Exception as e:
            safe_print(f"❌ 第 {period} 期資料下載失敗: {e}")
            return []

    def _calculate_period_dates(self, period):
        """計算週期的開始和結束日期"""
        try:
            # 以當前日期為基準，往前推算週期
            today = datetime.now()

            # 計算該週期的結束日期（每週期7天）
            period_end = today - timedelta(days=(period - 1) * 7)
            # 計算該週期的開始日期
            period_start = period_end - timedelta(days=6)

            start_date = period_start.strftime("%Y%m%d")
            end_date = period_end.strftime("%Y%m%d")

            return start_date, end_date

        except Exception as e:
            safe_print(f"❌ 週期日期計算失敗: {e}")
            # 回傳預設值
            today = datetime.now()
            start_date = (today - timedelta(days=7)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")
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
                search_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'][value*='搜'], input[type='button'][value*='搜'], button[value*='搜']")
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
        """等待搜尋結果載入"""
        safe_print("⏳ 等待搜尋結果載入...")

        for i in range(timeout):
            try:
                # 檢查多種可能的下載按鈕 ID
                download_button_ids = ["lnkbtnDownload", "btnDownload", "lnkDownload"]
                download_button_found = False

                for button_id in download_button_ids:
                    try:
                        download_button = self.driver.find_element(By.ID, button_id)
                        if download_button and download_button.is_displayed() and download_button.is_enabled():
                            safe_print(f"✅ 搜尋結果載入完成，下載按鈕已準備就緒: {button_id} ({i+1} 秒)")
                            return True
                    except:
                        continue

                # 如果沒找到特定 ID，嘗試搜尋下載相關的連結或按鈕
                try:
                    download_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '下載') or contains(text(), '明細下載') or contains(text(), '交易明細下載')]")
                    for element in download_elements:
                        if element.is_displayed() and element.is_enabled():
                            safe_print(f"✅ 搜尋結果載入完成，找到下載元素 ({i+1} 秒)")
                            return True
                except:
                    pass

            except Exception:
                pass

            time.sleep(1)
            if (i + 1) % 5 == 0:  # 每5秒報告一次
                safe_print(f"   等待搜尋結果中... ({i+1}/{timeout} 秒)")

        safe_print("⚠️ 搜尋結果載入超時，可能沒有符合條件的資料")
        return False

    def _click_download_button(self):
        """點擊交易明細下載按鈕"""
        safe_print("🖱️ 點擊交易明細下載按鈕...")

        try:
            download_button = None

            # 方法1: 嘗試多種可能的下載按鈕 ID
            download_button_ids = ["lnkbtnDownload", "btnDownload", "lnkDownload"]

            for button_id in download_button_ids:
                try:
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
                    ("CSS", "button[value*='下載']")
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
                safe_print("❌ 找不到任何下載按鈕，可能沒有資料可下載")
                return False

            # 點擊下載按鈕
            safe_print("🖱️ 執行下載點擊...")

            # 使用 JavaScript 點擊以避免攔截問題
            self.driver.execute_script("arguments[0].click();", download_button)

            # 處理可能的確認對話框
            time.sleep(1)
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
            safe_print(f"❌ 點擊下載按鈕失敗: {e}")
            return False

    def _wait_for_download(self, files_before, timeout=60):
        """等待檔案下載完成"""
        safe_print(f"⏳ 等待檔案下載完成（最多 {timeout} 秒）...")

        for i in range(timeout):
            time.sleep(1)
            files_after = set(self.download_dir.glob("*"))
            new_files = files_after - files_before

            if new_files:
                # 檢查檔案是否下載完成（不是 .crdownload 或 .tmp）
                completed_files = []
                for file_path in new_files:
                    if not str(file_path).endswith(('.crdownload', '.tmp', '.part')):
                        completed_files.append(file_path)

                if completed_files:
                    safe_print(f"✅ 檔案下載完成: {len(completed_files)} 個檔案")
                    return completed_files

            if i % 10 == 0:
                safe_print(f"   等待中... ({i}/{timeout} 秒)")

        safe_print("⚠️ 檔案下載超時")
        return []

    def _rename_period_files(self, downloaded_files, start_date, end_date):
        """重命名下載的檔案（格式：{帳號}_{開始日期}_{結束日期}）"""
        renamed_files = []

        for file_path in downloaded_files:
            try:
                original_name = file_path.stem
                extension = file_path.suffix

                # 新的檔案名稱格式：{帳號}_{開始日期}_{結束日期}
                new_name = f"{self.username}_{start_date}_{end_date}{extension}"
                new_path = file_path.parent / new_name

                # 如果目標檔案已存在，添加序號
                counter = 1
                while new_path.exists():
                    base_name = f"{self.username}_{start_date}_{end_date}_{counter}{extension}"
                    new_path = file_path.parent / base_name
                    counter += 1

                file_path.rename(new_path)
                renamed_files.append(new_path)
                safe_print(f"✅ 檔案重命名: {file_path.name} → {new_path.name}")

            except Exception as e:
                safe_print(f"⚠️ 檔案重命名失敗 {file_path.name}: {e}")
                renamed_files.append(file_path)  # 保留原始檔案

        return renamed_files

    def run_full_process(self):
        """執行完整的交易明細查詢自動化流程"""
        downloaded_files = []

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
                return {
                    "success": False,
                    "username": self.username,
                    "error": "登入失敗",
                    "downloads": []
                }

            # 3. 導航到交易明細表頁面
            nav_success = self.navigate_to_transaction_detail()
            if not nav_success:
                safe_print(f"❌ 帳號 {self.username} 導航失敗")
                return {
                    "success": False,
                    "username": self.username,
                    "error": "導航失敗",
                    "downloads": []
                }

            # 4. 設定週期搜尋方式
            period_success = self.set_period_search()
            if not period_success:
                safe_print(f"⚠️ 帳號 {self.username} 週期設定失敗，但繼續執行")

            # 5. 搜尋並下載各週期的交易明細
            downloaded_files = self.search_and_download_periods()

            if downloaded_files:
                safe_print(f"🎉 帳號 {self.username} 交易明細查詢流程完成！下載了 {len(downloaded_files)} 個檔案")
                return {
                    "success": True,
                    "username": self.username,
                    "downloads": [str(f) for f in downloaded_files]
                }
            else:
                safe_print(f"⚠️ 帳號 {self.username} 沒有下載到檔案")
                return {
                    "success": True,
                    "username": self.username,
                    "message": "無資料可下載",
                    "downloads": []
                }

        except Exception as e:
            safe_print(f"💥 帳號 {self.username} 流程執行失敗: {e}")
            return {
                "success": False,
                "username": self.username,
                "error": str(e),
                "downloads": [str(f) for f in downloaded_files]
            }
        finally:
            self.close()


def main():
    """主程式入口"""
    import argparse

    parser = argparse.ArgumentParser(description='黑貓宅急便交易明細表自動下載工具')
    parser.add_argument('--headless', action='store_true', help='使用無頭模式')
    parser.add_argument('--periods', type=int, default=2, help='要下載的週期數量 (預設: 2)')

    args = parser.parse_args()

    try:
        safe_print("🚛 黑貓宅急便交易明細表自動下載工具")

        manager = MultiAccountManager("accounts.json")
        # 只有在使用者明確指定 --headless 時才覆蓋設定檔
        headless_arg = True if '--headless' in sys.argv else None
        manager.run_all_accounts(
            UnpaidScraper,
            headless_override=headless_arg,
            periods=args.periods
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