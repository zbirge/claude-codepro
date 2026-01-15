FROM mcr.microsoft.com/devcontainers/base:ubuntu

SHELL ["/bin/bash", "-l", "-c"]

# Install essential packages
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libffi-dev \
        liblzma-dev \
        curl \
        git \
        jq \
        vim \
        gh \
        glab \
        dos2unix \
        netcat-openbsd \
        # Playwright/Chromium dependencies for Ubuntu 24.04+
        # (packages renamed with t64 suffix for 64-bit time_t support)
        libasound2t64 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0t64 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        libxshmfence1 \
        xvfb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
