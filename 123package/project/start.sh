#!/usr/bin/env bash
# start.sh - Install dependencies and start the MCP service using the CLI
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR" || exit 1
echo "[INFO] MCP Service Start Script (CLI-Based)"

# Environment variables for Python and pip executables
PYTHON_CMD="${PYTHON_EXECUTABLE:-python3}"
PIP_CMD="${PIP_EXECUTABLE:-pip3}"

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "[ERROR] Command not found: $1. Please ensure it is installed and in PATH."
        echo "If you are in a virtual environment, ensure it is activated."
        exit 1
    fi
}

# Function to install dependencies
install_dependencies() {
    echo "[INFO] Checking/Installing Python dependencies using $PIP_CMD..."
    check_command "$PYTHON_CMD"
    check_command "$PIP_CMD"
    
    # echo "[INFO] Upgrading pip..."
    # if $PIP_CMD install --upgrade pip &> /dev/null; then
    #   echo "[INFO] pip upgraded."
    # else
    #   echo "[WARNING] Failed to upgrade pip. Continuing with current version."
    # fi
    
    # Install mcpy_cli which contains our CLI
    echo "[INFO] Installing mcpy_cli and its dependencies..."
    if $PIP_CMD install --no-cache-dir mcpy_cli -i https://pypi.tuna.tsinghua.edu.cn/simple; then
        echo "[INFO] mcpy_cli installed successfully."
    elif $PIP_CMD install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple mcpy_cli; then
        echo "[INFO] mcpy_cli installed successfully using Tsinghua mirror."
    elif $PIP_CMD install --no-cache-dir -i https://pypi.python.org/simple mcpy_cli; then
        echo "[INFO] mcpy_cli installed successfully using Python.org mirror."
    else
        echo "[ERROR] Failed to install mcpy_cli. Please check your network and pip configuration."
        exit 1
    fi
    
    # Install any user-specific requirements if present
    if [ -f "requirements.txt" ]; then
        echo "[INFO] Installing user requirements from requirements.txt..."
        if ! $PIP_CMD install --no-cache-dir -r requirements.txt; then
            echo "[WARNING] Some requirements from requirements.txt could not be installed."
            echo "You may need to install them manually."
        fi
    fi
}

# Function to start the service using the CLI
start_service() {
    echo "[INFO] Starting MCP service using mcpy-cli CLI..."
    $PYTHON_CMD -m mcpy_cli \
        --source-path "simple_tool.py" \
        --mcp-name "MCPY-CLI" \
        --server-root "/mcp-server" \
        --mcp-base "/mcp" \
        --log-level "info" \
        --cors-enabled --cors-allow-origins "*" --mode composed --legacy-sse \
        run \
        --host "0.0.0.0" \
        --port 8080
}

# Main execution
echo "[INFO] Ensuring Python executable: $PYTHON_CMD can be found."
check_command "$PYTHON_CMD"
install_dependencies
start_service
echo "[INFO] MCP Service script finished."