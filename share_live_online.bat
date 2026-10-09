@echo off
title Share System Online - Instant Live Link
echo ===================================================
echo   Sharing QR Maintenance System Live Over The Internet
echo ===================================================
echo.
echo Make sure your server is running (start.bat or start_production.bat).
echo Generating your public HTTPS link...
echo.
echo NOTE: Keep this window OPEN while someone is viewing the system.
echo Press CTRL+C to stop sharing.
echo ===================================================
echo.
ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:5000 nokey@localhost.run
pause
