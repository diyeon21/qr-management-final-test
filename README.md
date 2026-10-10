# QR Code-Enabled Equipment Repair & Maintenance Management System

A production-ready full-stack web application built with **Python (Flask)** and **MySQL / MariaDB**. The system provides end-to-end laboratory and facility management, QR code equipment scanning, repair ticketing workflows, technician activity tracking, logbook generation, and administrative reports.

---

## 🌟 Key Features

- **Role-Based Access Control (RBAC):** Distinct dashboards and access levels for **Admin**, **Custodian**, **Technician**, and **Faculty**.
- **QR Code Asset Tracking:** Instant camera/scanner lookup of equipment details, health status, and historical maintenance logs.
- **Maintenance Lifecycle:** Ticketing pipeline from submission, assignment, repair in-progress, completed verification, to resolution.
- **Reporting & Auditing:** Executive KPIs, technician workload dossiers, CSV data exports, and audit logging.
- **Production & Deployment Ready:**
  - Multi-threaded WSGI production server support (**Waitress** for Windows, **Gunicorn** for Linux/Cloud).
  - Containerized deployment with **Docker** and **Docker Compose**.
  - Built-in `/health` monitoring endpoint for orchestrators and load balancers.
  - Security hardening (CSRF protection, secure session cookies, `ProxyFix` reverse proxy support, and nosniff/XSS/SAMEORIGIN headers).
  - Zero-effort automated database schema bootstrapping and indexing.

---

## 📋 System Prerequisites

1. **Python 3.10+** (Tested with Python 3.11, 3.12, and 3.14)
2. **MySQL Community Server** or **MariaDB** (Included in XAMPP or standalone)
3. *(Optional)* **Docker & Docker Compose** for containerized setup

---

## 🚀 Quick Start (Development)

### 1. Clone & Navigate to Project
```powershell
cd "c:\xampp\htdocs\Capstone Project\Capstone Project"
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Ensure your MySQL database connection parameters in `.env` match your local database (e.g. `127.0.0.1:3306`, user `root`, empty password if using default XAMPP).

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database & Seed Users
```powershell
python init_db.py --seed
```
*(Or double-click `seed_db.bat` on Windows)*

### 5. Launch Development Server
```powershell
python app.py
```
*(Or double-click `start.bat`)*

Access the portal in your browser: **[http://localhost:5000](http://localhost:5000)**

---

## 🛡️ Production Deployment Options

### Option A: Windows Production Server (Waitress WSGI)

For production deployment on Windows Server or on-premise XAMPP workstations:

1. Ensure MySQL is running (e.g., via XAMPP Control Panel or Windows Service).
2. Configure `.env` with:
   ```ini
   FLASK_ENV=production
   FLASK_DEBUG=0
   SECRET_KEY=generate_a_strong_random_secret_here
   PUBLIC_BASE_URL=http://your-server-ip:5000
   ```
3. Run the production launcher:
   ```cmd
   start_production.bat
   ```
   *(Or run `start_production.ps1` via PowerShell)*

This starts a multi-threaded **Waitress WSGI** server designed for production stability.

---

### Option B: Docker & Docker Compose (Recommended for Cloud/Containers)

Deploy the entire stack (Flask app + MySQL 8.0 + persistent volumes) with a single command:

```bash
docker compose up -d --build
```

- Web Portal: **http://localhost:5000**
- Health check: **http://localhost:5000/health**
- Data persistence: MySQL data and uploaded attachments are persisted in Docker volumes (`mysql_data` and `app_uploads`).

To seed the initial user accounts inside the container:
```bash
docker compose exec web python init_db.py --seed
```

To stop the containers:
```bash
docker compose down
```

---

### Option C: Linux / Cloud / VPS (Gunicorn + Nginx)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Initialize database:**
   ```bash
   python init_db.py --seed
   ```
3. **Configure Systemd service (`/etc/systemd/system/qr_maintenance.service`):**
   ```ini
   [Unit]
   Description=QR Maintenance Management Portal
   After=network.target mysql.service

   [Service]
   User=www-data
   WorkingDirectory=/var/www/qr_maintenance
   Environment="PATH=/var/www/qr_maintenance/.venv/bin"
   ExecStart=/var/www/qr_maintenance/.venv/bin/gunicorn wsgi:application --bind 127.0.0.1:5000 --workers 4 --threads 2

   [Install]
   WantedBy=multi-user.target
   ```
4. **Nginx Reverse Proxy:**
   Copy `nginx/qr_maintenance.conf` to `/etc/nginx/sites-available/qr_maintenance`, update your domain name and paths, then reload Nginx:
   ```bash
   sudo systemctl reload nginx
   ```

---

### Option D: Platform-as-a-Service (Render, Railway, Heroku)

The repository includes a ready-to-use `Procfile`:
```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120
release: python init_db.py --seed
```
Attach a managed MySQL database plugin and set the matching `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, and `SECRET_KEY` in the service environment settings.

---

## 🔑 Default Accounts

Default accounts seeded by `init_db.py --seed`:

| Role | Email | Password | Primary Permissions |
|------|-------|----------|---------------------|
| **Administrator** | `admin@school.edu` | `admin123` | Full system control, reports, user management, audit logs |
| **Custodian** | `custodian@school.edu` | `custodian123` | Equipment inventory, QR code generation, room assignments |
| **Technician** | `technician@school.edu` | `technician123` | Repair tickets, diagnostic notes, repair duration logging |
| **Faculty** | `faculty@school.edu` | `faculty123` | Issue reporting, QR scan view, my requests tracking |

> **Security Note:** In production environments, change all default passwords immediately after initial login.

---

## ⚙️ Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Application mode (`production` or `development`) |
| `FLASK_DEBUG` | `0` | Debugger toggle (`0` = disabled, `1` = enabled) |
| `SECRET_KEY` | *(built-in fallback)* | Secret key for signed session cookies and CSRF tokens |
| `MYSQL_HOST` | `127.0.0.1` | MySQL server hostname or IP address |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_USER` | `root` | Database user |
| `MYSQL_PASSWORD` | *(empty)* | Database password |
| `MYSQL_DB` | `qr_maintenance_db` | Name of database |
| `MYSQL_POOL_SIZE` | `10` | Database connection pool size (1–32) |
| `HOST` | `0.0.0.0` | IP interface to bind server to |
| `PORT` | `5000` | HTTP port to listen on |
| `PUBLIC_BASE_URL` | `http://localhost:5000` | Public URL encoded in generated QR codes |
| `BEHIND_PROXY` | `0` | Enable when behind Nginx, Apache, or Cloudflare for ProxyFix |
| `PROXY_FIX_NUM_PROXIES` | `1` | Number of reverse proxy hops |
| `SESSION_COOKIE_SECURE` | `0` | Set to `1` when HTTPS/SSL is active |
| `MAX_CONTENT_LENGTH` | `8388608` | Maximum file upload size in bytes (8 MB) |

---

## 🩺 Health Check & Monitoring

Send an HTTP GET request to `/health`:

```bash
curl http://localhost:5000/health
```

**Healthy Response (`200 OK`):**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "version": "1.0.0"
}
```

If the database becomes unreachable, `/health` returns `503 Service Unavailable` with error details, alerting monitoring agents or automated container restarts.

---

## 🧪 Running Automated Tests

Run the full test suite using `pytest`:

```powershell
python -m pytest -v
```
*(Or double-click `run_tests.bat` on Windows)*

---

## 📦 Project Structure

```text
Capstone Project/
├── app.py                     # Flask application factory, error handlers, & routes
├── config.py                  # Production configuration loader & environment parsing
├── wsgi.py                    # WSGI entrypoint for Waitress / Gunicorn
├── init_db.py                 # CLI database schema bootstrap & seeding utility
├── seed_mysql.py              # Default user credentials & initial data seeder
├── requirements.txt           # Python application dependencies
├── Dockerfile                 # Container image specification
├── docker-compose.yml         # Multi-container orchestration (App + MySQL)
├── .env.example               # Template environment configuration
├── .gitignore                 # Version control exclusions
├── Procfile                   # Cloud PaaS execution rules
├── start.bat                  # Development server launcher
├── start_production.bat       # Windows production server launcher (Waitress)
├── start_production.ps1       # PowerShell production launcher
├── run_tests.bat              # Test suite runner
├── seed_db.bat                # Database seeder launcher
├── models/                    # Database models, connection pool, security helpers
├── routes/                    # Blueprint routes (auth, equipment, requests, reports, etc.)
├── static/                    # CSS stylesheets, JavaScript files, images
├── templates/                 # Jinja2 HTML templates
├── tests/                     # Automated unit and integration test suite
├── uploads/                   # Uploaded equipment photos and documentation
├── nginx/                     # Nginx reverse proxy configuration template
└── apache/                    # Apache / XAMPP VirtualHost proxy configuration
```
