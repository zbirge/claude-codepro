#!/bin/bash

# =============================================================================
# Claude CodePro Installation Script
# Installs Claude CodePro directly on host machine (no container required)
# =============================================================================

set -e

# Repository configuration
REPO_URL="https://github.com/maxritter/claude-codepro"
REPO_BRANCH="main"

# Installation paths
PROJECT_DIR="$(pwd)"
TEMP_DIR=$(mktemp -d)

# Color codes
BLUE='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Print functions
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# Cleanup on exit
cleanup() {
    if [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
    tput cnorm 2>/dev/null || true
}
trap cleanup EXIT

# -----------------------------------------------------------------------------
# Download Functions
# -----------------------------------------------------------------------------

download_file() {
    local repo_path=$1
    local dest_path=$2
    local file_url="${REPO_URL}/raw/${REPO_BRANCH}/${repo_path}"

    mkdir -p "$(dirname "$dest_path")"

    if curl -sL --fail "$file_url" -o "$dest_path" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Get all files from repo directory
get_repo_files() {
    local dir_path=$1
    local branch="main"
    local repo_path
    repo_path="${REPO_URL#https://github.com/}"
    local tree_url="https://api.github.com/repos/${repo_path}/git/trees/${branch}?recursive=true"

    local response
    response=$(curl -sL "$tree_url")

    if command -v python3 &> /dev/null; then
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('tree', []):
    if item.get('type') == 'blob' and item.get('path', '').startswith('$dir_path'):
        print(item.get('path', ''))
"
    fi
}

# -----------------------------------------------------------------------------
# Installation Functions - Claude CodePro Files
# -----------------------------------------------------------------------------

install_directory() {
    local repo_dir=$1
    local dest_base=$2

    print_status "Installing $repo_dir..."

    local file_count=0
    local files
    files=$(get_repo_files "$repo_dir")

    if [[ -n "$files" ]]; then
        while IFS= read -r file_path; do
            if [[ -n "$file_path" ]]; then
                local dest_file="${dest_base}/${file_path}"

                if download_file "$file_path" "$dest_file"; then
                    ((file_count++)) || true
                fi
            fi
        done <<< "$files"
    fi

    print_success "Installed $file_count files"
}

install_file() {
    local repo_file=$1
    local dest_file=$2

    if download_file "$repo_file" "$dest_file"; then
        print_success "Installed $repo_file"
        return 0
    else
        print_warning "Failed to install $repo_file"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Dependency Installation Functions
# -----------------------------------------------------------------------------

install_uv() {
    if command -v uv &> /dev/null; then
        print_success "uv already installed"
        return 0
    fi

    print_status "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Source the uv env
    export PATH="$HOME/.cargo/bin:$PATH"

    print_success "Installed uv"
}

install_python_tools() {
    print_status "Installing Python tools globally..."

    uv tool install ruff
    uv tool install mypy
    uv tool install basedpyright

    print_success "Installed Python tools (ruff, mypy, basedpyright)"
}

install_qlty() {
    if command -v qlty &> /dev/null; then
        print_success "qlty already installed"
        return 0
    fi

    print_status "Installing qlty..."
    curl -s https://qlty.sh | sh

    # Add to PATH
    export QLTY_INSTALL="$HOME/.qlty"
    export PATH="$QLTY_INSTALL/bin:$PATH"

    # Initialize qlty for this project
    cd "$PROJECT_DIR" && "$HOME/.qlty/bin/qlty" check --install-only

    print_success "Installed qlty"
}

install_claude_code() {
    if command -v claude &> /dev/null; then
        print_success "Claude Code already installed"
        return 0
    fi

    print_status "Installing Claude Code..."
    curl -fsSL https://claude.ai/install.sh | bash

    print_success "Installed Claude Code"
}

install_cipher() {
    if command -v cipher &> /dev/null; then
        print_success "Cipher already installed"
        return 0
    fi

    print_status "Installing Cipher..."
    npm install -g @byterover/cipher

    print_success "Installed Cipher"
}

install_newman() {
    if command -v newman &> /dev/null; then
        print_success "Newman already installed"
        return 0
    fi

    print_status "Installing Newman..."
    npm install -g newman

    print_success "Installed Newman"
}

install_statusline() {
    print_status "Installing Claude Code Statusline..."
    curl -fsSL https://raw.githubusercontent.com/hagan/claudia-statusline/main/scripts/quick-install.sh | bash

    print_success "Installed Claude Code Statusline"
}

install_dotenvx() {
    if command -v dotenvx &> /dev/null; then
        print_success "dotenvx already installed"
        return 0
    fi

    print_status "Installing dotenvx..."
    curl -sfS https://dotenvx.sh | sh

    print_success "Installed dotenvx"
}

# -----------------------------------------------------------------------------
# Shell Configuration
# -----------------------------------------------------------------------------

add_cc_alias() {
    print_status "Adding cc alias to shell configurations..."

    local alias_line="alias cc=\"cd '$PROJECT_DIR' && bash scripts/build-rules.sh && clear && dotenvx run -- claude\""

    # Add to .bashrc
    if [[ -f "$HOME/.bashrc" ]]; then
        if ! grep -q "alias cc=" "$HOME/.bashrc"; then
            {
                echo ""
                echo "# Claude CodePro alias"
                echo "$alias_line"
            } >> "$HOME/.bashrc"
            print_success "Added alias to .bashrc"
        fi
    fi

    # Add to .zshrc
    if [[ -f "$HOME/.zshrc" ]]; then
        if ! grep -q "alias cc=" "$HOME/.zshrc"; then
            {
                echo ""
                echo "# Claude CodePro alias"
                echo "$alias_line"
            } >> "$HOME/.zshrc"
            print_success "Added alias to .zshrc"
        fi
    fi

    # Add to fish config
    if [[ -d "$HOME/.config/fish" ]]; then
        mkdir -p "$HOME/.config/fish"
        local fish_alias="alias cc='cd $PROJECT_DIR; and bash scripts/build-rules.sh; and clear; and dotenvx run -- claude'"

        if [[ ! -f "$HOME/.config/fish/config.fish" ]] || ! grep -q "alias cc=" "$HOME/.config/fish/config.fish"; then
            {
                echo ""
                echo "# Claude CodePro alias"
                echo "$fish_alias"
            } >> "$HOME/.config/fish/config.fish"
            print_success "Added alias to fish config"
        fi
    fi
}

# -----------------------------------------------------------------------------
# Build Rules
# -----------------------------------------------------------------------------

build_rules() {
    print_status "Building Claude Code commands and skills..."

    if [[ -f "$PROJECT_DIR/scripts/build-rules.sh" ]]; then
        bash "$PROJECT_DIR/scripts/build-rules.sh"
        print_success "Built commands and skills"
    else
        print_warning "build-rules.sh not found, skipping"
    fi
}

# -----------------------------------------------------------------------------
# Main Installation
# -----------------------------------------------------------------------------

main() {
    print_section "Claude CodePro Installation"

    print_status "Installing into: $PROJECT_DIR"
    echo ""

    # Ask about Python support
    echo "Do you want to install advanced Python features?"
    echo "This includes: uv, ruff, mypy, basedpyright, and Python quality hooks"
    read -r -p "Install Python support? (y/n): " -n 1 INSTALL_PYTHON
    echo ""
    echo ""

    # Check for existing Claude installation
    if [[ -d "$PROJECT_DIR/.claude" ]]; then
        print_warning ".claude already exists"
        read -r -p "Overwrite? (y/n): " -n 1
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled"
            exit 0
        fi
    fi

    # Install Claude CodePro files
    print_section "Installing Claude CodePro Files"

    # Download .claude directory first
    print_status "Downloading .claude files..."
    local files
    files=$(get_repo_files ".claude")

    local file_count=0
    if [[ -n "$files" ]]; then
        while IFS= read -r file_path; do
            if [[ -n "$file_path" ]]; then
                # Skip Python hook if Python not selected
                if [[ "$INSTALL_PYTHON" =~ ^[Yy]$ ]] || [[ "$file_path" != *"file_checker_python.sh"* ]]; then
                    # Handle settings.local.json specially
                    if [[ "$file_path" == *"settings.local.json"* ]]; then
                        if [[ -f "$PROJECT_DIR/.claude/settings.local.json" ]]; then
                            print_warning "settings.local.json already exists"
                            echo "This file contains Claude Code configuration (permissions, hooks, MCP servers)."
                            echo "Overwriting will replace your current configuration with Claude CodePro defaults."
                            read -r -p "Overwrite settings.local.json? (y/n): " -n 1
                            echo
                            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                                print_warning "Skipped settings.local.json (keeping existing)"
                                continue
                            fi
                        fi
                    fi

                    local dest_file="${PROJECT_DIR}/${file_path}"
                    if download_file "$file_path" "$dest_file"; then
                        ((file_count++)) || true
                    fi
                fi
            fi
        done <<< "$files"
    fi

    # Remove Python hook from settings.local.json if Python not selected
    if [[ ! "$INSTALL_PYTHON" =~ ^[Yy]$ ]] && [[ -f "$PROJECT_DIR/.claude/settings.local.json" ]]; then
        print_status "Removing Python hook from settings.local.json..."
        # Use Python to cleanly remove the Python hook entry from JSON
        python3 -c "
import json
with open('$PROJECT_DIR/.claude/settings.local.json', 'r') as f:
    config = json.load(f)

# Remove Python hook
if 'hooks' in config and 'PostToolUse' in config['hooks']:
    for hook_group in config['hooks']['PostToolUse']:
        if 'hooks' in hook_group:
            hook_group['hooks'] = [h for h in hook_group['hooks'] if 'file_checker_python.sh' not in h.get('command', '')]

# Remove Python-related permissions
python_perms = ['Bash(basedpyright:*)', 'Bash(mypy:*)', 'Bash(python tests:*)', 'Bash(python:*)',
                'Bash(pyright:*)', 'Bash(pytest:*)', 'Bash(ruff check:*)', 'Bash(ruff format:*)',
                'Bash(uv add:*)', 'Bash(uv pip show:*)', 'Bash(uv pip:*)', 'Bash(uv run:*)']
if 'permissions' in config and 'allow' in config['permissions']:
    config['permissions']['allow'] = [p for p in config['permissions']['allow'] if p not in python_perms]

with open('$PROJECT_DIR/.claude/settings.local.json', 'w') as f:
    json.dump(config, f, indent=2)
"
        print_success "Configured settings.local.json without Python support"
    fi

    chmod +x "$PROJECT_DIR/.claude/hooks/"*.sh 2>/dev/null || true
    print_success "Installed $file_count .claude files"
    echo ""

    if [[ ! -d "$PROJECT_DIR/.cipher" ]]; then
        install_directory ".cipher" "$PROJECT_DIR"
        echo ""
    fi

    if [[ ! -d "$PROJECT_DIR/.qlty" ]]; then
        install_directory ".qlty" "$PROJECT_DIR"
        echo ""
    fi

    print_status "Installing MCP configuration..."
    install_file ".mcp.json" "$PROJECT_DIR/.mcp.json"
    install_file ".mcp-funnel.json" "$PROJECT_DIR/.mcp-funnel.json"
    echo ""

    mkdir -p "$PROJECT_DIR/scripts"
    install_file "scripts/setup-env.sh" "$PROJECT_DIR/scripts/setup-env.sh"
    install_file "scripts/build-rules.sh" "$PROJECT_DIR/scripts/build-rules.sh"
    chmod +x "$PROJECT_DIR/scripts/"*.sh
    echo ""

    # Run .env setup
    print_section "Environment Setup"
    bash "$PROJECT_DIR/scripts/setup-env.sh"

    # Install dependencies
    print_section "Installing Dependencies"

    # Install Python tools if selected
    if [[ "$INSTALL_PYTHON" =~ ^[Yy]$ ]]; then
        install_uv
        echo ""

        install_python_tools
        echo ""
    fi

    install_qlty
    echo ""

    install_claude_code
    echo ""

    install_cipher
    echo ""

    install_newman
    echo ""

    install_statusline
    echo ""

    install_dotenvx
    echo ""

    # Build rules
    print_section "Building Rules"
    build_rules
    echo ""

    # Configure shells
    print_section "Configuring Shell"
    add_cc_alias
    echo ""

    # Success message
    print_section "Installation Complete!"

    echo -e "${GREEN}Claude CodePro has been successfully installed!${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo "1. Reload your shell or run: source ~/.bashrc (or ~/.zshrc)"
    echo "2. Run: cc"
    echo "3. Configure Claude Code with /config:"
    echo "   - Set 'Auto-connect to IDE' = true"
    echo "   - Set 'Auto-compact' = false"
    echo "4. Verify setup:"
    echo "   /ide     # Connect to VS Code"
    echo "   /mcp     # Check MCP servers"
    echo "   /context # Verify context usage"
    echo "5. Start building:"
    echo "   /quick     # Fast development"
    echo "   /plan      # Spec-driven workflow"
    echo "   /implement # Execute with TDD"
    echo "   /verify    # Quality checks"
    echo ""
    echo -e "${GREEN}📚 Learn more: https://www.claude-code.pro${NC}"
    echo ""
}

# Run main
main "$@"
