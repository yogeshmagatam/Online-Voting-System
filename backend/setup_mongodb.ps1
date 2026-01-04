# MongoDB Community Edition Installation Script for Windows
# This script downloads and installs MongoDB locally

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  MongoDB Community Edition Setup" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if MongoDB is already installed
$mongoInstalled = Get-Command mongod -ErrorAction SilentlyContinue
if ($mongoInstalled) {
    Write-Host "Successfully installed MongoDB!" -ForegroundColor Green
    mongod --version
    exit 0
}

Write-Host "MongoDB not found. Starting installation..." -ForegroundColor Yellow
Write-Host ""

# Option 1: Install via Chocolatey (recommended)
Write-Host "Checking for Chocolatey package manager..." -ForegroundColor Cyan
$chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue

if ($chocoInstalled) {
    Write-Host "Chocolatey found! Installing MongoDB..." -ForegroundColor Green
    choco install mongodb -y
    
    # Create data directory
    $dataDir = "C:\data\db"
    if (!(Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
        Write-Host "Created MongoDB data directory: $dataDir" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "MongoDB installation complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start MongoDB, run:" -ForegroundColor Cyan
    Write-Host "  mongod" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "Chocolatey not found." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "=== Installation Options ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 1: Install Chocolatey first (RECOMMENDED)" -ForegroundColor Green
    Write-Host "  Run in PowerShell (Admin):" -ForegroundColor Cyan
    Write-Host '  Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))' -ForegroundColor Yellow
    Write-Host "  Then run this script again." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 2: Manual Installation" -ForegroundColor Green
    Write-Host "  1. Download MongoDB from: https://www.mongodb.com/try/download/community" -ForegroundColor Yellow
    Write-Host "  2. Run the .msi installer" -ForegroundColor Yellow
    Write-Host "  3. Choose Complete installation" -ForegroundColor Yellow
    Write-Host "  4. Install MongoDB as a Windows Service (recommended)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 3: Use MongoDB Atlas (Cloud)" -ForegroundColor Green
    Write-Host "  - No local installation needed" -ForegroundColor Yellow
    Write-Host "  - Requires fixing DNS/network issues" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "===============================================" -ForegroundColor Cyan
