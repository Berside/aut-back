#!/bin/bash
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
BIN_DIR="$SCRIPT_DIR/.venv/bin"
"$BIN_DIR/python3" -m pytest
echo "Running tests times" > test_results.txt
for i in {1..100}; do
  echo "----------------------------------- Test run: $i" >> test_results.txt
  "$BIN_DIR/python3" -m pytest &>> test_results.txt
done