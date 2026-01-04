import multiprocessing
# Fix Windows multiprocessing freeze on import - must be before sklearn imports
if __name__ == '__main__':
    multiprocessing.freeze_support()
# Set spawn method to avoid scikit-learn/joblib hanging on Windows
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_access_cookies,
)
import os
from datetime import timedelta, datetime
import sqlite3
import pymongo
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import json
import hashlib
import uuid
import base64
from werkzeug.utils import secure_filename
import cv2
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except Exception as e:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not available:", e)
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import pyotp
import time
import re
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html
import bleach
import random
import string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps

app = Flask(__name__)
# Enable CORS with credentials so browsers can send cookies and Authorization headers
# Don't use * with credentials; use a specific origin (configurable via FRONTEND_ORIGIN)
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:3000')
CORS(app, supports_credentials=True, resources={r"/*": {"origins": FRONTEND_ORIGIN}})
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-for-development')

# Security configurations
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key-for-development')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
"""
For local development we enable both header and cookie JWTs and disable CSRF on cookies
to avoid 422 errors when the frontend doesn't send the CSRF header. In production,
set JWT_COOKIE_SECURE=True and JWT_COOKIE_CSRF_PROTECT=True.
"""
app.config['JWT_TOKEN_LOCATION'] = ["headers", "cookies"]
app.config['JWT_COOKIE_SECURE'] = False  # Dev: allow HTTP
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Dev: no CSRF header needed
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF
jwt = JWTManager(app)

# Dev feature flags
ALLOW_AUTO_FACE_ENROLLMENT = os.environ.get('ALLOW_AUTO_FACE_ENROLLMENT', 'true').lower() == 'true'
ALLOW_ID_VERIFICATION_BYPASS = os.environ.get('ALLOW_ID_VERIFICATION_BYPASS', 'true').lower() == 'true'
# Dev flag: allow bypassing strict voter master list validation
ALLOW_VOTER_VALIDATION_BYPASS = os.environ.get('ALLOW_VOTER_VALIDATION_BYPASS', 'true').lower() == 'true'
# ------------------------------
# MongoDB (optional integration)
# ------------------------------
# Read proper environment variables; do not hardcode the URI as a key
# See MONGODB_SETUP.md for configuration details
MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME', 'election_db')

mongo_client = None
mongo_db = None
MONGO_AVAILABLE = False

if MONGODB_URI:
    try:
        # Increase timeout for slower connections
        mongo_client = pymongo.MongoClient(
            MONGODB_URI, 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        # Ping to confirm connectivity
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[MONGODB_DB_NAME]
        MONGO_AVAILABLE = True
        print(f"✓ MongoDB connected successfully: db='{MONGODB_DB_NAME}'")
    except Exception as e:
        print(f"⚠ MongoDB not available (app will work without it): {e}")
        print("  → To fix: Install local MongoDB or check network/firewall settings")

# Health endpoint to quickly verify MongoDB config/connectivity
@app.route('/api/health', methods=['GET'])
def health():
    mongo_configured = bool(MONGODB_URI)
    mongo_connected = False
    mongo_error = None
    try:
        if mongo_configured and mongo_client is not None:
            mongo_client.admin.command('ping')
            mongo_connected = True
    except Exception as e:
        mongo_error = str(e)
    return jsonify({
        'status': 'ok',
        'mongo_configured': mongo_configured,
        'mongo_connected': mongo_connected,
        'mongo_error': mongo_error
    })


# Helpful JWT error messages to diagnose 422s
@jwt.unauthorized_loader
def handle_missing_jwt(err_msg):
    return jsonify({"error": "Missing or invalid authentication token", "detail": err_msg}), 401

@jwt.invalid_token_loader
def handle_invalid_jwt(err_msg):
    return jsonify({"error": "Invalid authentication token", "detail": err_msg}), 422

@jwt.expired_token_loader
def handle_expired_jwt(jwt_header, jwt_payload):
    return jsonify({"error": "Token expired"}), 401

# Email configuration for MFA
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'xxxx xxxx xxxx xxxx')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'election-system@example.com')

# Rate limiting - Enhanced for security
# Flask-Limiter v3+ expects key_func as the first positional arg; to avoid ambiguity, use init_app
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
limiter.init_app(app)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; object-src 'none'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Role-based access control decorator
def role_required(*allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role not in allowed_roles:
                log_security_event('unauthorized_role_access', {
                    'username': current_user,
                    'user_role': user_role,
                    'required_roles': list(allowed_roles),
                    'endpoint': request.endpoint,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                return jsonify({"error": "Unauthorized: insufficient permissions"}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'user_photos'), exist_ok=True)

# Encryption key for vote data
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
fernet = Fernet(ENCRYPTION_KEY)

# Homomorphic encryption for vote tallying
class HomomorphicVoteEncryption:
    def __init__(self):
        # In a real implementation, this would use a proper homomorphic encryption library
        # For this demo, we'll simulate homomorphic properties with a simplified approach
        self.public_key = os.environ.get('HE_PUBLIC_KEY', str(uuid.uuid4()))
        self.private_key = os.environ.get('HE_PRIVATE_KEY', str(uuid.uuid4()))
    
    def encrypt_vote(self, vote_data):
        """Encrypt vote data and return (encrypted_str, metadata).

        encrypted_str is a UTF-8 string suitable for storing in TEXT columns.
        metadata contains blinded fields for simple tallying.
        """
        vote_json = json.dumps(vote_data)
        encrypted_bytes = fernet.encrypt(vote_json.encode())
        encrypted_str = encrypted_bytes.decode('utf-8')

        metadata = {
            'candidate_id': self._blind_value(vote_data.get('candidate_id')),
            'precinct': self._blind_value(vote_data.get('precinct')),
            'timestamp': datetime.now().isoformat(),
            'public_key_id': self.public_key[:8]
        }
        return encrypted_str, metadata
    
    def decrypt_vote(self, encrypted_str):
        """Decrypt vote data from stored string"""
        if not encrypted_str:
            return None
        decrypted = fernet.decrypt(encrypted_str.encode('utf-8')).decode()
        return json.loads(decrypted)
    
    def tally_votes(self, encrypted_votes, group_by='candidate_id'):
        """Tally votes without decrypting individual votes"""
        # In a real homomorphic system, this would use homomorphic properties
        # Here we use the metadata which allows counting without full decryption
        tally = {}
        
        for vote in encrypted_votes:
            if 'homomorphic_metadata' not in vote:
                continue
                
            metadata = vote['homomorphic_metadata']
            key = metadata.get(group_by)
            
            if key not in tally:
                tally[key] = 0
            
            tally[key] += 1
            
        return tally
    
    def _blind_value(self, value):
        """Create a blinded representation of a value that preserves equality"""
        if value is None:
            return None
        
        # In a real implementation, this would use homomorphic encryption
        # Here we use a deterministic hash that preserves equality
        return hashlib.sha256(f"{value}{self.public_key}".encode()).hexdigest()

# Initialize homomorphic encryption
homomorphic_encryption = HomomorphicVoteEncryption()

# Security logging system
def log_security_event(event_type, event_data=None, level=None, metadata=None):
    """Log security events to database and file.

    Supports both dict and message-style usage:
      - log_security_event('type', { ... })
      - log_security_event('type', 'message text', 'info'|'error'|'warning'|'critical', metadata={...})
    """
    try:
        # Create timestamp
        timestamp = datetime.now().isoformat()

        # Normalize event_data
        if isinstance(event_data, dict):
            data = dict(event_data)
        else:
            data = {}
            if event_data is not None:
                data['message'] = str(event_data)
            if level:
                data['level'] = level
            if metadata:
                data['metadata'] = metadata

        # Enrich with request context if available
        try:
            ip_addr = request.remote_addr if request else None
            ua = request.headers.get('User-Agent', '') if request else None
        except RuntimeError:
            ip_addr, ua = None, None

        data.setdefault('ip_address', ip_addr)
        data.setdefault('user_agent', ua)
        data['timestamp'] = timestamp

        # Convert event data to JSON
        event_json = json.dumps(data)

    # Log to database (SQLite)
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            )
        ''')

        conn.execute(
            'INSERT INTO security_logs (timestamp, event_type, event_data, ip_address, user_agent) VALUES (?, ?, ?, ?, ?)',
            (timestamp, event_type, event_json, data.get('ip_address'), data.get('user_agent'))
        )
        conn.commit()
        conn.close()

        # Also log to MongoDB if available
        try:
            if MONGO_AVAILABLE:
                mongo_db.security_logs.insert_one({
                    'timestamp': timestamp,
                    'event_type': event_type,
                    'data': data
                })
        except Exception as me:
            print(f"Mongo security log error: {me}")

        # Log to file with rotation
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"security_{datetime.now().strftime('%Y-%m-%d')}.log")

        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] [{event_type}] {event_json}\n")

        return True
    except Exception as e:
        print(f"Error logging security event: {e}")
        return False

# Helper functions for security
# Helper functions for security
def generate_4digit_otp():
    """Generate a random 4-digit OTP code"""
    return ''.join(random.choices(string.digits, k=4))

def send_email_otp(email, otp):
    """Send OTP via email for MFA
    
    This function sends a 4-digit OTP code to the user's Gmail address.
    
    Args:
        email: Recipient email address
        otp: 4-digit OTP code to send
        
    Returns:
        Boolean: True if email sent successfully, False otherwise
    """
    try:
        # Validate email format
        if not email or '@' not in email:
            log_security_event('email_otp_invalid_email', {
                'email': email,
                'ip_address': request.remote_addr if request else 'unknown',
                'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
            })
            print(f"Error sending email: Invalid email address {email}")
            return False
        
        # Check if we're in development mode without real credentials
        if app.config['MAIL_USERNAME'] in ['your@gmail.com', 'your-email@gmail.com'] or \
           app.config['MAIL_PASSWORD'] in ['xxxx xxxx xxxx xxxx', 'your-app-password']:
            # Development mode - log the OTP for testing
            print(f"\n{'='*70}")
            print(f"DEVELOPMENT MODE - OTP EMAIL WOULD BE SENT TO: {email}")
            print(f"{'='*70}")
            print(f"OTP CODE: {otp}")
            print(f"Expiration: 10 minutes")
            print(f"{'='*70}\n")
            
            log_security_event('email_otp_dev_mode', {
                'email': email,
                'otp_code': otp,
                'ip_address': request.remote_addr if request else 'unknown',
                'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
            })
            
            return True
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your Election System Verification Code'
        msg['From'] = app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = email
        
        # Create HTML body with professional styling
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; color: #333; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
              .content {{ padding: 20px; background-color: #f9f9f9; }}
              .otp-code {{ 
                background-color: #ecf0f1; 
                padding: 20px; 
                font-size: 32px; 
                font-family: monospace; 
                letter-spacing: 8px; 
                text-align: center; 
                border-radius: 5px;
                margin: 20px 0;
              }}
              .footer {{ color: #7f8c8d; font-size: 12px; margin-top: 20px; }}
              .warning {{ color: #e74c3c; font-weight: bold; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h1>Election System Verification</h1>
              </div>
              <div class="content">
                <h2>Your Verification Code</h2>
                <p>Use the following code to complete your login to the Secure Election System:</p>
                <div class="otp-code">{otp}</div>
                <p><strong>Important:</strong></p>
                <ul>
                  <li>This code will expire in <strong>10 minutes</strong></li>
                  <li>Never share this code with anyone</li>
                  <li>The system will never ask for this code via email</li>
                </ul>
                <p class="warning">If you didn't request this code, please ignore this email and your account will remain secure.</p>
              </div>
              <div class="footer">
                <p>This is an automated message from the Secure Election System. Please do not reply to this email.</p>
                <p>© 2025 Election System. All rights reserved.</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        # Attach HTML content
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email via Gmail SMTP
        print(f"Attempting to send OTP email to {email}...")
        
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            # Enable TLS encryption
            server.starttls()
            
            # Login to Gmail account
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            
            # Send the email
            server.send_message(msg)
        
        print(f"OTP email successfully sent to {email}")
        
        # Log successful email sending event
        log_security_event('email_otp_sent', {
            'email': email,
            'recipient': email,
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        
        return True
        
    except smtplib.SMTPAuthenticationError as auth_error:
        error_msg = "Gmail authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD."
        print(f"Authentication Error: {error_msg}")
        print(f"Details: {str(auth_error)}")
        
        log_security_event('email_otp_auth_failed', {
            'email': email,
            'error': 'SMTP Authentication failed',
            'mail_server': app.config['MAIL_SERVER'],
            'mail_port': app.config['MAIL_PORT'],
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        return False
        
    except smtplib.SMTPException as smtp_error:
        error_msg = f"SMTP Error: {str(smtp_error)}"
        print(f"Error sending email: {error_msg}")
        
        log_security_event('email_otp_smtp_failed', {
            'email': email,
            'error': error_msg,
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        return False
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"Error sending email: {error_msg}")
        
        # Log email sending failure
        log_security_event('email_otp_failed', {
            'email': email,
            'error': error_msg,
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        return False

def send_sms_otp(phone, otp):
    """Send OTP via SMS for MFA
    Note: This is a placeholder. In production, use Twilio, AWS SNS, or similar service.
    """
    try:
        # For development/demo, just log the OTP
        # In production, integrate with SMS service like Twilio
        print(f"SMS OTP for {phone}: {otp}")
        
        # Placeholder for actual SMS sending
        # Example with Twilio:
        # from twilio.rest import Client
        # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=f"Your Election System verification code is: {otp}",
        #     from_=TWILIO_PHONE_NUMBER,
        #     to=phone
        # )
        
        log_security_event('sms_otp_sent', {
            'phone': phone,
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        
        return True
    except Exception as e:
        log_security_event('sms_otp_failed', {
            'phone': phone,
            'error': str(e),
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        print(f"Error sending SMS: {e}")
        return False

def create_login_otp(user_id, contact_method, contact_value):
    """Create and store OTP for login verification
    
    Args:
        user_id: User ID
        contact_method: 'email' or 'phone'
        contact_value: Email or phone number
    
    Returns:
        Tuple: (otp_code, success)
    """
    try:
        otp_code = generate_4digit_otp()
        created_at = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()
        
        conn = get_db_connection()
        
        # Clear any existing unverified OTP for this user
        try:
            conn.execute(
                'DELETE FROM login_otp WHERE user_id = ? AND verified = 0',
                (user_id,)
            )
            conn.commit()
        except Exception as de:
            print(f"Error deleting old OTP: {de}")
            conn.rollback()
        
        # Insert new OTP
        try:
            conn.execute('''
                INSERT INTO login_otp (user_id, otp_code, otp_type, contact_value, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, otp_code, contact_method, contact_value, created_at, expires_at))
            
            conn.commit()
            print(f"OTP created successfully for user {user_id}: {otp_code}")
            conn.close()
            return otp_code, True
        except Exception as ie:
            print(f"Error inserting OTP: {ie}")
            conn.rollback()
            conn.close()
            raise
    except Exception as e:
        print(f"Error creating OTP: {e}")
        import traceback
        traceback.print_exc()
        log_security_event('otp_creation_failed', {
            'user_id': user_id,
            'error': str(e)
        })
        return None, False

def verify_login_otp(user_id, otp_code):
    """Verify OTP for login
    
    Args:
        user_id: User ID
        otp_code: 4-digit OTP code provided by user
    
    Returns:
        Boolean: True if valid, False if invalid
    """
    try:
        conn = get_db_connection()
        
        otp_record = conn.execute('''
            SELECT * FROM login_otp 
            WHERE user_id = ? AND verified = 0 
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id,)).fetchone()
        
        conn.close()
        
        if not otp_record:
            return False
        
        # Check if OTP has expired
        expires_at = datetime.fromisoformat(otp_record['expires_at'])
        if datetime.now() > expires_at:
            # Mark as expired
            conn = get_db_connection()
            conn.execute('DELETE FROM login_otp WHERE id = ?', (otp_record['id'],))
            conn.commit()
            conn.close()
            return False
        
        # Check if too many attempts
        if otp_record['attempts'] >= 3:
            conn = get_db_connection()
            conn.execute('DELETE FROM login_otp WHERE id = ?', (otp_record['id'],))
            conn.commit()
            conn.close()
            return False
        
        # Verify OTP code
        if otp_record['otp_code'] != str(otp_code):
            # Increment attempts
            conn = get_db_connection()
            conn.execute(
                'UPDATE login_otp SET attempts = attempts + 1 WHERE id = ?',
                (otp_record['id'],)
            )
            conn.commit()
            conn.close()
            return False
        
        # Mark OTP as verified
        conn = get_db_connection()
        conn.execute(
            'UPDATE login_otp SET verified = 1 WHERE id = ?',
            (otp_record['id'],)
        )
        conn.commit()
        conn.close()
        
        log_security_event('login_otp_verified', {
            'user_id': user_id,
            'otp_type': otp_record['otp_type']
        })
        
        return True
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        log_security_event('otp_verification_failed', {
            'user_id': user_id,
            'error': str(e)
        })
        return False

def hash_password(password, salt=None):
    """Hash password using bcrypt"""
    if salt is None:
        salt = bcrypt.gensalt()
    
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed, salt

def verify_password(stored_hash, provided_password, salt):
    """Verify password using bcrypt"""
    return bcrypt.checkpw(provided_password.encode(), stored_hash)

def sanitize_input(input_string):
    """Sanitize user input to prevent XSS"""
    return bleach.clean(input_string, strip=True)

# Database encryption and setup
class EncryptedDatabase:
    def __init__(self, db_path, key=None):
        self.db_path = db_path
        # Generate or use provided encryption key
        self.key = key if key else Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
    def encrypt(self, data):
        """Encrypt sensitive data before storing in database"""
        if data is None:
            return None
        return self.cipher.encrypt(json.dumps(data).encode())
    
    def decrypt(self, encrypted_data):
        """Decrypt data retrieved from database"""
        if encrypted_data is None:
            return None
        return json.loads(self.cipher.decrypt(encrypted_data).decode())

# Initialize database encryption
db_encryption = EncryptedDatabase('election.db', ENCRYPTION_KEY)

# Database setup with encryption support
def get_db_connection():
    conn = sqlite3.connect('election.db')
    conn.row_factory = sqlite3.Row
    
    # Add encryption/decryption functions to SQLite connection
    conn.create_function('encrypt', 1, db_encryption.encrypt)
    conn.create_function('decrypt', 1, db_encryption.decrypt)
    
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password BLOB NOT NULL,
        role TEXT NOT NULL,
        photo_path TEXT,
        face_encoding BLOB,
        mfa_secret TEXT,
        mfa_type TEXT DEFAULT 'app',
        email TEXT,
        phone TEXT,
        verified BOOLEAN DEFAULT 0,
        voter_id TEXT UNIQUE,
        national_id TEXT UNIQUE,
        failed_login_attempts INTEGER DEFAULT 0,
        last_login_attempt TEXT,
        account_locked BOOLEAN DEFAULT 0,
        lock_expiration TEXT,
        salt BLOB,
        last_password_change TEXT,
        require_password_change BOOLEAN DEFAULT 0
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS election_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        precinct TEXT NOT NULL,
        votes_candidate_a INTEGER NOT NULL,
        votes_candidate_b INTEGER NOT NULL,
        registered_voters INTEGER NOT NULL,
        turnout_percentage REAL NOT NULL,
        timestamp TEXT NOT NULL,
        flagged_suspicious BOOLEAN DEFAULT 0
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS master_voter_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voter_id TEXT UNIQUE NOT NULL,
        national_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        eligible BOOLEAN DEFAULT 1,
        verification_status TEXT DEFAULT 'unverified'
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE NOT NULL,
        encrypted_vote TEXT NOT NULL,
        homomorphic_metadata TEXT,
        timestamp TEXT NOT NULL,
        precinct TEXT NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS behavioral_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_id TEXT,
        action TEXT,
        timestamp TEXT,
        metadata TEXT,
        flagged_suspicious BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS login_otp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        otp_code TEXT NOT NULL,
        otp_type TEXT NOT NULL,
        contact_value TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        verified BOOLEAN DEFAULT 0,
        attempts INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Add admin user if not exists (use bcrypt)
    admin_row = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_row:
        # Hash default admin password with bcrypt
        hashed_password, salt = hash_password('admin@123456')  # both are bytes

        # Generate MFA secret
        mfa_secret = pyotp.random_base32()

        # For development, keep MFA disabled for admin to simplify login
        conn.execute(
            'INSERT INTO users (username, password, role, mfa_secret, mfa_type, salt, verified) VALUES (?, ?, ?, ?, ?, ?, ?)',
            ('admin', hashed_password, 'admin', mfa_secret, 'none', salt, 1)
        )
    else:
        # Always update admin password to ensure it's correct
        try:
            new_hashed, new_salt = hash_password('admin@123456')
            conn.execute(
                'UPDATE users SET password = ?, salt = ?, mfa_type = ? WHERE username = ?',
                (new_hashed, new_salt, 'none', 'admin')
            )
            print("Admin password updated to admin@123456")
        except Exception as e:
            print(f"Error updating admin password: {e}")
            pass

        # Ensure admin MFA is disabled in development for easier testing
        try:
            conn.execute('UPDATE users SET mfa_type = ? WHERE username = ?', ('none', 'admin'))
        except Exception:
            pass
    
    # Add some sample voter IDs to master list if not exists
    sample_voters = [
        ('VID12345', 'NID12345', 'John Doe'),
        ('VID67890', 'NID67890', 'Jane Smith'),
        ('VID24680', 'NID24680', 'Robert Johnson'),
        ('VID13579', 'NID13579', 'Emily Davis')
    ]
    
    for voter_id, national_id, name in sample_voters:
        voter_exists = conn.execute('SELECT 1 FROM master_voter_list WHERE voter_id = ?', (voter_id,)).fetchone()
        if not voter_exists:
            conn.execute('INSERT INTO master_voter_list (voter_id, national_id, name) VALUES (?, ?, ?)', (voter_id, national_id, name))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# ML Model for fraud detection
class FraudDetectionModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        
    def train(self, data):
        # Features for fraud detection
        features = ['votes_candidate_a', 'votes_candidate_b', 'registered_voters', 'turnout_percentage']
        X = data[features]
        
        # For demo purposes, we'll create a synthetic target
        # In a real system, you would have labeled data
        # Here we're flagging high turnout with imbalanced votes as suspicious
        y = (data['turnout_percentage'] > 85) & (abs(data['votes_candidate_a'] - data['votes_candidate_b']) / data['registered_voters'] > 0.4)
        
        X_scaled = self.scaler.fit_transform(X)
        
        # Need at least 5 samples for meaningful train/test split
        if len(X_scaled) < 5:
            # For small datasets, train on all data without split
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_scaled, y)
            return 1.0  # Perfect score on training data (for demo only)
        
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        return self.model.score(X_test, y_test)
    
    def predict(self, data):
        if self.model is None:
            return None
        
        features = ['votes_candidate_a', 'votes_candidate_b', 'registered_voters', 'turnout_percentage']
        X = data[features]
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def save_model(self, path='model.pkl'):
        if self.model is not None:
            with open(path, 'wb') as f:
                pickle.dump((self.model, self.scaler), f)
    
    def load_model(self, path='model.pkl'):
        try:
            with open(path, 'rb') as f:
                self.model, self.scaler = pickle.load(f)
            return True
        except:
            return False

# Initialize ML model
fraud_model = FraudDetectionModel()

# Routes
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_photo(photo_data):
    """Save base64 encoded photo data to file"""
    try:
        # Extract the base64 data
        if ';base64,' in photo_data:
            header, encoded = photo_data.split(';base64,')
            file_ext = header.split('/')[-1]
        else:
            encoded = photo_data
            file_ext = 'jpg'  # Default extension
        
        # Decode the base64 data
        decoded_data = base64.b64decode(encoded)
        
        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'user_photos', filename)
        
        # Save the file
        with open(file_path, 'wb') as f:
            f.write(decoded_data)
        
        return file_path
    except Exception as e:
        print(f"Error saving photo: {e}")
        return None

def extract_face_encoding(photo_path):
    """Extract face encoding from photo"""
    if not FACE_RECOGNITION_AVAILABLE:
        print("face_recognition unavailable: cannot extract face encodings. See backend/INSTALL_FACE_RECOGNITION.md")
        return None
    try:
        # Load the image
        image = face_recognition.load_image_file(photo_path)
        
        # Find all face encodings in the image
        face_encodings = face_recognition.face_encodings(image)
        
        # If no faces are found, return None
        if len(face_encodings) == 0:
            return None
        
        # Return the first face encoding
        return pickle.dumps(face_encodings[0])
    except Exception as e:
        print(f"Error extracting face encoding: {e}")
        return None

def _register_internal(role='voter'):
    # Check if form data or JSON
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
    
    # Get required fields
    username = sanitize_input(data.get('username', ''))
    password = data.get('password', '')
    voter_id = sanitize_input(data.get('voter_id', '')) if role == 'voter' else None
    # National ID is now optional (frontend removed field); accept if provided, otherwise None
    national_id = sanitize_input(data.get('national_id', '')) if data.get('national_id') else None
    email = sanitize_input(data.get('email', ''))
    phone = sanitize_input(data.get('phone', ''))
    captcha_response = data.get('captcha')
    
    # Get photo data
    photo_data = data.get('photo')
    
    # Validate required fields (national_id optional)
    if role == 'voter':
        if not all([username, password, voter_id, email, photo_data, captcha_response]):
            return jsonify({"error": "Missing required fields"}), 400
    else:
        if not all([username, password, email, photo_data, captcha_response]):
            return jsonify({"error": "Missing required fields"}), 400
    
    # Validate username (alphanumeric only)
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return jsonify({"error": "Username must be alphanumeric"}), 400
    
    # Validate password strength
    if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{12,}$', password):
        return jsonify({"error": "Password must be at least 12 characters and include letters, numbers, and special characters"}), 400
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({"error": "Invalid email format"}), 400
    
    # Verify captcha (in a real system, you would verify with a service like reCAPTCHA)
    # For demo purposes, we'll just check if it's not empty
    if not captcha_response:
        return jsonify({"error": "Captcha verification failed"}), 400
    
    conn = get_db_connection()
    
    try:
        # Check if username already exists
        existing_user = conn.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            conn.close()
            return jsonify({"error": "Username already exists"}), 409
        
        if role == 'voter':
            # Check if voter ID exists in master list and is eligible (national_id no longer required)
            voter = conn.execute('SELECT * FROM master_voter_list WHERE voter_id = ? AND eligible = 1', 
                                (voter_id,)).fetchone()
            if not voter:
                if ALLOW_VOTER_VALIDATION_BYPASS:
                    try:
                        # Auto-enroll voter in development to unblock flow
                        auto_national = national_id if national_id else f"AUTO-{uuid.uuid4().hex[:8]}"
                        conn.execute('''
                            INSERT INTO master_voter_list (voter_id, national_id, name, eligible, verification_status)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (voter_id, auto_national, 'Auto Enrolled', 1, 'registered'))
                        voter = conn.execute('SELECT * FROM master_voter_list WHERE voter_id = ?', (voter_id,)).fetchone()
                    except Exception as ie:
                        conn.close()
                        return jsonify({"error": f"Voter enrollment failed: {str(ie)}"}), 500
                else:
                    conn.close()
                    return jsonify({"error": "Invalid or ineligible voter ID"}), 400
        
        if role == 'voter':
            # Check if voter ID is already registered
            registered_voter = conn.execute('SELECT 1 FROM users WHERE voter_id = ?', (voter_id,)).fetchone()
            if registered_voter:
                conn.close()
                return jsonify({"error": "Voter ID already registered"}), 409
        
        # National ID uniqueness check is skipped since it's optional/removed
        
        # Save photo
        photo_path = save_photo(photo_data)
        if not photo_path:
            conn.close()
            return jsonify({"error": "Failed to save photo"}), 500
        
        # Extract face encoding (optional if face_recognition is unavailable)
        face_encoding = None
        if FACE_RECOGNITION_AVAILABLE:
            face_encoding = extract_face_encoding(photo_path)
            if not face_encoding:
                conn.close()
                return jsonify({"error": "No face detected in photo"}), 400
        
        # Hash password with bcrypt
        hashed_password, salt = hash_password(password)
        
        # Generate MFA secret
        mfa_secret = pyotp.random_base32()
        
        # Determine MFA type
        mfa_type = data.get('mfa_type', 'app')  # Default to app-based
        if mfa_type not in ['app', 'email', 'sms']:
            mfa_type = 'app'  # Fallback to app if invalid type
        
        # Current timestamp for password change tracking
        current_time = datetime.now().isoformat()
        
      # Register new user with specified role
        conn.execute('''
            INSERT INTO users (username, password, role, photo_path, face_encoding, 
                              mfa_secret, mfa_type, voter_id, national_id, email, phone, salt, last_password_change) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ''', (username, hashed_password, role, photo_path, face_encoding, 
          mfa_secret, mfa_type, voter_id, national_id, email, phone, salt, current_time))
        
        # Update verification status in master voter list for voters only
        if role == 'voter' and voter_id:
            conn.execute(
                'UPDATE master_voter_list SET verification_status = ? WHERE voter_id = ?',
                ('registered', voter_id)
            )
        
        conn.commit()
        
        # Generate QR code for MFA setup
        totp = pyotp.TOTP(mfa_secret)
        provisioning_uri = totp.provisioning_uri(username, issuer_name="Secure Election System")
        
        # If email-based MFA, send initial verification email
        if mfa_type == 'email':
            otp = totp.now()
            send_email_otp(email, otp)
        
        return jsonify({
            "message": "User registered successfully. Please set up MFA.",
            "mfa_secret": mfa_secret if mfa_type == 'app' else None,
            "mfa_uri": provisioning_uri if mfa_type == 'app' else None,
            "mfa_type": mfa_type
        }), 201
        
    except Exception as e:
        conn.rollback()
        print(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500
    
    finally:
        conn.close()

@app.route('/api/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    return _register_internal('voter')

@app.route('/api/register/voter', methods=['POST'])
@limiter.limit("10 per hour")
def register_voter():
    return _register_internal('voter')

@app.route('/api/register/candidate', methods=['POST'])
@limiter.limit("10 per hour")
def register_candidate():
    return _register_internal('candidate')

def log_behavior(user_id, action, metadata=None):
    """Log user behavior for anomaly detection"""
    try:
        conn = get_db_connection()
        session_id = request.cookies.get('session_id', str(uuid.uuid4()))
        
        conn.execute('''
            INSERT INTO behavioral_logs (user_id, session_id, action, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_id, action, datetime.now().isoformat(), json.dumps(metadata or {})))
        
        conn.commit()
        conn.close()
        
        # Mirror to MongoDB if available
        try:
            if MONGO_AVAILABLE:
                mongo_db.behavioral_logs.insert_one({
                    'user_id': user_id,
                    'session_id': session_id,
                    'action': action,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata or {},
                    'ip_address': request.remote_addr if request else None,
                    'user_agent': request.headers.get('User-Agent', '') if request else None
                })
        except Exception as me:
            print(f"Mongo behavioral log error: {me}")
        return session_id
    except Exception as e:
        print(f"Error logging behavior: {e}")
        return None

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
    
    # Sanitize inputs
    username = sanitize_input(data.get('username', ''))
    password = data.get('password', '')
    mfa_code = sanitize_input(data.get('mfa_code', ''))
    mfa_type = sanitize_input(data.get('mfa_type', 'app'))
    
    if not username or not password:
        log_security_event('login_attempt_missing_fields', {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'provided_fields': list(data.keys())
        })
        return jsonify({"error": "Missing username or password"}), 400
    
    conn = get_db_connection()
    
    try:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        # Check if user exists
        if user is None:
            log_security_event('login_attempt_invalid_username', {
                'username': username,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Check if account is locked
        if user['account_locked'] == 1:
            lock_expiration = datetime.fromisoformat(user['lock_expiration']) if user['lock_expiration'] else None
            
            if lock_expiration and datetime.now() < lock_expiration:
                remaining_time = int((lock_expiration - datetime.now()).total_seconds() / 60)
                
                log_security_event('login_attempt_locked_account', {
                    'username': username,
                    'user_id': user['id'],
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'lock_expiration': user['lock_expiration']
                })
                
                conn.close()
                return jsonify({
                    'error': f'Account locked due to too many failed attempts. Try again in {remaining_time} minutes.'
                }), 403
            else:
                # Reset account lock if lock period has expired
                conn.execute('''
                    UPDATE users 
                    SET account_locked = 0, 
                        lock_expiration = NULL, 
                        failed_login_attempts = 0 
                    WHERE id = ?
                ''', (user['id'],))
                conn.commit()
        
        # Check for too many failed login attempts
        now = datetime.now()
        if user['failed_login_attempts'] >= 5:
            # Lock account for 30 minutes
            lock_expiration = datetime.now() + timedelta(minutes=30)
            
            conn.execute('''
                UPDATE users 
                SET account_locked = 1, 
                    lock_expiration = ? 
                WHERE id = ?
            ''', (lock_expiration.isoformat(), user['id']))
            
            conn.commit()
            
            log_security_event('account_locked', {
                'username': username,
                'user_id': user['id'],
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'lock_expiration': lock_expiration.isoformat(),
                'reason': 'Too many failed login attempts'
            })
            
            conn.close()
            return jsonify({'error': 'Account locked due to too many failed attempts. Try again in 30 minutes.'}), 403
        
        # Verify password using bcrypt
        stored_hash = user['password']
        salt = user['salt']
        
        if not verify_password(stored_hash, password, salt):
            # Increment failed login attempts
            conn.execute('''
                UPDATE users 
                SET failed_login_attempts = failed_login_attempts + 1, 
                    last_login_attempt = ? 
                WHERE id = ?
            ''', (now.isoformat(), user['id']))
            
            conn.commit()
            
            log_security_event('login_attempt_invalid_password', {
                'username': username,
                'user_id': user['id'],
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'failed_attempts': user['failed_login_attempts'] + 1
            })
            
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Generate and send 4-digit OTP for login verification
        # If OTP code is not provided, generate and send one
        # SKIP OTP for admin users (faster access for monitoring)
        if not mfa_code and user['role'] != 'admin':
            # Generate 4-digit OTP
            otp_code = generate_4digit_otp()
            
            # Determine contact method - prefer email if available
            contact_method = 'email'
            contact_value = user['email']
            
            # If email not available, try phone
            if not contact_value and user.get('phone'):
                contact_method = 'phone'
                contact_value = user['phone']
            
            if not contact_value:
                log_security_event('login_otp_failed_no_contact', {
                    'username': username,
                    'user_id': user['id'],
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                conn.close()
                return jsonify({'error': 'No email or phone on file to send OTP'}), 400
            
            # Store OTP in database
            otp_code, success = create_login_otp(user['id'], contact_method, contact_value)
            
            if not success:
                conn.close()
                return jsonify({'error': 'Failed to generate OTP'}), 500
            
            # Send OTP via appropriate method
            try:
                if contact_method == 'email':
                    send_email_otp(contact_value, otp_code)
                    delivery_method = 'email'
                else:
                    send_sms_otp(contact_value, otp_code)
                    delivery_method = 'phone'
                
                log_security_event('login_otp_sent', {
                    'username': username,
                    'user_id': user['id'],
                    'otp_method': delivery_method,
                    'contact_value': contact_value[-4:] if len(contact_value) > 4 else '****',  # Log last 4 chars for privacy
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                
            except Exception as e:
                print(f"OTP delivery failed: {e}")
                log_security_event('login_otp_delivery_failed', {
                    'username': username,
                    'user_id': user['id'],
                    'otp_method': contact_method,
                    'error': str(e),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                conn.close()
                return jsonify({'error': 'Failed to send OTP'}), 500
            
            conn.close()
            return jsonify({
                'message': f'4-digit OTP sent to your {delivery_method}',
                'otp_required': True,
                'otp_delivery_method': delivery_method
            }), 200
        
        # Verify 4-digit OTP code if provided (only for non-admin users OR if admin explicitly provided OTP)
        if mfa_code and user['role'] != 'admin':
            # Validate OTP code
            otp_verified, error_msg = verify_login_otp(user['id'], mfa_code)
            
            if not otp_verified:
                # Increment failed login attempts on OTP failure
                conn.execute('''
                    UPDATE users 
                    SET failed_login_attempts = failed_login_attempts + 1, 
                        last_login_attempt = ? 
                    WHERE id = ?
                ''', (now.isoformat(), user['id']))
                
                conn.commit()
                
                log_security_event('login_attempt_invalid_otp', {
                    'username': username,
                    'user_id': user['id'],
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'failed_attempts': user['failed_login_attempts'] + 1,
                    'error': error_msg
                })
                
                conn.close()
                return jsonify({"error": f"Invalid OTP: {error_msg}"}), 401
        elif user['role'] == 'admin' and not mfa_code and not user['verified']:
            # For admin users on first login, allow bypass of OTP requirement
            # This allows direct access to admin dashboard for monitoring
            pass
        
        # Reset failed login attempts on successful login
        conn.execute('''
            UPDATE users 
            SET failed_login_attempts = 0, 
                last_login_attempt = ?,
                account_locked = 0,
                lock_expiration = NULL
            WHERE id = ?
        ''', (now.isoformat(), user['id']))
        
        conn.commit()
        
        # Check if password change is required
        require_password_change = user['require_password_change'] == 1
        
        # Check password age if last_password_change is available
        password_expired = False
        if user['last_password_change']:
            last_change = datetime.fromisoformat(user['last_password_change'])
            password_age_days = (datetime.now() - last_change).days
            # Force password change after 90 days
            if password_age_days > 90:
                require_password_change = True
                password_expired = True
                
                # Update user record to require password change
                conn.execute('''
                    UPDATE users 
                    SET require_password_change = 1
                    WHERE id = ?
                ''', (user['id'],))
                conn.commit()
        
        # Log successful login behavior for anomaly detection
        session_id = log_behavior(user['id'], 'login', {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'timestamp': now.isoformat()
        })
        
        # Log successful login in security logs
        log_security_event('login_successful', {
            'username': username,
            'user_id': user['id'],
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        
        # Create access token with additional claims
        additional_claims = {
            'role': user['role'],
            'session_id': session_id,
            'jti': str(uuid.uuid4())  # Add unique token ID
        }
        
        access_token = create_access_token(
            identity=username,
            additional_claims=additional_claims
        )
        
        # Create response with enhanced security information
        response = jsonify({
            "access_token": access_token,
            "role": user['role'],
            "verified": bool(user['verified']),
            "require_password_change": require_password_change,
            "password_expired": password_expired
        })

        # Set JWT as an HttpOnly cookie as well (so subsequent requests work without Authorization header)
        # In dev, cookies are not secure and CSRF is disabled (configured above)
        set_access_cookies(response, access_token)

        # Keep a separate session_id cookie for behavior tracking if needed (non-sensitive)
        response.set_cookie(
            'session_id',
            session_id,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600
        )
        
        return response
        
    except Exception as e:
        print(f"Login error: {e}")
        log_security_event('login_error', {
            'username': username if username else 'unknown',
            'error': str(e),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        return jsonify({"error": "Login failed"}), 500
    
    finally:
        conn.close()

@app.route('/api/verify-login-otp', methods=['POST'])
@limiter.limit("5 per minute")
def verify_login_otp_endpoint():
    """
    Verify the 4-digit OTP code sent during login.
    
    Expected POST data:
    {
        "username": "user@example.com",
        "otp_code": "1234"
    }
    
    Returns:
    {
        "access_token": "jwt_token",
        "role": "voter|candidate|admin",
        "verified": true,
        ...
    }
    """
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
    
    # Get username and OTP code
    username = sanitize_input(data.get('username', ''))
    otp_code = sanitize_input(data.get('otp_code', ''))
    
    if not username or not otp_code:
        log_security_event('verify_otp_missing_fields', {
            'username': username if username else 'unknown',
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        return jsonify({"error": "Missing username or OTP code"}), 400
    
    # Validate OTP code is exactly 4 digits
    if not otp_code.isdigit() or len(otp_code) != 4:
        log_security_event('verify_otp_invalid_format', {
            'username': username,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        return jsonify({"error": "OTP must be exactly 4 digits"}), 400
    
    conn = get_db_connection()
    
    try:
        # Look up user
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user is None:
            log_security_event('verify_otp_invalid_username', {
                'username': username,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
            conn.close()
            return jsonify({"error": "Invalid username or OTP"}), 401
        
        # Verify the OTP code
        otp_verified = verify_login_otp(user['id'], otp_code)
        
        if not otp_verified:
            # Log failed OTP verification attempt
            log_security_event('verify_otp_invalid_code', {
                'username': username,
                'user_id': user['id'],
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'error': 'Invalid OTP code'
            })
            conn.close()
            return jsonify({"error": "Invalid OTP code"}), 401
        
        # Reset failed login attempts on successful OTP verification
        now = datetime.now()
        conn.execute('''
            UPDATE users 
            SET failed_login_attempts = 0, 
                last_login_attempt = ?,
                account_locked = 0,
                lock_expiration = NULL
            WHERE id = ?
        ''', (now.isoformat(), user['id']))
        
        conn.commit()
        
        # Log successful OTP verification
        log_security_event('verify_otp_successful', {
            'username': username,
            'user_id': user['id'],
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        
        # Log behavior for anomaly detection
        session_id = log_behavior(user['id'], 'otp_verified', {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'timestamp': now.isoformat()
        })
        
        # Create access token with role claim
        additional_claims = {
            'role': user['role'],
            'session_id': session_id,
            'jti': str(uuid.uuid4())  # Add unique token ID
        }
        
        access_token = create_access_token(
            identity=username,
            additional_claims=additional_claims
        )
        
        # Check if password change is required
        require_password_change = user['require_password_change'] == 1
        
        # Check password age if last_password_change is available
        password_expired = False
        if user['last_password_change']:
            last_change = datetime.fromisoformat(user['last_password_change'])
            password_age_days = (datetime.now() - last_change).days
            # Force password change after 90 days
            if password_age_days > 90:
                require_password_change = True
                password_expired = True
                
                # Update user record to require password change
                conn.execute('''
                    UPDATE users 
                    SET require_password_change = 1
                    WHERE id = ?
                ''', (user['id'],))
                conn.commit()
        
        # Create response with enhanced security information
        response = jsonify({
            "access_token": access_token,
            "role": user['role'],
            "verified": bool(user['verified']),
            "require_password_change": require_password_change,
            "password_expired": password_expired
        })

        # Set JWT as an HttpOnly cookie
        set_access_cookies(response, access_token)

        # Keep a separate session_id cookie for behavior tracking
        response.set_cookie(
            'session_id',
            session_id,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600
        )
        
        conn.close()
        return response
        
    except Exception as e:
        print(f"OTP verification error: {e}")
        log_security_event('verify_otp_error', {
            'username': username if username else 'unknown',
            'error': str(e),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        conn.close()
        return jsonify({"error": "OTP verification failed"}), 500

def detect_face_spoofing(image_path):
    """Detect if the face is from a spoof/fake source (photo, video, mask, etc.)
    
    Uses heuristics to detect:
    - Static images (liveness check)
    - Printed photos/screenshots
    - Screen replays
    - Masks or other spoofing attempts
    
    Returns:
        Tuple: (is_genuine, confidence_score, spoofing_indicators)
    """
    try:
        if not FACE_RECOGNITION_AVAILABLE:
            return None, 0, []
        
        image = face_recognition.load_image_file(image_path)
        
        # Detection heuristics
        spoofing_indicators = []
        
        # 1. Check for motion blur (indicates camera movement/liveness)
        # In a real implementation, compare with previous frame
        # For now, this is a placeholder for motion detection
        
        # 2. Check for unusual lighting patterns (reflection on glasses, face tracking)
        # More sophisticated: Use deep learning model for liveness detection
        
        # 3. Check if image dimensions are reasonable (not too small - screenshot)
        if image.shape[0] < 100 or image.shape[1] < 100:
            spoofing_indicators.append('image_too_small')
        
        # 4. Check color distribution (printed photos have different color distribution)
        # Placeholder: actual implementation would analyze color histogram
        
        # 5. Detect multiple faces (spoofing attempt with multiple photos)
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) > 1:
            spoofing_indicators.append('multiple_faces_detected')
        elif len(face_locations) == 0:
            spoofing_indicators.append('no_face_detected')
        
        # Calculate confidence: more indicators = lower confidence
        confidence_score = max(0, 1.0 - (len(spoofing_indicators) * 0.2))
        
        # If confidence is below threshold, it's likely a spoof
        is_genuine = confidence_score > 0.7
        
        return is_genuine, confidence_score, spoofing_indicators
        
    except Exception as e:
        print(f"Error in spoofing detection: {e}")
        return None, 0, ['detection_error']

def perform_liveness_check(image_path):
    """Perform liveness detection to ensure face is from a live person
    
    Returns:
        Tuple: (is_live, liveness_score, detection_method)
    """
    try:
        if not FACE_RECOGNITION_AVAILABLE:
            return None, 0, 'unavailable'
        
        image = face_recognition.load_image_file(image_path)
        
        # Basic liveness heuristics
        liveness_score = 0.5  # Default moderate confidence
        detection_method = 'heuristic'
        
        # Check for eye openness, mouth shape, face angle variation
        # (In production, use dedicated liveness detection library like antiface-spoofing)
        
        # For now, simulate liveness check by analyzing face landmarks
        # Real implementation would track:
        # - Eye blink frequency
        # - Mouth movements
        # - Head pose changes
        # - Texture analysis
        
        face_landmarks = face_recognition.face_landmarks(image)
        
        if face_landmarks:
            # Check if face is positioned naturally (not flat/direct spoof)
            # More landmarks = more expressive face = likely live
            num_landmarks = sum(len(points) for points in face_landmarks[0].values())
            
            # Normalize score (more landmarks = higher liveness)
            liveness_score = min(1.0, num_landmarks / 50.0)
        
        is_live = liveness_score > 0.6
        
        return is_live, liveness_score, detection_method
        
    except Exception as e:
        print(f"Error in liveness check: {e}")
        return None, 0, 'error'

@app.route('/api/verify-identity', methods=['POST'])
@jwt_required()
def verify_identity():
    """
    Verify user identity using face recognition with fraud detection.
    
    Expected POST data:
    {
        "live_photo": "base64_encoded_image_data",
        "camera_source": "webcam|file_upload"  (optional)
    }
    
    Returns:
    {
        "message": "Identity verified successfully",
        "verified": true,
        "face_match_confidence": 0.95,
        "liveness_score": 0.87,
        "fraud_indicators": [],
        "is_genuine": true
    }
    """
    current_user = get_jwt_identity()
    
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
    
    # Get live face scan
    live_photo = data.get('live_photo')
    camera_source = data.get('camera_source', 'webcam')
    
    if not live_photo:
        log_security_event('identity_verification_no_photo', {
            'username': current_user,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        return jsonify({"error": "Live photo required"}), 400
    
    conn = get_db_connection()
    
    try:
        if not FACE_RECOGNITION_AVAILABLE:
            # Optionally bypass in development to allow flow without FR installed
            if ALLOW_ID_VERIFICATION_BYPASS:
                conn.execute('UPDATE users SET verified = 1 WHERE username = ?', (current_user,))
                conn.commit()
                log_security_event('face_verification_bypassed', {
                    'username': current_user,
                    'reason': 'FR not available and bypass enabled',
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                conn.close()
                return jsonify({
                    "message": "Identity verification bypassed (development mode)",
                    "verified": True,
                    "dev": True
                }), 200
            conn.close()
            return jsonify({
                "error": "Face recognition is not available on this server. Please install dependencies. See backend/INSTALL_FACE_RECOGNITION.md.",
                "dev_bypass_hint": "Set ALLOW_ID_VERIFICATION_BYPASS=true to bypass in development"
            }), 501
        
        # Get user data
        user = conn.execute('SELECT * FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user:
            conn.close()
            log_security_event('identity_verification_user_not_found', {
                'username': current_user,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
            return jsonify({"error": "User not found"}), 404
        
        # Save live photo
        live_photo_path = save_photo(live_photo)
        if not live_photo_path:
            conn.close()
            return jsonify({"error": "Failed to save live photo"}), 500
        
        # Extract face encoding from live photo
        live_face_encoding = extract_face_encoding(live_photo_path)
        if not live_face_encoding:
            # Clean up the temporary file
            try:
                os.remove(live_photo_path)
            except:
                pass
            conn.close()
            
            log_security_event('identity_verification_no_face_detected', {
                'username': current_user,
                'user_id': user['id'],
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
            
            return jsonify({"error": "No face detected in live photo"}), 400
        
        # ===== FRAUD DETECTION CHECKS =====
        
        # 1. Liveness check (detect if face is from a live person or a spoof/photo)
        is_live, liveness_score, liveness_method = perform_liveness_check(live_photo_path)
        
        if is_live is None:
            is_live = True  # Fallback if detection fails
            liveness_score = 0.5
        
        # 2. Spoofing detection (detect printed photos, masks, screens, etc.)
        is_genuine, spoofing_confidence, spoofing_indicators = detect_face_spoofing(live_photo_path)
        
        if is_genuine is None:
            is_genuine = True  # Fallback
            spoofing_confidence = 0.5
        
        # Determine fraud risk level
        fraud_risk = {
            'is_live': is_live,
            'liveness_score': float(liveness_score),
            'is_genuine': is_genuine,
            'spoofing_confidence': float(spoofing_confidence),
            'spoofing_indicators': spoofing_indicators,
            'camera_source': camera_source
        }
        
        # Flag as suspicious if liveness or spoofing checks fail
        is_suspicious = (not is_live or not is_genuine or 
                        liveness_score < 0.6 or spoofing_confidence < 0.7)
        
        # Compare with stored face encoding
        stored_face_encoding_bytes = user['face_encoding']
        
        # If the user has no stored encoding yet, optionally enroll on the fly (dev)
        if not stored_face_encoding_bytes:
            if ALLOW_AUTO_FACE_ENROLLMENT:
                try:
                    # Save the live encoding as the user's baseline
                    conn.execute('UPDATE users SET face_encoding = ? WHERE id = ?', (live_face_encoding, user['id']))
                    conn.commit()
                    log_security_event('face_enrollment_auto', {
                        'user_id': user['id'],
                        'username': current_user,
                        'ip_address': request.remote_addr,
                        'fraud_check': fraud_risk
                    })
                    # Mark verified on first enrollment (dev convenience)
                    conn.execute('UPDATE users SET verified = 1 WHERE id = ?', (user['id'],))
                    conn.commit()
                    
                    try:
                        os.remove(live_photo_path)
                    except:
                        pass
                    
                    return jsonify({
                        "message": "Face enrolled and verified (development mode)",
                        "verified": True,
                        "dev": True,
                        "liveness_score": fraud_risk['liveness_score'],
                        "spoofing_check": fraud_risk['spoofing_indicators']
                    }), 200
                except Exception as ee:
                    try:
                        os.remove(live_photo_path)
                    except:
                        pass
                    conn.close()
                    return jsonify({"error": f"Failed to enroll face: {str(ee)}"}), 500
            else:
                try:
                    os.remove(live_photo_path)
                except:
                    pass
                conn.close()
                return jsonify({
                    "error": "No stored face found for this user. Please enroll your face first.",
                    "action": "Contact admin or enable ALLOW_AUTO_FACE_ENROLLMENT for development"
                }), 409

        stored_face_encoding = pickle.loads(stored_face_encoding_bytes)
        live_face_encoding_unpickled = pickle.loads(live_face_encoding)
        
        # Calculate face distance and determine if it's a match
        face_distance = face_recognition.face_distance([stored_face_encoding], live_face_encoding_unpickled)[0]
        face_match_confidence = max(0, 1.0 - face_distance)  # Convert distance to confidence (0-1)
        is_match = face_distance < 0.6  # Threshold for face matching
        
        # Combined fraud assessment
        verification_result = {
            'is_match': is_match,
            'face_match_confidence': float(face_match_confidence),
            'liveness_score': fraud_risk['liveness_score'],
            'liveness_status': 'LIVE' if is_live else 'SPOOF_DETECTED',
            'spoofing_indicators': spoofing_indicators,
            'is_genuine': is_genuine,
            'is_suspicious': is_suspicious,
            'face_distance': float(face_distance)
        }
        
        # Log verification attempt with fraud analysis
        log_behavior(user['id'], 'face_verification', {
            'success': is_match and not is_suspicious,
            'verification_result': verification_result,
            'ip_address': request.remote_addr
        })
        
        log_security_event('identity_verification_attempt', {
            'username': current_user,
            'user_id': user['id'],
            'is_match': is_match,
            'face_match_confidence': float(face_match_confidence),
            'liveness_score': fraud_risk['liveness_score'],
            'is_genuine': is_genuine,
            'is_suspicious': is_suspicious,
            'spoofing_indicators': spoofing_indicators,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'camera_source': camera_source
        })
        
        # Clean up the temporary file
        try:
            os.remove(live_photo_path)
        except:
            pass
        
        # Check if face match failed
        if not is_match:
            conn.close()
            
            log_security_event('identity_verification_failed_face_mismatch', {
                'username': current_user,
                'user_id': user['id'],
                'face_match_confidence': float(face_match_confidence),
                'face_distance': float(face_distance),
                'ip_address': request.remote_addr
            })
            
            return jsonify({
                "error": "Face verification failed - face does not match stored identity",
                "verified": False,
                "face_match_confidence": float(face_match_confidence),
                "face_distance": float(face_distance)
            }), 401
        
        # Check if suspicious fraud indicators detected
        if is_suspicious:
            conn.close()
            
            log_security_event('identity_verification_fraud_detected', {
                'username': current_user,
                'user_id': user['id'],
                'reason': 'Fraud indicators detected',
                'liveness_status': fraud_risk['liveness_score'],
                'spoofing_confidence': spoofing_confidence,
                'spoofing_indicators': spoofing_indicators,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'severity': 'HIGH'
            })
            
            return jsonify({
                "error": "Identity verification failed - potential fraud detected",
                "verified": False,
                "fraud_indicators": spoofing_indicators,
                "liveness_score": fraud_risk['liveness_score'],
                "spoofing_confidence": spoofing_confidence,
                "recommendation": "Please retry with a live photo from your webcam"
            }), 401
        
        # All checks passed - mark user as verified
        conn.execute('UPDATE users SET verified = 1 WHERE id = ?', (user['id'],))
        conn.commit()
        
        log_security_event('identity_verification_successful', {
            'username': current_user,
            'user_id': user['id'],
            'face_match_confidence': float(face_match_confidence),
            'liveness_score': fraud_risk['liveness_score'],
            'camera_source': camera_source,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        
        conn.close()
        
        return jsonify({
            "message": "Identity verified successfully",
            "verified": True,
            "face_match_confidence": float(face_match_confidence),
            "liveness_score": fraud_risk['liveness_score'],
            "fraud_indicators": [],
            "is_genuine": True
        }), 200
        
    except Exception as e:
        print(f"Identity verification error: {e}")
        
        log_security_event('identity_verification_error', {
            'username': current_user if current_user else 'unknown',
            'error': str(e),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        
        return jsonify({"error": "Identity verification failed - server error"}), 500
    
    finally:
        conn.close()

@app.route('/api/election-data', methods=['GET'])
@jwt_required()
def get_election_data():
    current_user = get_jwt_identity()
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM election_data').fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in data])

@app.route('/api/track-behavior', methods=['POST'])
@jwt_required()
def track_behavior():
    current_user = get_jwt_identity()
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    behavior_data = request.json.get('behavior_data', {})
    action = request.json.get('action', 'user_activity')
    
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT id FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Log the behavior
        session_id = log_behavior(user['id'], action, behavior_data)
        
        return jsonify({"success": True, "session_id": session_id}), 200
    
    except Exception as e:
        print(f"Error tracking behavior: {e}")
        return jsonify({"error": "Failed to track behavior"}), 500
    
    finally:
        conn.close()

@app.route('/api/anomaly-detection', methods=['GET'])
@role_required('admin')
def run_anomaly_detection():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Get all behavioral logs
        logs = conn.execute('''
            SELECT bl.id, bl.user_id, u.username, bl.action, bl.metadata, bl.timestamp, bl.session_id
            FROM behavioral_logs bl
            JOIN users u ON bl.user_id = u.id
            ORDER BY bl.timestamp DESC
        ''').fetchall()
        
        if not logs:
            return jsonify({"message": "No behavioral data available for analysis"}), 200
        
        # Convert to list of dictionaries
        logs_list = []
        for log in logs:
            log_dict = dict(log)
            try:
                log_dict['metadata'] = json.loads(log_dict['metadata'])
            except:
                pass
            logs_list.append(log_dict)
        
        return jsonify({
            "logs": logs_list,
            "count": len(logs_list)
        })
        
    except Exception as e:
        print(f"Error retrieving behavioral logs: {e}")
        return jsonify({"error": "Failed to retrieve behavioral logs"}), 500
    
    finally:
        conn.close()

@app.route('/api/anomaly-detection/analyze', methods=['POST'])
@role_required('admin')
def analyze_anomalies():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Get all behavioral logs
        logs = conn.execute('''
            SELECT bl.id, bl.user_id, u.username, bl.action, bl.metadata, bl.timestamp
            FROM behavioral_logs bl
            JOIN users u ON bl.user_id = u.id
            ORDER BY bl.timestamp
        ''').fetchall()
        
        if not logs:
            return jsonify({"message": "No behavioral data available for analysis"}), 200
        
        # Prepare data for anomaly detection
        features = []
        log_ids = []
        
        for log in logs:
            try:
                metadata = json.loads(log['metadata'])
                
                # Extract features based on action type
                feature_vector = []
                
                if log['action'] == 'login':
                    # Login features: time of day (0-23), login duration
                    login_time = datetime.fromisoformat(log['timestamp']).hour
                    duration = metadata.get('duration', 0)
                    feature_vector = [login_time, duration]
                    
                elif log['action'] == 'cast_vote':
                    # Voting features: time spent on page, mouse movements, keystrokes
                    time_spent = metadata.get('timeSpent', 0)
                    mouse_movements = len(metadata.get('mouseMovements', []))
                    keystrokes = len(metadata.get('keystrokes', []))
                    feature_vector = [time_spent, mouse_movements, keystrokes]
                    
                elif log['action'] == 'face_verification':
                    # Verification features: verification time, face_distance
                    verification_time = metadata.get('verificationTime', 0)
                    face_distance = metadata.get('face_distance', 0.5)
                    feature_vector = [verification_time, face_distance]
                
                # Only add if we have features
                if feature_vector:
                    features.append(feature_vector)
                    log_ids.append(log['id'])
                    
            except Exception as e:
                print(f"Error processing log {log['id']}: {e}")
                continue
        
        # Run anomaly detection if we have enough data
        if len(features) < 10:
            return jsonify({"message": "Not enough data for anomaly detection"}), 200
        
        # Normalize features
        features_array = np.array(features)
        features_normalized = (features_array - np.mean(features_array, axis=0)) / np.std(features_array, axis=0)
        
        # Replace NaN values with 0
        features_normalized = np.nan_to_num(features_normalized)
        
        # Run Isolation Forest for anomaly detection
        model = IsolationForest(contamination=0.05, random_state=42)
        predictions = model.fit_predict(features_normalized)
        
        # Update database with flagged anomalies
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:  # -1 indicates anomaly
                log_id = log_ids[i]
                conn.execute('UPDATE behavioral_logs SET flagged_suspicious = 1 WHERE id = ?', (log_id,))
                anomalies.append(log_id)
        
        conn.commit()
        
        # Get updated logs with flagged anomalies
        flagged_logs = conn.execute('''
            SELECT bl.id, bl.user_id, u.username, bl.action, bl.metadata, bl.timestamp
            FROM behavioral_logs bl
            JOIN users u ON bl.user_id = u.id
            WHERE bl.flagged_suspicious = 1
            ORDER BY bl.timestamp DESC
        ''').fetchall()
        
        return jsonify({
            "message": f"Anomaly detection completed. Found {len(anomalies)} anomalies.",
            "anomalies": [dict(log) for log in flagged_logs],
            "total_analyzed": len(features)
        })
        
    except Exception as e:
        print(f"Error running anomaly detection: {e}")
        return jsonify({"error": f"Failed to run anomaly detection: {str(e)}"}), 500
    
    finally:
        conn.close()

@app.route('/api/cast-vote', methods=['POST'])
@role_required('voter')
def cast_vote():
    current_user = get_jwt_identity()
    
    # Input validation
    if not request.is_json:
        log_security_event('cast_vote_error', f"Missing JSON in request for user {current_user}", 'error')
        return jsonify({"error": "Missing JSON in request"}), 400
    
    vote_data = request.json.get('vote')
    behavior_data = request.json.get('behavior_data', {})
    precinct = request.json.get('precinct')
    
    # Sanitize inputs
    precinct = sanitize_input(precinct) if precinct else None
    
    if not vote_data or not precinct:
        log_security_event('cast_vote_error', f"Missing vote data or precinct for user {current_user}", 'error')
        return jsonify({"error": "Missing vote data or precinct"}), 400
    
    conn = get_db_connection()
    
    try:
        # Get user data
        user = conn.execute('SELECT * FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user:
            log_security_event('cast_vote_error', f"User not found: {current_user}", 'error')
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if user is verified
        if not user['verified']:
            log_security_event('cast_vote_error', f"Unverified user attempted to vote: {current_user}", 'warning')
            conn.close()
            return jsonify({"error": "User not verified. Please complete identity verification."}), 403
        
        # Check if user has already voted
        existing_vote = conn.execute('SELECT * FROM votes WHERE user_id = ?', (user['id'],)).fetchone()
        if existing_vote:
            log_security_event('cast_vote_error', f"User attempted to vote multiple times: {current_user}", 'critical')
            conn.close()
            return jsonify({"error": "You have already cast a vote in this election"}), 403
        
        # Log voting behavior for anomaly detection
        session_id = log_behavior(user['id'], 'cast_vote', behavior_data)
        
        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Use homomorphic encryption for vote data
        encrypted_vote, vote_metadata = homomorphic_encryption.encrypt_vote(vote_data)
        
        # Current timestamp with microsecond precision
        timestamp = datetime.now().isoformat()
        
        # Save encrypted vote with homomorphic metadata
        conn.execute('''
            INSERT INTO votes (transaction_id, encrypted_vote, homomorphic_metadata, 
                              timestamp, precinct, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (transaction_id, encrypted_vote, json.dumps(vote_metadata), 
              timestamp, precinct, user['id']))
        
        conn.commit()
        
        # Log successful vote
        log_security_event('vote_cast', 
                          f"Vote successfully cast by user {current_user} from precinct {precinct}", 
                          'info', 
                          metadata={"transaction_id": transaction_id, "precinct": precinct})
        
        return jsonify({
            "success": True,
            "transaction_id": transaction_id,
            "message": "Vote cast successfully"
        }), 201
        
    except Exception as e:
        conn.rollback()
        log_security_event('cast_vote_error', f"Error casting vote for user {current_user}: {str(e)}", 'error')
        return jsonify({"error": "Failed to cast vote"}), 500
    
    finally:
        conn.close()

@app.route('/api/election-data', methods=['POST'])
@role_required('admin')
def add_election_data():
    current_user = get_jwt_identity()
    
    # Input validation
    if not request.is_json:
        log_security_event('election_data_error', f"Missing JSON in request for user {current_user}", 'error')
        return jsonify({"error": "Missing JSON in request"}), 400
    
    required_fields = ['precinct', 'votes_candidate_a', 'votes_candidate_b', 
                      'registered_voters', 'turnout_percentage', 'timestamp']
    
    for field in required_fields:
        if field not in request.json:
            log_security_event('election_data_error', f"Missing {field} in request for user {current_user}", 'error')
            return jsonify({"error": f"Missing {field} in request"}), 400
    
    # Sanitize and validate inputs
    try:
        precinct = sanitize_input(request.json['precinct'])
        votes_candidate_a = int(request.json['votes_candidate_a'])
        votes_candidate_b = int(request.json['votes_candidate_b'])
        registered_voters = int(request.json['registered_voters'])
        turnout_percentage = float(request.json['turnout_percentage'])
        timestamp = sanitize_input(request.json['timestamp'])
        
        # Validate numeric ranges
        if votes_candidate_a < 0 or votes_candidate_b < 0:
            raise ValueError("Vote counts cannot be negative")
        
        if registered_voters <= 0:
            raise ValueError("Registered voters must be positive")
            
        if turnout_percentage < 0 or turnout_percentage > 100:
            raise ValueError("Turnout percentage must be between 0 and 100")
            
        # Validate timestamp format
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            raise ValueError("Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
            
    except ValueError as e:
        log_security_event('election_data_error', f"Invalid input data: {str(e)}", 'error')
        return jsonify({"error": f"Invalid input data: {str(e)}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO election_data (precinct, votes_candidate_a, votes_candidate_b, 
                                registered_voters, turnout_percentage, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            precinct,
            votes_candidate_a,
            votes_candidate_b,
            registered_voters,
            turnout_percentage,
            timestamp
        ))
        
        conn.commit()
        data_id = cursor.lastrowid
        
        log_security_event('election_data_added', 
                          f"Election data added for precinct {precinct} by user {current_user}", 
                          'info', 
                          metadata={"precinct": precinct, "data_id": data_id})
        
        return jsonify({"success": True, "id": data_id})
    
    except Exception as e:
        conn.rollback()
        log_security_event('election_data_error', f"Database error: {str(e)}", 'error')
        return jsonify({"error": f"Failed to add election data: {str(e)}"}), 500
        
    finally:
        conn.close()

@app.route('/api/analyze', methods=['POST'])
@role_required('admin')
def analyze_data():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM election_data').fetchall()
    conn.close()
    
    if not data:
        return jsonify({"error": "No data available for analysis"}), 400
    
    # Convert to pandas DataFrame
    df = pd.DataFrame([dict(row) for row in data])
    
    # Train model if not already trained
    if fraud_model.model is None:
        accuracy = fraud_model.train(df)
        fraud_model.save_model()
    
    # Make predictions
    predictions = fraud_model.predict(df)
    
    # Update database with flagged entries
    conn = get_db_connection()
    for i, pred in enumerate(predictions):
        if pred:
            conn.execute('UPDATE election_data SET flagged_suspicious = 1 WHERE id = ?', (df.iloc[i]['id'],))
    conn.commit()
    conn.close()
    
    # Get updated data
    conn = get_db_connection()
    updated_data = conn.execute('SELECT * FROM election_data').fetchall()
    conn.close()
    
    return jsonify({
        "success": True,
        "flagged_count": int(sum(predictions)),
        "data": [dict(row) for row in updated_data]
    })

@app.route('/api/votes', methods=['GET'])
@role_required('admin')
def get_votes():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Get all votes
        votes = conn.execute('SELECT transaction_id, timestamp, precinct FROM votes').fetchall()
        
        return jsonify({
            "votes": [dict(vote) for vote in votes],
            "count": len(votes)
        })
        
    except Exception as e:
        print(f"Error retrieving votes: {e}")
        return jsonify({"error": "Failed to retrieve votes"}), 500
    
    finally:
        conn.close()

@app.route('/api/votes/verify/<transaction_id>', methods=['GET'])
@jwt_required()
def verify_vote(transaction_id):
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Get vote data
        vote = conn.execute('SELECT * FROM votes WHERE transaction_id = ?', (transaction_id,)).fetchone()
        
        if not vote:
            conn.close()
            return jsonify({"error": "Vote not found"}), 404
        
        # Check if user is admin or the vote belongs to the user
        user = conn.execute('SELECT id, role FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # For security, only admins can decrypt votes
        if user['role'] != 'admin':
            conn.close()
            return jsonify({
                "transaction_id": vote['transaction_id'],
                "timestamp": vote['timestamp'],
                "precinct": vote['precinct'],
                "verified": True
            })
        
        # Decrypt vote data for admins
        try:
            decrypted_vote = json.loads(fernet.decrypt(vote['encrypted_vote'].encode()).decode())
        except Exception:
            decrypted_vote = None
        
        return jsonify({
            "transaction_id": vote['transaction_id'],
            "timestamp": vote['timestamp'],
            "precinct": vote['precinct'],
            "vote_data": decrypted_vote if decrypted_vote else "Unable to decrypt",
            "verified": True
        })
        
    except Exception as e:
        print(f"Error verifying vote: {e}")
        return jsonify({"error": "Failed to verify vote"}), 500
    
    finally:
        conn.close()

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    conn = get_db_connection()
    
    # Get election data
    election_data = conn.execute('SELECT * FROM election_data').fetchall()
    
    # Get votes data
    votes_data = conn.execute('SELECT * FROM votes').fetchall()
    
    conn.close()
    
    if not election_data and not votes_data:
        return jsonify({"error": "No data available for statistics"}), 400
    
    stats = {}
    
    # Process election data if available
    if election_data:
        # Convert to pandas DataFrame
        df = pd.DataFrame([dict(row) for row in election_data])
        
        # Calculate basic statistics
        stats.update({
            "total_precincts": len(df),
            "total_votes_reported": int(df['votes_candidate_a'].sum() + df['votes_candidate_b'].sum()),
            "avg_turnout": float(df['turnout_percentage'].mean()),
            "suspicious_precincts": int(df['flagged_suspicious'].sum()),
            "candidate_a_votes": int(df['votes_candidate_a'].sum()),
            "candidate_b_votes": int(df['votes_candidate_b'].sum())
        })
    
    # Process votes data if available
    if votes_data:
        votes_df = pd.DataFrame([dict(row) for row in votes_data])
        stats.update({
            "total_votes_cast": len(votes_df),
            "votes_by_precinct": votes_df.groupby('precinct').size().to_dict()
        })
    
    return jsonify(stats)


@app.route('/api/statistics/benford', methods=['GET'])
@role_required('admin')
def get_benford_analysis():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Get all votes data
        votes = conn.execute('SELECT * FROM votes').fetchall()
        
        if not votes:
            return jsonify({"error": "No votes available for Benford's Law analysis"}), 400
        
        # Get election data for precinct vote counts
        election_data = conn.execute('SELECT * FROM election_data').fetchall()
        
        # Prepare data for Benford's Law analysis
        vote_counts = []
        
        # Add vote counts from election_data if available
        if election_data:
            df = pd.DataFrame([dict(row) for row in election_data])
            vote_counts.extend(df['votes_candidate_a'].tolist())
            vote_counts.extend(df['votes_candidate_b'].tolist())
        
        # Count votes by precinct from votes table
        votes_df = pd.DataFrame([dict(vote) for vote in votes])
        if not votes_df.empty and 'precinct' in votes_df.columns:
            precinct_counts = votes_df.groupby('precinct').size().tolist()
            vote_counts.extend(precinct_counts)
        
        # Filter out zeros and small numbers
        vote_counts = [count for count in vote_counts if count >= 10]
        
        if not vote_counts:
            return jsonify({"error": "Insufficient data for Benford's Law analysis"}), 400
        
        # Extract first digits
        first_digits = [int(str(count)[0]) for count in vote_counts]
        
        # Count occurrences of each first digit
        digit_counts = {}
        for digit in range(1, 10):  # Benford's Law applies to digits 1-9
            digit_counts[str(digit)] = first_digits.count(digit)
        
        # Calculate percentages
        total_counts = sum(digit_counts.values())
        digit_percentages = {digit: (count / total_counts) * 100 for digit, count in digit_counts.items()}
        
        # Expected Benford's Law distribution
        benford_expected = {
            "1": 30.1,
            "2": 17.6,
            "3": 12.5,
            "4": 9.7,
            "5": 7.9,
            "6": 6.7,
            "7": 5.8,
            "8": 5.1,
            "9": 4.6
        }
        
        # Calculate chi-square statistic
        chi_square = 0
        for digit in benford_expected.keys():
            expected = benford_expected[digit] * total_counts / 100
            observed = digit_counts[digit]
            chi_square += ((observed - expected) ** 2) / expected
        
        # Degrees of freedom = 9 - 1 = 8
        # Critical value for chi-square with df=8, p=0.05 is 15.51
        # If chi_square > 15.51, then the distribution significantly differs from Benford's Law
        conforms_to_benford = chi_square <= 15.51
        
        # Calculate deviation from expected
        deviations = {digit: abs(digit_percentages[digit] - benford_expected[digit]) for digit in benford_expected.keys()}
        avg_deviation = sum(deviations.values()) / len(deviations)
        
        return jsonify({
            "benford_analysis": {
                "observed_counts": digit_counts,
                "observed_percentages": digit_percentages,
                "expected_percentages": benford_expected,
                "deviations": deviations,
                "average_deviation": avg_deviation,
                "chi_square": chi_square,
                "conforms_to_benford": conforms_to_benford,
                "sample_size": total_counts
            },
            "interpretation": {
                "result": "The vote count distribution " + ("conforms" if conforms_to_benford else "does not conform") + " to Benford's Law.",
                "significance": "Chi-square value of {:.2f} is {}than the critical value (15.51) at p=0.05.".format(
                    chi_square, "less " if conforms_to_benford else "greater "
                ),
                "conclusion": "Based on this analysis, there " + 
                             ("is no" if conforms_to_benford else "may be") + 
                             " statistical evidence of potential irregularities in the vote counts."
            }
        })
        
    except Exception as e:
        print(f"Error performing Benford's Law analysis: {e}")
        return jsonify({"error": f"Failed to perform analysis: {str(e)}"}), 500
    
    finally:
        conn.close()

# ========================================
# ADMIN MONITORING ENDPOINTS
# ========================================

@app.route('/api/admin/user-stats', methods=['GET'])
@role_required('admin')
def get_user_statistics():
    """Get comprehensive user and system statistics for admin dashboard"""
    try:
        conn = get_db_connection()
        
        # Count users by role
        voters = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('voter',)).fetchone()
        candidates = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('candidate',)).fetchone()
        verified_voters = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ? AND verified = 1', ('voter',)).fetchone()
        
        # Count votes and precincts
        votes = conn.execute('SELECT COUNT(*) as count FROM votes').fetchone()
        election_data = conn.execute('SELECT COUNT(*) as count FROM election_data').fetchone()
        
        # Get election statistics
        election_stats = conn.execute('''
            SELECT 
                SUM(votes_candidate_a) as candidate_a,
                SUM(votes_candidate_b) as candidate_b,
                COUNT(DISTINCT precinct) as precincts,
                AVG(turnout_percentage) as avg_turnout,
                COUNT(CASE WHEN flagged_suspicious = 1 THEN 1 END) as suspicious
            FROM election_data
        ''').fetchone()
        
        conn.close()
        
        return jsonify({
            'total_voters': voters['count'] if voters else 0,
            'total_candidates': candidates['count'] if candidates else 0,
            'verified_voters': verified_voters['count'] if verified_voters else 0,
            'total_attempts': votes['count'] if votes else 0,
            'total_votes': votes['count'] if votes else 0,
            'total_precincts': election_data['count'] if election_data else 0,
            'candidate_a_votes': election_stats['candidate_a'] or 0,
            'candidate_b_votes': election_stats['candidate_b'] or 0,
            'avg_turnout': election_stats['avg_turnout'] or 0.0,
            'suspicious_precincts': election_stats['suspicious'] or 0
        })
    except Exception as e:
        print(f"Error fetching user statistics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/activity-logs', methods=['GET'])
@role_required('admin')
def get_activity_logs():
    """Get user activity logs for monitoring"""
    try:
        conn = get_db_connection()
        
        logs = conn.execute('''
            SELECT 
                id,
                user_id,
                action,
                timestamp,
                metadata,
                session_id
            FROM behavioral_logs
            ORDER BY timestamp DESC
            LIMIT 100
        ''').fetchall()
        
        conn.close()
        
        result = []
        for log in logs:
            result.append({
                'id': log['id'],
                'user_id': log['user_id'],
                'action': log['action'],
                'timestamp': log['timestamp'],
                'metadata': json.loads(log['metadata']) if log['metadata'] else {},
                'session_id': log['session_id']
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching activity logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/security-logs', methods=['GET'])
@role_required('admin')
def get_security_logs():
    """Get security event logs"""
    try:
        conn = get_db_connection()
        
        logs = conn.execute('''
            SELECT 
                id,
                timestamp,
                event_type,
                event_data,
                ip_address,
                user_agent
            FROM security_logs
            ORDER BY timestamp DESC
            LIMIT 100
        ''').fetchall()
        
        conn.close()
        
        result = []
        for log in logs:
            result.append({
                'id': log['id'],
                'timestamp': log['timestamp'],
                'event_type': log['event_type'],
                'event_data': json.loads(log['event_data']) if log['event_data'] else {},
                'ip_address': log['ip_address'],
                'user_agent': log['user_agent']
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching security logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/identity-verifications', methods=['GET'])
@role_required('admin')
def get_identity_verifications():
    """Get identity verification records"""
    try:
        conn = get_db_connection()
        
        # Get verification attempts from behavioral logs
        logs = conn.execute('''
            SELECT 
                id,
                user_id,
                timestamp,
                metadata
            FROM behavioral_logs
            WHERE action LIKE '%identity%' OR action LIKE '%verification%'
            ORDER BY timestamp DESC
            LIMIT 100
        ''').fetchall()
        
        conn.close()
        
        result = []
        for log in logs:
            metadata = json.loads(log['metadata']) if log['metadata'] else {}
            result.append({
                'id': log['id'],
                'user_id': log['user_id'],
                'timestamp': log['timestamp'],
                'is_genuine': metadata.get('is_genuine', False),
                'liveness_score': metadata.get('liveness_score', 0),
                'face_match_confidence': metadata.get('face_match_confidence', 0),
                'spoofing_indicators': metadata.get('spoofing_indicators', [])
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching identity verifications: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/voter-list', methods=['GET'])
@role_required('admin')
def get_voter_list():
    """Get list of all voters with status"""
    try:
        conn = get_db_connection()
        
        voters = conn.execute('''
            SELECT 
                u.id,
                u.username,
                u.voter_id,
                u.email,
                u.verified,
                u.last_login_attempt,
                m.verification_status
            FROM users u
            LEFT JOIN master_voter_list m ON u.voter_id = m.voter_id
            WHERE u.role = 'voter'
            ORDER BY u.id DESC
            LIMIT 500
        ''').fetchall()
        
        conn.close()
        
        result = [dict(voter) for voter in voters]
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching voter list: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/candidate-list', methods=['GET'])
@role_required('admin')
def get_candidate_list():
    """Get list of all candidates with status"""
    try:
        conn = get_db_connection()
        
        candidates = conn.execute('''
            SELECT 
                id,
                username,
                email,
                verified,
                last_login_attempt
            FROM users
            WHERE role = 'candidate'
            ORDER BY id DESC
            LIMIT 500
        ''').fetchall()
        
        conn.close()
        
        result = [dict(candidate) for candidate in candidates]
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching candidate list: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)