#!/usr/bin/env bash
# start.sh - Install dependencies and start the FastAPI-MCP arithmetic example service
# Usage: bash start.sh

set -euo pipefail

# Step 1: Install dependencies
if command -v uv &> /dev/null; then
    echo "[INFO] Installing dependencies with uv..."
    uv pip install --system --require-virtualenv --require-hashes --upgrade || uv pip install --system --upgrade
    uv pip install fastapi fastapi-mcp uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple
else
    echo "[INFO] uv not found, falling back to pip..."
    pip install fastapi fastapi-mcp uvicorn fastmcp -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

# Step 2: Start the FastAPI-MCP arithmetic service
echo "[INFO] Starting FastAPI-MCP modelservice example service..."
python fastmcpv2_working.py 