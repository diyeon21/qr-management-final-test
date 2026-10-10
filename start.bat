@echo off
title QR Maintenance Management System
echo =====================================================================
echo  QR Maintenance Management System
echo =====================================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Starting server...
python wsgi.py
pause
