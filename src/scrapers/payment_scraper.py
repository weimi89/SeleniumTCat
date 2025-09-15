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


class PaymentScraper(BaseScraper):
    """
    使用 Selenium 的黑貓宅急便自動登入抓取工具
    繼承自 BaseScraper，複用登入和驗證碼處理功能
    """

    def __init__(self, username, password, headless=False, download_base_dir="downloads", period_number=1):
        # 呼叫父類建構子
        super().__init__(username, password, headless, download_base_dir)

        # PaymentScraper 特有的屬性
        # 儲存當前選擇的結算區間
        self.current_settlement_period = None

        # 期數設定 (1=最新一期, 2=第二新期數, 依此類推)
        self.period_number = period_number

        # 儲存要下載的多期資訊
        self.periods_to_download = []

    def navigate_to_payment_query(self):
        """導航到貨到付款查詢頁面 - 優先使用直接 URL"""
        safe_print("🧭 導航到貨到付款查詢頁面...")

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
            safe_print("⚠️ 直接 URL 失敗，嘗試框架導航...")
            frame_success = self._wait_for_frame_content()
            if frame_success:
                return self._navigate_in_frame()

            safe_print("❌ 所有導航方法都失敗了")
            return False

        except Exception as e:
            safe_print(f"❌ 導航失敗: {e}")
            return False

    def _wait_for_frame_content(self):
        """等待框架內容載入並尋找導航元素"""
        safe_print("🔍 等待框架內容載入...")

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

        safe_print("❌ 框架內容載入超時")
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
                safe_print("❌ 找不到帳務選單，嘗試直接尋找貨到付款選項...")
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
            safe_print(f"❌ 框架內導航失敗: {e}")
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
                        safe_print(f"✅ 成功導航到: {current_url}")
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

    def get_settlement_periods_for_download(self):
        """根據期數下載最新N期的結算區間 - 專門處理 ddlDate 選單"""
        safe_print(f"📅 準備下載最新 {self.period_number} 期結算區間...")

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
                            # 獲取所有有效的結算區間選項
                            valid_options = [opt for opt in options if opt.text.strip()]

                            if valid_options:
                                # 確定實際要下載的期數
                                actual_periods = min(self.period_number, len(valid_options))
                                safe_print(f"   📋 找到 {len(valid_options)} 期可用，將下載最新 {actual_periods} 期")

                                # 儲存所有要下載的期數資訊
                                self.periods_to_download = []
                                for i in range(actual_periods):
                                    period_option = valid_options[i]
                                    period_text = period_option.text.strip()
                                    self.periods_to_download.append({
                                        'option': period_option,
                                        'text': period_text,
                                        'index': i + 1
                                    })
                                    safe_print(f"      期數 {i+1}: {period_text}")

                                selected_period = True
                                # 先選擇第一期作為起始點
                                try:
                                    first_valid_index = None
                                    for idx, opt in enumerate(options):
                                        if opt.text.strip():
                                            first_valid_index = idx
                                            break

                                    if first_valid_index is not None:
                                        select_obj.select_by_index(first_valid_index)
                                        time.sleep(2)
                                        self.current_settlement_period = valid_options[0].text.strip()
                                        safe_print(f"   ✅ 已選擇第 1 期作為起始: {self.current_settlement_period}")
                                        break
                                except Exception as select_e:
                                    safe_print(f"   ❌ 選擇第 1 期失敗: {select_e}")
                            else:
                                safe_print("   ⚠️ 沒有找到有效的結算期間選項")
                        else:
                            print("   ⚠️ 選項不包含日期相關內容，跳過此選單")

                except Exception as e:
                    print(f"   處理選單 {i} 失敗: {e}")
                    continue

            if not selected_period:
                safe_print("⚠️ 未能自動選擇結算期間，使用預設值繼續")

            return selected_period

        except Exception as e:
            safe_print(f"❌ 獲取結算區間失敗: {e}")
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
            safe_print(f"⚠️ 格式化結算期間失敗: {e}")
            # 返回安全的檔案名
            safe_text = re.sub(r'[^\w\-]', '_', period_text)
            return safe_text

    def download_cod_statement(self):
        """下載貨到付款匯款明細表"""
        safe_print("📥 開始下載貨到付款匯款明細表...")

        try:
            # 等待頁面載入
            time.sleep(3)

            # 首先嘗試執行查詢（有些頁面需要先查詢才會顯示下載按鈕）
            safe_print("🔍 執行查詢...")

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
            safe_print("🔍 尋找對帳單下載按鈕...")

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
                safe_print(f"📥 找到 {len(download_buttons_found)} 個可能的下載按鈕")

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

                        # 檢查是否有瀏覽器下載權限對話框並處理
                        try:
                            time.sleep(2)  # 等待可能的對話框出現

                            # 方法1：處理瀏覽器原生的權限對話框
                            try:
                                # 嘗試切換到可能的alert
                                alert = self.driver.switch_to.alert
                                alert_text = alert.text
                                print(f"   🔔 發現瀏覽器對話框: {alert_text}")
                                alert.accept()  # 點擊允許/確定
                                print("   ✅ 已自動允許下載權限")
                            except Exception:
                                pass  # 沒有alert對話框

                            # 方法2：處理Chrome的下載權限UI
                            self.driver.execute_script("""
                                // 自動點擊 "允許" 按鈕
                                const allowButtons = document.querySelectorAll('button, [role="button"]');
                                for (const button of allowButtons) {
                                    const text = button.textContent || button.innerText || '';
                                    if (text.includes('允許') ||
                                        text.includes('Allow') ||
                                        text.includes('允') ||
                                        text.includes('下載') ||
                                        text.includes('繼續')) {
                                        button.click();
                                        console.log('已點擊允許按鈕:', text);
                                        break;
                                    }
                                }
                            """)
                        except Exception as dialog_e:
                            pass  # 忽略對話框處理錯誤

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
                formatted_period = self.format_settlement_period_for_filename(self.current_settlement_period)
                target_filename = f"{self.username}_{formatted_period}.xlsx"
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
            safe_print(f"❌ 下載失敗: {e}")
            return []

    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            safe_print("🔚 瀏覽器已關閉")

    def run_full_process(self):
        """執行完整的自動化流程"""
        success = False
        downloaded_files = []

        try:
            print("=" * 60)
            safe_print(f"🤖 開始執行黑貓宅急便自動下載流程 (帳號: {self.username})")
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

            # 3. 導航到貨到付款查詢頁面
            nav_success = self.navigate_to_payment_query()
            if not nav_success:
                safe_print(f"❌ 帳號 {self.username} 導航失敗")
                return {
                    "success": False,
                    "username": self.username,
                    "error": "導航失敗",
                    "downloads": []
                }

            # 4. 獲取要下載的多期結算期間資訊
            periods_success = self.get_settlement_periods_for_download()
            if not periods_success:
                safe_print(f"⚠️ 帳號 {self.username} 未能獲取結算期間資訊，但嘗試繼續執行")
                # 如果獲取期間失敗，嘗試下載預設的一期
                downloaded_files = self.download_cod_statement()
            else:
                # 5. 逐一下載每期的貨到付款匯款明細表
                safe_print(f"🎯 開始下載 {len(self.periods_to_download)} 期資料...")

                for period_info in self.periods_to_download:
                    try:
                        safe_print(f"📅 處理第 {period_info['index']} 期: {period_info['text']}")

                        # 選擇當前期數
                        self.current_settlement_period = period_info['text']

                        # 重新選擇期數
                        try:
                            from selenium.webdriver.support.ui import Select
                            # 尋找日期選單
                            date_selects = self.driver.find_elements(By.NAME, "ddlDate")
                            if not date_selects:
                                date_selects = self.driver.find_elements(By.CSS_SELECTOR,
                                    "select[name*='date'], select[name*='Date'], select[id*='date'], select[id*='Date']")

                            for select_element in date_selects:
                                select_obj = Select(select_element)
                                options = select_obj.options

                                # 找到對應的選項並選擇
                                for option in options:
                                    if option.text.strip() == period_info['text']:
                                        select_obj.select_by_visible_text(period_info['text'])
                                        time.sleep(2)
                                        safe_print(f"   ✅ 已選擇期數: {period_info['text']}")
                                        break
                                break
                        except Exception as select_e:
                            safe_print(f"   ⚠️ 選擇期數失敗: {select_e}，繼續嘗試下載")

                        # 下載當期資料
                        period_files = self.download_cod_statement()
                        if period_files:
                            downloaded_files.extend(period_files)
                            safe_print(f"   ✅ 第 {period_info['index']} 期下載完成: {len(period_files)} 個檔案")
                        else:
                            safe_print(f"   ⚠️ 第 {period_info['index']} 期未找到可下載的檔案")

                    except Exception as period_e:
                        safe_print(f"   ❌ 處理第 {period_info['index']} 期失敗: {period_e}")
                        continue

            if downloaded_files:
                safe_print(f"🎉 帳號 {self.username} 自動化流程完成！下載了 {len(downloaded_files)} 個檔案")
                success = True
            else:
                safe_print(f"⚠️ 帳號 {self.username} 沒有下載到任何檔案")

            return {
                "success": success,
                "username": self.username,
                "downloads": [str(f) for f in downloaded_files]  # 轉換 PosixPath 為字串
            }

        except Exception as e:
            safe_print(f"💥 帳號 {self.username} 流程執行失敗: {e}")
            return {
                "success": False,
                "username": self.username,
                "error": str(e),
                "downloads": [str(f) for f in downloaded_files]  # 轉換 PosixPath 為字串
            }
        finally:
            self.close()



def main():
    """主程式入口"""
    import argparse

    parser = argparse.ArgumentParser(description='黑貓宅急便自動下載工具')
    parser.add_argument('--headless', action='store_true', help='使用無頭模式')
    parser.add_argument('--period', type=int, default=1, help='指定下載的期數 (1=最新一期, 2=第二新期數, 依此類推)')

    args = parser.parse_args()

    try:
        print("🐱 黑貓宅急便自動下載工具")

        manager = MultiAccountManager("accounts.json")
        # 只有在使用者明確指定 --headless 時才覆蓋設定檔
        headless_arg = True if '--headless' in sys.argv else None
        manager.run_all_accounts(
            PaymentScraper,
            headless_override=headless_arg,
            period_number=args.period
        )

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