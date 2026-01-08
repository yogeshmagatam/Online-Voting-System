@echo off
REM Start MongoDB Server
echo ===============================================
echo   Starting MongoDB Server
echo ===============================================
echo.

REM Create data directory if it doesn't exist
if not exist "C:\data\db" (
    echo Creating MongoDB data directory...
    mkdir C:\data\db
)

REM Start MongoDB
echo Starting MongoDB on localhost:27017...
echo.
mongod --dbpath C:\data\db

pause
