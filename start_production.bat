@echo off
title QR Maintenance Management System - Production Server (Waitress WSGI)
echo =====================================================================
echo  QR Maintenance Management System - Production Mode
echo =====================================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    echo [*] Activating Python virtual environment (.venv)...
    call .venv\Scripts\activate.bat
)

echo [*] Checking database connectivity and schema...
python init_db.py
if errorlevel 1 (
    echo.
    echo [ERROR] Database connection failed!
    echo Please make sure MySQL / MariaDB (e.g., in XAMPP) is started.
    echo Check your .env configuration file.
    pause
    exit /b 1
)

echo.
echo [*] Launching production WSGI server (Waitress)...
echo [*] Server will be accessible on your network.
echo [*] Press CTRL+C to stop the server at any time.
echo.
python wsgi.py
pause
