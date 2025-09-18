#!/bin/bash

# 黑貓宅急便自動下載工具 - 自動安裝腳本 (macOS/Linux)
echo "🐱 黑貓宅急便自動下載工具 - 自動安裝"
echo "=========================================="

# 檢測作業系統
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    echo "❌ 不支援的作業系統: $OSTYPE"
    exit 1
fi

echo "🖥️  檢測到作業系統: $OS"

# 檢查 Python 是否安裝
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        echo "✅ Python 已安裝: $PYTHON_VERSION"
        return 0
    else
        echo "❌ Python 未安裝"
        return 1
    fi
}

# 安裝 Python (macOS)
install_python_macos() {
    echo "🔧 在 macOS 上安裝 Python..."

    # 檢查 Homebrew
    if ! command -v brew &> /dev/null; then
        echo "📦 安裝 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # 添加 Homebrew 到 PATH (適用於 Apple Silicon)
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi

    echo "🐍 使用 Homebrew 安裝 Python..."
    brew install python3
}

# 安裝 Python (Linux)
install_python_linux() {
    echo "🔧 在 Linux 上安裝 Python..."

    # 檢測 Linux 發行版
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        echo "📦 使用 apt-get 安裝 Python..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip curl
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        echo "📦 使用 yum 安裝 Python..."
        sudo yum install -y python3 python3-pip curl
    elif command -v dnf &> /dev/null; then
        # Fedora
        echo "📦 使用 dnf 安裝 Python..."
        sudo dnf install -y python3 python3-pip curl
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        echo "📦 使用 pacman 安裝 Python..."
        sudo pacman -S python python-pip curl
    else
        echo "❌ 無法識別的 Linux 發行版，請手動安裝 Python3"
        echo "參考: https://www.python.org/downloads/"
        exit 1
    fi
}

# 安裝 uv
install_uv() {
    echo "⚡ 安裝 uv (Python 套件管理工具)..."

    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # 添加 uv 到當前 session 的 PATH
        export PATH="$HOME/.cargo/bin:$PATH"

        # 添加到 shell profile
        if [[ "$SHELL" == */zsh ]]; then
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
        elif [[ "$SHELL" == */bash ]]; then
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
        fi

        # 重新檢查
        if command -v uv &> /dev/null; then
            echo "✅ uv 安裝成功"
        else
            echo "❌ uv 安裝失敗，請手動安裝"
            echo "參考: https://github.com/astral-sh/uv#installation"
            exit 1
        fi
    else
        echo "✅ uv 已安裝"
    fi
}

# 設定 Chrome 路徑
setup_chrome() {
    echo "🌐 設定 Chrome 瀏覽器路徑..."

    if [ ! -f ".env" ]; then
        if [[ "$OS" == "macOS" ]]; then
            CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        else
            # Linux 常見路徑
            if [ -f "/usr/bin/google-chrome" ]; then
                CHROME_PATH="/usr/bin/google-chrome"
            elif [ -f "/usr/bin/chromium-browser" ]; then
                CHROME_PATH="/usr/bin/chromium-browser"
            elif [ -f "/usr/bin/chromium" ]; then
                CHROME_PATH="/usr/bin/chromium"
            else
                echo "⚠️  未找到 Chrome/Chromium，請手動安裝"
                echo "   macOS: 從 https://www.google.com/chrome/ 下載"
                echo "   Linux: sudo apt-get install google-chrome-stable"
                CHROME_PATH=""
            fi
        fi

        if [ ! -z "$CHROME_PATH" ]; then
            echo "CHROME_BINARY_PATH=\"$CHROME_PATH\"" > .env
            echo "✅ Chrome 路徑設定完成: $CHROME_PATH"
        fi
    else
        echo "✅ .env 檔案已存在"
    fi
}

# 初始化專案
setup_project() {
    echo "📦 初始化專案環境..."

    # 建立虛擬環境
    uv venv

    # 安裝依賴
    echo "📦 安裝 Python 套件..."
    uv sync
    echo "✅ Python 套件安裝完成"

    # 確保腳本可執行
    if [ -f "run_payment.sh" ]; then
        chmod +x run_payment.sh
    fi

    # 建立帳號設定範例
    if [ ! -f "accounts.json" ]; then
        if [ -f "accounts.json.example" ]; then
            cp "accounts.json.example" "accounts.json"
            echo "✅ 已從範例建立 accounts.json 檔案"
        else
            echo "⚠️ 未找到 accounts.json.example，請手動建立 accounts.json"
        fi
    else
        echo "✅ accounts.json 檔案已存在"
    fi
}

# 主安裝流程
main() {
    echo ""
    echo "🚀 開始安裝流程..."
    echo ""

    # Step 1: 檢查並安裝 Python
    if ! check_python; then
        if [[ "$OS" == "macOS" ]]; then
            install_python_macos
        elif [[ "$OS" == "Linux" ]]; then
            install_python_linux
        fi

        # 重新檢查
        if ! check_python; then
            echo "❌ Python 安裝失敗，請手動安裝後再試"
            exit 1
        fi
    fi

    # Step 2: 安裝 uv
    install_uv

    # Step 3: 設定 Chrome
    setup_chrome

    # Step 4: 初始化專案
    setup_project

    echo ""
    echo "🎉 安裝完成！"
    echo "=========================================="
    echo ""
    echo "📝 下一步:"
    echo "1. 編輯 accounts.json 設定您的帳號資訊"
    echo "2. 執行程式:"
    echo "   ./run_payment.sh"
    echo ""
    echo "需要幫助？請查看 CLAUDE.md 或 README.md"
}

# 執行主程式
main