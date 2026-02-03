@echo off
echo ============================================
echo   Deploying to Vercel
echo ============================================
echo.

cd frontend

echo Step 1: Building the application...
call npm run build
if errorlevel 1 (
    echo Build failed! Please fix errors and try again.
    pause
    exit /b 1
)

echo.
echo Step 2: Deploying to Vercel...
echo.
echo IMPORTANT: When prompted:
echo - For "Set up and deploy": Press Y
echo - For "Which scope": Select your account
echo - For "Link to existing project": Press N (first time) or Y (updating)
echo - For "Project name": Press Enter or type a name
echo - For "Directory": Press Enter (should be frontend)
echo.

npx vercel --prod

echo.
echo ============================================
echo   Deployment Complete!
echo ============================================
echo.
echo Don't forget to:
echo 1. Deploy your backend to Railway/Render
echo 2. Update REACT_APP_API_URL in Vercel dashboard
echo 3. Update FRONTEND_ORIGIN in backend environment
echo.
echo See VERCEL_DEPLOYMENT.md for detailed instructions
echo.
pause
