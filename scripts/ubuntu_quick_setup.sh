#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Ubuntu 快速部署腳本 - SeleniumTCat (向後兼容入口)
# ═══════════════════════════════════════════════════════════════════════════
# 用途: Ubuntu 環境快速部署（現已整合至 install.sh）
# 支援: Ubuntu 24.04 LTS (測試通過)
# 執行: bash scripts/ubuntu_quick_setup.sh
#
# 註: 此腳本現在調用統一的 install.sh，功能完全相同
# ═══════════════════════════════════════════════════════════════════════════

# 確保在專案根目錄執行
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "📝 註: ubuntu_quick_setup.sh 已整合至 install.sh"
echo "   兩個腳本功能完全相同，現在調用統一的安裝邏輯..."
echo ""

# 調用統一安裝腳本
if [ -f "scripts/install.sh" ]; then
    bash scripts/install.sh "$@"
else
    echo "❌ 錯誤: 找不到 scripts/install.sh"
    echo "請確認您在專案根目錄執行此腳本"
    exit 1
fi
