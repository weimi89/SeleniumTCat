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

from ..utils.windows_encoding_utils import safe_print


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

            safe_print(f"✅ 已載入設定檔: {self.config_file}")

        except json.JSONDecodeError as e:
            raise ValueError(f"⛔ 設定檔格式錯誤: {e}")
        except Exception as e:
            raise RuntimeError(f"⛔ 載入設定檔失敗: {e}")

    def get_enabled_accounts(self):
        """取得啟用的帳號列表"""
        return [acc for acc in self.config["accounts"] if acc.get("enabled", True)]

    def run_all_accounts(self, scraper_class, headless_override=None, progress_callback=None, **scraper_kwargs):
        """
        執行所有啟用的帳號

        Args:
            scraper_class: 要使用的抓取器類別 (例如 PaymentScraper)
            headless_override: 覆寫無頭模式設定
            progress_callback: 進度回呼函數
            **scraper_kwargs: 額外的 scraper 參數 (例如 period_number, start_date, end_date)
        """
        accounts = self.get_enabled_accounts()
        results = []
        settings = self.config.get("settings", {})

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
                # 優先級：命令列參數（如果有指定）> 設定檔 > 預設值 False
                if headless_override is not None:
                    use_headless = headless_override
                    safe_print(f"🔧 使用命令列 headless 設定: {use_headless}")
                else:
                    use_headless = settings.get("headless", False)
                    safe_print(f"🔧 使用設定檔 headless 設定: {use_headless}")

                # 準備 scraper 基本參數
                scraper_init_kwargs = {
                    "username": username,
                    "password": password,
                    "headless": use_headless,
                    "download_base_dir": settings.get("download_base_dir", "downloads")
                }

                # 合併額外的 scraper 參數
                scraper_init_kwargs.update(scraper_kwargs)

                scraper = scraper_class(**scraper_init_kwargs)
                result = scraper.run_full_process()
                results.append(result)

                # 帳號間暫停一下避免過於頻繁
                if i < len(accounts):
                    safe_print("⏳ 等待 3 秒後處理下一個帳號...")
                    time.sleep(3)

            except Exception as e:
                safe_print(f"💥 帳號 {username} 處理失敗: {e}")
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
        safe_print("📋 多帳號執行總結報告")
        print("=" * 80)

        successful_accounts = [r for r in results if r["success"]]
        failed_accounts = [r for r in results if not r["success"]]
        total_downloads = sum(len(r["downloads"]) for r in results)

        safe_print(f"📊 執行統計:")
        print(f"   總帳號數: {len(results)}")
        print(f"   成功帳號: {len(successful_accounts)}")
        print(f"   失敗帳號: {len(failed_accounts)}")
        print(f"   總下載檔案: {total_downloads}")

        if successful_accounts:
            safe_print(f"\n✅ 成功帳號詳情:")
            for result in successful_accounts:
                username = result["username"]
                download_count = len(result["downloads"])
                if result.get("message") == "無資料可下載":
                    safe_print(f"   🔸 {username}: 無資料可下載")
                else:
                    safe_print(f"   🔸 {username}: 成功下載 {download_count} 個檔案")

        if failed_accounts:
            safe_print(f"\n❌ 失敗帳號詳情:")
            for result in failed_accounts:
                username = result["username"]
                error = result.get("error", "未知錯誤")
                safe_print(f"   🔸 {username}: {error}")

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
                "records": len(result.get("records", [])) if result.get("records") else 0
            }
            if "error" in result:
                clean_result["error"] = result["error"]
            if "message" in result:
                clean_result["message"] = result["message"]
            clean_results.append(clean_result)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_accounts": len(results),
                "successful_accounts": len(successful_accounts),
                "failed_accounts": len(failed_accounts),
                "total_downloads": total_downloads,
                "details": clean_results
            }, f, ensure_ascii=False, indent=2)

        safe_print(f"\n💾 詳細報告已保存: {report_file}")
        print("=" * 80)