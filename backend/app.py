from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
# ------------------------------
# MongoDB (optional integration)
# ------------------------------
MONGODB_URI = os.environ.get('mongodb+srv://yogeshmagatam_db_user:0yS9slaSGAcNZ0NP@cluster116454.sypvlt0.mongodb.net/')
MONGODB_DB_NAME = os.environ.get('yogeshmagatam_db_user')

mongo_client = None
mongo_db = None
MONGO_AVAILABLE = False

if MONGODB_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        # Ping to confirm connectivity
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[MONGODB_DB_NAME]
        MONGO_AVAILABLE = True
        print(f"MongoDB connected: db='{MONGODB_DB_NAME}'")
    except Exception as e:
        print(f"MongoDB not available: {e}")


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
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
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
def send_email_otp(email, otp):
    """Send OTP via email for MFA"""
    try:
        msg = MIMEMultipart()
        msg['Subject'] = 'Your Election System Verification Code'
        msg['From'] = app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = email
        
        body = f"""
        <html>
          <body>
            <h2>Your Verification Code</h2>
            <p>Use the following code to complete your login:</p>
            <h1 style="background-color: #f0f0f0; padding: 10px; font-family: monospace;">{otp}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        
        # Log email sending event
        log_security_event('email_otp_sent', {
            'email': email,
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        
        return True
    except Exception as e:
        # Log email sending failure
        log_security_event('email_otp_failed', {
            'email': email,
            'error': str(e),
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else 'unknown'
        })
        print(f"Error sending email: {e}")
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
    
    # Add admin user if not exists (use bcrypt)
    admin_row = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_row:
        # Hash default admin password with bcrypt
        hashed_password, salt = hash_password('admin123')  # both are bytes

        # Generate MFA secret
        mfa_secret = pyotp.random_base32()

        # For development, keep MFA disabled for admin to simplify login
        conn.execute(
            'INSERT INTO users (username, password, role, mfa_secret, mfa_type, salt, verified) VALUES (?, ?, ?, ?, ?, ?, ?)',
            ('admin', hashed_password, 'admin', mfa_secret, 'none', salt, 1)
        )
    else:
        # Migration: if previous admin password was stored as a hex string (sha256), convert to bcrypt
        try:
            stored_pwd = admin_row['password']
            if isinstance(stored_pwd, str):
                # Re-hash to bcrypt using default password 'admin123'
                new_hashed, new_salt = hash_password('admin123')
                conn.execute(
                    'UPDATE users SET password = ?, salt = ?, require_password_change = 1 WHERE id = ?',
                    (new_hashed, new_salt, admin_row['id'])
                )
        except Exception as _e:
            pass

        # Ensure admin MFA is disabled in development for easier testing
        try:
            conn.execute('UPDATE users SET mfa_type = ? WHERE username = ? AND (mfa_type IS NULL OR mfa_type <> ?)', ('none', 'admin', 'none'))
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

@app.route('/api/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    # Check if form data or JSON
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
    
    # Get required fields
    username = sanitize_input(data.get('username', ''))
    password = data.get('password', '')
    voter_id = sanitize_input(data.get('voter_id', ''))
    national_id = sanitize_input(data.get('national_id', ''))
    email = sanitize_input(data.get('email', ''))
    phone = sanitize_input(data.get('phone', ''))
    captcha_response = data.get('captcha')
    
    # Get photo data
    photo_data = data.get('photo')
    
    # Validate required fields
    if not all([username, password, voter_id, national_id, email, photo_data, captcha_response]):
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
        
        # Check if voter ID exists in master list and is eligible
        voter = conn.execute('SELECT * FROM master_voter_list WHERE voter_id = ? AND national_id = ? AND eligible = 1', 
                            (voter_id, national_id)).fetchone()
        if not voter:
            conn.close()
            return jsonify({"error": "Invalid or ineligible voter ID/National ID combination"}), 400
        
        # Check if voter ID is already registered
        registered_voter = conn.execute('SELECT 1 FROM users WHERE voter_id = ?', (voter_id,)).fetchone()
        if registered_voter:
            conn.close()
            return jsonify({"error": "Voter ID already registered"}), 409
        
        # Check if national ID is already registered
        registered_national = conn.execute('SELECT 1 FROM users WHERE national_id = ?', (national_id,)).fetchone()
        if registered_national:
            conn.close()
            return jsonify({"error": "National ID already registered"}), 409
        
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
        
        # Register new user with 'voter' role
        conn.execute('''
            INSERT INTO users (username, password, role, photo_path, face_encoding, 
                              mfa_secret, mfa_type, voter_id, national_id, email, phone, salt, last_password_change) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, 'voter', photo_path, face_encoding, 
              mfa_secret, mfa_type, voter_id, national_id, email, phone, salt, current_time))
        
        # Update verification status in master voter list
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
        
        # Handle MFA verification based on type
        user_mfa_type = user['mfa_type']
        
        # If MFA code is not provided but required
        if not mfa_code and user_mfa_type != 'none':
            # For email-based MFA, send a new code
            if user_mfa_type == 'email' and user['email']:
                totp = pyotp.TOTP(user['mfa_secret'])
                otp = totp.now()
                send_email_otp(user['email'], otp)
                
                log_security_event('mfa_email_code_sent', {
                    'username': username,
                    'user_id': user['id'],
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                
                conn.close()
                return jsonify({
                    'message': 'MFA code sent to your email',
                    'mfa_required': True,
                    'mfa_type': 'email'
                }), 200
            
            # For app-based MFA, prompt for code
            elif user_mfa_type == 'app':
                conn.close()
                return jsonify({
                    'message': 'Please provide MFA code',
                    'mfa_required': True,
                    'mfa_type': 'app'
                }), 200
        
        # Verify MFA code if provided
        if mfa_code:
            totp = pyotp.TOTP(user['mfa_secret'])
            if not totp.verify(mfa_code):
                # Increment failed login attempts
                conn.execute('''
                    UPDATE users 
                    SET failed_login_attempts = failed_login_attempts + 1, 
                        last_login_attempt = ? 
                    WHERE id = ?
                ''', (now.isoformat(), user['id']))
                
                conn.commit()
                
                log_security_event('login_attempt_invalid_mfa', {
                    'username': username,
                    'user_id': user['id'],
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'failed_attempts': user['failed_login_attempts'] + 1
                })
                
                conn.close()
                return jsonify({"error": "Invalid MFA code"}), 401
        
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

@app.route('/api/verify-identity', methods=['POST'])
@jwt_required()
def verify_identity():
    current_user = get_jwt_identity()
    
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
    
    # Get live face scan
    live_photo = data.get('live_photo')
    
    if not live_photo:
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
                    'ip': request.remote_addr
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
            os.remove(live_photo_path)
            conn.close()
            return jsonify({"error": "No face detected in live photo"}), 400
        
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
                        'ip': request.remote_addr
                    })
                    # Mark verified on first enrollment (dev convenience)
                    conn.execute('UPDATE users SET verified = 1 WHERE id = ?', (user['id'],))
                    conn.commit()
                    os.remove(live_photo_path)
                    return jsonify({
                        "message": "Face enrolled and verified (development mode)",
                        "verified": True,
                        "dev": True
                    }), 200
                except Exception as ee:
                    os.remove(live_photo_path)
                    conn.close()
                    return jsonify({"error": f"Failed to enroll face: {str(ee)}"}), 500
            else:
                os.remove(live_photo_path)
                conn.close()
                return jsonify({
                    "error": "No stored face found for this user. Please enroll your face first.",
                    "action": "Contact admin or enable ALLOW_AUTO_FACE_ENROLLMENT for development"
                }), 409

        stored_face_encoding = pickle.loads(stored_face_encoding_bytes)
        live_face_encoding_unpickled = pickle.loads(live_face_encoding)
        
        # Calculate face distance and determine if it's a match
        face_distance = face_recognition.face_distance([stored_face_encoding], live_face_encoding_unpickled)[0]
        is_match = face_distance < 0.6  # Threshold for face matching
        
        # Log verification attempt
        log_behavior(user['id'], 'face_verification', {
            'success': is_match,
            'face_distance': float(face_distance),
            'ip': request.remote_addr
        })
        
        # Clean up the temporary file
        os.remove(live_photo_path)
        
        if not is_match:
            conn.close()
            return jsonify({"error": "Face verification failed"}), 401
        
        # Mark user as verified
        conn.execute('UPDATE users SET verified = 1 WHERE id = ?', (user['id'],))
        conn.commit()
        
        return jsonify({"message": "Identity verified successfully", "verified": True}), 200
        
    except Exception as e:
        print(f"Identity verification error: {e}")
        return jsonify({"error": "Identity verification failed"}), 500
    
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
@jwt_required()
def run_anomaly_detection():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Check if user is admin
        user = conn.execute('SELECT role FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user or user['role'] != 'admin':
            conn.close()
            return jsonify({"error": "Unauthorized access"}), 403
        
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
@jwt_required()
def analyze_anomalies():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Check if user is admin
        user = conn.execute('SELECT role FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user or user['role'] != 'admin':
            conn.close()
            return jsonify({"error": "Unauthorized access"}), 403
        
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
def analyze_data():
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
@jwt_required()
def get_votes():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Check if user is admin
        user = conn.execute('SELECT role FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user or user['role'] != 'admin':
            conn.close()
            return jsonify({"error": "Unauthorized access"}), 403
        
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


@app.route('/api/health', methods=['GET'])
def health():
    # Basic health info including Mongo connectivity
    mongo_status = False
    mongo_error = None
    if MONGODB_URI:
        try:
            mongo_client.admin.command('ping')
            mongo_status = True
        except Exception as e:
            mongo_status = False
            mongo_error = str(e)
    return jsonify({
        'status': 'ok',
        'mongo_configured': bool(MONGODB_URI),
        'mongo_connected': mongo_status,
        'mongo_error': mongo_error
    }), 200

@app.route('/api/statistics/benford', methods=['GET'])
@jwt_required()
def get_benford_analysis():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    try:
        # Check if user is admin
        user = conn.execute('SELECT role FROM users WHERE username = ?', (current_user,)).fetchone()
        
        if not user or user['role'] != 'admin':
            conn.close()
            return jsonify({"error": "Unauthorized access"}), 403
        
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)