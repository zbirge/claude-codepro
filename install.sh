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
VERSION="4.8.0"

REPO="zbirge/claude-codepro"
REPO_RAW="https://raw.githubusercontent.com/${REPO}/v${VERSION}"
BINARY_PREFIX="ccp-installer"
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

# Check if running inside a container
is_in_container() {
    [ -f "/.dockerenv" ] || [ -f "/run/.containerenv" ]
}

# Check if we can get interactive input from a terminal
# More robust than just checking if /dev/tty exists - actually tests usability
can_use_tty() {
    # First check: is stdin already a terminal?
    if [ -t 0 ]; then
        return 0
    fi

    # Second check: is /dev/tty available and actually a terminal?
    # This handles cases where /dev/tty exists but isn't properly connected
    # (common in PowerShell + WSL/Git Bash environments)
    if [ -e /dev/tty ] && [ -c /dev/tty ]; then
        # Try to open it and verify it's a terminal
        if ( exec 3</dev/tty && [ -t 3 ] ) 2>/dev/null; then
            return 0
        fi
    fi

    return 1
}

# Read from the best available input source (stdin or /dev/tty)
read_interactive() {
    if [ -t 0 ]; then
        read -r "$@"
    elif [ -e /dev/tty ] && [ -c /dev/tty ]; then
        read -r "$@" </dev/tty
    else
        return 1
    fi
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

# Check if Homebrew is installed
check_homebrew() {
    command -v brew >/dev/null 2>&1
}

# Install Homebrew if not present
install_homebrew() {
    echo "  [..] Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add to PATH for current session
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

# Install required packages via Homebrew
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

# Confirm local installation with user
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
    if can_use_tty; then
        printf "  Continue? [Y/n]: "
        read_interactive confirm
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

# Dev Container setup flow
setup_devcontainer() {
    if [ -d ".devcontainer" ]; then
        echo "  [OK] .devcontainer already exists"
    else
        echo "  [..] Downloading dev container configuration..."
        download_file ".devcontainer/Dockerfile" ".devcontainer/Dockerfile"
        download_file ".devcontainer/devcontainer.json" ".devcontainer/devcontainer.json"

        # Replace placeholders with current directory name
        PROJECT_NAME="$(basename "$(pwd)")"
        PROJECT_SLUG="$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' _' '-')"
        if [ -f ".devcontainer/devcontainer.json" ]; then
            sed -i.bak "s/{{PROJECT_NAME}}/${PROJECT_NAME}/g" ".devcontainer/devcontainer.json"
            sed -i.bak "s/{{PROJECT_SLUG}}/${PROJECT_SLUG}/g" ".devcontainer/devcontainer.json"
            rm -f ".devcontainer/devcontainer.json.bak"
        fi

        echo "  [OK] Dev container configuration installed"
    fi

    # Download VS Code extensions recommendations
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

# Phase 1: Not in container - offer choice
if ! is_in_container; then
    echo ""
    echo "======================================================================"
    echo "  Claude CodePro Installer (v${VERSION})"
    echo "======================================================================"
    echo ""

    # Auto-select Dev Container if .devcontainer already exists
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
    elif can_use_tty; then
        # Interactive mode - show menu and prompt
        echo "  Choose installation method:"
        echo ""
        echo "    1) Dev Container - Isolated environment, consistent tooling"
        echo "    2) Local - Install directly on your system via Homebrew (macOS/Linux)"
        echo ""
        printf "  Enter choice [1-2]: "
        read_interactive choice
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

# Phase 2/3: Run full installer (inside container or local)
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

# Determine platform (linux for container, darwin/linux for local)
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

BINARY_NAME="${BINARY_PREFIX}-${PLATFORM}-${ARCH}"
DOWNLOAD_URL="https://github.com/${REPO}/releases/download/v${VERSION}/${BINARY_NAME}"
INSTALL_PATH="/tmp/${BINARY_NAME}"

echo "Downloading Claude CodePro Installer (v${VERSION})..."
echo "  Platform: ${PLATFORM}-${ARCH}"
echo ""

# Download binary
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$DOWNLOAD_URL" -o "$INSTALL_PATH"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$DOWNLOAD_URL" -O "$INSTALL_PATH"
else
    echo "Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi

# Make executable
chmod +x "$INSTALL_PATH"

# Run installer with appropriate flags
if [ "$LOCAL_INSTALL" = true ]; then
    "$INSTALL_PATH" install --local-system "$@"
else
    "$INSTALL_PATH" install "$@"
fi

# Clean up
rm -f "$INSTALL_PATH"
