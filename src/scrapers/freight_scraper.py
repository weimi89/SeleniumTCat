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


class FreightScraper(BaseScraper):
    """
    黑貓宅急便運費查詢自動下載工具
    繼承自 BaseScraper，複用登入和驗證碼處理功能
    """

    def __init__(self, username, password, headless=False, download_base_dir="downloads", start_date=None, end_date=None):
        # 呼叫父類建構子
        super().__init__(username, password, headless, download_base_dir)

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
                last_month = datetime.now().replace(day=1) - timedelta(days=1)
                self.end_date = last_month.strftime("%Y%m%d")

        safe_print(f"📅 查詢日期範圍: {self.start_date} - {self.end_date}")

    def navigate_to_freight_query(self):
        """導航到對帳單明細頁面"""
        safe_print("🧭 導航到對帳單明細頁面...")

        try:
            # 等待登入完成
            safe_print("⏳ 等待登入完成...")
            time.sleep(5)

            # 方法1: 嘗試直接使用 URL
            direct_success = self._try_direct_freight_url()
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

    def _try_direct_freight_url(self):
        """嘗試直接訪問對帳單明細頁面"""
        try:
            # 基於用戶提供的正確 URL 格式，參考 PaymentScraper 的成功模式
            direct_urls = [
                # 使用 RedirectFunc 的正確方式（基於用戶提供的 FuncNo=166）
                'https://www.takkyubin.com.tw/YMTContract/aspx/RedirectFunc.aspx?FuncNo=166',
                # 其他可能的直接 URL
                'https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentList.aspx?SudaType=01&TimeOut=N',
                'https://www.takkyubin.com.tw/YMTContract/aspx/SudaPaymentList.aspx',
            ]

            for full_url in direct_urls:
                try:
                    safe_print(f"🎯 嘗試直接訪問: {full_url}")

                    self.driver.get(full_url)
                    time.sleep(5)  # 增加等待時間以確保頁面完全載入

                    # 檢查是否成功到達對帳單明細頁面
                    if self._is_freight_page():
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

            time.sleep(3)  # 等待選單展開

            # 步驟2: 尋找並點擊「對帳單明細」
            statement_success = self._click_statement_detail_menu()
            if not statement_success:
                safe_print("❌ 找不到對帳單明細選項")
                self.driver.switch_to.default_content()
                return False

            # 等待頁面載入
            time.sleep(5)

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

    def _click_statement_detail_menu(self):
        """點擊對帳單明細選項"""
        try:
            # 基於用戶提供的連結特徵
            statement_keywords = ["對帳單明細", "對帳單", "明細"]

            # 特別尋找包含 RedirectFunc.aspx?FuncNo=166 的連結
            links = self.driver.find_elements(By.TAG_NAME, "a")

            for link in links:
                try:
                    href = link.get_attribute('href') or ''
                    text = link.text or ''

                    # 優先匹配特定的 URL 模式
                    if 'RedirectFunc.aspx?FuncNo=166' in href:
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
            url_indicators = [
                "SudaPaymentList.aspx",
                "SudaType=01"
            ]

            # 基於真實 HTML 結構的精確內容檢查
            content_indicators = [
                "速達應付帳款查詢",  # 基於 HTML 中的 lblSudaType
                "發票日期區間",      # 基於表格標題
                "txtDateS",         # 開始日期輸入框 ID
                "txtDateE",         # 結束日期輸入框 ID
                "btnSearch",        # 搜尋按鈕 ID
                "客戶帳號",          # 基於表格標題
                "查詢種類"          # 基於表格標題
            ]

            url_match = any(indicator in current_url for indicator in url_indicators)
            content_match = any(indicator in page_source for indicator in content_indicators)

            # 更精確的元素檢查
            element_check = False
            try:
                # 檢查關鍵元素是否存在
                key_elements = [
                    ("ID", "txtDateS"),
                    ("ID", "txtDateE"),
                    ("ID", "btnSearch")
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

        for i in range(timeout):
            try:
                # 檢查下載按鈕是否出現且可用
                download_button = self.driver.find_element(By.ID, "btnDownload")
                if download_button and download_button.is_displayed() and download_button.is_enabled():
                    safe_print(f"✅ AJAX 載入完成，下載按鈕已準備就緒 ({i+1} 秒)")
                    return True

            except Exception:
                pass

            time.sleep(1)
            if (i + 1) % 5 == 0:  # 每5秒報告一次
                safe_print(f"   等待 AJAX 結果中... ({i+1}/{timeout} 秒)")

        safe_print("⚠️ AJAX 結果載入超時，可能沒有符合條件的資料")
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
                    ("CSS", "input[type='submit'][value*='搜尋']")
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

            # 短暫等待讓 AJAX 開始
            time.sleep(1)
            return True

        except Exception as e:
            safe_print(f"❌ 點擊搜尋按鈕失敗: {e}")
            return False

    def _download_results(self):
        """下載搜尋結果"""
        safe_print("📥 開始下載搜尋結果...")

        try:
            # 首先解析表格資料以獲取發票資訊
            invoice_data = self._parse_invoice_table()

            # 記錄下載前的檔案
            files_before = set(self.download_dir.glob("*"))

            # 使用確切的 btnDownload ID（基於用戶提供的 HTML）
            download_button = None
            try:
                download_button = self.driver.find_element(By.ID, "btnDownload")
                if download_button and download_button.is_displayed() and download_button.is_enabled():
                    safe_print("✅ 找到下載按鈕: btnDownload (ID)")
                else:
                    safe_print("⚠️ btnDownload 按鈕存在但不可用")
                    return []
            except Exception as e:
                safe_print(f"❌ 找不到 btnDownload 按鈕: {e}")

                # 備用方法：尋找明細下載按鈕
                backup_selectors = [
                    ("NAME", "btnDownload"),
                    ("VALUE", "明細下載"),
                    ("CSS", "input[type='submit'][value='明細下載']")
                ]

                for method, selector in backup_selectors:
                    try:
                        if method == "NAME":
                            download_button = self.driver.find_element(By.NAME, selector)
                        elif method == "VALUE":
                            download_button = self.driver.find_element(By.CSS_SELECTOR, f"input[value='{selector}']")
                        elif method == "CSS":
                            download_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                        if download_button and download_button.is_displayed() and download_button.is_enabled():
                            safe_print(f"✅ 找到備用下載按鈕: {method}={selector}")
                            break

                    except Exception:
                        continue

            if not download_button:
                safe_print("❌ 找不到任何下載按鈕，可能沒有資料可下載")
                return []

            # 點擊下載按鈕
            safe_print("🖱️ 點擊明細下載按鈕...")

            # 處理可能的確認對話框
            try:
                self.driver.execute_script("arguments[0].click();", download_button)

                # 檢查是否有確認對話框
                time.sleep(1)
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    safe_print(f"🔔 發現確認對話框: {alert_text}")
                    alert.accept()
                    safe_print("✅ 已確認下載")
                except Exception:
                    pass  # 沒有對話框

            except Exception as e:
                safe_print(f"❌ 點擊下載按鈕失敗: {e}")
                return []

            # 等待檔案下載
            safe_print("⏳ 等待檔案下載...")
            downloaded_files = self._wait_for_download(files_before)

            if downloaded_files:
                # 重命名檔案（格式：{帳號}_{發票日期}_{發票號碼}）
                renamed_files = self._rename_downloaded_files_with_invoice_info(downloaded_files, invoice_data)
                safe_print(f"✅ 成功下載並重命名 {len(renamed_files)} 個檔案")
                return renamed_files
            else:
                safe_print("⚠️ 沒有檢測到新的下載檔案")
                return []

        except Exception as e:
            safe_print(f"❌ 下載失敗: {e}")
            return []

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
                                date_parts = invoice_date.split('/')
                                if len(date_parts) == 3:
                                    formatted_date = f"{date_parts[0]}{date_parts[1].zfill(2)}{date_parts[2].zfill(2)}"
                                else:
                                    formatted_date = invoice_date.replace('/', '')
                            except:
                                formatted_date = invoice_date.replace('/', '')

                            invoice_info = {
                                'customer_code': customer_code,
                                'invoice_date': formatted_date,
                                'invoice_number': invoice_number
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
                    new_name = f"{self.username}_{first_invoice['invoice_date']}_{first_invoice['invoice_number']}{extension}"
                else:
                    # 備用格式：使用日期範圍
                    new_name = f"{self.username}_{self.start_date}-{self.end_date}_{original_name}{extension}"

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
                renamed_files.append(file_path)  # 保留原始檔案

        return renamed_files

    def _rename_downloaded_files(self, downloaded_files):
        """重命名下載的檔案（備用方法）"""
        renamed_files = []

        for file_path in downloaded_files:
            try:
                # 生成新的檔案名稱（格式：{帳號}_{發票日期}_{發票號碼}）
                # 這裡使用月份範圍作為日期部分，實際可能需要從檔案內容或頁面獲取具體發票信息
                original_name = file_path.stem
                extension = file_path.suffix

                # 簡化的命名格式
                new_name = f"{self.username}_{self.start_date}-{self.end_date}_{original_name}{extension}"
                new_path = file_path.parent / new_name

                # 如果目標檔案已存在，添加序號
                counter = 1
                while new_path.exists():
                    base_name = f"{self.username}_{self.start_date}-{self.end_date}_{original_name}_{counter}{extension}"
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
        """執行完整的運費查詢自動化流程"""
        downloaded_files = []

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
                return {
                    "success": False,
                    "username": self.username,
                    "error": "登入失敗",
                    "downloads": []
                }

            # 3. 導航到對帳單明細頁面
            nav_success = self.navigate_to_freight_query()
            if not nav_success:
                safe_print(f"❌ 帳號 {self.username} 導航失敗")
                return {
                    "success": False,
                    "username": self.username,
                    "error": "導航失敗",
                    "downloads": []
                }

            # 4. 設定發票日期區間
            date_success = self.set_invoice_date_range()
            if not date_success:
                safe_print(f"⚠️ 帳號 {self.username} 日期設定失敗，但繼續執行")

            # 5. 搜尋並下載對帳單明細
            downloaded_files = self.search_and_download_statement()

            if downloaded_files:
                safe_print(f"🎉 帳號 {self.username} 運費查詢流程完成！下載了 {len(downloaded_files)} 個檔案")
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

    parser = argparse.ArgumentParser(description='黑貓宅急便運費查詢自動下載工具')
    parser.add_argument('--headless', action='store_true', help='使用無頭模式')
    parser.add_argument('--start-date', type=str, help='開始日期 (格式: YYYYMMDD)')
    parser.add_argument('--end-date', type=str, help='結束日期 (格式: YYYYMMDD)')

    args = parser.parse_args()

    try:
        safe_print("🚛 黑貓宅急便運費查詢自動下載工具")

        manager = MultiAccountManager("accounts.json")
        # 只有在使用者明確指定 --headless 時才覆蓋設定檔
        headless_arg = True if '--headless' in sys.argv else None
        manager.run_all_accounts(
            FreightScraper,
            headless_override=headless_arg,
            start_date=args.start_date,
            end_date=args.end_date
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