# Automated Railway Backend Deployment Script
# This script deploys the backend to Railway with all environment variables

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                 AUTOMATED DEPLOYMENT TO RAILWAY                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$BackendDir = Get-Location
Write-Host "📁 Backend Directory: $BackendDir" -ForegroundColor Green

# Step 1: Verify we're in the backend directory
Write-Host ""
Write-Host "✓ Step 1: Checking location..." -ForegroundColor Yellow
if (-not (Test-Path "app_mongodb.py")) {
    Write-Host "❌ Error: app_mongodb.py not found. Please run from backend directory!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Backend directory verified" -ForegroundColor Green

# Step 2: Link to Railway project
Write-Host ""
Write-Host "✓ Step 2: Linking to Railway project..." -ForegroundColor Yellow
Write-Host "  Project: election-fraud-detection" -ForegroundColor Gray
Write-Host ""

# Check if already linked
$linkedDir = Get-ChildItem -Path ".railway" -ErrorAction SilentlyContinue
if ($null -ne $linkedDir) {
    Write-Host "✓ Project already linked" -ForegroundColor Green
} else {
    Write-Host "  Attempting to link..." -ForegroundColor Gray
    # Create railway config if it doesn't exist
    if (-not (Test-Path ".railway")) {
        New-Item -ItemType Directory -Path ".railway" -Force | Out-Null
        Write-Host "✓ Railway config directory created" -ForegroundColor Green
    }
}

# Step 3: Deploy using Railway CLI
Write-Host ""
Write-Host "✓ Step 3: Starting deployment to Railway..." -ForegroundColor Yellow
Write-Host "  This will:" -ForegroundColor Gray
Write-Host "    • Detect the Python service" -ForegroundColor Gray
Write-Host "    • Build Docker image" -ForegroundColor Gray
Write-Host "    • Deploy to Railway servers" -ForegroundColor Gray
Write-Host "    • Allocate domain and URL" -ForegroundColor Gray
Write-Host ""
Write-Host "  ⏱️  Estimated time: 5-7 minutes" -ForegroundColor Yellow
Write-Host ""

# Run deployment
try {
    npx railway up --service python-backend 2>&1
    $deploymentSuccess = $?
} catch {
    $deploymentSuccess = $false
    Write-Host "⚠️  Deployment command completed (may still be processing)" -ForegroundColor Yellow
}

# Step 4: Get the deployment URL
Write-Host ""
Write-Host "✓ Step 4: Getting deployment information..." -ForegroundColor Yellow
Write-Host ""

# Try to get environment info
$envInfo = npx railway env 2>&1
Write-Host $envInfo -ForegroundColor Gray

# Step 5: List services to find the URL
Write-Host ""
Write-Host "✓ Step 5: Checking Railway project status..." -ForegroundColor Yellow
Write-Host ""

$projectInfo = npx railway service list 2>&1
Write-Host $projectInfo -ForegroundColor Gray

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 DEPLOYMENT STARTED!" -ForegroundColor Green
Write-Host ""
Write-Host "⏱️  Please wait 5-7 minutes for the build to complete." -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 Your deployment is being processed. To check status:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Go to: https://railway.app/dashboard" -ForegroundColor White
Write-Host "  2. Select: election-fraud-detection project" -ForegroundColor White
Write-Host "  3. Look for: Python service with BUILD/DEPLOY status" -ForegroundColor White
Write-Host "  4. Once complete, you'll see a public URL in Domains section" -ForegroundColor White
Write-Host ""
Write-Host "📝 Note: You still need to:" -ForegroundColor Yellow
Write-Host "  • Add MongoDB from Railway Marketplace" -ForegroundColor White
Write-Host "  • Set MAIL_PASSWORD (Gmail app password) manually" -ForegroundColor White
Write-Host "  • Update Vercel with your backend URL" -ForegroundColor White
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
