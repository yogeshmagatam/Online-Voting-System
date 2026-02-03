#!/usr/bin/env bash
# Railway Backend Deployment Checklist
# Use this to track your deployment progress

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         RAILWAY BACKEND DEPLOYMENT CHECKLIST                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Pre-Deployment
echo "📋 PRE-DEPLOYMENT CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Code pushed to GitHub"
echo "[ ] requirements.txt is up to date"
echo "[ ] Dockerfile exists and is valid"
echo "[ ] Environment variables prepared"
echo "[ ] Gmail 2FA enabled"
echo "[ ] App password generated"
echo ""

# Railway Account Setup
echo "🔧 RAILWAY SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Visit https://railway.app"
echo "[ ] Sign up/Login with GitHub"
echo "[ ] Authorize Railway access to repositories"
echo "[ ] Create new project"
echo "[ ] Deploy from GitHub (yogeshmagatam/Online-Voting-System)"
echo "[ ] Wait for build to complete (5-10 minutes)"
echo ""

# MongoDB Setup
echo "🗄️  MONGODB SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Click '+ Add Service' in Railway"
echo "[ ] Select 'Add from Marketplace'"
echo "[ ] Choose 'MongoDB'"
echo "[ ] Wait for MongoDB provisioning (2-3 minutes)"
echo "[ ] Verify MongoDB status shows 'Ready'"
echo ""

# Environment Variables
echo "⚙️  ENVIRONMENT VARIABLES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Go to Python Service → Variables"
echo "[ ] Add FLASK_ENV=production"
echo "[ ] Add FLASK_DEBUG=False"
echo "[ ] Add SECRET_KEY=<generate-secure-value>"
echo "[ ] Add JWT_SECRET_KEY=<generate-secure-value>"
echo "[ ] Add MAIL_USERNAME=<your-gmail>"
echo "[ ] Add MAIL_PASSWORD=<app-password>"
echo "[ ] Add MAIL_DEFAULT_SENDER=noreply@election.com"
echo "[ ] Add FRONTEND_ORIGIN=https://online-voting-system-six-flax.vercel.app"
echo "[ ] Add MONGO_URI=\${{Mongo.MONGO_URL}}"
echo "[ ] Add RF_MODELS_DIR=/app/models/rf"
echo ""

# Deployment
echo "🚀 DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Click 'Deploy' to start deployment"
echo "[ ] Wait for all environment variables to be applied"
echo "[ ] Check logs for any errors"
echo "[ ] Backend service shows 'Running' status"
echo "[ ] Get backend URL from Domains section"
echo ""

# Verification
echo "✅ VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Test backend URL in browser"
echo "[ ] Check MongoDB connection (no errors in logs)"
echo "[ ] Verify CORS is working (check browser console)"
echo "[ ] Test email OTP sending"
echo "[ ] Backend API responds to requests"
echo ""

# Frontend Update
echo "🎨 FRONTEND UPDATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Copy backend URL from Railway"
echo "[ ] Go to Vercel Dashboard"
echo "[ ] Project Settings → Environment Variables"
echo "[ ] Update REACT_APP_API_URL with backend URL"
echo "[ ] Save and redeploy frontend"
echo "[ ] Wait for deployment to complete"
echo ""

# Testing
echo "🧪 TESTING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Frontend loads without errors"
echo "[ ] Can register a new voter account"
echo "[ ] Can login with email OTP"
echo "[ ] Identity verification works"
echo "[ ] Can cast a vote"
echo "[ ] Admin dashboard loads"
echo "[ ] Fraud detection shows alerts"
echo ""

# Final Steps
echo "🎉 FINAL STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[ ] Set up monitoring alerts in Railway"
echo "[ ] Enable automatic deployments"
echo "[ ] Configure custom domain (optional)"
echo "[ ] Set up backup strategy"
echo "[ ] Document API endpoints for team"
echo "[ ] Create user accounts for testing"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  DEPLOYMENT COMPLETE! 🎉                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Frontend: https://online-voting-system-six-flax.vercel.app"
echo "Backend:  [Your Railway URL from step 7]"
echo ""
echo "For help, see README_DEPLOYMENT.md"
