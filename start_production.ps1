# PowerShell Production Server Runner for QR Maintenance System
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " QR Maintenance Management System - Production Mode (Waitress WSGI)" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[*] Activating virtual environment (.venv)..." -ForegroundColor Yellow
    . .venv\Scripts\Activate.ps1
}

Write-Host "[*] Checking database connectivity and schema..." -ForegroundColor Yellow
python init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Could not connect to MySQL database." -ForegroundColor Red
    Write-Host "Please verify that MySQL (e.g. XAMPP) is running and your .env configuration is correct." -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "[*] Launching Waitress production server..." -ForegroundColor Green
Write-Host "[*] Press CTRL+C to stop the server at any time." -ForegroundColor Gray
Write-Host ""
python wsgi.py
