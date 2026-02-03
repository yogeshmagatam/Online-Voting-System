# Generate Secure Keys for Production

Use this Python script to generate secure random keys for your Railway deployment:

```python
import secrets
import string

# Generate SECRET_KEY
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")

# Generate JWT_SECRET_KEY
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET_KEY={jwt_secret}")

# Generate a random string for any purpose
random_string = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
print(f"RANDOM_STRING={random_string}")
```

Or use this one-liner in PowerShell:

```powershell
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32)); print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

Then add these to Railway Environment Variables.

## Gmail App Password

To get Gmail App Password:

1. Enable 2-Factor Authentication on your Google account
   - Go to https://myaccount.google.com/security
   - Turn on 2FA

2. Generate App Password
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Click "Generate"
   - Copy the 16-character password
   - Paste into Railway as MAIL_PASSWORD

## Important Security Notes

⚠️  **DO NOT:**
- Commit .env files to GitHub
- Share your SECRET_KEY or JWT_SECRET_KEY
- Use the same key for multiple services
- Use default/weak passwords

✅ **DO:**
- Generate new keys for each environment (dev, staging, production)
- Store keys securely in Railway Variables only
- Rotate keys periodically
- Use strong, random values (20+ characters)
