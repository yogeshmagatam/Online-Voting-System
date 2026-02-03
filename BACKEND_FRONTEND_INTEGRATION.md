# 🔗 Backend-Frontend Integration Guide

## Status: Backend Deploying to Railway ✅

Your backend is currently deploying to Railway. This guide will help you complete the integration.

---

## Step 1: Wait for Railway Deployment (In Progress)

**What's happening:**
- Docker image is being built
- Dependencies are being installed (pip requirements)
- Container is being pushed to Railway registry
- Service is being deployed

**Timeline:** 5-7 minutes total

**When it's done, you'll see:**
```
✅ Successfully deployed
Build Status: Green
```

---

## Step 2: Get Your Backend URL

Once deployment completes:

1. Go to: https://railway.app/dashboard
2. Click: "election-fraud-detection" project
3. Click: The Python service
4. Click: "Settings" tab
5. Scroll to: "Domains" section
6. Copy: The public URL (looks like `https://election-fraud-xyz.railway.app`)
7. **Save this URL** - you'll need it in Step 3

---

## Step 3: Update Vercel with Backend URL

### 3A. In Vercel Dashboard:

1. Go to: https://vercel.com/yogeshmagatams-projects/online-voting-system
2. Click: "Settings"
3. Click: "Environment Variables"
4. Find: `REACT_APP_API_URL`
5. Update the value with your Railway URL from Step 2
6. Click: "Save"

### 3B. Redeploy Frontend:

1. Go back to: "Deployments" tab
2. Click on: Latest deployment
3. Click: "Redeploy" button
4. Wait: For redeployment (1-2 minutes)

---

## Step 4: Test Integration

### 4A. Clear Browser Cache:
```
Open your site in Incognito/Private mode to ensure fresh load
Or press: Ctrl+Shift+Delete and clear cache
```

### 4B. Test Frontend-Backend Communication:

1. Go to: https://online-voting-system-six-flax.vercel.app
2. **Test Registration:**
   - Click "Register"
   - Fill in details
   - Submit
   - Check email for OTP
   - If email arrives → Backend is working! ✅

3. **Test Login:**
   - Enter OTP from email
   - Login should succeed
   - If login works → API communication is working! ✅

4. **Test Identity Verification:**
   - Proceed to identity verification
   - Take a photo
   - Upload should succeed
   - If upload works → Backend file handling is working! ✅

5. **Test Voting:**
   - Select a candidate
   - Submit vote
   - If vote is recorded → Full integration is working! ✅

6. **Test Admin Dashboard:**
   - Go to admin area
   - Check fraud detection data
   - If data shows → Database is working! ✅

---

## Environment Variables Reference

### Frontend (Vercel):
```
REACT_APP_API_URL = https://your-railway-backend.railway.app
```

### Backend (Railway):
```
FLASK_ENV = production
FLASK_DEBUG = False
SECRET_KEY = ZQNFBoyEWu43GKKXKEWiyth2gy_Ce9I412KXEch6gHY
JWT_SECRET_KEY = FKE29Vh4eno_8sqRevOJ96Yop0pCnWVxqTg8QPwfV9o
MAIL_USERNAME = yogeshmagatam@gmail.com
MAIL_PASSWORD = [Your Gmail app password]
MAIL_SERVER = smtp.gmail.com
MAIL_PORT = 587
MAIL_DEFAULT_SENDER = noreply@election.com
FRONTEND_ORIGIN = https://online-voting-system-six-flax.vercel.app
MONGO_URI = mongodb://mongodb:27017/election_fraud
RF_MODELS_DIR = /app/models/rf
```

---

## API Endpoints Your Frontend Will Call

These are automatically called by the React frontend:

```
POST   /register              → User registration
POST   /verify-otp           → Email OTP verification
POST   /login                → User login
POST   /generate-otp         → Generate OTP for login
POST   /identity-verify      → Upload identity photo
POST   /cast-vote            → Record a vote
GET    /get-fraud-stats      → Fraud detection analytics
GET    /get-admin-dashboard  → Admin statistics
POST   /logout               → Logout user
```

---

## Troubleshooting

### Issue: "Failed to fetch" errors in browser console

**Solution:**
1. Check Vercel has correct `REACT_APP_API_URL`
2. Check Railway URL is accessible
3. Check CORS is enabled in backend (it is by default)
4. Wait 2-3 minutes after Vercel redeploy for DNS to update

### Issue: "CORS error"

**Solution:**
The backend includes:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://online-voting-system-six-flax.vercel.app"],
        "allow_headers": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE"]
    }
})
```

If still getting CORS errors:
1. Hard refresh the page (Ctrl+Shift+R)
2. Check browser console for exact error
3. Verify Railway backend is running (check logs)

### Issue: "Email not received"

**Solution:**
1. Check Gmail app password is set correctly
2. Check MAIL_USERNAME is set in Railway
3. Check spam folder
4. Verify Gmail account is accessible from Railway region

### Issue: "Database connection error"

**Solution:**
If you need to add MongoDB:
1. Go to Railway dashboard
2. Click "+ Add Service"
3. Select "Add from Marketplace"
4. Find "MongoDB"
5. Click "Add"
6. Wait 2-3 minutes
7. Update `MONGO_URI` to use Railway MongoDB

---

## Architecture Overview

```
┌─────────────────────────────────┐
│   Browser (User)                │
└────────────┬────────────────────┘
             │
             │ HTTPS
             ▼
┌─────────────────────────────────┐
│   Vercel Frontend               │ ← React App + Next.js
│   (online-voting-system....)    │
└────────────┬────────────────────┘
             │
             │ API Calls (HTTPS)
             │ REACT_APP_API_URL
             ▼
┌─────────────────────────────────┐
│   Railway Backend               │ ← Flask API Server
│   (election-fraud-xyz.railway..) │
└────────────┬────────────────────┘
             │
             │ Database Connection
             ▼
┌─────────────────────────────────┐
│   MongoDB                       │ ← Managed by Railway
│   (Election Data Storage)       │
└─────────────────────────────────┘
```

---

## Integration Timeline

| Phase | Action | Time | Status |
|-------|--------|------|--------|
| Current | Backend Building | 5-7 min | ⏳ In Progress |
| Next | Get Backend URL | 1 min | ⏳ Waiting |
| Then | Update Vercel | 1 min | ⏳ Waiting |
| Then | Vercel Redeploy | 1-2 min | ⏳ Waiting |
| Final | Test Integration | 5 min | ⏳ Waiting |

**Total Time:** ~15 minutes from now

---

## How API Communication Works

When you register on the frontend:

```
1. Frontend → Vercel → Gets React app
2. User fills registration form
3. Frontend JavaScript → Makes POST to REACT_APP_API_URL/register
4. Request → Goes to Railway backend
5. Backend → Validates input, creates user in MongoDB
6. Backend → Sends email via Gmail SMTP
7. Backend → Returns response to Frontend
8. Frontend → Shows "Check your email"
```

---

## Quick Checklist

After your backend finishes deploying:

- [ ] Backend deployment complete (Railway shows GREEN)
- [ ] Got backend URL from Railway Domains
- [ ] Updated REACT_APP_API_URL in Vercel
- [ ] Clicked "Redeploy" in Vercel
- [ ] Vercel shows new deployment is done
- [ ] Visited frontend in new incognito tab
- [ ] Tested registration (OTP email arrived)
- [ ] Tested login with OTP
- [ ] Tested identity verification
- [ ] Tested vote casting
- [ ] Tested admin dashboard
- [ ] 🎉 INTEGRATION COMPLETE!

---

## Success Indicators

### Frontend loads successfully:
```
https://online-voting-system-six-flax.vercel.app loads without errors
```

### API calls work:
```
Browser Console → Network tab → Shows successful API calls
Status codes: 200, 201 (success)
```

### Email arrives:
```
Email received at the address you registered with
OTP format: 4 digits
Comes within 30 seconds of registration
```

### Votes are recorded:
```
Cast a vote → Page updates immediately
Go to admin dashboard → Vote appears in results
```

---

## You're Almost Done! 🎉

Your backend is deploying right now. In about 15 minutes total, your entire election system will be live with full frontend-backend integration!

**Current Status:**
- ✅ Frontend deployed on Vercel
- ⏳ Backend deploying to Railway (5-7 min)
- ⏳ Integration with Vercel (8-10 min)

Just follow the steps above as the backend finishes building, and you'll be fully integrated!
