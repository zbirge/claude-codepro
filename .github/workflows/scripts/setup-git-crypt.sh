#!/bin/bash
# Setup git-crypt for CI/CD builds
# This script decodes the GIT_CRYPT_KEY secret and unlocks the repository

set -e

if [ -z "$GIT_CRYPT_KEY" ]; then
    echo "Error: GIT_CRYPT_KEY environment variable not set"
    exit 1
fi

# Create temporary key file
KEY_FILE=$(mktemp)
trap 'rm -f "$KEY_FILE"' EXIT

# Decode base64 key and write to file
echo "$GIT_CRYPT_KEY" | base64 -d > "$KEY_FILE"

# Unlock the repository
git-crypt unlock "$KEY_FILE"

echo "Repository unlocked successfully"
