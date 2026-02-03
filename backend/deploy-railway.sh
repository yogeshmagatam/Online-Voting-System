#!/bin/bash
# Railway Backend Auto-Deployment Script
# This script automates the Railway deployment process

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     RAILWAY BACKEND DEPLOYMENT - AUTOMATED SETUP              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed"
fi

echo ""
echo "🔐 STEP 1: Authenticate with Railway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please login to Railway. This will open a browser window."
railway login

echo ""
echo "✅ Logged in successfully!"
echo ""

echo "📁 STEP 2: Initialize Railway Project"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cd backend
railway init --name "election-fraud-detection"

echo ""
echo "✅ Project initialized!"
echo ""

echo "🚀 STEP 3: Deploy Backend Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
railway up

echo ""
echo "✅ Backend deployed!"
echo ""

echo "🗄️  STEP 4: Add MongoDB Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Going to Railway dashboard to add MongoDB..."
echo "The project has been pushed to Railway."
echo ""
echo "Next steps:"
echo "1. Go to your Railway project dashboard"
echo "2. Click '+ Add Service'"
echo "3. Select 'Add from Marketplace'"
echo "4. Choose 'MongoDB'"
echo "5. Click 'Add' to provision"
echo ""
echo "Press Enter when MongoDB is ready..."
read

echo ""
echo "⚙️  STEP 5: Configure Environment Variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Generate secure keys
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)

echo "Generated secure keys:"
echo "SECRET_KEY=$SECRET_KEY"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo ""

# Set environment variables
railway variables set FLASK_ENV=production
railway variables set FLASK_DEBUG=False
railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set JWT_SECRET_KEY="$JWT_SECRET_KEY"
railway variables set FRONTEND_ORIGIN=https://online-voting-system-six-flax.vercel.app
railway variables set RF_MODELS_DIR=/app/models/rf

echo ""
echo "📧 Email Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Enter your Gmail address:"
read MAIL_USERNAME

echo "Enter your Gmail App Password (from https://myaccount.google.com/apppasswords):"
read -s MAIL_PASSWORD

railway variables set MAIL_USERNAME="$MAIL_USERNAME"
railway variables set MAIL_PASSWORD="$MAIL_PASSWORD"
railway variables set MAIL_DEFAULT_SENDER="noreply@election.com"
railway variables set MAIL_SERVER=smtp.gmail.com
railway variables set MAIL_PORT=587

echo ""
echo "✅ Environment variables set!"
echo ""

echo "🔗 MongoDB Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Setting MongoDB connection string..."
railway variables set MONGO_URI='${{Mongo.MONGO_URL}}'

echo ""
echo "✅ MongoDB connected!"
echo ""

echo "📊 FINAL: Get Your Backend URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
BACKEND_URL=$(railway variables get RAILWAY_SERVICE_DOMAIN)
echo "✅ Your Backend URL is: https://$BACKEND_URL"
echo ""
echo "Save this URL! You'll need it for the next step."
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            🎉 BACKEND DEPLOYMENT COMPLETE!                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Your backend is now live at: https://$BACKEND_URL"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Update Vercel Frontend with backend URL"
echo "2. Test API endpoints"
echo "3. Monitor logs in Railway dashboard"
echo ""
echo "Backend URL to save: https://$BACKEND_URL"
