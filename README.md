# Lottery Management System

A Flask web application for lottery retailers to manage instant ticket inventory, track real-time sales via barcode scanning, generate daily financial reports, and produce PDF invoices — all backed by an encrypted SQLite database.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Installation Guide](#installation-guide)
5. [Running the Application](#running-the-application)
6. [Project Structure](#project-structure)
7. [Usage](#usage)
8. [Configuration](#configuration)
9. [Database](#database)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Future Improvements](#future-improvements)

---

## Overview

### What It Does

The Lottery Management System is a web-based point-of-sale and reporting tool built for lottery retailers. It allows store operators to:

- **Scan physical lottery ticket barcodes** to record each sale in real time
- **Track multiple active ticket books** simultaneously with per-book open/close ticket numbers
- **Submit a daily sales report** that atomically finalises all pending scans into a numbered report
- **Generate and email PDF invoices** summarising each day's financial activity
- **Manage users** with role-based access control for staff and administrators

### Problem It Solves

Lottery retailers must track the sale of individual instant tickets across many different games and ticket books. Manual spreadsheets are error-prone, time-consuming, and offer no audit trail. This system replaces that workflow with a structured, database-backed application that:

- Eliminates manual entry errors by reading barcodes directly
- Maintains a complete, immutable history of every scan and every report
- Protects financially sensitive data with database encryption at rest
- Generates professional invoices suitable for bookkeeping and submission to lottery distributors

### Why It Is Useful

- **For store staff**: A simple scanning interface — point a barcode scanner at a ticket and the system handles the rest
- **For store managers**: Role-based access means staff can only scan; managers approve daily submissions
- **For accountants**: Every report is downloadable as a PDF invoice with full financial detail
- **For compliance**: Encrypted storage, parameterised SQL queries, CSRF protection, and rate-limited login reduce audit and security risk

---

## Features

- **Barcode Scanning** — Parse 29-digit lottery barcodes to extract game number, ticket price, book ID, and ticket quantity; validate against a multi-state lottery game lookup table
- **Polling-Based Scanner API** — Connect any USB or networked barcode scanner via the `/receive` endpoint; the frontend polls `/check_barcode_stack` to consume scans without page reloads
- **Book Lifecycle Management** — Add, activate, deactivate, and delete ticket books; automatic deactivation of sold-out books on daily submission
- **Undo Last Scan** — Remove the most recent ticket scan for any active book, restoring the previous ticket number and sales log entry
- **Sold-Out Detection** — Mark a book as completely sold out; the system updates the closing ticket number and flags the book for removal on submission
- **Daily Report Submission** — Atomic three-phase commit that transitions all "Pending" scan data to a sequentially numbered, date-stamped report
- **Editable Reports** — Admin users can correct individual sales log entries; changes cascade automatically to adjacent reports to maintain continuity
- **PDF Invoice Generation** — ReportLab-powered invoices containing business info, per-book ticket detail, and a full financial summary
- **Email Invoices** — Send generated invoices directly via Gmail SMTP from the application
- **Role-Based Access Control** — Three roles: `standard` (scan only), `admin` (full access), and `default_admin` (protected system account that cannot be deleted)
- **Database Encryption at Rest** — The SQLite database is Fernet-encrypted on shutdown and decrypted on startup; the plaintext file never persists between sessions
- **Configurable Settings** — Ticket counting direction (ascending/descending), invoice output path, timezone, and barcode polling toggle — all adjustable from the UI
- **Business Profile** — Store name, address, phone, and email fields with validation, embedded in every generated invoice
- **Rate-Limited Login** — Brute-force protection: the `/login` endpoint is capped at 10 requests per minute per IP
- **CSRF Protection** — Flask-WTF CSRFProtect applied globally to all state-changing requests
- **Version Update Notifications** — Background thread checks for new releases on GitHub and notifies users on their next page load

---

## Tech Stack

| Category | Technology | Version |
|---|---|---|
| Web Framework | Flask | 3.0.3 |
| Authentication | Flask-Login | 0.6.3 |
| CSRF Protection | Flask-WTF | 1.2.2 |
| Rate Limiting | Flask-Limiter | 3.11.0 |
| Real-Time / WebSocket | Flask-SocketIO | 5.5.1 |
| Database | SQLite 3 (built-in) | — |
| Database Encryption | cryptography (Fernet) | 46.0.7 |
| Password Hashing | Werkzeug Security | (Flask dependency) |
| Environment Variables | python-dotenv | 1.2.1 |
| Data Processing | pandas | 2.2.3 |
| PDF Generation | ReportLab | 4.4.10 |
| HTTP Client | requests | 2.31.0 |
| JSON Handling | simplejson | 3.20.2 |
| WSGI Server (production) | Gunicorn | 21.2.0 |
| Packaging | PyInstaller | 6.19.10 |
| Test Framework | pytest | 8.4.2 |
| Mocking | pytest-mock | 3.15.1 |
| Linting | Pylint, Ruff | — |

---

## Installation Guide

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 or higher |
| pip | 23.0 or higher |
| git | Any recent version |

> **Note:** The application is developed and tested on macOS and Linux. Windows is supported but may require minor path adjustments.

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/LotteryManagementSystem.git
cd LotteryManagementSystem
```

### Step 2 — Create and Activate a Virtual Environment

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate it — macOS / Linux
source .venv/bin/activate

# Activate it — Windows (Command Prompt)
.venv\Scripts\activate.bat

# Activate it — Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of your terminal prompt once activated.

### Step 3 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 — Install the Package in Editable Mode

The source code lives under `src/`. Installing in editable mode makes the `lottery_app` package importable from anywhere in the project (required for tests and CLI entry points).

```bash
pip install -e .
```

### Step 5 — Generate a Fernet Encryption Key

The application encrypts its database at rest using a Fernet symmetric key. Generate one now:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output — you will use it in the next step.

### Step 6 — Create the `.env` File

Create `src/.env` with the following content. Replace every placeholder value with your own:

```dotenv
# ── Required ─────────────────────────────────────────────────────────────────

# 44-character Base64 Fernet key (generated in Step 5)
FERNET_KEY=your-generated-fernet-key-here

# Secret key for Flask session signing — use a long, random hex string
FLASK_SECRET_KEY=change-me-to-a-long-random-secret

# ── Optional ──────────────────────────────────────────────────────────────────

# Set to 1 to enable Flask debug mode (never use in production)
FLASK_DEBUG=0

# API key for the external barcode scanner endpoint (/receive)
# If omitted, the endpoint accepts requests from any source
SCANNER_API_KEY=

# Gmail credentials for sending PDF invoices by email
GMAIL_SENDER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
```

> **Security note:** Never commit `.env` to version control. It is already listed in `.gitignore`.

---

## Running the Application

### Development Server

```bash
# Make sure the virtual environment is active, then:
python src/lottery_app/app.py
```

The application starts on **port 7777** and automatically opens your default browser to:

```
http://127.0.0.1:7777
```

### Using the Flask CLI

```bash
export FLASK_APP=src/lottery_app:create_app
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=7777
```

### First-Time Login

On first startup the database is initialised and a `default_admin` account is created. Log in with:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin` |

> **Change the default password immediately** via **Settings → Change Password** after your first login.

---

## Project Structure

```
LotteryManagementSystem-master/
│
├── src/
│   └── lottery_app/               # Main application package
│       ├── __init__.py            # App factory (create_app); encryption lifecycle
│       ├── app.py                 # Entry point: launch_app() + CLI main
│       ├── extensions.py          # Shared Flask extensions (CSRF, rate limiter)
│       ├── decorators.py          # get_db_cursor context manager; @admin_required
│       ├── config.json            # Persistent runtime configuration
│       │
│       ├── routes/                # Flask Blueprints — one per feature area
│       │   ├── security.py        # /login, /logout, /signup, /change_password, /delete_user
│       │   ├── tickets.py         # /scan_tickets, /undo_scan, /book_sold_out, /submit
│       │   ├── books.py           # /books_managment, /activate_book, /deactivate_book, /delete_book
│       │   ├── reports.py         # /edit_reports, /edit_report/<id>, /update_salesLog, /download/<id>
│       │   ├── scanner.py         # /receive (external scanner API), /check_barcode_stack
│       │   ├── settings.py        # /settings (ticket order, invoice path, polling toggle)
│       │   ├── business_profile.py# /business_profile
│       │   └── home.py            # / (index)
│       │
│       ├── database/              # All database interaction
│       │   ├── Lottery_DB_Schema.sql       # SQLite schema (tables, triggers, indexes)
│       │   ├── setup_database.py           # initialize_database(); migration helpers
│       │   ├── database_queries.py         # 30+ read-only SELECT query functions
│       │   ├── user_model.py               # User class with CRUD operations
│       │   ├── update_books.py             # Book INSERT/UPDATE/DELETE
│       │   ├── update_activated_books.py   # ActivatedBooks management
│       │   ├── update_sale_log.py          # SalesLog INSERT/UPDATE
│       │   ├── update_sale_report.py       # SaleReport INSERT/UPDATE
│       │   ├── update_ticket_timeline.py   # TicketTimeLine INSERT/DELETE
│       │   └── update_ticket_name_lookup.py# TicketNameLookup population
│       │
│       ├── utils/                 # Shared utilities
│       │   ├── config.py          # load_config(), update_*(), get_timezone(), BARCODE_QUEUE
│       │   ├── encrypted_db.py    # encrypt_file(), decrypt_file(), get_cipher()
│       │   ├── reports.py         # calculate_instant_tickets_sold(); sales log cascade logic
│       │   ├── tickets.py         # insert_ticket() — create TicketTimeLine + SalesLog entries
│       │   ├── books.py           # Book activation / addition business logic
│       │   ├── version_check.py   # GitHub release check; background thread
│       │   └── error_hanlder.py   # check_error() validation helper
│       │
│       ├── scanned_code_information_management.py  # ScannedCodeManagement — 29-digit barcode parser
│       ├── game_number_lookup_table.py              # Pandas DataFrame: game numbers → ticket names/prices
│       ├── generate_invoice.py                      # ReportLab PDF invoice builder
│       ├── email_invoice.py                         # Gmail SMTP invoice sender
│       ├── utc_to_local_time.py                     # UTC → configured local timezone
│       │
│       ├── templates/             # Jinja2 HTML templates
│       │   ├── login.html
│       │   ├── scan_tickets.html
│       │   ├── books_managment.html
│       │   ├── edit_reports.html
│       │   ├── edit_single_report.html
│       │   ├── settings.html
│       │   ├── business_profile.html
│       │   └── index.html
│       │
│       ├── static/                # CSS stylesheets and image assets
│       └── instance_folder/       # Runtime data — created automatically on first run
│           ├── Lottery_Management_Database.db      # SQLite database (plaintext, only at runtime)
│           └── Lottery_Management_Database.db.enc  # Fernet-encrypted database (persisted to disk)
│
├── tests/                         # Full test suite (~34 modules)
│   ├── conftest.py                # Shared pytest fixtures
│   ├── database/                  # Database query and update tests
│   ├── routes/                    # Route and blueprint tests
│   ├── security/                  # Auth, authorisation, and input validation tests
│   └── utils/                     # Utility function tests
│
├── requirements.txt               # Python dependencies
├── setup.py                       # Package configuration
├── pytest.ini                     # Pytest settings
├── .pylintrc                      # Pylint configuration
├── lottery_app.spec               # PyInstaller build specification
└── .gitignore
```

---

## Usage

### Typical Daily Workflow

#### 1. Log In

Navigate to `http://127.0.0.1:7777` and log in with your credentials. Staff with the `standard` role can scan tickets; `admin` users have access to all management screens.

---

#### 2. Activate Ticket Books

Go to **Books Management** (`/books_managment`).

To add a new book, scan its barcode or type the 29-digit code manually. The system validates the code against the lottery game lookup table and stores the book.

To activate a book for scanning, click **Activate** (or scan the book's barcode on the Activate screen). The book will appear in the active books list on the scan page.

---

#### 3. Scan Tickets

Go to **Scan Tickets** (`/scan_tickets`).

Either:
- **Type** a ticket barcode into the input field and press Enter, or
- **Use a connected barcode scanner** — if polling is enabled (Settings → Enable Scanner Polling), the page automatically detects the scan without any manual input

The system records the ticket number, updates the sales log for that book, and displays the running total of tickets sold.

If you make a mistake, click **Undo Last Scan** to remove the most recent entry for any active book.

When a book runs out of tickets, click **Mark Book as Sold Out**. The book is flagged and will be removed from the active list on the next submission.

---

#### 4. Submit the Day's Report

Go to **Scan Tickets → Submit** (`/submit`) at the end of the day.

The system performs an atomic commit that:
1. Assigns the next sequential Report ID to all "Pending" scan data
2. Creates a `SaleReport` record with the current date and time
3. Removes sold-out books from the active list
4. Generates a PDF invoice saved to the configured output path
5. Optionally emails the invoice to the configured address

Once submitted, the report cannot be undone from the scan screen. Admins can edit individual lines via **Edit Reports**.

---

#### 5. Review and Download Reports

Go to **Edit Reports** (`/edit_reports`).

All historical reports are listed with date, time, and totals. Click a report to open it. Admin users can correct any sales log line — corrections cascade automatically to adjacent reports to maintain sequential ticket number continuity.

Click **Download Invoice** to regenerate and save the PDF for any past report.

---

### Example: Adding a New User (Admin Only)

1. Log in as an `admin` or `default_admin` user
2. Navigate to **Settings → Sign Up** (`/signup`)
3. Enter a username, password, and role (`standard` or `admin`)
4. The new user can log in immediately

---

## Configuration

### `config.json`

Located at `src/lottery_app/config.json`, this file stores all runtime settings. It is managed entirely through the application UI — you should not need to edit it manually.

| Key | Type | Default | Description |
|---|---|---|---|
| `ticket_order` | string | `"ascending"` | Direction tickets are counted: `"ascending"` (0 → max) or `"descending"` (max → 0) |
| `should_poll` | string | `"false"` | Enable barcode polling from the `/receive` endpoint: `"true"` or `"false"` |
| `invoice_output_path` | string | `~/Downloads` | Absolute path to the folder where PDF invoices are saved |
| `timezone` | string | `"America/New_York"` | IANA timezone name used for report timestamps |
| `business_name` | string | `""` | Your store name (printed on invoices) |
| `business_address` | string | `""` | Your store address (validated by regex) |
| `business_phone` | string | `""` | Your store phone number (10–15 digits) |
| `business_email` | string | `""` | Invoice recipient email address |

To update settings, go to **Settings** (`/settings`) or **Business Profile** (`/business_profile`) in the UI.

---

### Environment Variables

All secrets and environment-specific values live in `src/.env`. See [Step 6 of the Installation Guide](#step-6--create-the-env-file) for the full list.

| Variable | Required | Description |
|---|---|---|
| `FERNET_KEY` | **Yes** | 44-character Base64 key for database encryption |
| `FLASK_SECRET_KEY` | **Yes** | Secret key for signing Flask sessions and CSRF tokens |
| `FLASK_DEBUG` | No | Set to `1` for debug mode (never in production) |
| `SCANNER_API_KEY` | No | If set, `/receive` requires this value in the `X-Scanner-Key` header |
| `GMAIL_SENDER` | No | Gmail address used to send invoice emails |
| `GMAIL_APP_PASSWORD` | No | Gmail App Password (not your account password) |

---

### Modifying the Timezone

1. Go to **Settings** in the UI
2. Enter a valid [IANA timezone name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (e.g., `America/Chicago`, `Europe/London`)
3. Click **Save** — all subsequent report timestamps will display in the new timezone

If an invalid timezone is entered, the system silently falls back to `America/New_York`.

---

## Database

### Engine

**SQLite 3** — a single-file, serverless relational database. The database file is located at:

```
src/lottery_app/instance_folder/Lottery_Management_Database.db
```

> The plaintext `.db` file only exists **while the application is running**. On shutdown it is encrypted to `Lottery_Management_Database.db.enc` and the plaintext file is deleted. On the next startup the `.enc` file is decrypted back to `.db`. This means the database is never readable on disk between sessions.

---

### Schema Overview

| Table | Purpose |
|---|---|
| **Users** | Application user accounts with hashed passwords and roles (`standard`, `admin`, `default_admin`) |
| **Books** | All lottery ticket books (active, inactive, or sold); stores game number, ticket price, and book size |
| **ActivatedBooks** | Books currently in use for scanning; tracks the current open ticket number per book |
| **SalesLog** | One row per active book per report period; stores opening and closing ticket numbers and derived quantity sold |
| **TicketTimeLine** | Every individual scan event with timestamps; the immutable audit log |
| **SaleReport** | Daily financial summary: instant and online tickets sold and cashed, cash on hand, total due |
| **TicketNameLookup** | Lookup table mapping game numbers to ticket names (populated from the game lookup table on startup) |

#### Key Relationships

```
Users           (no FK relations — standalone auth table)

Books ────────────────────────────────> TicketNameLookup (via GameNumber)
  │
  └──> ActivatedBooks ──> SalesLog ──> SaleReport
                     │
                     └──> TicketTimeLine
```

#### Computed Values

- **`SalesLog.Ticket_Sold_Quantity`** = `ABS(current_TicketNum - prev_TicketNum)`
- **`SaleReport.TotalDue`** = `(InstantTicketSold + OnlineTicketSold) − (InstantTicketCashed + OnlineTicketCashed)`

#### Database Trigger

```sql
-- Prevents the default_admin account from being deleted at the SQL level
CREATE TRIGGER prevent_delete_default_user ...
```

---

### Database Initialisation

The schema is applied automatically on first run via `setup_database.initialize_database()`. You do not need to run any migration scripts manually.

---

## Testing

### Running the Test Suite

```bash
# Activate the virtual environment first, then:

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test category
pytest tests/routes/
pytest tests/security/
pytest tests/database/

# Run a single test file
pytest tests/routes/test_scanner_route.py

# Run a single test by name
pytest -k "test_receive_barcode_polling_enabled"

# Stop after first failure
pytest -x
```

### Test Configuration (`pytest.ini`)

```ini
[pytest]
minversion = 7.0
addopts = -v --tb=short -s
testpaths = tests
pythonpath = src
```

The `pythonpath = src` entry ensures `lottery_app` is importable without requiring the package to be installed in the test environment.

### Test Structure

| Directory | What It Tests |
|---|---|
| `tests/database/` | Database query functions, update operations, schema initialisation, user model CRUD |
| `tests/routes/` | Every Flask route: correct responses, redirect behaviour, form handling, login enforcement |
| `tests/security/` | Authentication enforcement, role-based authorisation, SQL injection resistance, XSS input validation, privilege escalation |
| `tests/utils/` | Config loading and updating, Fernet encryption/decryption, invoice generation, ticket insertion logic |
| `tests/` (root) | Barcode parsing (`ScannedCodeManagement`), game number lookup table, version checking |

### Shared Fixtures (`tests/conftest.py`)

| Fixture | Scope | Description |
|---|---|---|
| `app` | function | Flask test app backed by a temporary in-memory SQLite database |
| `client` | function | Flask test client |
| `auth` | function | `AuthActions` helper — provides `.login()` and `.logout()` convenience methods |
| `db_path` | function | Path to the temporary test database file |
| `db_cursor` | function | SQLite cursor connected to an initialised test database |
| `update_env` | function | Factory fixture — sets up a fake `config.json` and mocks for testing `update_*` functions |
| `captured_templates` | function | Records every rendered template and its context during a test |

### Tools Used

| Tool | Purpose |
|---|---|
| **pytest** | Test discovery, execution, and reporting |
| **pytest-mock / unittest.mock** | Patching external dependencies (database, email, file I/O) |
| **monkeypatch** | In-test overrides for environment variables and module attributes |
| **Flask test client** | Simulates HTTP requests without running a real server |
| **in-memory SQLite** | Isolated database per test — no state leaks between tests |

---

## Deployment

### Local / Development

Follow the [Installation Guide](#installation-guide) and run:

```bash
python src/lottery_app/app.py
```

The app opens automatically at `http://127.0.0.1:7777`.

---

### Production with Gunicorn

Gunicorn is included in `requirements.txt` for production deployments.

```bash
# From the project root, with the virtual environment active:
gunicorn \
  --workers 1 \
  --bind 0.0.0.0:7777 \
  --timeout 120 \
  "lottery_app:create_app()"
```

> **Important:** Use `--workers 1`. The application relies on an in-process `queue.Queue` (`BARCODE_QUEUE`) for the barcode scanner pipeline. Multiple worker processes do not share memory, so a multi-worker setup would cause barcode scans from the `/receive` endpoint to be lost.

---

### Standalone Executable (PyInstaller)

The repository includes a PyInstaller spec file for building a self-contained desktop executable that requires no Python installation on the target machine.

```bash
# Build the executable
pyinstaller lottery_app.spec

# The output is placed in dist/lottery_app/
# On macOS/Linux:
./dist/lottery_app/lottery_app

# On Windows:
dist\lottery_app\lottery_app.exe
```

Place your `.env` file in the **same directory as the executable** before running.

---

### Reverse Proxy with Nginx (Recommended for LAN Deployment)

If the application is accessed by multiple computers on the same network, place Nginx in front of Gunicorn:

```nginx
server {
    listen 80;
    server_name lottery.local;

    location / {
        proxy_pass         http://127.0.0.1:7777;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

### Production Considerations

| Concern | Recommendation |
|---|---|
| **FLASK_DEBUG** | Must be `0` in production — debug mode exposes a REPL to the network |
| **FLASK_SECRET_KEY** | Use a cryptographically random value: `python -c "import secrets; print(secrets.token_hex(64))"` |
| **FERNET_KEY** | Back up this key securely — losing it means losing access to the encrypted database |
| **SCANNER_API_KEY** | Set this if the `/receive` endpoint is reachable from the network to prevent barcode injection |
| **HTTPS** | Always deploy behind HTTPS in production; use Let's Encrypt / Certbot with Nginx |
| **Single Worker** | Keep `--workers 1` with Gunicorn (see above) |
| **Database Backups** | Regularly back up the `.db.enc` file **and** your `FERNET_KEY` together |
| **Firewall** | Restrict port 7777 to localhost; expose only the Nginx port (80/443) publicly |

---

## Future Improvements

- **Multi-store support** — partition data by store location to support franchise-level reporting
- **Role granularity** — add a `manager` role between `standard` and `admin` for report-editing without user management
- **WebSocket-based scanning** — replace the polling loop with a persistent WebSocket connection to reduce latency and server load
- **REST API** — expose a versioned JSON API so third-party point-of-sale systems can push scan data programmatically
- **PostgreSQL / MySQL support** — abstract the database layer behind an ORM (e.g., SQLAlchemy) to support larger deployments that outgrow SQLite
- **Automated database backups** — scheduled Fernet-encrypted backups to a configurable remote location (S3, SFTP)
- **Two-factor authentication** — TOTP-based 2FA for admin accounts
- **Audit log UI** — expose the `TicketTimeLine` table as a searchable, filterable audit screen
- **Mobile-responsive UI** — optimise the scanning screen for tablet and phone browsers to reduce hardware requirements
- **Dark mode** — configurable colour theme stored per user
- **Report export to CSV / Excel** — complement the existing PDF export with spreadsheet-friendly formats for bookkeeping software
- **Password strength enforcement** — server-side minimum length and complexity rules on `/signup` and `/change_password`
- **Containerisation** — Docker image and `docker-compose.yml` for one-command deployment
