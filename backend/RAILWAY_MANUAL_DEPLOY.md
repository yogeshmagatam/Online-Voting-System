# 🚀 Railway Backend Deployment - Step by Step (Manual)

## Overview
This guide walks you through deploying your Flask backend to Railway with MongoDB.

---

## Prerequisites ✅
- [ ] GitHub account with your code pushed
- [ ] Railway account (free at https://railway.app)
- [ ] Gmail account with 2FA enabled
- [ ] Node.js installed (for Railway CLI)

---

## Step-by-Step Deployment

### Step 1: Create Railway Account (2 minutes)
1. Go to https://railway.app
2. Click "Start New Project"
3. Select "Deploy with GitHub"
4. Sign in with your GitHub account
5. Authorize Railway to access your repositories

### Step 2: Deploy Backend (5 minutes)
1. Click "New Project" button
2. Select "Deploy from GitHub repo"
3. Find and select: **yogeshmagatam/Online-Voting-System**
4. Select branch: **feature/yogesh/login** (or main)
5. Railway will auto-detect Python and start building
6. Wait 3-5 minutes for build to complete
7. You'll see "Build Successful" when done

### Step 3: Add MongoDB Database (5 minutes)
1. In your Railway project, click **"+ Add Service"** button
2. Click **"Add from Marketplace"**
3. Search for and select **"MongoDB"**
4. Click **"Add"** to provision
5. Wait 2-3 minutes for MongoDB to be ready
6. You'll see status change to "Running"

### Step 4: Configure Environment Variables (5 minutes)

In your Railway project dashboard:

1. Click on your **Python/Flask service** (the one you deployed)
2. Click **"Variables"** tab on the right
3. Click **"New Variable"** and add each of these:

```
Name: FLASK_ENV
Value: production

Name: FLASK_DEBUG
Value: False

Name: SECRET_KEY
Value: (generate a random secure string - see below)

Name: JWT_SECRET_KEY
Value: (generate another random secure string)

Name: MAIL_USERNAME
Value: your-email@gmail.com

Name: MAIL_PASSWORD
Value: (your app-specific password from Google)

Name: MAIL_DEFAULT_SENDER
Value: noreply@election.com

Name: MAIL_SERVER
Value: smtp.gmail.com

Name: MAIL_PORT
Value: 587

Name: FRONTEND_ORIGIN
Value: https://online-voting-system-six-flax.vercel.app

Name: RF_MODELS_DIR
Value: /app/models/rf

Name: MONGO_URI
Value: ${{Mongo.MONGO_URL}}
```

**How to generate secure keys:**
```python
import secrets
SECRET_KEY = secrets.token_urlsafe(32)
JWT_SECRET_KEY = secrets.token_urlsafe(32)
```

Or use this PowerShell command:
```powershell
[System.Convert]::ToBase64String([System.Random]::new().Next(1, 2147483647) | out-string)
```

**How to get Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication (if not done)
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and "Windows Computer"
5. Click "Generate"
6. Copy the 16-character password
7. Use that as MAIL_PASSWORD

### Step 5: Restart Backend (2 minutes)
After adding all variables:
1. Click **"Deploy"** button to restart with new variables
2. Wait for deployment to complete
3. Check logs to ensure no errors

### Step 6: Get Your Backend URL (1 minute)
1. Click your **Python service**
2. Click **"Settings"** tab
3. Look for **"Domains"** section
4. You'll see a URL like: `https://your-app-xxxx.railway.app`
5. **Save this URL** - you'll need it next!

### Step 7: Update Frontend with Backend URL (5 minutes)
1. Go to Vercel Dashboard: https://vercel.com/yogeshmagatams-projects/online-voting-system
2. Click **"Settings"** → **"Environment Variables"**
3. Find the variable named **REACT_APP_API_URL**
4. Update its value to your Railway backend URL
5. Click **"Save"**
6. Go to **"Deployments"** tab
7. Find the latest deployment and click **"Redeploy"**
8. Wait for redeployment to complete

### Step 8: Test Your Application (5 minutes)
1. Go to https://online-voting-system-six-flax.vercel.app
2. Try to **Register** - should work without CORS errors
3. Check your **email for OTP**
4. **Login** with the OTP
5. Complete **Identity Verification**
6. **Cast a Vote**
7. Check **Admin Dashboard** for fraud alerts
8. ✅ If all works, you're done!

---

## Troubleshooting

### MongoDB Connection Error
**Error**: "MongoDB connection failed"
**Solution**: 
- Wait 3-5 minutes for MongoDB to fully provision
- Check MongoDB service status is "Running" in Railway
- Verify MONGO_URI = ${{Mongo.MONGO_URL}} is set

### CORS Errors in Browser Console
**Error**: "Access to XMLHttpRequest blocked by CORS"
**Solution**:
- Verify FRONTEND_ORIGIN matches your Vercel URL exactly
- Make sure it includes `https://` prefix
- Wait 1-2 minutes after updating variables for changes to take effect
- Restart backend service

### Backend returns 502 Bad Gateway
**Error**: "502 Bad Gateway" in browser
**Solution**:
- Backend is starting up. Wait 30 seconds and try again
- Check Railway logs for errors
- Verify all environment variables are set correctly

### Email OTP Not Sending
**Error**: "Failed to send OTP email"
**Solution**:
- Verify MAIL_USERNAME is correct Gmail address
- Generate new App Password from myaccount.google.com/apppasswords
- Make sure 2FA is enabled on Gmail account
- Check that MAIL_PASSWORD matches the generated password exactly

### Build Fails on Railway
**Error**: "Build failed" in Railway dashboard
**Solution**:
- Check build logs in Railway dashboard
- Common issues:
  - Python version mismatch
  - Missing system dependencies
  - Large files taking too long to upload
- Try deleting and redeploying

---

## Monitoring Your Backend

### View Logs
1. Go to your Railway project
2. Click Python service
3. Click **"Logs"** tab
4. You'll see real-time application logs

### View Metrics
1. Go to your Railway project
2. Click Python service
3. Click **"Metrics"** tab
4. See CPU, memory, and network usage

---

## Important Notes

⚠️ **Security**:
- Never share your SECRET_KEY or JWT_SECRET_KEY
- Never use your actual Gmail password (use App Password)
- Keep MAIL_PASSWORD private
- Don't commit .env files to GitHub

✅ **Best Practices**:
- Monitor logs regularly
- Set up alerts for errors
- Keep dependencies updated
- Regular backups (Railway does this automatically)

---

## Cost

Railway offers:
- **Free Tier**: $5/month in free credits
- **Included**: 512MB RAM, 1GB bandwidth, MongoDB
- **No credit card** required initially
- Perfect for development and testing

---

## Next Steps After Successful Deployment

1. ✅ Test all voting functionality
2. ✅ Create test user accounts
3. ✅ Load sample voting data via Admin Dashboard
4. ✅ Test fraud detection with suspicious patterns
5. ✅ Monitor performance and logs
6. ✅ Set up automated backups
7. ✅ Share your app with others!

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Flask Docs: https://flask.palletsprojects.com
- MongoDB Docs: https://docs.mongodb.com

---

**Estimated Total Time**: 30 minutes ⏱️

You've got this! 🚀
