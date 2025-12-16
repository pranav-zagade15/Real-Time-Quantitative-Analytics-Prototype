#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"
PYTHON=${PYTHON:-python3}
$PYTHON -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Virtual environment created and dependencies installed. Activate with: source $VENV_DIR/bin/activate"}
