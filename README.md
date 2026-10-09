# QR Code-Enabled Equipment Repair and Maintenance Management System

A web-based maintenance management portal built with **Python Flask** and **MySQL**. It enables end-to-end tracking of school/facility equipment lifecycle, QR code scanning, maintenance request submissions, technician assignment, repair logs, and reporting.

---

## Features

- **Role-Based Access Control (RBAC):** Distinct dashboards and permissions for **Admin**, **Custodian**, **Technician**, and **Faculty**.
- **QR Code Dispatch & Scanning:** Each piece of equipment has a unique QR code for quick scanning and instant maintenance reporting.
- **Request Lifecycle Management:** Submit maintenance tickets with photos, set priority/urgency, assign technicians, track repair progress, and log resolutions.
- **Maintenance Logbook:** Detailed audit trail of all repairs, cost tracking, and equipment histories.
- **Analytics & Export:** Visual summaries, status breakdowns, and report exports.
- **Auto-Bootstrapping Database:** Automatically creates tables and seeds default baseline accounts on first startup.

---

## Technology Stack

- **Backend:** Python (Flask 3.x), MySQL Connector, Gunicorn / Waitress WSGI
- **Database:** MySQL 8.0+ / MariaDB
- **Frontend:** Jinja2 templates, CSS3, JavaScript
- **Security:** Bcrypt password hashing, CSRF protection, secure sessions

---

## Quick Start (Local Development)

### 1. Prerequisites
- **Python 3.10+**: [python.org](https://www.python.org/)
- **XAMPP** (or MySQL Server): [apachefriends.org](https://www.apachefriends.org/)

### 2. Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/diyeon21/qr-management-system-final.git
   cd qr-management-system-final
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start MySQL in XAMPP** (Default port `3306`, user `root`, no password).

5. **Run the development server:**
   ```bash
   python app.py
   ```
   *(Or double-click `start.bat` on Windows)*

Open your browser at **`http://127.0.0.1:5000`**.

---

## Production Deployment

### Option A: Cloud Platforms (Render / Railway / Heroku)

This repository is pre-configured with a [`Procfile`](file:///c:/xampp/htdocs/Capstone%20Project/Capstone%20Project/Procfile) and [`wsgi.py`](file:///c:/xampp/htdocs/Capstone%20Project/Capstone%20Project/wsgi.py) for automatic detection.

1. Connect your GitHub repository to **Render** or **Railway**.
2. Add a **MySQL database** service on the platform.
3. Configure Environment Variables in the platform's settings dashboard:
   - `SECRET_KEY`: Generate a long random secret key.
   - `DATABASE_URL` or `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`.
   - `FLASK_DEBUG`: Set to `0`.
   - `PUBLIC_BASE_URL`: Your production app domain (e.g. `https://your-domain.onrender.com`).
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn wsgi:app --workers 3 --timeout 120`

---

### Option B: Docker & Docker Compose (1-Command Deploy)

Run the full stack (Flask app + MySQL 8.0 database) with one command:

```bash
docker compose up -d --build
```

The application will start on port `5000` with automated database healthchecks and persistent storage.

---

### Option C: Windows Server (Waitress Production WSGI)

For Windows hosting without development server warnings:

1. Copy `.env.example` to `.env` and set production credentials:
   ```powershell
   copy .env.example .env
   ```
2. Double-click **`start_production.bat`** or run:
   ```powershell
   python -m waitress --listen=0.0.0.0:5000 wsgi:app
   ```

---

## Environment Variables Reference

See [`.env.example`](file:///c:/xampp/htdocs/Capstone%20Project/Capstone%20Project/.env.example) for the full list:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Session encryption secret key | *Development default* |
| `FLASK_DEBUG` | `1` for debug mode, `0` for production | `0` |
| `PORT` | Port for the HTTP server | `5000` |
| `MYSQL_HOST` | MySQL database host | `127.0.0.1` |
| `MYSQL_PORT` | MySQL database port | `3306` |
| `MYSQL_USER` | MySQL database username | `root` |
| `MYSQL_PASSWORD` | MySQL database password | *(empty)* |
| `MYSQL_DB` | Database schema name | `qr_maintenance_db` |
| `DATABASE_URL` | Complete MySQL connection URI (overrides individual vars) | *None* |
| `PUBLIC_BASE_URL` | Base URL embedded in generated QR codes | *None* |

---

## Default Login Credentials

Upon first startup, the database automatically initializes with these baseline accounts:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@school.edu` | `admin123` |
| **Custodian** | `custodian@school.edu` | `custodian123` |
| **Technician** | `technician@school.edu` | `technician123` |
| **Faculty** | `faculty@school.edu` | `faculty123` |

> **Security Note:** Change default passwords immediately after deploying to a public environment.

---

## Project Structure

```text
├── app.py                  # Main Flask application
├── wsgi.py                 # Production WSGI entry point
├── config.py               # Dynamic environment and DB config
├── requirements.txt        # Production dependencies (gunicorn, waitress, etc.)
├── Procfile                # Cloud PaaS deployment file (Render, Railway)
├── Dockerfile              # Docker container configuration
├── docker-compose.yml      # Multi-container orchestration (App + MySQL)
├── .dockerignore           # Excludes local environments from Docker build
├── .env.example            # Environment variables template
├── start.bat               # Windows local development script
├── start_production.bat    # Windows Waitress production script
├── seed_mysql.py           # Manual baseline accounts seeder
├── models/                 # Database connection pool and schema
├── routes/                 # Blueprint controllers
├── static/                 # CSS, JS, branding assets
├── templates/              # Jinja2 dashboard templates
└── uploads/                # User uploaded equipment ticket photos
```
