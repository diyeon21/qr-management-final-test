# QR Code-Enabled Equipment Repair and Maintenance Management System

Full-stack laboratory equipment and maintenance tracking portal built with Python (Flask) and MySQL. Supports role-based access for Administrator, Custodian, Technician, and Faculty, QR code scanning, repair requests workflow, activity logging, and reporting.

## Features

- Role-based access control (Admin, Custodian, Technician, Faculty)
- QR code generation and mobile camera scanning
- Maintenance ticketing from submission to verification and resolution
- Technician assignment, repair tracking, and duration logs
- Logbook and summary reports with CSV export
- Health check monitoring endpoint (`/health`)

## Requirements

- Python 3.10+
- MySQL Community Server or MariaDB (e.g. XAMPP)

## Local Setup

1. Configure environment:
   Copy `.env.example` to `.env` and verify database settings.

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize database and default accounts:
   ```bash
   python init_db.py --seed
   ```

4. Start the server:
   ```bash
   start.bat
   ```
   Or:
   ```bash
   python wsgi.py
   ```
   Open `http://localhost:5000` in your browser.

## Cloud Deployment (Render + TiDB Cloud)

1. Database: Create a free Serverless cluster on TiDB Cloud (or any MySQL host).
2. Web Service: Connect repository on Render using Python runtime.
   - Build Command: `pip install -r requirements.txt gunicorn`
   - Start Command: `python init_db.py --seed && gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2`
3. Environment variables:
   - `MYSQL_HOST`: Database host
   - `MYSQL_PORT`: `4000` (for TiDB) or `3306`
   - `MYSQL_USER`: Database username
   - `MYSQL_PASSWORD`: Database password
   - `MYSQL_DB`: Database name
   - `MYSQL_SSL_DISABLED`: `0` (for cloud SSL)
   - `BEHIND_PROXY`: `1`
   - `PUBLIC_BASE_URL`: Public HTTPS URL of the deployed application

## Default Accounts

| Role | Email | Password |
|---|---|---|
| Administrator | admin@school.edu | admin123 |
| Custodian | custodian@school.edu | custodian123 |
| Technician | technician@school.edu | technician123 |
| Faculty | faculty@school.edu | faculty123 |

## Health Check

`GET /health` returns JSON status:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "version": "1.0.0"
}
```
