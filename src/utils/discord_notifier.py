#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discord 通知工具模組
"""

import os
import json
import requests
from datetime import datetime
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
        self, security_warning_accounts: List[Dict], total_execution_minutes: float = 0
    ) -> bool:
        """
        發送密碼安全警告通知

        Args:
            security_warning_accounts: 密碼安全警告帳號列表
            total_execution_minutes: 總執行時間（分鐘）

        Returns:
            bool: 是否成功發送
        """
        if not security_warning_accounts:
            return False

        if not self.is_enabled():
            return False

        # 建立嵌入式訊息
        embed = {
            "title": "🚨 黑貓宅急便密碼安全警告",
            "description": f"偵測到 **{len(security_warning_accounts)}** 個帳號需要更新密碼",
            "color": 16744192,  # 橘紅色
            "timestamp": datetime.now().isoformat(),
            "fields": [],
        }

        # 加入每個帳號的詳細資訊
        for i, result in enumerate(security_warning_accounts, 1):
            username = result["username"]
            duration_minutes = result.get("duration_minutes", 0)

            embed["fields"].append(
                {
                    "name": f"帳號 {i}: {username}",
                    "value": f"⚠️ 需要更新密碼才能繼續使用\n⏱️ 執行時間: {duration_minutes:.2f} 分鐘",
                    "inline": False,
                }
            )

        # 加入總執行時間
        if total_execution_minutes > 0:
            embed["fields"].append(
                {
                    "name": "總執行時間",
                    "value": f"⏱️ {total_execution_minutes:.2f} 分鐘",
                    "inline": False,
                }
            )

        # 加入說明
        embed["footer"] = {
            "text": "請盡快登入黑貓宅急便網站更新這些帳號的密碼",
        }

        # 發送通知
        return self.send_message(
            content="@here 黑貓宅急便自動化執行完成，發現密碼安全警告！",
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

        Returns:
            bool: 是否成功發送
        """
        if not self.is_enabled():
            return False

        # 建立嵌入式訊息
        embed = {
            "title": "📊 黑貓宅急便執行摘要",
            "description": "多帳號自動化執行完成",
            "color": 3447003,  # 藍色
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {"name": "總帳號數", "value": str(total_accounts), "inline": True},
                {"name": "成功", "value": f"✅ {successful_accounts}", "inline": True},
                {"name": "失敗", "value": f"❌ {failed_accounts}", "inline": True},
                {"name": "密碼警告", "value": f"🚨 {security_warning_accounts}", "inline": True},
                {"name": "下載檔案", "value": f"📥 {total_downloads}", "inline": True},
                {"name": "執行時間", "value": f"⏱️ {total_execution_minutes:.2f} 分鐘", "inline": True},
            ],
        }

        # 根據結果選擇通知內容
        if security_warning_accounts > 0:
            content = "@here 執行完成，發現密碼安全警告！"
        elif failed_accounts > 0:
            content = "執行完成，但有部分帳號失敗"
        else:
            content = "執行完成，所有帳號處理成功！"

        return self.send_message(content=content, embeds=[embed])
