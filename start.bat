@echo off
title CASHLY - Personal Finance Manager
echo ===================================================
echo             Starting CASHLY (Fast Boot)
echo ===================================================
echo.
echo [1/2] Launching your web browser...
start http://127.0.0.1:5000/

echo.
echo [2/2] Booting Flask server...
python app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Flask server terminated unexpectedly.
    pause
)
