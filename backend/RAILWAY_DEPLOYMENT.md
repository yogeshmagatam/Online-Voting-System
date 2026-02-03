# Railway Deployment Guide for Election Fraud Detection Backend

## Quick Start (5-10 minutes)

### Step 1: Prepare Your Code
Push your code to GitHub (if not already):
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub (recommended)
3. Authorize Railway to access your repositories

### Step 3: Deploy on Railway
1. Click **"New Project"** → **"Deploy from GitHub repo"**
2. Select your repository
3. Select the **backend** folder as root directory
4. Railway will auto-detect it's a Python app
5. Click **Deploy**

### Step 4: Add MongoDB
1. In your Railway project, click **"+ Add Service"**
2. Select **"Add from Marketplace"** → **MongoDB**
3. Wait for MongoDB to provision (2-3 minutes)

### Step 5: Configure Environment Variables
Go to your Railway project → **Variables**

Add these variables:
```
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here

# Database
MONGO_URI=${{Mongo.MONGO_URL}}

# Email Configuration
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@yourapp.com

# Frontend URL (update with your Vercel URL)
FRONTEND_ORIGIN=https://online-voting-system-six-flax.vercel.app

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here

# Model directory
RF_MODELS_DIR=/app/models/rf
```

**For MAIL_PASSWORD:**
- Use Google App Password (2FA required)
- Go to https://myaccount.google.com/apppasswords
- Generate one for "Mail" and "Windows Computer"

### Step 6: Verify Deployment
1. Railway will show your backend URL (e.g., `https://your-app.railway.app`)
2. Test API: `curl https://your-app.railway.app/api/health`
3. Update Vercel frontend environment variable:
   - Go to Vercel Dashboard
   - Project Settings → Environment Variables
   - Set `REACT_APP_API_URL=https://your-app.railway.app`
   - Redeploy: `npx vercel --prod`

## Detailed Configuration

### Railway Dashboard Features
- **Logs**: View build and runtime logs
- **Metrics**: Monitor CPU, memory, and network
- **Variables**: Manage environment variables
- **Domains**: See your auto-generated URL
- **Settings**: Configure deployment behavior

### MongoDB Connection
Railway provides MongoDB with environment variable `${{Mongo.MONGO_URL}}`

This includes:
- Auto-provisioned MongoDB instance
- Automatic backups
- Built-in monitoring

### Port Configuration
- Railway auto-detects the port from `$PORT` environment variable
- App will listen on port from env or default 5000
- No need to manually configure ports

## Troubleshooting

### Build Fails with "pip install" errors
**Solution**: Railway has some packages pre-compiled. If specific packages fail:
1. Check build logs in Railway dashboard
2. Try removing problematic optional packages from requirements.txt
3. Restart deployment

### App crashes after deployment
**Solution**: 
1. Check logs in Railway dashboard
2. Verify all environment variables are set
3. Check MongoDB connection string

### API returns 502 or 503 errors
**Solution**:
1. Wait 30-60 seconds after deployment (app may still be starting)
2. Check if MongoDB is ready (should show "Ready" status)
3. Verify environment variables are correct

### CORS errors from frontend
**Solution**:
1. Update `FRONTEND_ORIGIN` in Railway environment variables
2. Make sure frontend URL matches exactly (with https://)
3. Restart deployment after updating

## Advanced: Custom Domain

To use your own domain:
1. Go to Railway project → **Settings**
2. Click **"Add Custom Domain"**
3. Enter your domain (e.g., `api.yourapp.com`)
4. Update DNS records as shown
5. Update frontend `REACT_APP_API_URL` to use custom domain

## Monitoring & Logs

View logs in Railway:
1. Project Dashboard
2. Click on the Python service
3. **Logs** tab shows real-time output

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Configure MongoDB
3. ✅ Set environment variables
4. ✅ Update Vercel frontend
5. Test full voting workflow:
   - Register as voter/admin
   - Login with OTP
   - Cast votes
   - View admin dashboard

## Support

- Railway Docs: https://docs.railway.app
- MongoDB in Railway: https://docs.railway.app/guides/mongodb
- Issues? Check Railway dashboard logs for detailed errors
