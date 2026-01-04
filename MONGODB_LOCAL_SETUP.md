# MongoDB Local Setup Guide

## Current Status
Your backend is configured to use **local MongoDB** at `mongodb://localhost:27017/`

MongoDB is used for **optional enhanced logging** (security logs and behavioral logs). The main application data is stored in SQLite, so the app works fine without MongoDB.

## Quick Setup Options

### Option 1: Install MongoDB Locally (Recommended for Development)

#### Using Chocolatey (Easiest)
1. **Install Chocolatey** (if not installed):
   - Open PowerShell as Administrator
   - Run:
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force
     [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
     iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
     ```

2. **Install MongoDB**:
   ```powershell
   choco install mongodb -y
   ```

3. **Create data directory**:
   ```powershell
   mkdir C:\data\db
   ```

4. **Start MongoDB**:
   - Double-click `start_mongodb.bat` in the backend folder
   - Or run: `mongod` in terminal

#### Manual Installation
1. Download MongoDB Community Edition from: https://www.mongodb.com/try/download/community
2. Run the `.msi` installer
3. Choose "Complete" installation
4. Check "Install MongoDB as a Service" (recommended)
5. The service will start automatically

### Option 2: Use MongoDB Atlas (Cloud) - Requires DNS Fix

Your Atlas cluster has DNS resolution issues. To fix:

1. **Check network access**:
   - Go to https://cloud.mongodb.com/
   - Navigate to: Network Access → Add IP Address
   - Click "Allow Access from Anywhere" or add your current IP

2. **Test DNS resolution**:
   ```powershell
   nslookup _mongodb._tcp.cluster116454.sypvlt0.mongodb.net
   ```

3. **If DNS fails, use direct connection**:
   - Get node addresses from MongoDB Atlas Connect dialog
   - Update `.env` with the non-SRV connection string

4. **Use VPN** if your ISP blocks MongoDB DNS queries

### Option 3: Disable MongoDB (Already Works)

MongoDB is optional. Your app works perfectly without it using SQLite for all data storage.

## Verify MongoDB Connection

After starting MongoDB, restart your backend and check:
```
✓ MongoDB connected successfully: db='election_db'
```

If you see this message, MongoDB is working!

## Configuration File

Edit `backend/.env`:

```env
# Local MongoDB (current setting)
MONGODB_URI=mongodb://localhost:27017/

# OR MongoDB Atlas (if DNS is fixed)
# MONGODB_URI=mongodb+srv://username:password@cluster116454.sypvlt0.mongodb.net/?retryWrites=true&w=majority

MONGODB_DB_NAME=election_db
```

## What MongoDB Does in This Project

- **Security Logs**: Tracks login attempts, role access violations, etc.
- **Behavioral Logs**: Records user actions for analytics

All critical data (users, votes, candidates) is stored in SQLite, not MongoDB.

## Troubleshooting

### "mongod not recognized"
- MongoDB is not installed or not in PATH
- Restart terminal after installation
- Check installation: `mongod --version`

### Connection timeout
- MongoDB service not running
- Run `start_mongodb.bat` or start the Windows service

### Port already in use
- Another MongoDB instance is running
- Stop it: `taskkill /F /IM mongod.exe`
- Or use a different port in the connection string

## Quick Start (After Installation)

1. **Start MongoDB** (if not running as service):
   ```bash
   mongod
   ```

2. **Start your backend**:
   ```bash
   python app.py
   ```

3. **Check for success message**:
   ```
   ✓ MongoDB connected successfully: db='election_db'
   ```

That's it! Your backend now has MongoDB integrated for enhanced logging.
