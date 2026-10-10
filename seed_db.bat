@echo off
title Initialize and Seed QR Maintenance Database
echo =====================================================================
echo  Database Setup and Seeding Utility
echo =====================================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python init_db.py --seed
echo.
pause
