#!/usr/bin/env python3
"""
Gmail OTP Configuration Setup Script
This script helps configure Gmail SMTP settings for the Election System
"""

import os
import sys
from pathlib import Path

def print_banner():
    print("\n" + "="*70)
    print("Election System - Gmail OTP Configuration Setup")
    print("="*70 + "\n")

def check_env_file():
    """Check if .env file exists in backend directory"""
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    return env_file

def create_env_file(env_file, mail_username, mail_password):
    """Create or update .env file with Gmail configuration"""
    try:
        # Create backend directory if it doesn't exist
        env_file.parent.mkdir(parents=True, exist_ok=True)
        
        env_content = f"""# Gmail Configuration for OTP Emails
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME={mail_username}
MAIL_PASSWORD={mail_password}
MAIL_DEFAULT_SENDER={mail_username}

# Optional: Other security settings
# Set to 'true' for development, 'false' for production
ALLOW_AUTO_FACE_ENROLLMENT=true
ALLOW_ID_VERIFICATION_BYPASS=true
ALLOW_VOTER_VALIDATION_BYPASS=true
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✓ .env file created/updated at: {env_file}")
        return True
    except Exception as e:
        print(f"✗ Error creating .env file: {e}")
        return False

def set_system_env_vars(mail_username, mail_password):
    """Set system environment variables"""
    try:
        os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
        os.environ['MAIL_PORT'] = '587'
        os.environ['MAIL_USERNAME'] = mail_username
        os.environ['MAIL_PASSWORD'] = mail_password
        os.environ['MAIL_DEFAULT_SENDER'] = mail_username
        
        print("✓ Environment variables set for current session")
        return True
    except Exception as e:
        print(f"✗ Error setting environment variables: {e}")
        return False

def validate_email(email):
    """Validate email format"""
    if '@' in email and '.' in email:
        return True
    return False

def validate_app_password(app_password):
    """Validate app password format (should be 16 characters without spaces)"""
    cleaned = app_password.replace(" ", "")
    if len(cleaned) == 16 and cleaned.isalnum():
        return True
    return False

def main():
    print_banner()
    
    # Get Gmail credentials from user
    print("Please provide your Gmail configuration.\n")
    
    while True:
        mail_username = input("Gmail Address (example@gmail.com): ").strip()
        if validate_email(mail_username):
            break
        else:
            print("✗ Invalid email format. Please try again.\n")
    
    print("\nNote: This should be your App Password from Google Account settings,")
    print("NOT your regular Gmail password.\n")
    
    while True:
        mail_password = input("App Password (16-character from Google Account): ").strip()
        if validate_app_password(mail_password):
            break
        else:
            print("✗ Invalid app password format. Should be 16 alphanumeric characters.")
            print("   Remove any spaces if present.\n")
    
    print("\n" + "="*70)
    print("Configuration Summary:")
    print("="*70)
    print(f"Gmail Address: {mail_username}")
    print(f"App Password: {'*' * (len(mail_password) - 4) + mail_password[-4:]}")
    print(f"SMTP Server: smtp.gmail.com")
    print(f"SMTP Port: 587")
    print("="*70 + "\n")
    
    # Ask which setup method to use
    print("Choose configuration method:\n")
    print("1. Create .env file (Recommended for development)")
    print("2. Set system environment variables (Requires admin/sudo)")
    print("3. Both")
    print("4. Cancel\n")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == '1':
        env_file = check_env_file()
        if create_env_file(env_file, mail_username, mail_password):
            print("\n✓ Setup complete! The .env file will be used when you run the Flask app.")
            print(f"  Location: {env_file}")
    
    elif choice == '2':
        if set_system_env_vars(mail_username, mail_password):
            print("\n✓ Setup complete for current session!")
            print("  Note: These changes are temporary. Restart terminal for new session.")
            if sys.platform == 'win32':
                print("  For permanent setup on Windows, use: setup_gmail_otp.bat")
    
    elif choice == '3':
        env_file = check_env_file()
        env_created = create_env_file(env_file, mail_username, mail_password)
        set_created = set_system_env_vars(mail_username, mail_password)
        
        if env_created and set_created:
            print("\n✓ Setup complete! Both methods configured.")
    
    elif choice == '4':
        print("Setup cancelled.")
        sys.exit(0)
    else:
        print("✗ Invalid choice. Setup cancelled.")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("Next Steps:")
    print("="*70)
    print("1. Start the Flask backend: python backend/app.py")
    print("2. Start the React frontend: npm start (from frontend directory)")
    print("3. Attempt to login through the web interface")
    print("4. Check your Gmail inbox for the OTP code")
    print("5. Enter the OTP to complete login")
    print("\nFor issues, see: GMAIL_OTP_SETUP.md")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
