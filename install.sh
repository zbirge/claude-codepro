#!/bin/bash
# Claude CodePro Installer Bootstrap Script
#
# Usage: install.sh [OPTIONS]
#   --devcontainer    Install Dev Container configuration (non-interactive)
#   --local           Install locally via Homebrew (non-interactive)
#   -h, --help        Show help message
#
# When run interactively: prompts for Dev Container vs Local installation
# When piped (curl | bash): use --devcontainer or --local flags
#
# Phases:
#   1. Not in container - offer Dev Container or Local installation
#   2. Inside container - run full installer
#   3. Local installation - install via Homebrew then run installer

set -e

# Version updated by semantic-release
VERSION="4.11.0"

REPO="zbirge/claude-codepro"
REPO_RAW="https://raw.githubusercontent.com/${REPO}/v${VERSION}"
LOCAL_INSTALL=false
PRESELECT_MODE=""

# Show usage information
show_usage() {
    echo "Claude CodePro Installer (v${VERSION})"
    echo ""
    echo "Usage: install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --devcontainer    Install Dev Container configuration (non-interactive)"
    echo "  --local           Install locally via Homebrew (non-interactive)"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Interactive mode (prompts for choice)"
    echo "  curl -fsSL https://raw.githubusercontent.com/${REPO}/v${VERSION}/install.sh | bash"
    echo ""
    echo "  # Non-interactive Dev Container setup"
    echo "  curl -fsSL https://raw.githubusercontent.com/${REPO}/v${VERSION}/install.sh | bash -s -- --devcontainer"
    echo ""
    echo "  # Non-interactive local installation"
    echo "  curl -fsSL https://raw.githubusercontent.com/${REPO}/v${VERSION}/install.sh | bash -s -- --local"
}

# Parse command-line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --local)
            PRESELECT_MODE="local"
            shift
            ;;
        --devcontainer)
            PRESELECT_MODE="devcontainer"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            # Pass through unknown arguments to installer binary
            break
            ;;
    esac
done

is_in_container() {
    [ -f "/.dockerenv" ] || [ -f "/run/.containerenv" ]
}

# Download a file from the repo
download_file() {
    local path="$1"
    local dest="$2"
    local url="${REPO_RAW}/${path}"

    mkdir -p "$(dirname "$dest")"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$dest"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$url" -O "$dest"
    else
        echo "Error: Neither curl nor wget found."
        exit 1
    fi
}

check_homebrew() {
    command -v brew >/dev/null 2>&1
}

install_homebrew() {
    echo "  [..] Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    if [ -d "/opt/homebrew/bin" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)" # macOS ARM
    elif [ -d "/usr/local/bin" ] && [ -f "/usr/local/bin/brew" ]; then
        eval "$(/usr/local/bin/brew shellenv)" # macOS Intel
    elif [ -d "/home/linuxbrew/.linuxbrew/bin" ]; then
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" # Linux
    fi

    if ! check_homebrew; then
        echo ""
        echo "  [!!] Homebrew installation failed or brew not in PATH."
        echo "      Please install Homebrew manually or use Dev Container instead."
        exit 1
    fi
    echo "  [OK] Homebrew installed"
}

BREW_PACKAGES="git gh python@3.12 node@22 nvm pnpm bun uv"

install_brew_packages() {
    echo ""
    echo "  Installing required packages via Homebrew..."
    echo ""
    for pkg in $BREW_PACKAGES; do
        if brew list "$pkg" >/dev/null 2>&1; then
            echo "  [OK] $pkg already installed"
        else
            echo "  [..] Installing $pkg..."
            if ! brew install "$pkg"; then
                echo "  [!!] Failed to install $pkg"
                echo "      Please try installing manually or use Dev Container instead."
                exit 1
            fi
            echo "  [OK] $pkg installed"
        fi
    done
    echo ""
    echo "  [OK] All Homebrew packages installed"
}

confirm_local_install() {
    echo ""
    echo "  Local installation will:"
    echo "    • Install Homebrew packages: python@3.12, node@22, nvm, pnpm, bun, uv, git, gh"
    echo "    • Add PATH and 'ccp' alias to your shell config (~/.bashrc, ~/.zshrc, fish)"
    echo "    • Configure Claude Code (~/.claude.json): theme, auto-compact off, MCP servers"
    echo ""

    # If using --local flag (non-interactive), skip confirmation
    if [ "$PRESELECT_MODE" = "local" ]; then
        echo "  (Skipping confirmation due to --local flag)"
        return 0
    fi

    # Interactive confirmation
    confirm=""
    if [ -t 0 ]; then
        printf "  Continue? [Y/n]: "
        read -r confirm
    else
        echo "  No interactive terminal available, continuing with defaults."
        confirm="y"
    fi

    case "$confirm" in
    [Nn] | [Nn][Oo])
        echo "  Cancelled. Run again to choose Dev Container instead."
        exit 0
        ;;
    esac
}

setup_devcontainer() {
    if [ -d ".devcontainer" ]; then
        echo "  [OK] .devcontainer already exists"
    else
        echo "  [..] Downloading dev container configuration..."
        download_file ".devcontainer/Dockerfile" ".devcontainer/Dockerfile"
        download_file ".devcontainer/devcontainer.json" ".devcontainer/devcontainer.json"

        PROJECT_NAME="$(basename "$(pwd)")"
        PROJECT_SLUG="$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' _' '-')"
        if [ -f ".devcontainer/devcontainer.json" ]; then
            sed -i.bak "s/{{PROJECT_NAME}}/${PROJECT_NAME}/g" ".devcontainer/devcontainer.json"
            sed -i.bak "s/{{PROJECT_SLUG}}/${PROJECT_SLUG}/g" ".devcontainer/devcontainer.json"
            rm -f ".devcontainer/devcontainer.json.bak"
        fi

        echo "  [OK] Dev container configuration installed"
    fi

    if [ ! -f ".vscode/extensions.json" ]; then
        echo "  [..] Downloading VS Code extensions recommendations..."
        download_file ".vscode/extensions.json" ".vscode/extensions.json"
        echo "  [OK] VS Code extensions recommendations installed"
    else
        echo "  [OK] .vscode/extensions.json already exists"
    fi

    echo ""
    echo "  Next steps:"
    echo "    1. Open this folder in VS Code"
    echo "    2. Install the 'Dev Containers' extension"
    echo "    3. Press Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows/Linux)"
    echo "    4. Run: 'Dev Containers: Reopen in Container'"
    echo "    5. Once inside the container, run this installer again"
    echo ""
    echo "======================================================================"
    echo ""
    exit 0
}

if ! is_in_container; then
    echo ""
    echo "======================================================================"
    echo "  Claude CodePro Installer (v${VERSION})"
    echo "======================================================================"
    echo ""

    if [ -d ".devcontainer" ]; then
        echo "  Detected existing .devcontainer - using Dev Container mode."
        echo ""
        setup_devcontainer
    fi

    # Check for preselected mode via CLI flags first
    choice=""
    if [ "$PRESELECT_MODE" = "local" ]; then
        echo "  Using --local flag: Local installation selected"
        choice="2"
    elif [ "$PRESELECT_MODE" = "devcontainer" ]; then
        echo "  Using --devcontainer flag: Dev Container selected"
        choice="1"
    elif [ -t 0 ]; then
        # Interactive mode - show menu and prompt
        echo "  Choose installation method:"
        echo ""
        echo "    1) Dev Container - Isolated environment, consistent tooling"
        echo "    2) Local - Install directly on your system via Homebrew (macOS/Linux)"
        echo ""
        printf "  Enter choice [1-2]: "
        read -r choice
    else
        # No terminal available and no preselection - show helpful error
        echo "  Choose installation method:"
        echo ""
        echo "    1) Dev Container - Isolated environment, consistent tooling"
        echo "    2) Local - Install directly on your system via Homebrew (macOS/Linux)"
        echo ""
        echo "  [!!] No interactive terminal available."
        echo ""
        echo "  To install, re-run with a flag:"
        echo "    curl -fsSL ${REPO_RAW}/install.sh | bash -s -- --devcontainer"
        echo "    curl -fsSL ${REPO_RAW}/install.sh | bash -s -- --local"
        echo ""
        echo "  Or run --help for more options:"
        echo "    curl -fsSL ${REPO_RAW}/install.sh | bash -s -- --help"
        echo ""
        exit 1
    fi

    case $choice in
    2)
        LOCAL_INSTALL=true
        echo ""
        echo "  Local Installation selected"
        echo ""

        # Confirm what will be installed
        confirm_local_install

        # Check/install Homebrew
        if check_homebrew; then
            echo "  [OK] Homebrew already installed"
        else
            install_homebrew
        fi

        # Install required packages
        install_brew_packages
        ;;
    *)
        # Dev Container flow
        setup_devcontainer
        ;;
    esac
fi

ARCH="$(uname -m)"
case "$ARCH" in
x86_64 | amd64) ARCH="x86_64" ;;
arm64 | aarch64) ARCH="arm64" ;;
*)
    echo "Error: Unsupported architecture: $ARCH"
    echo "Supported: x86_64, arm64"
    exit 1
    ;;
esac

OS="$(uname -s)"
case "$OS" in
Linux) PLATFORM="linux" ;;
Darwin) PLATFORM="darwin" ;;
*)
    echo "Error: Unsupported operating system: $OS"
    echo "Supported: Linux, macOS (Darwin)"
    exit 1
    ;;
esac

INSTALLER_NAME="ccp-installer-${PLATFORM}-${ARCH}"
INSTALLER_URL="https://github.com/${REPO}/releases/download/v${VERSION}/${INSTALLER_NAME}"
INSTALLER_PATH=".claude/bin/ccp-installer"

CCP_NAME="ccp-${PLATFORM}-${ARCH}"
CCP_URL="https://github.com/${REPO}/releases/download/v${VERSION}/${CCP_NAME}"
CCP_PATH=".claude/bin/ccp"

echo "Downloading Claude CodePro (v${VERSION})..."
echo "  Platform: ${PLATFORM}-${ARCH}"
echo ""

mkdir -p .claude/bin

if [ -f ".claude/bin/ccp" ]; then
    if ! rm -f ".claude/bin/ccp" 2>/dev/null; then
        echo "Error: Cannot update CCP binary - it may be in use."
        echo ""
        echo "Please quit Claude CodePro first (Ctrl+C or /exit), then run this installer again."
        exit 1
    fi
fi

echo "  [..] Downloading installer..."
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$INSTALLER_URL" -o "$INSTALLER_PATH"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$INSTALLER_URL" -O "$INSTALLER_PATH"
else
    echo "Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi
chmod +x "$INSTALLER_PATH"
# Remove macOS quarantine flag if on Darwin
if [ "$(uname -s)" = "Darwin" ]; then
    xattr -cr "$INSTALLER_PATH" 2>/dev/null || true
fi
echo "  [OK] Installer downloaded"

echo "  [..] Downloading ccp binary..."
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$CCP_URL" -o "$CCP_PATH"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$CCP_URL" -O "$CCP_PATH"
else
    echo "Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi
chmod +x "$CCP_PATH"
# Remove macOS quarantine flag if on Darwin
if [ "$(uname -s)" = "Darwin" ]; then
    xattr -cr "$CCP_PATH" 2>/dev/null || true
fi
echo "  [OK] CCP binary downloaded"
echo ""

if [ "$LOCAL_INSTALL" = true ]; then
    "$INSTALLER_PATH" install --local-system "$@"
else
    "$INSTALLER_PATH" install "$@"
fi
