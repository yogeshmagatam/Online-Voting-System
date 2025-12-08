@echo off
REM Script to set up Gmail OTP environment variables for the Election System
REM Run this script in PowerShell as Administrator or from Command Prompt

echo ============================================================
echo Election System - Gmail OTP Configuration Setup
echo ============================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: This script should be run as Administrator for permanent system-wide changes.
    echo Continuing with temporary environment variables (session only)...
    echo.
)

echo Enter your Gmail configuration:
echo.

set /p MAIL_USERNAME="Gmail Address (example@gmail.com): "
set /p MAIL_PASSWORD="App Password (16-character from Google Account): "

echo.
echo Configuring environment variables...

REM Set environment variables
setx MAIL_SERVER "smtp.gmail.com"
setx MAIL_PORT "587"
setx MAIL_USERNAME "%MAIL_USERNAME%"
setx MAIL_PASSWORD "%MAIL_PASSWORD%"
setx MAIL_DEFAULT_SENDER "%MAIL_USERNAME%"

echo.
echo ============================================================
echo Configuration Complete!
echo ============================================================
echo.
echo Environment variables have been set:
echo   MAIL_SERVER: smtp.gmail.com
echo   MAIL_PORT: 587
echo   MAIL_USERNAME: %MAIL_USERNAME%
echo   MAIL_DEFAULT_SENDER: %MAIL_USERNAME%
echo.
echo NOTE: Please restart your terminal/IDE for changes to take effect.
echo.
echo To verify the configuration, run the Flask application and attempt to login.
echo The OTP email should be sent to %MAIL_USERNAME%
echo.
pause
