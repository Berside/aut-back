#!/bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
BIN_DIR="$SCRIPT_DIR/.venv/bin"
"$BIN_DIR/python3" -m pytest