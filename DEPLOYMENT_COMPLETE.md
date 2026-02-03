# 🚀 Complete Deployment Guide - Railway Backend

## ✅ What's Done
- ✅ Frontend deployed on Vercel: https://online-voting-system-six-flax.vercel.app
- ✅ Code pushed to GitHub with Railway configuration
- ⏳ Backend deployment pending

## 📋 Railway Deployment Steps (15 minutes)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Click **"Start New Project"**
3. Sign in with GitHub (recommended)
4. Authorize Railway to access your repositories

### Step 2: Deploy Backend from GitHub
1. In Railway, click **"New Project"** → **"Deploy from GitHub repo"**
2. Find and select: **yogeshmagatam/Online-Voting-System**
3. **IMPORTANT**: 
   - Select the **feature/yogesh/login** branch (your current branch)
   - Or deploy from **main** if you prefer the default branch
4. Railway will auto-detect Python and start building
5. Wait for deployment to complete (3-5 minutes)

### Step 3: Add MongoDB Service
1. In your Railway project dashboard, click **"+ Add Service"**
2. Select **"Add from Marketplace"**
3. Find **"MongoDB"** and click it
4. Click **"Add"** to provision MongoDB
5. Wait 2-3 minutes for MongoDB to be ready

### Step 4: Configure Environment Variables
Go to your Railway project dashboard:

1. Click on your **Python/Flask service**
2. Go to **"Variables"** tab
3. Click **"New Variable"** and add these:

```
FLASK_ENV = production
FLASK_DEBUG = False
SECRET_KEY = generate-a-random-string-here
JWT_SECRET_KEY = generate-another-random-string-here
MAIL_USERNAME = your-gmail@gmail.com
MAIL_PASSWORD = your-app-password
MAIL_DEFAULT_SENDER = noreply@election.com
FRONTEND_ORIGIN = https://online-voting-system-six-flax.vercel.app
RF_MODELS_DIR = /app/models/rf
```

**For MAIL_PASSWORD** (Gmail):
- Enable 2FA on your Google account
- Go to https://myaccount.google.com/apppasswords
- Select "Mail" and "Windows Computer"
- Generate app password (16 characters)
- Paste it as MAIL_PASSWORD

### Step 5: Link MongoDB to Flask Service
1. In Railway dashboard, click the **Python service**
2. Go to **Variables** tab
3. You'll see `${{Mongo.MONGO_URL}}` variable available
4. Add this variable:
   ```
   MONGO_URI = ${{Mongo.MONGO_URL}}
   ```
5. Click **Deploy** to restart with MongoDB

### Step 6: Get Your Backend URL
1. In Railway dashboard, click your **Python service**
2. Go to **"Settings"** tab
3. Look for **"Domains"** section
4. You'll see auto-generated URL like: `https://your-backend-xxxx.railway.app`
5. Copy this URL

### Step 7: Update Frontend with Backend URL
1. Go to https://vercel.com/yogeshmagatams-projects/online-voting-system
2. Go to **Settings** → **Environment Variables**
3. Find `REACT_APP_API_URL` variable
4. Update it with your Railway backend URL
5. Click **Save**
6. Go to **Deployments** and click the latest one
7. Click **Redeploy** (or run `npx vercel --prod` from frontend folder)

## 🔍 Verify Deployment

### Test Backend API
Open a terminal and run:
```bash
curl https://your-backend-url.railway.app/api/health
```

You should get a JSON response.

### Test Full Application
1. Go to https://online-voting-system-six-flax.vercel.app
2. Click **"Register"**
3. Create a test account
4. Login with email OTP
5. Verify identity (take a photo)
6. Cast votes
7. Check Admin Dashboard for fraud detection

## 🐛 Troubleshooting

### Backend shows "502 Bad Gateway"
- **Solution**: App is still starting. Wait 30 seconds and refresh.

### MongoDB connection fails
- **Solution**: 
  1. Check MongoDB service status in Railway (should show "Ready")
  2. Verify `MONGO_URI = ${{Mongo.MONGO_URL}}` is set
  3. Check logs for connection errors

### Email OTP not sending
- **Solution**:
  1. Verify MAIL_USERNAME and MAIL_PASSWORD are correct
  2. Check if 2FA is enabled on Gmail
  3. Use App Password from myaccount.google.com/apppasswords

### CORS errors on frontend
- **Solution**:
  1. Verify `FRONTEND_ORIGIN` matches your Vercel URL exactly
  2. Check Railway logs for CORS errors
  3. Restart the backend service in Railway

### Build fails in Railway
- **Solution**:
  1. Check build logs in Railway dashboard
  2. Common issues:
     - Missing system dependencies (should be in Dockerfile)
     - Large file uploads taking too long (Railway has upload limits)
  3. Try redeploying

## 📊 Monitoring

### View Backend Logs
1. Railway dashboard → Python service → **Logs** tab
2. You'll see:
   - Build progress
   - Deployment logs
   - Real-time application logs
   - Error messages

### Monitor Performance
1. Railway dashboard → Python service → **Metrics** tab
2. View:
   - CPU usage
   - Memory usage
   - Network I/O
   - Response times

## 🔐 Security Checklist

- ✅ Use strong SECRET_KEY and JWT_SECRET_KEY (at least 32 characters)
- ✅ Use Gmail App Password (not your actual password)
- ✅ Set FLASK_DEBUG=False in production
- ✅ Update FRONTEND_ORIGIN to your Vercel URL
- ✅ Keep environment variables private (never commit .env files)
- ✅ Use HTTPS for all URLs (Railway provides this automatically)

## 📞 Support Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Project GitHub**: https://github.com/yogeshmagatam/Online-Voting-System
- **MongoDB Docs**: https://docs.mongodb.com

## 🎉 Next Steps

After successful deployment:

1. ✅ Share your application URL: https://online-voting-system-six-flax.vercel.app
2. Create admin accounts for testing
3. Load voting data using the admin dashboard
4. Test fraud detection with test cases
5. Monitor logs and performance in Railway

---

**Estimated Time**: 15 minutes
**Cost**: Free tier available on Railway (up to $5/month credits)
