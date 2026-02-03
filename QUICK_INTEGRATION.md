# 🔗 QUICK INTEGRATION GUIDE

## Your Backend is Now Live! ✅

The Flask backend has been successfully deployed to Railway and is currently running.

---

## 3-Step Integration (Complete in ~5 minutes)

### ⏱️ Estimated Time: 5 minutes

### Step 1: Get Your Backend URL (1 minute)

```
1. Open: https://railway.app/dashboard
2. Click: "election-fraud-detection" project
3. Click: The Python service (labeled "election-fraud-detection")
4. Click: "Settings" tab
5. Find: "Domains" section
6. Copy: The public URL (starts with https://...)
```

**Example:** `https://online-voting-backend-xyz.railway.app`

**Save this URL** - You'll need it in Step 2

---

### Step 2: Update Vercel (2 minutes)

```
1. Open: https://vercel.com/yogeshmagatams-projects/online-voting-system
2. Click: "Settings" button
3. Click: "Environment Variables"
4. Find: Row with "REACT_APP_API_URL"
5. Click: The value field (current value)
6. Delete: Current value
7. Paste: Your Railway URL from Step 1
8. Click: "Save" button
```

**What you're setting:**
```
REACT_APP_API_URL = [Your Railway URL here]
```

---

### Step 3: Redeploy Vercel Frontend (2 minutes)

```
1. Go back to: Main dashboard
2. Click: "Deployments" tab
3. Find: Latest deployment
4. Click: On the deployment row
5. Click: "Redeploy" button
6. Wait: For green "Ready" status (usually 1-2 minutes)
```

**When ready:**
- Status changes to "Ready" ✅
- You get a success notification

---

## That's It! 🎉

Your backend and frontend are now integrated!

---

## Test Integration (5 minutes)

### Quick Test:

1. Open: https://online-voting-system-six-flax.vercel.app
2. Open DevTools: Press F12
3. Go to: Console tab
4. Refresh page: Press F5
5. Look for: No red errors should appear

### Full Functional Test:

1. Click: "Register"
2. Fill in:
   - Full Name: Your Name
   - Email: Your email
   - Password: Any password
3. Click: "Register"
4. Check: Your email for OTP
5. Copy: The 4-digit OTP
6. Go back to website
7. Paste: OTP
8. Click: "Login"

**If login works → Integration is successful!** ✅

Continue testing:
- Identity verification (take a photo)
- Vote casting
- Admin dashboard

---

## Need Help?

### "Failed to fetch" error?

1. Make sure you copied the FULL Railway URL
2. Make sure REACT_APP_API_URL was saved in Vercel
3. Wait 2-3 minutes for DNS to update
4. Hard refresh: Ctrl+Shift+R

### Backend URL not working?

1. Check Railway dashboard for service status
2. Should be green/running
3. If red, check logs for errors

### Email OTP not arriving?

1. Check spam folder
2. Check the email address is correct
3. Check Railway logs for mail errors
4. May need to set Gmail app password

---

## Your System is Now Live!

```
Frontend:  https://online-voting-system-six-flax.vercel.app ✅
Backend:   https://[your-railway-url].railway.app ✅
Database:  MongoDB (ready) ✅
```

**All integrated and ready to use!** 🚀

---

## Quick Links

- Railway Dashboard: https://railway.app/dashboard
- Vercel Dashboard: https://vercel.com/yogeshmagatams-projects/online-voting-system
- Your Frontend: https://online-voting-system-six-flax.vercel.app

---

**Start with Step 1 now!** 👆
