#!/usr/bin/env bash
# =============================================================================
# Lottery Management System — macOS Setup Script
# =============================================================================
# Run this script from the project root directory:
#   chmod +x setup_mac.sh
#   ./setup_mac.sh
#
# What it does:
#   1. Checks / installs Python 3.11+ and pip (via Homebrew if needed)
#   2. Creates a virtual environment and installs all dependencies
#   3. Prompts for your Gmail address and App Password
#   4. Auto-generates FERNET_KEY, FLASK_SECRET_KEY, and SCANNER_API_KEY
#   5. Builds the standalone executable with PyInstaller
#   6. Writes .env to dist/lottery_app/
#   7. Prints this machine's IP address and the SCANNER_API_KEY
# =============================================================================

set -euo pipefail

MIN_PYTHON_MINOR=11

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

step() { echo -e "\n${BLUE}${BOLD}━━ $* ${NC}"; }
ok()   { echo -e "  ${GREEN}✔${NC}  $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $*"; }
info() { echo -e "  ${CYAN}→${NC}  $*"; }
die()  { echo -e "\n${RED}${BOLD}ERROR:${NC} $*\n" >&2; exit 1; }

# ── Verify we are in the project root ────────────────────────────────────────
[[ -f "requirements.txt" && -f "lottery_app.spec" ]] ||
    die "Run this script from the LotteryManagementSystem project root directory."

PROJECT_DIR="$(pwd)"

# ── Step 1 — Python 3.11+ ────────────────────────────────────────────────────
step "Checking Python installation"

PYTHON_CMD=""
for cmd in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        MAJOR="${VER%%.*}"
        MINOR="${VER#*.}"; MINOR="${MINOR%%.*}"
        if [[ "${MAJOR:-0}" -ge 3 && "${MINOR:-0}" -ge $MIN_PYTHON_MINOR ]]; then
            PYTHON_CMD="$cmd"
            ok "Found Python $VER at $(command -v "$cmd")"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    warn "Python 3.$MIN_PYTHON_MINOR+ not found."
    if ! command -v brew &>/dev/null; then
        info "Installing Homebrew first…"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Add brew to PATH for Apple Silicon
        eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null || true)"
    fi
    info "Installing Python 3.11 via Homebrew…"
    brew install python@3.11
    PYTHON_CMD="python3.11"
    ok "Python 3.11 installed."
fi

# ── Step 2 — Virtual environment ─────────────────────────────────────────────
step "Setting up virtual environment"

if [[ -d ".venv" ]]; then
    info ".venv already exists — skipping creation."
else
    "$PYTHON_CMD" -m venv .venv
    ok "Virtual environment created at .venv/"
fi

VENV_PYTHON="${PROJECT_DIR}/.venv/bin/python"
VENV_PIP="${PROJECT_DIR}/.venv/bin/pip"
VENV_PYINSTALLER="${PROJECT_DIR}/.venv/bin/pyinstaller"

# ── Step 3 — Install dependencies ────────────────────────────────────────────
step "Installing dependencies"

info "Upgrading pip…"
"$VENV_PIP" install --upgrade pip --quiet

info "Installing requirements.txt…"
"$VENV_PIP" install -r requirements.txt --quiet

ok "All dependencies installed."

# ── Step 4 — Gmail credentials ───────────────────────────────────────────────
step "Gmail configuration  (used to email PDF invoices)"
echo ""
echo "  Leave both fields blank to skip — you can configure email later in the app."
echo "  To create a Gmail App Password:"
echo "    Google Account → Security → 2-Step Verification → App Passwords"
echo ""
read -rp  "  Gmail address       : " GMAIL_SENDER
read -rsp "  Gmail App Password  : " GMAIL_APP_PASSWORD
echo ""

# ── Step 5 — Generate security keys ──────────────────────────────────────────
step "Generating security keys"

FERNET_KEY=$(
    "$VENV_PYTHON" -c \
        "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
)
FLASK_SECRET_KEY=$(
    "$VENV_PYTHON" -c \
        "import secrets; print(secrets.token_hex(32))"
)
SCANNER_API_KEY=$(
    "$VENV_PYTHON" -c \
        "import secrets; print(secrets.token_hex(32))"
)

ok "FERNET_KEY generated."
ok "FLASK_SECRET_KEY generated."
ok "SCANNER_API_KEY generated."

# ── Step 6 — Write src/.env ───────────────────────────────────────────────────
step "Writing src/.env"

printf 'FERNET_KEY=%s\nFLASK_SECRET_KEY=%s\nFLASK_DEBUG=0\nSCANNER_API_KEY=%s\nGMAIL_SENDER=%s\nGMAIL_APP_PASSWORD=%s\n' \
    "$FERNET_KEY" "$FLASK_SECRET_KEY" "$SCANNER_API_KEY" \
    "$GMAIL_SENDER" "$GMAIL_APP_PASSWORD" \
    > src/.env

ok "src/.env written."

# ── Step 7 — Build with PyInstaller ──────────────────────────────────────────
step "Building standalone executable  (this may take a few minutes)"

info "Running PyInstaller…"
PYTHONPATH="${PROJECT_DIR}/src" \
    "$VENV_PYINSTALLER" lottery_app.spec --noconfirm

ok "Build complete → dist/lottery_app/lottery_app"

# ── Step 8 — Write dist/lottery_app/.env ─────────────────────────────────────
step "Writing dist/lottery_app/.env"

mkdir -p dist/lottery_app

printf 'FERNET_KEY=%s\nFLASK_SECRET_KEY=%s\nFLASK_DEBUG=0\nSCANNER_API_KEY=%s\nGMAIL_SENDER=%s\nGMAIL_APP_PASSWORD=%s\n' \
    "$FERNET_KEY" "$FLASK_SECRET_KEY" "$SCANNER_API_KEY" \
    "$GMAIL_SENDER" "$GMAIL_APP_PASSWORD" \
    > dist/lottery_app/.env

ok "dist/lottery_app/.env written."

# ── Step 9 — Detect local IP ──────────────────────────────────────────────────
step "Detecting local IP address"

LOCAL_IP=$(
    ipconfig getifaddr en0 2>/dev/null ||
    ipconfig getifaddr en1 2>/dev/null ||
    ipconfig getifaddr en2 2>/dev/null ||
    ifconfig 2>/dev/null \
        | grep 'inet ' \
        | grep -v '127\.0\.0\.1' \
        | awk '{print $2}' \
        | head -1 ||
    echo "unknown"
)
ok "Local IP: ${LOCAL_IP}"

# ── Done — Summary ────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║              Setup Complete!                         ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Executable:${NC}"
echo -e "    ${CYAN}${PROJECT_DIR}/dist/lottery_app/lottery_app${NC}"
echo ""
echo -e "  ${BOLD}To run the app:${NC}"
echo -e "    ${CYAN}./dist/lottery_app/lottery_app${NC}"
echo ""
echo -e "  ${BOLD}This computer's IP address:${NC}"
echo -e "    ${CYAN}${LOCAL_IP}${NC}"
echo ""
echo -e "  ${BOLD}App URL (accessible from other devices on the same network):${NC}"
echo -e "    ${CYAN}http://${LOCAL_IP}:7777${NC}"
echo ""
echo -e "  ${BOLD}Scanner API Key${NC}  (set this in your scanner device's header):"
echo -e "    ${CYAN}${SCANNER_API_KEY}${NC}"
echo ""
echo -e "  ${BOLD}First login credentials:${NC}"
echo -e "    Username: ${CYAN}admin${NC}    Password: ${CYAN}admin${NC}"
echo -e "  ${YELLOW}  ⚠  Change the default password immediately after first login!${NC}"
echo ""
