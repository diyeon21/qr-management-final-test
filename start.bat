@echo off
title QR Maintenance Management System - Development Server
echo =====================================================================
echo  QR Maintenance Management System - Development Mode
echo =====================================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    echo [*] Activating Python virtual environment (.venv)...
    call .venv\Scripts\activate.bat
)

echo [*] Starting Flask development server...
echo [*] Press CTRL+C to stop the server at any time.
echo.
python app.py
pause
