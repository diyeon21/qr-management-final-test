@echo off
title Run Test Suite - QR Maintenance Management System
echo =====================================================================
echo  Running Pytest Test Suite
echo =====================================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -m pytest -v
echo.
pause
