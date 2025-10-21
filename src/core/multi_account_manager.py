#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多帳號管理器共用模組
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from ..utils.windows_encoding_utils import safe_print
from ..utils.discord_notifier import DiscordNotifier


class MultiAccountManager:
    """多帳號管理器"""

    def __init__(self, config_file="accounts.json"):
        # 載入環境變數
        load_dotenv()

        self.config_file = config_file
        self.load_config()

        # 執行時間統計
        self.total_start_time = None
        self.total_end_time = None
        self.total_execution_minutes = 0

        # Discord 通知器
        self.discord_notifier = DiscordNotifier()

    def load_config(self):
        """載入設定檔"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"⛔ 設定檔 '{self.config_file}' 不存在！\n"
                "📝 請建立 accounts.json 檔案，格式為帳號陣列\n"
                "範例: [{\"username\": \"...\", \"password\": \"...\", \"enabled\": true}]"
            )

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 檢測舊格式（dict 且包含 accounts 或 settings）
            if isinstance(config, dict):
                safe_print("⚠️  警告: 檢測到舊的配置格式")
                safe_print("請將 accounts.json 改為純陣列格式，並移除 settings 設定")
                safe_print("範例: [{\"username\": \"...\", \"password\": \"...\", \"enabled\": true}]")
                safe_print("環境設定請改用 .env 檔案 (HEADLESS, PAYMENT_DOWNLOAD_DIR 等)")
                safe_print("詳細說明: README.md#配置遷移")
                safe_print("")

                # 嘗試自動提取 accounts 陣列（但仍警告）
                if "accounts" in config:
                    self.config = config["accounts"]
                    safe_print("✅ 暫時相容舊格式: 已自動提取 accounts 陣列")
                else:
                    raise ValueError("舊格式配置但沒有 'accounts' 欄位")

                # 檢查並警告舊的 settings
                if "settings" in config:
                    old_settings = config["settings"]
                    safe_print("⚠️  舊的 settings 設定將被忽略，請改用 .env 檔案:")
                    if "headless" in old_settings:
                        safe_print(f"   - HEADLESS={str(old_settings['headless']).lower()}")
                    if "download_base_dir" in old_settings:
                        safe_print(f"   - PAYMENT_DOWNLOAD_DIR={old_settings['download_base_dir']}")
                        safe_print(f"   - FREIGHT_DOWNLOAD_DIR={old_settings['download_base_dir']}")
                        safe_print(f"   - UNPAID_DOWNLOAD_DIR={old_settings['download_base_dir']}")
                    safe_print("")
            else:
                # 新格式（陣列）
                self.config = config

            if not self.config:
                raise ValueError("⛔ 設定檔中沒有找到帳號資訊！")

            safe_print(f"✅ 已載入設定檔: {self.config_file}")

        except json.JSONDecodeError as e:
            raise ValueError(f"⛔ 設定檔格式錯誤: {e}")
        except Exception as e:
            raise RuntimeError(f"⛔ 載入設定檔失敗: {e}")

    def get_enabled_accounts(self):
        """取得啟用的帳號列表"""
        return [acc for acc in self.config if acc.get("enabled", True)]

    def run_all_accounts(self, scraper_class, headless_override=None, progress_callback=None, **scraper_kwargs):
        """
        執行所有啟用的帳號

        Args:
            scraper_class: 要使用的抓取器類別 (例如 PaymentScraper)
            headless_override: 覆寫無頭模式設定
            progress_callback: 進度回呼函數
            **scraper_kwargs: 額外的 scraper 參數 (例如 period_number, start_date, end_date)
        """
        # 開始總執行時間計時
        self.total_start_time = datetime.now()
        safe_print(f"⏱️ 總執行開始時間: {self.total_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        accounts = self.get_enabled_accounts()
        results = []

        if progress_callback:
            progress_callback(f"🚀 開始執行多帳號黑貓宅急便自動下載 (共 {len(accounts)} 個帳號)")
        else:
            print("\n" + "=" * 80)
            safe_print(f"🚀 開始執行多帳號黑貓宅急便自動下載 (共 {len(accounts)} 個帳號)")
            print("=" * 80)

        for i, account in enumerate(accounts, 1):
            username = account["username"]
            password = account["password"]

            progress_msg = f"📊 [{i}/{len(accounts)}] 處理帳號: {username}"
            if progress_callback:
                progress_callback(progress_msg)
            else:
                print(f"\n{progress_msg}")
                print("-" * 50)

            try:
                # headless 優先級：命令列參數 > 環境變數 > 預設值
                # headless_override 傳遞給 scraper，由 scraper 處理優先級
                if headless_override is not None:
                    use_headless = headless_override
                    safe_print(f"🔧 使用命令列 headless 設定: {use_headless}")
                else:
                    # None 表示使用環境變數或預設值
                    use_headless = None
                    env_headless = os.getenv("HEADLESS", "true").lower()
                    safe_print(f"🔧 使用環境變數 HEADLESS 設定: {env_headless}")

                # 準備 scraper 基本參數
                scraper_init_kwargs = {
                    "username": username,
                    "password": password,
                    "headless": use_headless,
                }

                # 合併額外的 scraper 參數
                scraper_init_kwargs.update(scraper_kwargs)

                scraper = scraper_class(**scraper_init_kwargs)

                result = scraper.run_full_process()

                # 將時間統計添加到結果中
                execution_summary = scraper.get_execution_summary()
                result.update(execution_summary)

                results.append(result)

                # 帳號間隔等待 (保留此處固定等待)
                # 原因: 避免連續請求過於頻繁導致伺服器限制或封鎖
                # 此等待是有意的速率限制 (rate limiting)，不應優化移除
                if i < len(accounts):
                    safe_print("⏳ 等待 3 秒後處理下一個帳號...")
                    time.sleep(3)

            except Exception as e:
                safe_print(f"💥 帳號 {username} 處理失敗: {e}")
                results.append({"success": False, "username": username, "error": str(e), "downloads": []})
                continue

        # 結束總執行時間計時
        self.total_end_time = datetime.now()
        if self.total_start_time:
            total_duration = self.total_end_time - self.total_start_time
            self.total_execution_minutes = total_duration.total_seconds() / 60
            safe_print(f"⏱️ 總執行結束時間: {self.total_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            safe_print(f"📊 總執行時長: {self.total_execution_minutes:.2f} 分鐘")

        # 生成總報告
        self.generate_summary_report(results)
        return results

    def generate_summary_report(self, results):
        """生成總體執行報告"""
        print("\n" + "=" * 80)
        safe_print("📋 多帳號執行總結報告")
        print("=" * 80)

        successful_accounts = [r for r in results if r["success"]]
        failed_accounts = [r for r in results if not r["success"]]
        security_warning_accounts = [r for r in failed_accounts if r.get("error_type") == "security_warning"]
        other_failed_accounts = [r for r in failed_accounts if r.get("error_type") != "security_warning"]
        total_downloads = sum(len(r["downloads"]) for r in results)

        safe_print(f"📊 執行統計:")
        print(f"   總帳號數: {len(results)}")
        print(f"   成功帳號: {len(successful_accounts)}")
        print(f"   失敗帳號: {len(other_failed_accounts)}")
        if security_warning_accounts:
            print(f"   密碼安全警告: {len(security_warning_accounts)}")
        print(f"   總下載檔案: {total_downloads}")
        if hasattr(self, "total_execution_minutes") and self.total_execution_minutes > 0:
            print(f"   總執行時長: {self.total_execution_minutes:.2f} 分鐘")

        if successful_accounts:
            safe_print(f"\n✅ 成功帳號詳情:")
            for result in successful_accounts:
                username = result["username"]
                download_count = len(result["downloads"])
                duration_minutes = result.get("duration_minutes", 0)

                if result.get("message") == "無資料可下載":
                    safe_print(f"   🔸 {username}: 無資料可下載 (執行時間: {duration_minutes:.2f} 分鐘)")
                else:
                    safe_print(
                        f"   🔸 {username}: 成功下載 {download_count} 個檔案 (執行時間: {duration_minutes:.2f} 分鐘)"
                    )

                # 顯示期間詳細資訊（如果有的話）
                period_details = result.get("period_details", [])
                if period_details:
                    safe_print(f"      📅 期間詳情:")
                    for detail in period_details:
                        period = detail["period"]
                        start_date = detail["start_date"]
                        end_date = detail["end_date"]
                        status = detail["status"]
                        file_count = len(detail["files"])

                        if status == "success":
                            safe_print(
                                f"         第 {period} 期 ({start_date}-{end_date}): ✅ 成功下載 {file_count} 個檔案"
                            )
                        elif status == "no_records":
                            safe_print(f"         第 {period} 期 ({start_date}-{end_date}): ⚠️ 無交易記錄")
                        elif status == "search_failed":
                            safe_print(f"         第 {period} 期 ({start_date}-{end_date}): ❌ 搜尋失敗")
                        elif status == "download_failed":
                            safe_print(f"         第 {period} 期 ({start_date}-{end_date}): ❌ 下載失敗")
                        elif status == "download_timeout":
                            safe_print(f"         第 {period} 期 ({start_date}-{end_date}): ⏰ 下載超時")
                        else:
                            error_msg = detail.get("error", "未知錯誤")
                            safe_print(f"         第 {period} 期 ({start_date}-{end_date}): ❌ {error_msg}")

        if security_warning_accounts:
            safe_print(f"\n🚨 密碼安全警告帳號詳情:")
            for result in security_warning_accounts:
                username = result["username"]
                duration_minutes = result.get("duration_minutes", 0)
                safe_print(f"   🔸 {username}: 需要更新密碼才能繼續使用 (執行時間: {duration_minutes:.2f} 分鐘)")

        if other_failed_accounts:
            safe_print(f"\n❌ 失敗帳號詳情:")
            for result in other_failed_accounts:
                username = result["username"]
                error = result.get("error", "未知錯誤")
                duration_minutes = result.get("duration_minutes", 0)
                safe_print(f"   🔸 {username}: {error} (執行時間: {duration_minutes:.2f} 分鐘)")

        # 保存詳細報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{timestamp}.json"
        report_file = Path("reports") / report_filename

        # 確保 reports 目錄存在
        report_file.parent.mkdir(parents=True, exist_ok=True)

        # 清理結果中的不可序列化物件
        clean_results = []
        for result in results:
            clean_result = {
                "success": result["success"],
                "username": result["username"],
                "downloads": result["downloads"],
                "records": len(result.get("records", [])) if result.get("records") else 0,
                "duration_minutes": result.get("duration_minutes", 0),
                "start_time": result.get("start_time"),
                "end_time": result.get("end_time"),
            }
            if "error" in result:
                clean_result["error"] = result["error"]
            if "error_type" in result:
                clean_result["error_type"] = result["error_type"]
            if "message" in result:
                clean_result["message"] = result["message"]
            clean_results.append(clean_result)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_start_time": (
                        self.total_start_time.strftime("%Y-%m-%d %H:%M:%S") if self.total_start_time else None
                    ),
                    "total_end_time": (
                        self.total_end_time.strftime("%Y-%m-%d %H:%M:%S") if self.total_end_time else None
                    ),
                    "total_execution_minutes": (
                        round(self.total_execution_minutes, 2) if hasattr(self, "total_execution_minutes") else 0
                    ),
                    "total_accounts": len(results),
                    "successful_accounts": len(successful_accounts),
                    "failed_accounts": len(other_failed_accounts),
                    "security_warning_accounts": len(security_warning_accounts),
                    "total_downloads": total_downloads,
                    "details": clean_results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        safe_print(f"\n💾 詳細報告已保存: {report_file}")

        # 發送 Discord 通知
        if self.discord_notifier.is_enabled():
            safe_print("\n📢 正在發送 Discord 通知...")

            # 發送執行摘要
            self.discord_notifier.send_execution_summary(
                total_accounts=len(results),
                successful_accounts=len(successful_accounts),
                failed_accounts=len(other_failed_accounts),
                security_warning_accounts=len(security_warning_accounts),
                total_downloads=total_downloads,
                total_execution_minutes=self.total_execution_minutes if hasattr(self, "total_execution_minutes") else 0,
            )

            # 如果有密碼安全警告，額外發送詳細通知
            if security_warning_accounts:
                self.discord_notifier.send_security_warning_notification(
                    security_warning_accounts=security_warning_accounts,
                    total_execution_minutes=self.total_execution_minutes if hasattr(self, "total_execution_minutes") else 0,
                )

        print("=" * 80)
