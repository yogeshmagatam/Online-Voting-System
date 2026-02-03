╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   🚀 RAILWAY DEPLOYMENT - YOUR CHECKLIST                    ║
║                                                                              ║
║                    Generated Keys (Copy these!)                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ YOUR GENERATED SECURE KEYS - SAVE THESE NOW!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECRET_KEY:
juR650sTZTQ_PHRMAfJLHAAfV8KQ1VjWuOFnuj8sA-E

JWT_SECRET_KEY:
tOgoxds7DSyCXhnvVAk7zfGdkLsAPzEpebezbR4xKLQ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 DEPLOYMENT CHECKLIST
════════════════════════════════════════════════════════════════════════════════

STEP 1: Go to Railway Dashboard
  ☐ Open: https://railway.app/dashboard
  ☐ You should see your project "election-fraud-detection"
  ☐ Click to enter the project

STEP 2: Add Python Service from GitHub
  ☐ Click "+ Add Service" button
  ☐ Select "GitHub Repo"
  ☐ Search: "yogeshmagatam/Online-Voting-System"
  ☐ Select the repo
  ☐ Branch: "feature/yogesh/login"
  ☐ Wait 5-10 minutes for build
  ☐ Verify: Status shows "Running" (green)
  ☐ Check: No build errors in logs

STEP 3: Add MongoDB Database
  ☐ Click "+ Add Service" in your project
  ☐ Click "Add from Marketplace"
  ☐ Search: "MongoDB"
  ☐ Click "Add"
  ☐ Wait 2-3 minutes for provisioning
  ☐ Verify: MongoDB status is "Ready"

STEP 4: Configure Environment Variables
  ☐ Click on Python service
  ☐ Go to "Variables" tab
  ☐ Add each variable (click "New Variable"):

    ☐ FLASK_ENV = production
    ☐ FLASK_DEBUG = False
    ☐ SECRET_KEY = juR650sTZTQ_PHRMAfJLHAAfV8KQ1VjWuOFnuj8sA-E
    ☐ JWT_SECRET_KEY = tOgoxds7DSyCXhnvVAk7zfGdkLsAPzEpebezbR4xKLQ
    ☐ MAIL_USERNAME = [YOUR GMAIL HERE]
    ☐ MAIL_PASSWORD = [YOUR APP PASSWORD HERE]
    ☐ MAIL_DEFAULT_SENDER = noreply@election.com
    ☐ MAIL_SERVER = smtp.gmail.com
    ☐ MAIL_PORT = 587
    ☐ FRONTEND_ORIGIN = https://online-voting-system-six-flax.vercel.app
    ☐ MONGO_URI = ${{Mongo.MONGO_URL}}
    ☐ RF_MODELS_DIR = /app/models/rf

  ☐ Click "Deploy" button to apply variables
  ☐ Wait for service to restart

STEP 5: Get Your Backend URL
  ☐ Click Python service
  ☐ Go to "Settings" tab
  ☐ Find "Domains" section
  ☐ Copy the URL (format: https://your-app-xxxx.railway.app)
  ☐ SAVE THIS URL! You'll need it next

STEP 6: Update Frontend with Backend URL
  ☐ Go to: https://vercel.com/yogeshmagatams-projects/online-voting-system
  ☐ Click "Settings" tab
  ☐ Click "Environment Variables"
  ☐ Find "REACT_APP_API_URL"
  ☐ Update value = [YOUR RAILWAY URL]
  ☐ Click "Save"
  ☐ Go to "Deployments" tab
  ☐ Click latest deployment
  ☐ Click "Redeploy"
  ☐ Wait for redeploy to finish

STEP 7: Test the Application
  ☐ Go to: https://online-voting-system-six-flax.vercel.app
  ☐ Click "Register"
  ☐ Fill in registration form
  ☐ Click "Register"
  ☐ Check your email for OTP code
  ☐ Enter OTP and login
  ☐ Click "Verify Identity"
  ☐ Take a photo (or upload)
  ☐ Click "Cast Vote"
  ☐ Select candidate and vote
  ☐ Verify vote was recorded
  ☐ Go to Admin Dashboard
  ☐ Check fraud detection is working

STEP 8: Verify Everything Works
  ☐ No CORS errors in browser console
  ☐ Email OTP received successfully
  ☐ Login successful
  ☐ Vote recorded in database
  ☐ Admin dashboard shows voting data
  ☐ Fraud detection alerts present

════════════════════════════════════════════════════════════════════════════════

🔑 GETTING YOUR GMAIL APP PASSWORD

If you don't have it yet:
  1. Go to: https://myaccount.google.com/security
  2. Enable 2FA if not already done
  3. Go to: https://myaccount.google.com/apppasswords
  4. Select "Mail" and "Windows Computer"
  5. Click "Generate"
  6. Copy the 16-character password
  7. Use that as MAIL_PASSWORD in step 4

════════════════════════════════════════════════════════════════════════════════

📞 TROUBLESHOOTING

If build fails:
  → Check Railway logs for error messages
  → Most common: dependency issue - try redeploying
  → Check Dockerfile exists in backend folder

If MongoDB won't connect:
  → Wait 5 minutes for full provisioning
  → Verify MONGO_URI = ${{Mongo.MONGO_URL}} is set
  → Restart the service (click Redeploy)

If CORS errors appear:
  → Make sure FRONTEND_ORIGIN is set correctly
  → Should be exactly: https://online-voting-system-six-flax.vercel.app
  → Restart backend service

If email not sending:
  → Verify MAIL_USERNAME (Gmail address) is correct
  → Generate new app password - don't use main Gmail password
  → Ensure 2FA is enabled on Gmail

════════════════════════════════════════════════════════════════════════════════

✨ YOU'VE GOT THIS! 

Everything is ready. Just follow the 8 steps and your app will be live! 🚀

Need help? Check the Railway dashboard logs or re-read FINAL_DEPLOYMENT_STEPS.md

════════════════════════════════════════════════════════════════════════════════
