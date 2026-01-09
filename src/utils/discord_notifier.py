#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord 通知工具模組
"""

import os
import requests
from typing import List, Dict, Optional
from .windows_encoding_utils import safe_print


class DiscordNotifier:
    """Discord Webhook 通知器"""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        初始化 Discord 通知器

        Args:
            webhook_url: Discord Webhook URL（若不提供則從環境變數讀取）
        """
        webhook_url_raw = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        # 清理可能的格式問題（移除開頭的 = 或引號）
        if webhook_url_raw:
            webhook_url_raw = webhook_url_raw.strip().lstrip('=').strip('"').strip("'")
        self.webhook_url = webhook_url_raw if webhook_url_raw else None

    def is_enabled(self) -> bool:
        """檢查是否啟用 Discord 通知"""
        return bool(self.webhook_url)

    def send_message(self, content: str, embeds: Optional[List[Dict]] = None) -> bool:
        """
        發送訊息到 Discord

        Args:
            content: 訊息內容
            embeds: 嵌入式訊息（可選）

        Returns:
            bool: 是否成功發送
        """
        if not self.is_enabled():
            safe_print("⚠️  Discord Webhook URL 未設定，跳過通知")
            return False

        try:
            payload = {"content": content}
            if embeds:
                payload["embeds"] = embeds

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code in (200, 204):
                safe_print("✅ Discord 通知發送成功")
                return True
            else:
                safe_print(f"⚠️  Discord 通知發送失敗: HTTP {response.status_code}")
                safe_print(f"   回應內容: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            safe_print(f"❌ Discord 通知發送錯誤: {e}")
            return False
        except Exception as e:
            safe_print(f"❌ Discord 通知發生未預期的錯誤: {e}")
            return False

    def send_security_warning_notification(
        self, security_warning_accounts: List[Dict], function_name: str = "", **kwargs
    ) -> bool:
        """
        發送密碼安全警告通知

        Args:
            security_warning_accounts: 密碼安全警告帳號列表
            function_name: 執行的功能名稱

        Returns:
            bool: 是否成功發送
        """
        if not security_warning_accounts:
            return False

        if not self.is_enabled():
            return False

        # 組合帳號列表
        account_list = "\n".join([
            f"• `{result['username']}`"
            for result in security_warning_accounts
        ])

        # 建立嵌入式訊息
        title = f"🔐 【{function_name}】密碼更新提醒" if function_name else "🔐 密碼更新提醒"
        embed = {
            "title": title,
            "description": (
                f"偵測到 **{len(security_warning_accounts)}** 個帳號需要更新密碼\n\n"
                f"這些帳號因安全政策要求，必須更新密碼後才能繼續使用。"
            ),
            "color": 15105570,  # 橘色
            "fields": [
                {
                    "name": "🔑 需更新密碼的帳號",
                    "value": account_list,
                    "inline": False
                },
                {
                    "name": "📋 處理步驟",
                    "value": (
                        "1️⃣ 登入 [黑貓宅急便契客專區](https://www.t-cat.com.tw/)\n"
                        "2️⃣ 依照系統提示更新密碼\n"
                        "3️⃣ 更新 `accounts.json` 中的密碼"
                    ),
                    "inline": False
                }
            ],
            "footer": {
                "text": "黑貓宅急便自動化工具"
            }
        }

        # 發送通知
        func_text = f"【{function_name}】" if function_name else ""
        return self.send_message(
            content=f"@here {func_text}發現 **{len(security_warning_accounts)}** 個帳號需要更新密碼！",
            embeds=[embed],
        )

    def send_execution_summary(
        self,
        total_accounts: int,
        successful_accounts: int,
        failed_accounts: int,
        security_warning_accounts: int,
        total_downloads: int,
        total_execution_minutes: float,
        function_name: str = "",
        downloaded_files: Optional[List[Dict]] = None,
    ) -> bool:
        """
        發送執行摘要通知

        Args:
            total_accounts: 總帳號數
            successful_accounts: 成功帳號數
            failed_accounts: 失敗帳號數
            security_warning_accounts: 密碼安全警告帳號數
            total_downloads: 總下載檔案數
            total_execution_minutes: 總執行時間（分鐘）
            function_name: 執行的功能名稱
            downloaded_files: 下載的檔案清單 [{"username": "...", "filename": "..."}]

        Returns:
            bool: 是否成功發送
        """
        if not self.is_enabled():
            return False

        if downloaded_files is None:
            downloaded_files = []

        # 計算成功率
        success_rate = (successful_accounts / total_accounts * 100) if total_accounts > 0 else 0

        # 根據結果決定顏色和狀態
        if security_warning_accounts > 0:
            color = 16744192  # 橘紅色
            status_emoji = "🚨"
            status_text = "需要注意"
        elif failed_accounts > 0:
            color = 15158332  # 紅色
            status_emoji = "⚠️"
            status_text = "部分失敗"
        elif successful_accounts == total_accounts:
            color = 3066993  # 綠色
            status_emoji = "✅"
            status_text = "全部成功"
        else:
            color = 3447003  # 藍色
            status_emoji = "📊"
            status_text = "執行完成"

        # 建立進度條視覺化
        bar_length = 10
        filled = int(success_rate / 100 * bar_length)
        progress_bar = "🟩" * filled + "⬜" * (bar_length - filled)

        # 建立嵌入式訊息
        embed = {
            "title": f"{status_emoji} 【{function_name}】執行報告" if function_name else f"{status_emoji} 執行報告",
            "description": f"```\n{progress_bar}  {success_rate:.0f}%\n```",
            "color": color,
            "fields": [],
            "footer": {
                "text": f"黑貓宅急便自動化工具 • 執行時間: {total_execution_minutes:.2f} 分鐘"
            }
        }

        # 狀態區塊
        embed["fields"].append({
            "name": "📋 執行狀態",
            "value": f"**{status_text}**",
            "inline": False
        })

        # 帳號統計區塊
        account_stats = f"總計: **{total_accounts}** 個帳號\n"
        account_stats += f"✅ 成功: **{successful_accounts}**"
        if failed_accounts > 0:
            account_stats += f"　❌ 失敗: **{failed_accounts}**"
        if security_warning_accounts > 0:
            account_stats += f"\n🚨 密碼警告: **{security_warning_accounts}**"

        embed["fields"].append({
            "name": "👥 帳號統計",
            "value": account_stats,
            "inline": True
        })

        # 下載統計區塊
        download_stats = f"檔案數: **{total_downloads}** 個"
        if total_downloads > 0 and successful_accounts > 0:
            avg_per_account = total_downloads / successful_accounts
            download_stats += f"\n平均: **{avg_per_account:.1f}** 個/帳號"

        embed["fields"].append({
            "name": "📥 下載統計",
            "value": download_stats,
            "inline": True
        })

        # 下載檔案清單區塊
        if downloaded_files:
            # 按帳號分組顯示檔案
            files_by_account = {}
            for item in downloaded_files:
                username = item.get("username", "未知")
                filename = item.get("filename", "")
                if username not in files_by_account:
                    files_by_account[username] = []
                files_by_account[username].append(filename)

            # 組合檔案清單文字
            file_list_parts = []
            for username, files in files_by_account.items():
                for filename in files:
                    # 截短檔名避免太長
                    display_name = filename if len(filename) <= 40 else filename[:37] + "..."
                    file_list_parts.append(f"📄 `{display_name}`")

            # Discord embed field 最多 1024 字元
            file_list_text = "\n".join(file_list_parts)
            if len(file_list_text) > 1000:
                file_list_text = "\n".join(file_list_parts[:10])
                remaining = len(downloaded_files) - 10
                if remaining > 0:
                    file_list_text += f"\n... 還有 **{remaining}** 個檔案"

            embed["fields"].append({
                "name": "📁 下載檔案清單",
                "value": file_list_text if file_list_text else "無",
                "inline": False
            })
        else:
            embed["fields"].append({
                "name": "📁 下載檔案清單",
                "value": "無檔案下載",
                "inline": False
            })

        # 根據結果選擇通知內容
        if security_warning_accounts > 0:
            content = f"@here 【{function_name}】執行完成，發現 **{security_warning_accounts}** 個帳號需要更新密碼！"
        elif failed_accounts > 0:
            content = f"【{function_name}】執行完成，**{failed_accounts}** 個帳號處理失敗"
        else:
            content = f"【{function_name}】執行完成 ✨ 成功處理 **{successful_accounts}** 個帳號"

        return self.send_message(content=content, embeds=[embed])
