#!/bin/bash
set -e
export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

cd "$SCRIPT_DIR/../asutg_dev"
git lfs install
git lfs pull
git lfs install
git lfs pull
cd "$SCRIPT_DIR"
"$SCRIPT_DIR/../asutg_dev/install/install_python.sh"
