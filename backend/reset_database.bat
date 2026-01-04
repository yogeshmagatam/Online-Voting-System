@echo off
echo ========================================
echo Resetting Election Database
echo ========================================
echo.

echo Stopping any running processes...
timeout /t 2 /nobreak >nul

echo Deleting old database...
if exist election.db (
    del /f election.db
    echo Database deleted successfully!
) else (
    echo No database file found (already clean).
)

echo.
echo ========================================
echo Database Reset Complete!
echo ========================================
echo.
echo The database has been deleted.
echo.
echo NEXT STEPS:
echo 1. Start the backend: python app.py
echo 2. Login with:
echo    Username: admin
echo    Password: admin@123456
echo.
echo The database will be recreated automatically on startup.
echo ========================================
pause
