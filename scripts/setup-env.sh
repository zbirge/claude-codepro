#!/bin/bash

# =============================================================================
# Claude CodePro Environment Setup
# Interactive script to create .env file with API keys
# =============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Color codes
BLUE='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# -----------------------------------------------------------------------------
# Interactive .env Setup
# -----------------------------------------------------------------------------

setup_env_file() {
    print_section "API Keys Setup"

    if [[ -f "$PROJECT_DIR/.env" ]]; then
        print_warning "Found existing .env file"
        read -r -p "Do you want to keep it? (y/n): " -n 1
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_success "Keeping existing .env file"
            return 0
        fi
    fi

    echo "Let's set up your API keys. I'll guide you through each one."
    echo ""

    # Zilliz Cloud (Milvus)
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}1. Zilliz Cloud - Free Vector DB for Semantic Search & Memory${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "   Used for: Persistent memory across CC sessions & semantic code search"
    echo "   Create at: https://zilliz.com/cloud"
    echo ""
    echo "   Steps:"
    echo "   1. Sign up for free account"
    echo "   2. Create a new cluster (Serverless is free)"
    echo "   3. Go to Cluster -> Overview -> Connect"
    echo "   4. Copy the Token and Public Endpoint"
    echo "   5. Go to Clusters -> Users -> Admin -> Reset Password"
    echo ""
    read -r -p "   Enter MILVUS_TOKEN: " MILVUS_TOKEN
    read -r -p "   Enter MILVUS_ADDRESS (Public Endpoint): " MILVUS_ADDRESS
    read -r -p "   Enter VECTOR_STORE_USERNAME (usually db_xxxxx): " VECTOR_STORE_USERNAME
    read -r -p "   Enter VECTOR_STORE_PASSWORD: " VECTOR_STORE_PASSWORD
    echo ""

    # OpenAI API Key
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}2. OpenAI API Key - For Memory LLM Calls${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "   Used for: Low-usage LLM calls in Cipher memory system"
    echo "   Create at: https://platform.openai.com/account/api-keys"
    echo ""
    read -r -p "   Enter OPENAI_API_KEY: " OPENAI_API_KEY
    echo ""

    # Context7 API Key
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}3. Context7 API Key - Free Library Documentation${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "   Used for: Up-to-date library documentation access"
    echo "   Create at: https://context7.com/dashboard"
    echo "   Note: Free tier available, set token limit to 2000 in dashboard"
    echo ""
    read -r -p "   Enter CONTEXT7_API_KEY: " CONTEXT7_API_KEY
    echo ""

    # Ref API Key
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}4. Ref API Key - Free Documentation Search${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "   Used for: Searching public and private documentation"
    echo "   Create at: https://ref.tools/dashboard"
    echo "   Note: You can add your own resources in the UI"
    echo ""
    read -r -p "   Enter REF_API_KEY: " REF_API_KEY
    echo ""

    # Firecrawl API Key
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}5. Firecrawl API Key - Web Crawling${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "   Used for: Web scraping and crawling capabilities"
    echo "   Create at: https://www.firecrawl.dev/app"
    echo ""
    read -r -p "   Enter FIRECRAWL_API_KEY: " FIRECRAWL_API_KEY
    echo ""

    # Create .env file
    cat > "$PROJECT_DIR/.env" <<EOF
# Zilliz Cloud (Free Vector DB for Semantic Search & Persistent Memory)
# Create at https://zilliz.com/cloud
MILVUS_TOKEN=${MILVUS_TOKEN}
MILVUS_ADDRESS=${MILVUS_ADDRESS}
VECTOR_STORE_URL=${MILVUS_ADDRESS}
VECTOR_STORE_USERNAME=${VECTOR_STORE_USERNAME}
VECTOR_STORE_PASSWORD=${VECTOR_STORE_PASSWORD}

# OpenAI API Key - Used for Persistent Memory LLM Calls (Low Usage)
# Create at https://platform.openai.com/account/api-keys
OPENAI_API_KEY=${OPENAI_API_KEY}

# Context7 API Key - Free Tier Available, Limit Tokens to 2000 in Libraries -> Token Limit
# Create at https://context7.com/dashboard
CONTEXT7_API_KEY=${CONTEXT7_API_KEY}

# Ref API Key - Free Tier Available, You can add your own Resources in the UI
# Create at https://ref.tools/dashboard
REF_API_KEY=${REF_API_KEY}

# Firecrawl API Key - Free Tier Available, Used for Web Crawling
# Create at https://www.firecrawl.dev/app
FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}

# Configuration Settings - No need to adjust
USE_ASK_CIPHER=true
VECTOR_STORE_TYPE=milvus
FASTMCP_LOG_LEVEL=ERROR
EOF

    print_success "Created .env file with your API keys"
    echo ""
}

# Main
setup_env_file
