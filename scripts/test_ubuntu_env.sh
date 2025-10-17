#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Ubuntu 環境驗證腳本 - SeleniumTCat
# ═══════════════════════════════════════════════════════════════════════════
# 用途: 驗證 Ubuntu 環境是否正確配置（Chromium、Python、權限等）
# 支援: Ubuntu 24.04 LTS
# 執行: bash scripts/test_ubuntu_env.sh
# ═══════════════════════════════════════════════════════════════════════════

set +e  # 不因錯誤停止（繼續檢查所有項目）

# ───────────────────────────────────────────────────────────────────────────
# 顏色定義
# ───────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ───────────────────────────────────────────────────────────────────────────
# 計數器
# ───────────────────────────────────────────────────────────────────────────
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# ───────────────────────────────────────────────────────────────────────────
# 輔助函數
# ───────────────────────────────────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS_COUNT++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN_COUNT++))
}

# ═══════════════════════════════════════════════════════════════════════════
# 開始測試
# ═══════════════════════════════════════════════════════════════════════════
print_header "Ubuntu 環境驗證 - SeleniumTCat"
echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"

# ───────────────────────────────────────────────────────────────────────────
# 1. 平台檢查
# ───────────────────────────────────────────────────────────────────────────
print_header "1. 平台檢查"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    test_pass "平台: Linux"

    # 檢查是否為 Ubuntu
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "   作業系統: $NAME $VERSION"
        if [[ "$ID" == "ubuntu" ]]; then
            test_pass "Ubuntu 系統偵測"
        else
            test_warn "非 Ubuntu 系統 ($ID)，部分功能可能不相容"
        fi
    fi
else
    test_fail "此腳本僅支援 Linux 平台 (當前: $OSTYPE)"
fi

# ───────────────────────────────────────────────────────────────────────────
# 2. Chromium 瀏覽器檢查
# ───────────────────────────────────────────────────────────────────────────
print_header "2. Chromium 瀏覽器檢查"

if command -v chromium-browser &> /dev/null; then
    CHROMIUM_VERSION=$(chromium-browser --version 2>/dev/null || echo "未知版本")
    test_pass "Chromium 已安裝: $CHROMIUM_VERSION"

    # 檢查執行權限
    CHROMIUM_PATH=$(which chromium-browser)
    if [ -x "$CHROMIUM_PATH" ]; then
        test_pass "Chromium 可執行: $CHROMIUM_PATH"
    else
        test_fail "Chromium 無執行權限: $CHROMIUM_PATH"
    fi
else
    test_fail "Chromium 未安裝"
    echo "   解決方案: sudo apt install -y chromium-browser"
fi

# ───────────────────────────────────────────────────────────────────────────
# 3. ChromeDriver 檢查
# ───────────────────────────────────────────────────────────────────────────
print_header "3. ChromeDriver 檢查"

if command -v chromedriver &> /dev/null; then
    CHROMEDRIVER_VERSION=$(chromedriver --version 2>/dev/null || echo "未知版本")
    test_pass "ChromeDriver 已安裝: $CHROMEDRIVER_VERSION"

    # 檢查執行權限
    CHROMEDRIVER_PATH=$(which chromedriver)
    if [ -x "$CHROMEDRIVER_PATH" ]; then
        test_pass "ChromeDriver 可執行: $CHROMEDRIVER_PATH"
    else
        test_fail "ChromeDriver 無執行權限: $CHROMEDRIVER_PATH"
    fi
else
    test_fail "ChromeDriver 未安裝"
    echo "   解決方案: sudo apt install -y chromium-chromedriver"
fi

# ───────────────────────────────────────────────────────────────────────────
# 4. Python 與 UV 檢查
# ───────────────────────────────────────────────────────────────────────────
print_header "4. Python 與 UV 檢查"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    test_pass "Python3 已安裝: $PYTHON_VERSION"
else
    test_fail "Python3 未安裝"
fi

if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version 2>&1)
    test_pass "UV 已安裝: $UV_VERSION"
else
    test_fail "UV 未安裝"
    echo "   解決方案: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# ───────────────────────────────────────────────────────────────────────────
# 5. 專案檔案檢查
# ───────────────────────────────────────────────────────────────────────────
print_header "5. 專案檔案檢查"

# 檢查必要檔案
for file in pyproject.toml .env.example; do
    if [ -f "$file" ]; then
        test_pass "檔案存在: $file"
    else
        test_fail "檔案不存在: $file"
    fi
done

# 檢查 .env 檔案
if [ -f ".env" ]; then
    test_pass ".env 檔案存在"

    # 檢查權限（應該是 600）
    ENV_PERMS=$(stat -c "%a" .env 2>/dev/null || stat -f "%Lp" .env 2>/dev/null)
    if [ "$ENV_PERMS" = "600" ]; then
        test_pass ".env 檔案權限正確 (600)"
    else
        test_warn ".env 檔案權限不安全 ($ENV_PERMS)，建議: chmod 600 .env"
    fi

    # 檢查必要環境變數
    if grep -q "CHROME_BINARY_PATH" .env; then
        test_pass ".env 包含 CHROME_BINARY_PATH 設定"
    else
        test_warn ".env 缺少 CHROME_BINARY_PATH 設定"
    fi
else
    test_fail ".env 檔案不存在"
    echo "   解決方案: cp .env.example .env && nano .env"
fi

# 檢查 accounts.json
if [ -f "accounts.json" ]; then
    test_pass "accounts.json 檔案存在"

    # 檢查權限
    ACCOUNTS_PERMS=$(stat -c "%a" accounts.json 2>/dev/null || stat -f "%Lp" accounts.json 2>/dev/null)
    if [ "$ACCOUNTS_PERMS" = "600" ]; then
        test_pass "accounts.json 檔案權限正確 (600)"
    else
        test_warn "accounts.json 檔案權限不安全 ($ACCOUNTS_PERMS)，建議: chmod 600 accounts.json"
    fi
else
    test_warn "accounts.json 檔案不存在"
    echo "   請從 accounts.json.example 建立並設定帳號資訊"
fi

# ───────────────────────────────────────────────────────────────────────────
# 6. 目錄檢查
# ───────────────────────────────────────────────────────────────────────────
print_header "6. 目錄檢查"

for dir in downloads logs temp; do
    if [ -d "$dir" ]; then
        test_pass "目錄存在: $dir"

        # 檢查寫入權限
        if [ -w "$dir" ]; then
            test_pass "目錄可寫入: $dir"
        else
            test_fail "目錄無寫入權限: $dir"
            echo "   解決方案: chmod 755 $dir"
        fi
    else
        test_warn "目錄不存在: $dir"
        echo "   建議建立: mkdir -p $dir && chmod 755 $dir"
    fi
done

# ───────────────────────────────────────────────────────────────────────────
# 7. Python 依賴檢查
# ───────────────────────────────────────────────────────────────────────────
print_header "7. Python 依賴檢查"

if [ -d ".venv" ]; then
    test_pass "虛擬環境已建立: .venv"

    # 檢查關鍵套件
    if [ -f ".venv/bin/python" ] || [ -f ".venv/Scripts/python.exe" ]; then
        # 嘗試導入關鍵模組
        PYTHON_CMD=".venv/bin/python"

        # 檢查關鍵模組（模組名稱 -> 導入名稱映射）
        declare -A module_map=(
            ["selenium"]="selenium"
            ["ddddocr"]="ddddocr"
            ["openpyxl"]="openpyxl"
            ["python-dotenv"]="dotenv"
        )

        for module in selenium ddddocr openpyxl python-dotenv; do
            import_name="${module_map[$module]}"
            if $PYTHON_CMD -c "import $import_name" 2>/dev/null; then
                test_pass "Python 模組已安裝: $module"
            else
                test_warn "Python 模組未安裝或無法導入: $module"
            fi
        done
    else
        test_warn "虛擬環境損毀或不完整"
    fi
else
    test_warn "虛擬環境未建立"
    echo "   解決方案: uv sync"
fi

# ───────────────────────────────────────────────────────────────────────────
# 8. 網路連線檢查 (選用)
# ───────────────────────────────────────────────────────────────────────────
print_header "8. 網路連線檢查"

if ping -c 1 8.8.8.8 &> /dev/null; then
    test_pass "網路連線正常"
else
    test_warn "網路連線異常或防火牆阻擋 ping"
fi

# ═══════════════════════════════════════════════════════════════════════════
# 測試結果總結
# ═══════════════════════════════════════════════════════════════════════════
print_header "測試結果總結"

echo ""
echo -e "${GREEN}✅ 通過: $PASS_COUNT${NC}"
echo -e "${YELLOW}⚠️  警告: $WARN_COUNT${NC}"
echo -e "${RED}❌ 失敗: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    if [ $WARN_COUNT -eq 0 ]; then
        echo -e "${GREEN}🎉 完美！所有檢查都通過了！${NC}"
        echo ""
        echo "下一步："
        echo "  bash scripts/test_browser.py  # 執行瀏覽器測試"
        EXIT_CODE=0
    else
        echo -e "${YELLOW}✅ 環境基本可用，但有 $WARN_COUNT 個警告項目${NC}"
        echo "   建議修正警告項目以確保最佳效能和安全性"
        EXIT_CODE=0
    fi
else
    echo -e "${RED}❌ 環境配置不完整，有 $FAIL_COUNT 個失敗項目${NC}"
    echo ""
    echo "建議執行快速部署腳本："
    echo "  bash scripts/ubuntu_quick_setup.sh"
    EXIT_CODE=1
fi

echo ""
echo "結束時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

exit $EXIT_CODE
