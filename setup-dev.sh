#!/bin/bash
# Cross-platform setup wrapper for Linux/macOS
# This script ensures the correct Python command is used

set -e

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

exec "$PYTHON_CMD" setup-env.py "$@"
