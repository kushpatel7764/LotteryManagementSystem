# =============================================================================
# Lottery Management System — Windows Setup Script
# =============================================================================
# Run this script from the project root directory in PowerShell:
#   PowerShell -ExecutionPolicy Bypass -File setup_windows.ps1
#
# What it does:
#   1. Checks / installs Python 3.11+ and pip (via winget if needed)
#   2. Creates a virtual environment and installs all dependencies
#   3. Prompts for your Gmail address and App Password
#   4. Auto-generates FERNET_KEY, FLASK_SECRET_KEY, and SCANNER_API_KEY
#   5. Builds the standalone executable with PyInstaller
#   6. Writes .env to dist\lottery_app\
#   7. Prints this machine's IP address and the SCANNER_API_KEY
# =============================================================================

# Allow script to run even if execution policy is restricted
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue

$ErrorActionPreference = "Stop"

# ── Helpers ───────────────────────────────────────────────────────────────────
function Step  ($msg) { Write-Host "`n━━ $msg" -ForegroundColor Blue }
function Ok    ($msg) { Write-Host "  ✔  $msg" -ForegroundColor Green }
function Warn  ($msg) { Write-Host "  ⚠  $msg" -ForegroundColor Yellow }
function Info  ($msg) { Write-Host "  →  $msg" -ForegroundColor Cyan }
function Die   ($msg) { Write-Host "`nERROR: $msg`n" -ForegroundColor Red; exit 1 }

# ── Verify we are in the project root ────────────────────────────────────────
if (-not (Test-Path "requirements.txt") -or -not (Test-Path "lottery_app.spec")) {
    Die "Run this script from the LotteryManagementSystem project root directory."
}

$PROJECT_DIR = (Get-Location).Path

# ── Step 1 — Python 3.11+ ────────────────────────────────────────────────────
Step "Checking Python installation"

$PYTHON_CMD = $null
$MIN_MINOR  = 11

# Try common command names
foreach ($candidate in @("python", "python3")) {
    try {
        $output = & $candidate --version 2>&1
        if ($output -match "Python (\d+)\.(\d+)") {
            if ([int]$Matches[1] -ge 3 -and [int]$Matches[2] -ge $MIN_MINOR) {
                $PYTHON_CMD = $candidate
                Ok "Found $output at $(Get-Command $candidate | Select-Object -ExpandProperty Source)"
                break
            }
        }
    } catch { }
}

# Try the Windows py launcher (checks 3.13, 3.12, 3.11 in order)
if (-not $PYTHON_CMD) {
    foreach ($v in @("3.13", "3.12", "3.11")) {
        try {
            $output = & py "-$v" --version 2>&1
            if ($output -match "Python") {
                $PYTHON_CMD  = "py"
                $PYTHON_VER  = "-$v"
                Ok "Found $output via py launcher."
                break
            }
        } catch { }
    }
}

# Try winget install
if (-not $PYTHON_CMD) {
    Warn "Python 3.$MIN_MINOR+ not found."
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Info "Installing Python 3.11 via winget…"
        winget install --id Python.Python.3.11 --source winget --silent --accept-package-agreements --accept-source-agreements
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
        $PYTHON_CMD = "python"
        Ok "Python 3.11 installed."
    } else {
        Die "Python 3.$MIN_MINOR+ is required.`nDownload it from https://www.python.org/downloads/ and re-run this script."
    }
}

# Build the final python invocation (handles "py -3.11" form)
if ($PYTHON_VER) {
    $PythonInvoke = { & py $PYTHON_VER @args }
} else {
    $PythonInvoke = { & $PYTHON_CMD @args }
}

# ── Step 2 — Virtual environment ─────────────────────────────────────────────
Step "Setting up virtual environment"

if (Test-Path ".venv") {
    Info ".venv already exists — skipping creation."
} else {
    if ($PYTHON_VER) {
        & py $PYTHON_VER -m venv .venv
    } else {
        & $PYTHON_CMD -m venv .venv
    }
    Ok "Virtual environment created at .venv\"
}

$VENV_PYTHON      = "$PROJECT_DIR\.venv\Scripts\python.exe"
$VENV_PIP         = "$PROJECT_DIR\.venv\Scripts\pip.exe"
$VENV_PYINSTALLER = "$PROJECT_DIR\.venv\Scripts\pyinstaller.exe"

# ── Step 3 — Install dependencies ────────────────────────────────────────────
Step "Installing dependencies"

Info "Upgrading pip…"
& $VENV_PIP install --upgrade pip --quiet

Info "Installing requirements.txt…"
& $VENV_PIP install -r requirements.txt --quiet

Ok "All dependencies installed."

# ── Step 4 — Gmail credentials ───────────────────────────────────────────────
Step "Gmail configuration  (used to email PDF invoices)"
Write-Host ""
Write-Host "  Leave both fields blank to skip — you can configure email later in the app."
Write-Host "  To create a Gmail App Password:"
Write-Host "    Google Account -> Security -> 2-Step Verification -> App Passwords"
Write-Host ""

$GMAIL_SENDER = Read-Host "  Gmail address"

$securePass = Read-Host "  Gmail App Password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePass)
$GMAIL_APP_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

# ── Step 5 — Generate security keys ──────────────────────────────────────────
Step "Generating security keys"

$FERNET_KEY = & $VENV_PYTHON -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$FLASK_SECRET_KEY = & $VENV_PYTHON -c "import secrets; print(secrets.token_hex(32))"
$SCANNER_API_KEY  = & $VENV_PYTHON -c "import secrets; print(secrets.token_hex(32))"

Ok "FERNET_KEY generated."
Ok "FLASK_SECRET_KEY generated."
Ok "SCANNER_API_KEY generated."

# ── Step 6 — Write src\.env ───────────────────────────────────────────────────
Step "Writing src\.env"

$envContent = @"
FERNET_KEY=$FERNET_KEY
FLASK_SECRET_KEY=$FLASK_SECRET_KEY
FLASK_DEBUG=0
SCANNER_API_KEY=$SCANNER_API_KEY
GMAIL_SENDER=$GMAIL_SENDER
GMAIL_APP_PASSWORD=$GMAIL_APP_PASSWORD
"@

# Write without BOM so python-dotenv can read it cleanly
[System.IO.File]::WriteAllText("$PROJECT_DIR\src\.env", $envContent, [System.Text.Encoding]::UTF8)

Ok "src\.env written."

# ── Step 7 — Build with PyInstaller ──────────────────────────────────────────
Step "Building standalone executable  (this may take a few minutes)"

Info "Running PyInstaller…"

$env:PYTHONPATH = "$PROJECT_DIR\src"
& $VENV_PYINSTALLER lottery_app.spec --noconfirm

Ok "Build complete -> dist\lottery_app\lottery_app.exe"

# ── Step 8 — Write dist\lottery_app\.env ─────────────────────────────────────
Step "Writing dist\lottery_app\.env"

New-Item -ItemType Directory -Path "dist\lottery_app" -Force | Out-Null

[System.IO.File]::WriteAllText(
    "$PROJECT_DIR\dist\lottery_app\.env",
    $envContent,
    [System.Text.Encoding]::UTF8
)

Ok "dist\lottery_app\.env written."

# ── Step 9 — Detect local IP ─────────────────────────────────────────────────
Step "Detecting local IP address"

$LOCAL_IP = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.IPAddress -notlike '127.*' -and
        $_.IPAddress -notlike '169.254.*' -and
        $_.PrefixOrigin -ne 'WellKnown'
    } |
    Sort-Object -Property PrefixLength |
    Select-Object -First 1
).IPAddress

if (-not $LOCAL_IP) { $LOCAL_IP = "unknown" }
Ok "Local IP: $LOCAL_IP"

# ── Done — Summary ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              Setup Complete!                         ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Executable:" -ForegroundColor White
Write-Host "    $PROJECT_DIR\dist\lottery_app\lottery_app.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To run the app:" -ForegroundColor White
Write-Host "    .\dist\lottery_app\lottery_app.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "  This computer's IP address:" -ForegroundColor White
Write-Host "    $LOCAL_IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "  App URL (accessible from other devices on the same network):" -ForegroundColor White
Write-Host "    http://${LOCAL_IP}:7777" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Scanner API Key  (set this in your scanner device's header):" -ForegroundColor White
Write-Host "    $SCANNER_API_KEY" -ForegroundColor Cyan
Write-Host ""
Write-Host "  First login credentials:" -ForegroundColor White
Write-Host "    Username: admin    Password: admin" -ForegroundColor Cyan
Write-Host "  ⚠  Change the default password immediately after first login!" -ForegroundColor Yellow
Write-Host ""
