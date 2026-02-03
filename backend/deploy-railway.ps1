# Railway Backend Deployment Script for Windows PowerShell
# Automates the entire Railway deployment process

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     RAILWAY BACKEND DEPLOYMENT - WINDOWS SETUP               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Function to generate secure random string
function Generate-SecureKey {
    $random = New-Object System.Random
    $chars = [char[]]"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%"
    $key = ""
    for ($i = 0; $i -lt 32; $i++) {
        $key += $chars[$random.Next($chars.Count)]
    }
    return $key
}

# Step 1: Check and install Railway CLI
Write-Host "📦 STEP 1: Installing Railway CLI" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Railway CLI globally..." -ForegroundColor Cyan
    npm install -g @railway/cli
    Write-Host "✅ Railway CLI installed" -ForegroundColor Green
} else {
    Write-Host "✅ Railway CLI already installed" -ForegroundColor Green
}
Write-Host ""

# Step 2: Login to Railway
Write-Host "🔐 STEP 2: Login to Railway" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "Opening Railway login in browser..." -ForegroundColor Cyan
Write-Host ""

npx railway login

Write-Host ""
Write-Host "✅ Logged in successfully!" -ForegroundColor Green
Write-Host ""

# Step 3: Initialize Railway Project
Write-Host "📁 STEP 3: Initialize Railway Project" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

cd backend
npx railway init --name "election-fraud-detection"

Write-Host ""
Write-Host "✅ Project initialized!" -ForegroundColor Green
Write-Host ""

# Step 4: Deploy Backend
Write-Host "🚀 STEP 4: Deploy Backend Service" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "Uploading code to Railway..." -ForegroundColor Cyan

npx railway up

Write-Host ""
Write-Host "✅ Backend deployed!" -ForegroundColor Green
Write-Host ""

# Step 5: Generate Secure Keys
Write-Host "🔑 STEP 5: Generating Secure Keys" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$SECRET_KEY = Generate-SecureKey
$JWT_SECRET_KEY = Generate-SecureKey

Write-Host "Generated Keys:" -ForegroundColor Cyan
Write-Host "SECRET_KEY=$SECRET_KEY" -ForegroundColor Green
Write-Host "JWT_SECRET_KEY=$JWT_SECRET_KEY" -ForegroundColor Green
Write-Host ""

# Step 6: Configure Environment Variables
Write-Host "⚙️  STEP 6: Configuring Environment Variables" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "Setting Flask configuration..." -ForegroundColor Cyan

npx railway variables set FLASK_ENV=production
npx railway variables set FLASK_DEBUG=False
npx railway variables set SECRET_KEY="$SECRET_KEY"
npx railway variables set JWT_SECRET_KEY="$JWT_SECRET_KEY"
npx railway variables set FRONTEND_ORIGIN=https://online-voting-system-six-flax.vercel.app
npx railway variables set RF_MODELS_DIR=/app/models/rf

Write-Host "✅ Flask variables set!" -ForegroundColor Green
Write-Host ""

# Step 7: Email Configuration
Write-Host "📧 STEP 7: Email Configuration" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "Enter your Gmail address:" -ForegroundColor Cyan
$MAIL_USERNAME = Read-Host "Gmail"

Write-Host ""
Write-Host "Get your Gmail App Password:" -ForegroundColor Cyan
Write-Host "1. Go to https://myaccount.google.com/apppasswords" -ForegroundColor Gray
Write-Host "2. Enable 2FA if you haven't already" -ForegroundColor Gray
Write-Host "3. Select 'Mail' and 'Windows Computer'" -ForegroundColor Gray
Write-Host "4. Generate app password" -ForegroundColor Gray
Write-Host "5. Copy the 16-character password below" -ForegroundColor Gray
Write-Host ""

$MAIL_PASSWORD = Read-Host "App Password" -AsSecureString
$MAIL_PASSWORD_PLAIN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($MAIL_PASSWORD))

npx railway variables set MAIL_USERNAME="$MAIL_USERNAME"
npx railway variables set MAIL_PASSWORD="$MAIL_PASSWORD_PLAIN"
npx railway variables set MAIL_DEFAULT_SENDER="noreply@election.com"
npx railway variables set MAIL_SERVER=smtp.gmail.com
npx railway variables set MAIL_PORT=587

Write-Host ""
Write-Host "✅ Email configured!" -ForegroundColor Green
Write-Host ""

# Step 8: Add MongoDB
Write-Host "🗄️  STEP 8: Add MongoDB Service" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  IMPORTANT: Go to Railway Dashboard and add MongoDB:" -ForegroundColor Yellow
Write-Host "   1. Go to your Railway project dashboard" -ForegroundColor White
Write-Host "   2. Click '+ Add Service'" -ForegroundColor White
Write-Host "   3. Select 'Add from Marketplace'" -ForegroundColor White
Write-Host "   4. Choose 'MongoDB'" -ForegroundColor White
Write-Host "   5. Click 'Add' to provision" -ForegroundColor White
Write-Host "   6. Wait 2-3 minutes for MongoDB to be ready" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter when MongoDB is ready in Railway"

Write-Host ""
Write-Host "Setting MongoDB connection..." -ForegroundColor Cyan
npx railway variables set MONGO_URI='${{Mongo.MONGO_URL}}'

Write-Host ""
Write-Host "✅ MongoDB connected!" -ForegroundColor Green
Write-Host ""

# Step 9: Get Backend URL
Write-Host "🔗 STEP 9: Getting Backend URL" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "Opening Railway dashboard to get your backend URL..." -ForegroundColor Cyan
Write-Host ""
Write-Host "To get your backend URL:" -ForegroundColor Yellow
Write-Host "1. Go to your Railway project dashboard" -ForegroundColor Gray
Write-Host "2. Click on the Python service" -ForegroundColor Gray
Write-Host "3. Go to 'Settings' tab" -ForegroundColor Gray
Write-Host "4. Look for 'Domains' section" -ForegroundColor Gray
Write-Host "5. Copy the URL (should look like: https://your-app-xxxx.railway.app)" -ForegroundColor Gray
Write-Host ""
Write-Host "Enter your backend URL:" -ForegroundColor Cyan
$BACKEND_URL = Read-Host "Backend URL"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║            🎉 BACKEND DEPLOYMENT COMPLETE!                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "Your backend is now live!" -ForegroundColor Green
Write-Host "Backend URL: $BACKEND_URL" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "1. Update Vercel Frontend with Backend URL" -ForegroundColor White
Write-Host "   • Go to Vercel Dashboard" -ForegroundColor Gray
Write-Host "   • Project Settings → Environment Variables" -ForegroundColor Gray
Write-Host "   • Set REACT_APP_API_URL=$BACKEND_URL" -ForegroundColor Gray
Write-Host "   • Redeploy: npx vercel --prod" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test API" -ForegroundColor White
Write-Host "   • curl $BACKEND_URL/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test Full Application" -ForegroundColor White
Write-Host "   • Go to https://online-voting-system-six-flax.vercel.app" -ForegroundColor Gray
Write-Host "   • Register, login, vote" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Monitor Backend" -ForegroundColor White
Write-Host "   • Check logs in Railway dashboard" -ForegroundColor Gray
Write-Host "   • View metrics and performance" -ForegroundColor Gray
Write-Host ""

Write-Host "✨ All done! Your election system is now fully deployed!" -ForegroundColor Green
Write-Host ""
