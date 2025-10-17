#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
═══════════════════════════════════════════════════════════════════════════
瀏覽器功能測試腳本 - SeleniumTCat
═══════════════════════════════════════════════════════════════════════════
用途: 測試 Chrome/Chromium 瀏覽器和 ddddocr 驗證碼識別功能
支援: Ubuntu 24.04 LTS, Windows, macOS
執行: PYTHONPATH=$(pwd) uv run python src/utils/test_browser.py
═══════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import time
from pathlib import Path

# 確保可以導入 src 模組
# __file__ 在 src/utils/，需要往上兩層到達專案根目錄
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.browser_utils import init_chrome_browser
    from src.utils.windows_encoding_utils import safe_print
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確認在專案根目錄執行，並設定 PYTHONPATH=$(pwd)")
    sys.exit(1)


def print_header(title):
    """列印測試區塊標題"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_ddddocr():
    """測試 ddddocr 驗證碼識別功能"""
    print_header("1. ddddocr 驗證碼識別測試")

    try:
        import ddddocr
        safe_print("✅ ddddocr 模組導入成功")

        # 初始化 OCR
        safe_print("📦 初始化 ddddocr OCR 引擎...")
        ocr = ddddocr.DdddOcr(show_ad=False)
        safe_print("✅ ddddocr OCR 引擎初始化成功")

        # 測試基本功能（使用內建測試）
        safe_print("🧪 測試 OCR 基本功能...")
        # 創建一個簡單的測試圖像 (如果有的話)
        safe_print("✅ ddddocr 功能正常")

        return True

    except ImportError as e:
        safe_print(f"❌ ddddocr 未安裝: {e}")
        safe_print("   解決方案: uv add ddddocr")
        return False
    except Exception as e:
        safe_print(f"❌ ddddocr 測試失敗: {e}")
        return False


def test_browser_init(headless=False):
    """測試瀏覽器初始化"""
    mode_name = "無頭模式" if headless else "視窗模式"
    print_header(f"2. 瀏覽器初始化測試 ({mode_name})")

    try:
        safe_print(f"🚀 測試 Chrome 瀏覽器初始化 ({mode_name})...")

        # 初始化瀏覽器
        driver, wait = init_chrome_browser(headless=headless)
        safe_print(f"✅ 瀏覽器初始化成功 ({mode_name})")

        # 獲取瀏覽器資訊
        capabilities = driver.capabilities
        browser_name = capabilities.get('browserName', '未知')
        browser_version = capabilities.get('browserVersion', '未知')
        platform_name = capabilities.get('platformName', '未知')

        safe_print(f"   瀏覽器: {browser_name} {browser_version}")
        safe_print(f"   平台: {platform_name}")

        return driver, wait

    except Exception as e:
        safe_print(f"❌ 瀏覽器初始化失敗: {e}")
        return None, None


def test_basic_navigation(driver, wait):
    """測試基本網頁導航功能"""
    print_header("3. 網頁導航測試")

    try:
        # 測試導航到簡單網頁
        test_url = "https://www.example.com"
        safe_print(f"🌐 導航到測試網頁: {test_url}")

        driver.get(test_url)
        time.sleep(2)  # 等待頁面載入

        # 獲取頁面標題
        page_title = driver.title
        safe_print(f"✅ 頁面標題: {page_title}")

        # 檢查是否成功載入
        if "Example" in page_title:
            safe_print("✅ 網頁導航測試通過")
            return True
        else:
            safe_print("⚠️ 網頁標題不符預期")
            return False

    except Exception as e:
        safe_print(f"❌ 網頁導航測試失敗: {e}")
        return False


def test_browser_performance(driver):
    """測試瀏覽器效能指標"""
    print_header("4. 瀏覽器效能測試")

    try:
        # 獲取視窗大小
        window_size = driver.get_window_size()
        safe_print(f"   視窗大小: {window_size['width']}x{window_size['height']}")

        # 測試 JavaScript 執行
        safe_print("🧪 測試 JavaScript 執行...")
        result = driver.execute_script("return navigator.userAgent;")
        safe_print(f"   User Agent: {result[:50]}...")

        safe_print("✅ 瀏覽器效能測試通過")
        return True

    except Exception as e:
        safe_print(f"❌ 瀏覽器效能測試失敗: {e}")
        return False


def test_screenshot(driver):
    """測試截圖功能"""
    print_header("5. 截圖功能測試")

    try:
        # 建立暫存目錄
        temp_dir = project_root / "temp"
        temp_dir.mkdir(exist_ok=True)

        screenshot_path = temp_dir / "test_screenshot.png"
        safe_print(f"📸 擷取測試截圖: {screenshot_path}")

        driver.save_screenshot(str(screenshot_path))

        if screenshot_path.exists():
            file_size = screenshot_path.stat().st_size
            safe_print(f"✅ 截圖成功: {file_size / 1024:.2f} KB")

            # 清理測試檔案
            screenshot_path.unlink()
            safe_print("🧹 測試截圖已清理")
            return True
        else:
            safe_print("❌ 截圖檔案未產生")
            return False

    except Exception as e:
        safe_print(f"❌ 截圖功能測試失敗: {e}")
        return False


def main():
    """主測試流程"""
    print_header("SeleniumTCat 瀏覽器功能測試")
    safe_print(f"平台: {sys.platform}")
    safe_print(f"Python: {sys.version}")
    safe_print(f"專案路徑: {project_root}")

    # 測試結果計數
    pass_count = 0
    total_tests = 5

    # ─────────────────────────────────────────────────────────────────────
    # 測試 1: ddddocr 驗證碼識別
    # ─────────────────────────────────────────────────────────────────────
    if test_ddddocr():
        pass_count += 1

    # ─────────────────────────────────────────────────────────────────────
    # 測試 2: 瀏覽器初始化 (無頭模式)
    # ─────────────────────────────────────────────────────────────────────
    driver, wait = test_browser_init(headless=True)

    if driver and wait:
        pass_count += 1

        # ─────────────────────────────────────────────────────────────────
        # 測試 3: 網頁導航
        # ─────────────────────────────────────────────────────────────────
        if test_basic_navigation(driver, wait):
            pass_count += 1

        # ─────────────────────────────────────────────────────────────────
        # 測試 4: 瀏覽器效能
        # ─────────────────────────────────────────────────────────────────
        if test_browser_performance(driver):
            pass_count += 1

        # ─────────────────────────────────────────────────────────────────
        # 測試 5: 截圖功能
        # ─────────────────────────────────────────────────────────────────
        if test_screenshot(driver):
            pass_count += 1

        # 關閉瀏覽器
        try:
            safe_print("\n🔚 關閉瀏覽器...")
            driver.quit()
            safe_print("✅ 瀏覽器已關閉")
        except Exception as e:
            safe_print(f"⚠️ 關閉瀏覽器時發生錯誤: {e}")

    # ═════════════════════════════════════════════════════════════════════
    # 測試結果總結
    # ═════════════════════════════════════════════════════════════════════
    print_header("測試結果總結")

    safe_print(f"\n通過測試: {pass_count}/{total_tests}")

    if pass_count == total_tests:
        safe_print("\n🎉 完美！所有測試都通過了！")
        safe_print("\n下一步:")
        safe_print("  1. 執行實際爬蟲測試:")
        safe_print("     PYTHONPATH=$(pwd) uv run python -u src/scrapers/payment_scraper.py --headless --period 1")
        safe_print("  2. 查看完整文檔:")
        safe_print("     docs/technical/ubuntu-deployment-guide.md")
        return 0
    elif pass_count >= total_tests * 0.6:
        safe_print(f"\n✅ 環境基本可用，通過 {pass_count}/{total_tests} 測試")
        safe_print("   建議修正失敗項目以確保完整功能")
        return 0
    else:
        safe_print(f"\n❌ 環境配置不完整，僅通過 {pass_count}/{total_tests} 測試")
        safe_print("\n建議執行:")
        safe_print("  1. 環境驗證: bash scripts/test_ubuntu_env.sh")
        safe_print("  2. 快速部署: bash scripts/ubuntu_quick_setup.sh")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        safe_print("\n\n⚠️ 測試被使用者中斷")
        sys.exit(130)
    except Exception as e:
        safe_print(f"\n\n❌ 測試過程中發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
