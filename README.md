# QR Code-Enabled Equipment Repair and Maintenance Management System

A web-based maintenance management portal built with **Python Flask** and **MySQL**. It enables end-to-end tracking of school/facility equipment lifecycle, QR code scanning, maintenance request submissions, technician assignment, repair logs, and reporting.

---

## Features

- **Role-Based Access Control (RBAC):** Distinct dashboards and permissions for **Admin**, **Custodian**, **Technician**, and **Faculty**.
- **QR Code Dispatch & Scanning:** Each piece of equipment has a unique QR code for quick scanning and instant maintenance reporting.
- **Request Lifecycle Management:** Submit maintenance tickets with photos, set priority/urgency, assign technicians, track repair progress, and log resolutions.
- **Maintenance Logbook:** Detailed audit trail of all repairs, cost tracking, and equipment histories.
- **Analytics & Export:** Visual summaries, status breakdowns, and report exports.
- **Auto-Bootstrapping Database:** Automatically creates tables and schema relationships on first startup.

---

## Technology Stack

- **Backend:** Python (Flask 3.x), MySQL Connector
- **Database:** MySQL (via XAMPP or standalone MySQL Server)
- **Frontend:** Jinja2 templates, CSS3, JavaScript
- **Security:** Bcrypt password hashing, CSRF protection, session management

---

## Getting Started

### 1. Prerequisites
- **Python 3.10+**: [python.org](https://www.python.org/)
- **XAMPP** (or standalone MySQL Server): [apachefriends.org](https://www.apachefriends.org/)

### 2. Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/diyeon21/qr-management-system-final.git
   cd qr-management-system-final
   ```

2. **Create and activate a virtual environment (optional but recommended):**
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

### 3. Database Configuration

1. Start **Apache** and **MySQL** in your XAMPP Control Panel.
2. The application defaults to standard XAMPP settings:
   - **Host:** `127.0.0.1`
   - **Port:** `3306`
   - **User:** `root`
   - **Password:** *(empty)*
   - **Database:** `qr_maintenance_db` (created automatically on startup)

> If you need custom credentials, configure them in `config.py` or set environment variables (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`).

### 4. Seed Default Accounts (Fresh Install)

To create the initial default user accounts with fresh, empty data:

```bash
python seed_mysql.py
```

### 5. Run the Application

Start the Flask server:

```bash
python app.py
```
*(On Windows, you can also double-click `start.bat`)*

Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## Default Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@school.edu` | `admin123` |
| **Custodian** | `custodian@school.edu` | `custodian123` |
| **Technician** | `technician@school.edu` | `technician123` |
| **Faculty** | `faculty@school.edu` | `faculty123` |

*(Be sure to change passwords in a production environment).*

---

## Project Structure

```text
├── app.py                  # Main Flask application entry point
├── config.py               # Application and database configuration
├── requirements.txt        # Python package dependencies
├── start.bat               # Windows quick-launch script
├── seed_mysql.py           # Seeds default role accounts for a clean system
├── models/
│   ├── db.py               # MySQL connection pool and auto table creation
│   └── security.py         # CSRF and password hashing utilities
├── routes/                 # Flask route blueprints (auth, requests, equipment, etc.)
├── static/                 # Static assets (CSS, JS, images, logos)
├── templates/              # Jinja2 HTML templates & dashboards
├── tests/                  # Unit and integration test suite
└── uploads/                # Directory for uploaded equipment report images
```
