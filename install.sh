#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Heirloom GUI"
DESKTOP_ID="heirloom-gui.desktop"

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
VENV_DIR="${REPO_DIR}/.venv"
LAUNCHER="${REPO_DIR}/run-heirloom-gui.sh"
ICON_PATH="${REPO_DIR}/heirloom/gui/assets/heirloom.png"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/${DESKTOP_ID}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 was not found. Install Python 3.10 or newer and rerun this script." >&2
    exit 1
fi

PYTHON_VERSION="$(python3 - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
if sys.version_info < (3, 10):
    raise SystemExit(1)
PY
)" || {
    echo "Python 3.10 or newer is required." >&2
    exit 1
}

echo "Using Python ${PYTHON_VERSION}"
echo "Repository: ${REPO_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
    echo "Creating virtual environment at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
else
    echo "Using existing virtual environment at ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

echo "Upgrading pip tooling"
python -m pip install --upgrade pip setuptools wheel

echo "Installing requirements"
python -m pip install --upgrade -r "${REPO_DIR}/requirements.txt"

echo "Installing Heirloom Games Manager"
python -m pip install --upgrade "${REPO_DIR}"

chmod +x "${LAUNCHER}"

mkdir -p "${DESKTOP_DIR}"

cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=Browse, install, launch, and uninstall Legacy Games on Linux
Exec=${LAUNCHER}
Icon=${ICON_PATH}
Terminal=false
Categories=Game;
StartupNotify=true
EOF

chmod 0644 "${DESKTOP_FILE}"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_DIR}" >/dev/null 2>&1 || true
fi

echo
echo "Installation complete."
echo "KDE menu item written to: ${DESKTOP_FILE}"
echo "Launch from the Games menu as: ${APP_NAME}"
echo
echo "You can also run:"
echo "  ${LAUNCHER}"
