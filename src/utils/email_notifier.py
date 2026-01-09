#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Email 通知工具模組
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from .windows_encoding_utils import safe_print


class EmailNotifier:
    """Email SMTP 通知器"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        encryption: Optional[str] = None,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
    ):
        """
        初始化 Email 通知器

        Args:
            host: SMTP 伺服器位址（若不提供則從環境變數讀取）
            port: SMTP 伺服器埠號（若不提供則從環境變數讀取）
            username: SMTP 帳號（若不提供則從環境變數讀取）
            password: SMTP 密碼（若不提供則從環境變數讀取）
            encryption: 加密方式 tls/ssl/none（若不提供則從環境變數讀取）
            from_address: 寄件人地址（若不提供則從環境變數讀取）
            to_address: 收件人地址，支援逗號分隔多個地址（若不提供則從環境變數讀取）
        """
        self.host = self._clean_value(host or os.getenv("MAIL_HOST"))
        self.port = int(self._clean_value(port or os.getenv("MAIL_PORT") or "587"))
        self.username = self._clean_value(username or os.getenv("MAIL_USERNAME"))
        self.password = self._clean_value(password or os.getenv("MAIL_PASSWORD"))
        self.encryption = self._clean_value(
            encryption or os.getenv("MAIL_ENCRYPTION") or "tls"
        ).lower()
        self.from_address = self._clean_value(
            from_address or os.getenv("MAIL_FROM_ADDRESS")
        )
        # 支援多個收件人（逗號分隔）
        raw_to_address = self._clean_value(to_address or os.getenv("MAIL_TO_ADDRESS"))
        self.to_addresses = self._parse_addresses(raw_to_address)

    def _clean_value(self, value: Optional[str]) -> Optional[str]:
        """清理設定值（移除開頭的 = 或引號）"""
        if value is None:
            return None
        if isinstance(value, int):
            return str(value)
        return str(value).strip().lstrip("=").strip('"').strip("'")

    def _parse_addresses(self, addresses: Optional[str]) -> List[str]:
        """解析收件人地址（支援逗號分隔多個地址）"""
        if not addresses:
            return []
        # 支援逗號或分號分隔
        result = []
        for addr in addresses.replace(";", ",").split(","):
            addr = addr.strip()
            if addr:
                result.append(addr)
        return result

    def is_enabled(self) -> bool:
        """檢查是否啟用 Email 通知"""
        return bool(
            self.host
            and self.username
            and self.password
            and self.from_address
            and self.to_addresses
        )

    def send_message(
        self, subject: str, body: str, html_body: Optional[str] = None
    ) -> bool:
        """
        發送郵件

        Args:
            subject: 郵件主旨
            body: 純文字內容
            html_body: HTML 內容（可選，第一版不使用）

        Returns:
            bool: 是否成功發送
        """
        if not self.is_enabled():
            safe_print("⚠️  Email SMTP 設定不完整，跳過通知")
            return False

        try:
            # 建立郵件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_address
            msg["To"] = ", ".join(self.to_addresses)

            # 加入純文字內容
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # 連線並發送
            if self.encryption == "ssl":
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=30)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=30)
                if self.encryption == "tls":
                    server.starttls()

            server.login(self.username, self.password)
            server.sendmail(self.from_address, self.to_addresses, msg.as_string())
            server.quit()

            safe_print(f"✅ Email 通知發送成功 (共 {len(self.to_addresses)} 位收件人)")
            return True

        except smtplib.SMTPAuthenticationError as e:
            safe_print(f"❌ Email 驗證失敗: {e}")
            return False
        except smtplib.SMTPException as e:
            safe_print(f"❌ Email 發送錯誤: {e}")
            return False
        except Exception as e:
            safe_print(f"❌ Email 通知發生未預期的錯誤: {e}")
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
        account_list = "\n".join(
            [f"  • {result['username']}" for result in security_warning_accounts]
        )

        # 建立郵件主旨
        title = (
            f"[{function_name}] 密碼更新提醒" if function_name else "密碼更新提醒"
        )
        subject_prefix = "黑貓宅急便自動化工具 - "

        # 建立郵件內容
        body = f"""
========================================
🔐 {title}
========================================

偵測到 {len(security_warning_accounts)} 個帳號需要更新密碼

這些帳號因安全政策要求，必須更新密碼後才能繼續使用。

----------------------------------------
🔑 需更新密碼的帳號：
----------------------------------------
{account_list}

----------------------------------------
📋 處理步驟：
----------------------------------------
1. 登入黑貓宅急便契客專區 (https://www.t-cat.com.tw/)
2. 依照系統提示更新密碼
3. 更新 accounts.json 中的密碼

========================================
黑貓宅急便自動化工具
========================================
""".strip()

        return self.send_message(subject=f"{subject_prefix}⚠️ {title}", body=body)

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
        failed_accounts_details: Optional[List[Dict]] = None,
        executed_accounts: Optional[List[str]] = None,
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
            failed_accounts_details: 失敗帳號詳情 [{"username": "...", "error": "..."}]
            executed_accounts: 執行的帳號清單 ["username1", "username2", ...]

        Returns:
            bool: 是否成功發送
        """
        if not self.is_enabled():
            return False

        if downloaded_files is None:
            downloaded_files = []
        if failed_accounts_details is None:
            failed_accounts_details = []
        if executed_accounts is None:
            executed_accounts = []

        # 計算成功率
        success_rate = (
            (successful_accounts / total_accounts * 100) if total_accounts > 0 else 0
        )

        # 根據結果決定狀態
        if security_warning_accounts > 0:
            status_emoji = "🚨"
            status_text = "需要注意"
        elif failed_accounts > 0:
            status_emoji = "⚠️"
            status_text = "部分失敗"
        elif successful_accounts == total_accounts:
            status_emoji = "✅"
            status_text = "全部成功"
        else:
            status_emoji = "📊"
            status_text = "執行完成"

        # 建立進度條視覺化
        bar_length = 20
        filled = int(success_rate / 100 * bar_length)
        progress_bar = "█" * filled + "░" * (bar_length - filled)

        # 建立郵件主旨
        title = f"[{function_name}] 執行報告" if function_name else "執行報告"
        subject_prefix = "黑貓宅急便自動化工具 - "

        # 建立失敗帳號對照表
        failed_usernames = {d.get("username"): d.get("error", "未知錯誤") for d in failed_accounts_details}

        # 組合執行帳號清單（含狀態）
        account_list_parts = []
        if executed_accounts:
            for username in executed_accounts:
                if username in failed_usernames:
                    error = failed_usernames[username]
                    account_list_parts.append(f"  ❌ {username} - {error}")
                else:
                    account_list_parts.append(f"  ✅ {username}")
        account_list_text = "\n".join(account_list_parts) if account_list_parts else "  (無)"

        # 組合統計行
        stats_parts = [f"成功 {successful_accounts}"]
        if failed_accounts > 0:
            stats_parts.append(f"失敗 {failed_accounts}")
        if security_warning_accounts > 0:
            stats_parts.append(f"密碼警告 {security_warning_accounts}")
        stats_parts.append(f"下載 {total_downloads} 個檔案")
        stats_line = " | ".join(stats_parts)

        # 組合下載檔案清單
        file_list_text = ""
        if downloaded_files:
            file_list_parts = []
            for item in downloaded_files:
                filename = item.get("filename", "")
                if filename:
                    display_name = filename if len(filename) <= 50 else filename[:47] + "..."
                    file_list_parts.append(f"  • {display_name}")

            # 限制顯示數量
            if len(file_list_parts) > 15:
                file_list_text = "\n".join(file_list_parts[:15])
                remaining = len(file_list_parts) - 15
                file_list_text += f"\n  ... 還有 {remaining} 個檔案"
            else:
                file_list_text = "\n".join(file_list_parts)

        # 建立郵件內容
        body_parts = [
            "========================================",
            f"{status_emoji} {title}",
            "========================================",
            "",
            f"[{progress_bar}] {success_rate:.0f}% | {status_text}",
            "",
            f"📋 執行帳號 ({total_accounts} 個)",
            account_list_text,
            "",
            f"📊 統計: {stats_line}",
            "",
            "📁 下載檔案",
            file_list_text if file_list_text else "  (無)",
            "",
            "========================================",
            f"黑貓宅急便自動化工具 • {total_execution_minutes:.2f} 分鐘",
            "========================================",
        ]

        body = "\n".join(body_parts)

        return self.send_message(subject=f"{subject_prefix}{status_emoji} {title}", body=body)
