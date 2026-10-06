@echo off
title TOC Ambiguity Checker
color 0A

echo =======================================================
echo        TOC AMBIGUITY CHECKER - INITIALIZATION
echo =======================================================
echo.
echo Verifying Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo Starting Web Server Dashboard...
echo.
python web_server.py

echo.
echo Application closed.
pause
