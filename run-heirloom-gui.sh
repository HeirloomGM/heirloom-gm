#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

if [[ ! -x "${VENV_DIR}/bin/heirloom-gui" ]]; then
    echo "Heirloom GUI is not installed in ${VENV_DIR}." >&2
    echo "Run ${SCRIPT_DIR}/install.sh first." >&2
    exit 1
fi

source "${VENV_DIR}/bin/activate"
exec heirloom-gui "$@"
