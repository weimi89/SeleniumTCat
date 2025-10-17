#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# SeleniumTCat 更新入口點
# ═══════════════════════════════════════════════════════════════════════════
# 此腳本為更新入口點，實際邏輯在 scripts/update.sh
# 執行: ./Linux_更新.sh 或 bash Linux_更新.sh
# ═══════════════════════════════════════════════════════════════════════════

# 確保在專案根目錄執行
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 調用實際更新腳本
if [ -f "scripts/update.sh" ]; then
    bash scripts/update.sh "$@"
else
    echo "❌ 錯誤: 找不到 scripts/update.sh"
    echo "請確認您在專案根目錄執行此腳本"
    exit 1
fi
