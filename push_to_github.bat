@echo off
title Push to GitHub - qr-maintenance-system
echo =====================================================================
echo  Pushing code to https://github.com/diyeon21/qr-maintenance-system
echo =====================================================================
echo.
git push -u origin main
echo.
if errorlevel 1 (
    echo [NOTE] If this failed, make sure you created the empty repository at:
    echo        https://github.com/new (Repository name: qr-maintenance-system)
) else (
    echo [SUCCESS] Code pushed to GitHub successfully!
)
echo.
pause
