#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# SeleniumTCat 安裝工具 - 統一安裝邏輯
# ═══════════════════════════════════════════════════════════════════════════
# 用途: 自動安裝 Python、uv、Chrome/Chromium、專案依賴並設定環境
# 支援: macOS, Linux (Ubuntu/Debian/CentOS/Fedora/Arch)
# 執行: bash scripts/install.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e  # 遇到錯誤立即停止

# ───────────────────────────────────────────────────────────────────────────
# 顏色定義
# ───────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ───────────────────────────────────────────────────────────────────────────
# 輔助函數
# ───────────────────────────────────────────────────────────────────────────
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# 主安裝流程
# ═══════════════════════════════════════════════════════════════════════════
echo ""
print_header "🐱 SeleniumTCat 自動安裝工具"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 0: 平台偵測與環境檢查
# ───────────────────────────────────────────────────────────────────────────
print_info "檢查系統環境..."

# 偵測作業系統
IS_LINUX=false
IS_UBUNTU=false
IS_MACOS=false

if [[ "$OSTYPE" == "darwin"* ]]; then
    IS_MACOS=true
    print_info "偵測到 macOS 系統"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    IS_LINUX=true
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]] || [[ "$ID_LIKE" == *"ubuntu"* ]] || [[ "$ID" == "debian" ]]; then
            IS_UBUNTU=true
            print_info "偵測到 Ubuntu/Debian 系統"
        else
            print_info "偵測到 Linux 系統: $ID"
        fi
    else
        print_info "偵測到 Linux 系統"
    fi
else
    print_error "不支援的作業系統: $OSTYPE"
    exit 1
fi

# 檢查是否為 root 使用者
if [ "$EUID" -eq 0 ]; then
    print_warning "偵測到以 root 使用者執行"
    print_info "注意: 某些套件（如 UV）可能需要特殊處理"
    IS_ROOT=true
    SUDO_CMD=""
    UV_INSTALL_DIR="/root/.local/bin"
else
    print_info "當前使用者: $(whoami)"
    IS_ROOT=false
    SUDO_CMD="sudo"
    UV_INSTALL_DIR="$HOME/.local/bin"
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 1: 檢查並安裝 Python
# ───────────────────────────────────────────────────────────────────────────
print_header "步驟 1/7: Python 環境檢查"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python: $PYTHON_VERSION"

    # Ubuntu 環境檢查並安裝 Pillow 編譯依賴
    if [ "$IS_UBUNTU" = true ]; then
        print_info "檢查 Pillow 編譯依賴..."

        # 檢查 zlib1g-dev 是否已安裝（代表性套件）
        if ! dpkg -l | grep -q "zlib1g-dev"; then
            print_warning "缺少 Pillow 編譯依賴，開始安裝..."

            if [ "$IS_ROOT" = false ]; then
                if ! sudo -v; then
                    print_error "需要 sudo 權限安裝系統套件"
                    exit 1
                fi
            fi

            print_info "安裝 Pillow 編譯依賴 (用於 ddddocr)..."
            $SUDO_CMD apt-get update -qq
            $SUDO_CMD apt-get install -y \
                build-essential \
                python3-dev \
                zlib1g-dev \
                libjpeg-dev \
                libtiff-dev \
                libfreetype6-dev \
                liblcms2-dev \
                libwebp-dev \
                libopenjp2-7-dev

            print_success "Pillow 編譯依賴安裝完成"
        else
            print_success "Pillow 編譯依賴已安裝"
        fi
    fi
else
    print_warning "Python 未安裝"

    if [ "$IS_UBUNTU" = true ]; then
        print_info "正在安裝 Python 和編譯依賴..."
        if [ "$IS_ROOT" = false ]; then
            if ! sudo -v; then
                print_error "需要 sudo 權限安裝系統套件"
                exit 1
            fi
        fi
        $SUDO_CMD apt-get update -qq

        # 安裝 Python 和 Pillow 編譯依賴
        print_info "安裝 Python 基礎套件..."
        $SUDO_CMD apt-get install -y python3 python3-pip python3-dev curl

        print_info "安裝 Pillow 編譯依賴 (用於 ddddocr)..."
        $SUDO_CMD apt-get install -y \
            build-essential \
            zlib1g-dev \
            libjpeg-dev \
            libtiff-dev \
            libfreetype6-dev \
            liblcms2-dev \
            libwebp-dev \
            libopenjp2-7-dev

        if command -v python3 &> /dev/null; then
            PYTHON_VERSION=$(python3 --version)
            print_success "Python 安裝成功: $PYTHON_VERSION"
            print_success "Pillow 編譯依賴安裝完成"
        else
            print_error "Python 安裝失敗"
            exit 1
        fi
    elif [ "$IS_MACOS" = true ]; then
        print_error "請先安裝 Python"
        echo "  macOS: brew install python3"
        exit 1
    else
        print_error "請手動安裝 Python 3.8+"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
        exit 1
    fi
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 2: 檢查並安裝 Chrome/Chromium
# ───────────────────────────────────────────────────────────────────────────
print_header "步驟 2/7: Chrome/Chromium 瀏覽器檢查"

CHROME_INSTALLED=false
CHROME_PATH=""
CHROMEDRIVER_PATH=""

# Linux 平台優先檢查 Chromium
if [ "$IS_LINUX" = true ]; then
    CHROME_PATHS=(
        "/usr/bin/chromium-browser"
        "/usr/bin/chromium"
        "/usr/bin/google-chrome"
        "/usr/bin/google-chrome-stable"
        "/opt/google/chrome/chrome"
    )
else
    CHROME_PATHS=(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        "/usr/bin/google-chrome"
        "/usr/bin/google-chrome-stable"
        "/usr/bin/chromium"
        "/usr/bin/chromium-browser"
    )
fi

# 檢查 Chrome/Chromium 是否已安裝
for chrome_path in "${CHROME_PATHS[@]}"; do
    if [ -x "$chrome_path" ]; then
        print_success "Chrome/Chromium 已安裝: $chrome_path"
        CHROME_INSTALLED=true
        CHROME_PATH="$chrome_path"
        break
    fi
done

# Ubuntu 環境自動安裝 Chromium
if [ "$CHROME_INSTALLED" = false ] && [ "$IS_UBUNTU" = true ]; then
    print_warning "未找到 Chrome/Chromium，將自動安裝 Chromium"
    echo ""

    # 檢查 sudo 權限（非 root 使用者需要）
    if [ "$IS_ROOT" = false ]; then
        if ! sudo -v; then
            print_error "需要 sudo 權限安裝系統套件"
            print_info "建議: 使用 root 使用者執行或確保有 sudo 權限"
            exit 1
        fi
    fi

    # 更新套件清單
    print_info "更新系統套件清單..."
    $SUDO_CMD apt-get update -qq

    # 安裝 Chromium
    print_info "安裝 Chromium 瀏覽器..."
    if $SUDO_CMD apt-get install -y chromium-browser; then
        CHROMIUM_VERSION=$(chromium-browser --version 2>/dev/null || echo "未知版本")
        print_success "Chromium 安裝完成: $CHROMIUM_VERSION"
        CHROME_INSTALLED=true
        CHROME_PATH=$(which chromium-browser 2>/dev/null || echo "/usr/bin/chromium-browser")
    else
        print_error "Chromium 安裝失敗"
        exit 1
    fi

    # 安裝 ChromeDriver
    print_info "安裝 ChromeDriver..."
    if $SUDO_CMD apt-get install -y chromium-chromedriver; then
        CHROMEDRIVER_VERSION=$(chromedriver --version 2>/dev/null | cut -d' ' -f2 || echo "未知版本")
        print_success "ChromeDriver 安裝完成: $CHROMEDRIVER_VERSION"
        CHROMEDRIVER_PATH=$(which chromedriver 2>/dev/null || echo "/usr/bin/chromedriver")
    else
        print_error "ChromeDriver 安裝失敗"
        exit 1
    fi

    echo ""
fi

# 如果仍未找到 Chrome/Chromium，提示手動安裝
if [ "$CHROME_INSTALLED" = false ]; then
    print_error "未找到 Chrome/Chromium"
    echo ""
    print_info "請先安裝 Chrome 或 Chromium:"
    if [ "$IS_LINUX" = true ]; then
        echo "  • Ubuntu/Debian: sudo apt install chromium-browser chromium-chromedriver"
        echo "  • Google Chrome: https://www.google.com/chrome/"
    elif [ "$IS_MACOS" = true ]; then
        echo "  • macOS: brew install --cask google-chrome"
        echo "  • 或從 https://www.google.com/chrome/ 下載"
    fi
    echo ""
    exit 1
fi

# 偵測 ChromeDriver 路徑（如果尚未設定）
if [ -z "$CHROMEDRIVER_PATH" ]; then
    CHROMEDRIVER_PATH=$(which chromedriver 2>/dev/null || echo "")
    if [ -n "$CHROMEDRIVER_PATH" ]; then
        print_info "ChromeDriver 路徑: $CHROMEDRIVER_PATH"
    fi
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 3: 檢查並安裝 UV
# ───────────────────────────────────────────────────────────────────────────
print_header "步驟 3/7: UV 套件管理器安裝"

if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version)
    print_success "UV 已安裝: $UV_VERSION"
else
    print_info "正在安裝 UV (Python 套件管理器)..."

    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        # 更新 PATH
        export PATH="$UV_INSTALL_DIR:$HOME/.cargo/bin:$PATH"

        # 載入環境設定檔（如果存在）
        if [ -f "$UV_INSTALL_DIR/env" ]; then
            source "$UV_INSTALL_DIR/env"
        fi

        # 驗證安裝
        if command -v uv &> /dev/null; then
            UV_VERSION=$(uv --version)
            print_success "UV 安裝成功: $UV_VERSION"
        elif [ -x "$UV_INSTALL_DIR/uv" ]; then
            # 使用絕對路徑
            export PATH="$UV_INSTALL_DIR:$PATH"
            UV_VERSION=$("$UV_INSTALL_DIR/uv" --version)
            print_success "UV 安裝成功（使用絕對路徑）: $UV_VERSION"

            # 建立函式代替 alias
            uv() { "$UV_INSTALL_DIR/uv" "$@"; }
            export -f uv
        else
            print_error "UV 安裝失敗，找不到執行檔"
            print_info "預期路徑: $UV_INSTALL_DIR/uv"
            exit 1
        fi

        # 添加到 shell profile
        if [[ "$SHELL" == */zsh ]]; then
            if ! grep -q "$UV_INSTALL_DIR" ~/.zshrc 2>/dev/null; then
                echo "export PATH=\"$UV_INSTALL_DIR:\$PATH\"" >> ~/.zshrc
                print_info "已添加 UV 到 ~/.zshrc"
            fi
        elif [[ "$SHELL" == */bash ]]; then
            if ! grep -q "$UV_INSTALL_DIR" ~/.bashrc 2>/dev/null; then
                echo "export PATH=\"$UV_INSTALL_DIR:\$PATH\"" >> ~/.bashrc
                print_info "已添加 UV 到 ~/.bashrc"
            fi
        fi
    else
        print_error "UV 安裝失敗"
        print_info "請參考: https://docs.astral.sh/uv/"
        exit 1
    fi
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 4: 安裝 Python 依賴
# ───────────────────────────────────────────────────────────────────────────
print_header "步驟 4/7: 安裝 Python 依賴"

# 檢查 pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    print_error "找不到 pyproject.toml！請確認您在專案根目錄執行此腳本"
    exit 1
fi

print_info "使用 UV 安裝依賴..."
if uv sync; then
    print_success "Python 依賴安裝完成"
else
    print_error "依賴安裝失敗"
    exit 1
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 5: 設定配置檔案
# ───────────────────────────────────────────────────────────────────────────
print_header "步驟 5/7: 設定配置檔案"

# 建立 .env 檔案
if [ ! -f ".env" ]; then
    if [ "$IS_LINUX" = true ] && [ -n "$CHROME_PATH" ]; then
        # Ubuntu/Linux 環境自動配置
        print_info "配置 .env 檔案（Linux 環境）..."

        cat > ".env" <<EOL
# Chrome 瀏覽器路徑（Linux 環境自動配置）
CHROME_BINARY_PATH=$CHROME_PATH
EOL

        # 添加 ChromeDriver 路徑（如果有）
        if [ -n "$CHROMEDRIVER_PATH" ]; then
            echo "CHROMEDRIVER_PATH=$CHROMEDRIVER_PATH" >> ".env"
        fi

        echo "" >> ".env"
        echo "# 由 scripts/install.sh 自動生成於 $(date)" >> ".env"

        chmod 600 ".env"
        print_success ".env 檔案配置完成"
        print_info "Chrome 路徑: $CHROME_PATH"
        if [ -n "$CHROMEDRIVER_PATH" ]; then
            print_info "ChromeDriver 路徑: $CHROMEDRIVER_PATH"
        fi
    else
        # macOS 或其他平台從範例複製
        if [ -f ".env.example" ]; then
            cp ".env.example" ".env"
            chmod 600 ".env"
            print_success "已建立 .env 檔案"
            if [ "$IS_MACOS" = true ]; then
                print_warning "請編輯 .env 檔案並設定正確的 Chrome 路徑"
                print_info "macOS 預設路徑: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            fi
        else
            print_error "找不到 .env.example 檔案"
        fi
    fi
else
    print_info ".env 檔案已存在"
    # Linux 環境檢查並更新路徑（如果需要）
    if [ "$IS_LINUX" = true ] && [ -n "$CHROME_PATH" ]; then
        if ! grep -q "CHROME_BINARY_PATH" ".env"; then
            print_info "更新 .env 檔案中的 Chrome 路徑..."
            echo "" >> ".env"
            echo "# Linux 環境路徑（由 scripts/install.sh 更新於 $(date)）" >> ".env"
            echo "CHROME_BINARY_PATH=$CHROME_PATH" >> ".env"
            if [ -n "$CHROMEDRIVER_PATH" ]; then
                echo "CHROMEDRIVER_PATH=$CHROMEDRIVER_PATH" >> ".env"
            fi
            print_success "已更新 .env 檔案"
        fi
    fi
fi

# 建立 accounts.json 檔案
if [ ! -f "accounts.json" ]; then
    if [ -f "accounts.json.example" ]; then
        cp "accounts.json.example" "accounts.json"
        chmod 600 "accounts.json"
        print_success "已建立 accounts.json 檔案"
        print_warning "請編輯 accounts.json 檔案並填入實際的帳號資訊"
    else
        print_warning "找不到 accounts.json.example，請手動建立 accounts.json"
    fi
else
    print_info "accounts.json 檔案已存在"
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 6: 建立必要目錄並設定權限
# ───────────────────────────────────────────────────────────────────────────
print_header "步驟 6/7: 建立目錄與設定權限"

# 建立必要目錄
directories=("downloads" "logs" "temp")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chmod 755 "$dir"
        print_success "已建立目錄: $dir"
    else
        print_info "目錄已存在: $dir"
    fi
done

# 設定腳本執行權限
print_info "設定腳本執行權限..."
chmod +x Linux_*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

# 確保敏感檔案有正確的權限
if [ -f ".env" ]; then
    chmod 600 ".env"
fi
if [ -f "accounts.json" ]; then
    chmod 600 "accounts.json"
fi

print_success "權限設定完成"

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 步驟 7: 執行基本測試
# ───────────────────────────────────────────────────────────────────────────
print_header "步驟 7/7: 執行基本測試"

export PYTHONPATH="$(pwd)"
export PYTHONUNBUFFERED=1

print_info "測試瀏覽器初始化..."
if uv run python -c "
from src.core.browser_utils import init_chrome_browser
print('🔍 測試瀏覽器初始化...')
try:
    driver, wait = init_chrome_browser(headless=True)
    print('✅ Chrome WebDriver 啟動成功')
    driver.quit()
    print('✅ 基本功能測試通過')
except Exception as e:
    print(f'❌ 基本功能測試失敗: {e}')
    exit(1)
"; then
    print_success "基本測試通過"
else
    print_warning "基本測試失敗，請檢查配置"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# 完成訊息
# ═══════════════════════════════════════════════════════════════════════════
print_success "══════════════════════════════════════"
print_success "  SeleniumTCat 安裝完成！"
print_success "══════════════════════════════════════"
echo ""

# 根據平台顯示不同的後續步驟
if [ "$IS_UBUNTU" = true ]; then
    print_info "Ubuntu 環境設定完成！"
    echo ""
    print_info "📝 下一步操作："
    echo "  1. 編輯帳號設定:"
    echo "     nano accounts.json  # 填入實際帳號資訊"
    echo ""
    echo "  2. 執行環境驗證:"
    echo "     bash scripts/test_ubuntu_env.sh"
    echo ""
    echo "  3. 測試瀏覽器:"
    echo "     PYTHONPATH=\$(pwd) uv run python src/utils/test_browser.py"
    echo ""
    echo "  4. 執行爬蟲（無頭模式）:"
    echo "     bash Linux_客樂得對帳單.sh     # 貨到付款匯款明細"
    echo "     bash Linux_發票明細.sh         # 運費對帳單"
    echo "     bash Linux_客戶交易明細.sh     # 交易明細表"
    echo ""
    print_info "📖 完整文檔: docs/technical/ubuntu-deployment-guide.md"
elif [ "$IS_MACOS" = true ]; then
    print_info "macOS 環境設定完成！"
    echo ""
    print_info "📝 下一步操作："
    echo "  1. 編輯配置檔案:"
    echo "     • .env - 設定 Chrome 路徑"
    echo "     • accounts.json - 填入帳號資訊"
    echo ""
    echo "  2. 執行爬蟲:"
    echo "     ./Linux_客樂得對帳單.sh     # 貨到付款匯款明細"
    echo "     ./Linux_發票明細.sh         # 運費對帳單"
    echo "     ./Linux_客戶交易明細.sh     # 交易明細表"
else
    print_info "Linux 環境設定完成！"
    echo ""
    print_info "📝 下一步操作："
    echo "  1. 編輯 .env 和 accounts.json 檔案"
    echo "  2. 執行爬蟲腳本"
fi

echo ""
print_info "需要幫助？請查看 CLAUDE.md"
echo ""
