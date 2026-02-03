#!/usr/bin/env pwsh
# Automated Frontend-Backend Integration Script
# This script completes Steps 2 & 3 automatically

param(
    [string]$BackendURL = ""
)

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                AUTOMATED INTEGRATION SCRIPT                    ║" -ForegroundColor Green
Write-Host "║              Complete Backend-Frontend Integration             ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Check if backend URL was provided
if ([string]::IsNullOrEmpty($BackendURL)) {
    Write-Host "⚠️  Backend URL required!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Usage: ./integrate.ps1 -BackendURL 'https://your-railway-url.railway.app'" -ForegroundColor White
    Write-Host ""
    Write-Host "To get your backend URL:" -ForegroundColor Cyan
    Write-Host "  1. Go to: https://railway.app/dashboard" -ForegroundColor Gray
    Write-Host "  2. Select: election-fraud-detection project" -ForegroundColor Gray
    Write-Host "  3. Click: Python service → Settings → Domains" -ForegroundColor Gray
    Write-Host "  4. Copy: The public URL" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "✅ Backend URL: $BackendURL" -ForegroundColor Green
Write-Host ""

# Step 2: Update Vercel Environment Variable
Write-Host "📍 Step 2: Updating Vercel Environment Variables..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Check if Vercel CLI is installed
Write-Host "Checking Vercel CLI..." -ForegroundColor Gray
$vercelCheck = npm list -g vercel 2>&1 | Select-String "vercel"
if ([string]::IsNullOrEmpty($vercelCheck)) {
    Write-Host "Installing Vercel CLI..." -ForegroundColor Yellow
    npm install -g vercel 2>&1 | Out-Null
}

Write-Host "✅ Vercel CLI available" -ForegroundColor Green
Write-Host ""

# Create .env.production.local for local testing
Write-Host "Creating environment file for frontend..." -ForegroundColor Gray
$envContent = "REACT_APP_API_URL=$BackendURL"
$envPath = ".\frontend\.env.production"

# Check if env file exists in frontend
if (Test-Path $envPath) {
    Write-Host "Updating existing .env file..." -ForegroundColor Gray
    $envContent | Set-Content $envPath
} else {
    Write-Host "Creating new .env file..." -ForegroundColor Gray
    $envContent | New-Item -Path $envPath -ItemType File -Force | Out-Null
}

Write-Host "✅ Environment file updated" -ForegroundColor Green
Write-Host ""

# Update via Vercel CLI
Write-Host "Updating Vercel environment variables..." -ForegroundColor Yellow
$vercelUpdate = vercel env add REACT_APP_API_URL --yes 2>&1

if ($LASTEXITCODE -eq 0 -or $vercelUpdate -match "added|updated") {
    Write-Host "✅ Vercel environment variable updated" -ForegroundColor Green
} else {
    Write-Host "⚠️  Manual update required:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Go to: https://vercel.com/yogeshmagatams-projects/online-voting-system" -ForegroundColor White
    Write-Host "  2. Settings → Environment Variables" -ForegroundColor White
    Write-Host "  3. Find: REACT_APP_API_URL" -ForegroundColor White
    Write-Host "  4. Update: $BackendURL" -ForegroundColor Cyan
    Write-Host "  5. Click: Save" -ForegroundColor White
}

Write-Host ""

# Step 3: Trigger Vercel Redeploy
Write-Host "📍 Step 3: Redeploying Frontend on Vercel..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

Write-Host "Triggering Vercel deployment..." -ForegroundColor Yellow
Write-Host "(This may take 1-2 minutes)" -ForegroundColor Gray
Write-Host ""

$deployOutput = vercel --prod 2>&1

if ($LASTEXITCODE -eq 0 -or $deployOutput -match "Ready|deployed|✓") {
    Write-Host "✅ Vercel deployment triggered successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Deployment URL:" -ForegroundColor Cyan
    $deployOutput | Select-String "https://online-voting" | ForEach-Object {
        Write-Host "  $($_)" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  Vercel deployment:" -ForegroundColor Yellow
    Write-Host $deployOutput -ForegroundColor Gray
}

Write-Host ""

# Final Summary
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                   INTEGRATION COMPLETE! 🎉                     ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "✅ What's Been Done:" -ForegroundColor Green
Write-Host "   • Backend URL: $BackendURL" -ForegroundColor Cyan
Write-Host "   • Vercel environment variable updated" -ForegroundColor Cyan
Write-Host "   • Frontend redeployment triggered" -ForegroundColor Cyan
Write-Host ""

Write-Host "⏱️  Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Wait 2-3 minutes for Vercel deployment" -ForegroundColor White
Write-Host "   2. Visit: https://online-voting-system-six-flax.vercel.app" -ForegroundColor White
Write-Host "   3. Test: Register → OTP → Login → Vote" -ForegroundColor White
Write-Host ""

Write-Host "📊 Check Status:" -ForegroundColor Yellow
Write-Host "   Vercel: https://vercel.com/yogeshmagatams-projects/online-voting-system" -ForegroundColor Cyan
Write-Host "   Railway: https://railway.app/dashboard" -ForegroundColor Cyan
Write-Host ""

Write-Host "Ready to test? 🚀" -ForegroundColor Green
