#!/bin/bash
# Railway deployment script for Windows PowerShell

# Check if Git is installed
if (-Not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

# Change to backend directory
Set-Location backend

# Check if requirements.txt exists
if (-Not (Test-Path requirements.txt)) {
    Write-Host "requirements.txt not found!" -ForegroundColor Red
    exit 1
}

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Railway Backend Deployment Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Install Railway CLI
Write-Host "Installing Railway CLI..." -ForegroundColor Yellow
npm install -g @railway/cli

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Go to https://railway.app and sign up with GitHub" -ForegroundColor Green
Write-Host "2. Run: railway login" -ForegroundColor Green
Write-Host "3. Run: railway init" -ForegroundColor Green
Write-Host "4. Run: railway up" -ForegroundColor Green
Write-Host ""
Write-Host "Then add MongoDB service in Railway Dashboard and set environment variables." -ForegroundColor Yellow
