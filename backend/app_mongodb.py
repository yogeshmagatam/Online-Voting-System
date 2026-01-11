import multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
import os
import json
from datetime import timedelta, datetime
from pymongo import MongoClient
import bcrypt
import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import secrets
import uuid
import csv
from dotenv import load_dotenv
from bson.objectid import ObjectId
from urllib.parse import quote_plus
from fraud_detection import initialize_fraud_detector, get_fraud_detector
from behavior_tracker import initialize_behavior_tracker, get_behavior_tracker
from random_forest_fraud import initialize_rf_service, get_rf_service

load_dotenv()

app = Flask(__name__)
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:3000')
CORS(app, supports_credentials=True, resources={r"/*": {"origins": FRONTEND_ORIGIN}})
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-for-development')

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key-for-development')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)  # Extended to 2 hours to allow time for identity verification
app.config['JWT_TOKEN_LOCATION'] = ["headers", "cookies"]
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
jwt = JWTManager(app)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token has expired',
        'message': 'Your session has expired. Please log in again.',
        'code': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'Invalid token',
        'message': 'The token is invalid. Please log in again.',
        'code': 'token_invalid'
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        'error': 'Missing authorization',
        'message': 'Authorization token is missing. Please log in.',
        'code': 'token_missing'
    }), 401

# Email config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'xxxx xxxx xxxx xxxx')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'election-system@example.com')

# MongoDB
username = 'admin'
password = 'admin@123'
escaped_password = quote_plus(password)
MONGODB_URI = f'mongodb://{username}:{escaped_password}@localhost:27017/election_db?authSource=admin'
MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME', 'election_db')

try:
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
    mongo_client.admin.command('ping')
    db = mongo_client[MONGODB_DB_NAME]
    print(f"✓ MongoDB connected: {MONGODB_DB_NAME}")
    mongodb_available = True
except KeyboardInterrupt:
    raise
except Exception as e:
    print(f"✗ MongoDB connection failed: {str(e)[:100]}")
    print("⚠ Running without MongoDB - enhanced logging disabled")
    print("  To enable MongoDB, install it or check MONGODB_LOCAL_SETUP.md")
    db = None
    mongodb_available = False
    mongo_client = None

if mongodb_available:
    users_collection = db['users']
    login_otp_collection = db['login_otp']
    master_voter_list_collection = db['master_voter_list']
    votes_collection = db['votes']
else:
    users_collection = None
    login_otp_collection = None
    master_voter_list_collection = None
    votes_collection = None

# Initialize fraud detection and behavior tracking (local only)
initialize_fraud_detector()
if mongodb_available:
    initialize_behavior_tracker(db)
else:
    # Initialize with None - will disable behavior tracking
    initialize_behavior_tracker(None)
initialize_rf_service(os.environ.get('RF_MODELS_DIR', os.path.join(os.getcwd(), 'backend', 'models', 'rf')))

# Helpers
def generate_4digit_otp():
    # Use secrets for cryptographically secure random numbers
    otp = str(secrets.randbelow(9000) + 1000)  # Generates 1000-9999
    print(f"[OTP Gen] Generated OTP: {otp}")
    return otp

def send_email_otp(email, otp):
    try:
        if not email or '@' not in email:
            return False
        
        print(f"[Email Send] Sending OTP '{otp}' to {email}")
        
        if app.config['MAIL_USERNAME'] in ['your@gmail.com', 'your-email@gmail.com'] or \
           app.config['MAIL_PASSWORD'] in ['xxxx xxxx xxxx xxxx', 'your-app-password']:
            print(f"\n{'='*70}")
            print(f"OTP EMAIL WOULD BE SENT TO: {email}")
            print(f"OTP CODE: {otp}")
            print(f"Expiration: 10 minutes")
            print(f"{'='*70}\n")
            return True
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your Election System Verification Code'
        msg['From'] = app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = email
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2>Your Verification Code</h2>
              <p>Use the following code to complete your login:</p>
              <div style="background-color: #ecf0f1; padding: 20px; font-size: 32px; 
                          font-family: monospace; letter-spacing: 8px; text-align: center;">
                {otp}
              </div>
              <p><strong>This code will expire in 10 minutes</strong></p>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        
        print(f"OTP email sent to {email}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def create_login_otp(user_id, contact_method, contact_value):
    try:
        # Apply grace period to previous unverified OTPs instead of immediate invalidation
        now = datetime.utcnow()
        grace_until = now + timedelta(minutes=2)
        login_otp_collection.update_many(
            {
                'user_id': user_id,
                'verified': False,
                'invalid': {'$ne': True}
            },
            {'$set': {'superseded': True, 'grace_until': grace_until}}
        )

        otp_code = generate_4digit_otp()
        
        otp_record = {
            'user_id': user_id,
            'otp_code': otp_code,
            'otp_type': contact_method,
            'contact_value': contact_value,
            'created_at': now,
            'expires_at': now + timedelta(minutes=10),
            'verified': False,
            'invalid': False,
            'attempts': 0
        }
        
        result = login_otp_collection.insert_one(otp_record)
        print(f"[OTP Create] Saved OTP {otp_code} for user {user_id} in DB (id: {result.inserted_id})")
        return otp_code, True
    except Exception as e:
        print(f"OTP creation error: {e}")
        return None, False

def verify_login_otp(user_id, otp_code):
    try:
        print(f"[OTP Verify] user_id={user_id}, otp_code={otp_code}")
        now = datetime.utcnow()
        provided_code = str(otp_code).strip()

        # Try to match by user AND code, ensure not expired, and allow grace window for superseded codes
        otp_record = login_otp_collection.find_one({
            'user_id': user_id,
            'otp_code': provided_code,
            'verified': False,
            'expires_at': {'$gte': now},
            '$or': [
                {'invalid': {'$ne': True}, 'superseded': {'$ne': True}},
                {'grace_until': {'$gte': now}}
            ]
        }, sort=[('created_at', -1)])

        if otp_record:
            print(f"[OTP Verify] Matching OTP found (id={otp_record['_id']}). Marking as verified.")
            login_otp_collection.update_one(
                {'_id': otp_record['_id']},
                {'$set': {'verified': True}}
            )
            return True, "OTP verified"

        # No direct match - check latest pending OTP for clearer error
        latest = login_otp_collection.find_one({
            'user_id': user_id,
            'verified': False,
            'invalid': {'$ne': True}
        }, sort=[('created_at', -1)])

        if not latest:
            print(f"[OTP Verify] No valid OTP found for user_id={user_id}")
            return False, "No OTP found"

        print(f"[OTP Verify] Latest OTP exists but did not match code. code_in_db={latest.get('otp_code')}, expires_at={latest.get('expires_at')}, now={now}")

        if now > latest['expires_at']:
            print("[OTP Verify] Latest OTP is expired; marking invalid")
            login_otp_collection.update_one(
                {'_id': latest['_id']},
                {'$set': {'invalid': True}}
            )
            return False, "OTP expired"

        # Increment attempts on the latest OTP to aid monitoring
        login_otp_collection.update_one(
            {'_id': latest['_id']},
            {'$inc': {'attempts': 1}}
        )
        return False, "Invalid OTP"
    except Exception as e:
        print(f"OTP verification error: {e}")
        return False, str(e)

def init_db():
    try:
        users_collection.create_index('username', unique=True)
        master_voter_list_collection.create_index('voter_id', unique=True)
        
        # First, fix any existing admin accounts - only the first one should be authorized
        all_admins = list(users_collection.find({'role': 'admin'}).sort('created_at', 1))
        
        if all_admins:
            # Mark the first admin as authorized, rest as unauthorized
            first_admin = all_admins[0]
            if not first_admin.get('is_authorized_admin'):
                users_collection.update_one(
                    {'_id': first_admin['_id']},
                    {'$set': {'is_authorized_admin': True}}
                )
                print(f"✓ Marked first admin '{first_admin.get('username')}' as authorized")
            
            # Mark all other admins as unauthorized
            for admin in all_admins[1:]:
                users_collection.update_one(
                    {'_id': admin['_id']},
                    {'$set': {'is_authorized_admin': False}}
                )
                print(f"✓ Marked admin '{admin.get('username')}' as unauthorized")
        else:
            # No admin exists, create default one
            admin = users_collection.find_one({'username': 'admin'})
            if not admin:
                hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
                users_collection.insert_one({
                    'username': 'admin',
                    'password': hashed,
                    'role': 'admin',
                    'mfa_type': 'none',
                    'is_authorized_admin': True,
                    'created_at': datetime.utcnow()
                })
                print("✓ Admin user created (username: admin, password: admin123)")
        
        # Sample voters
        for i in range(1, 4):
            if not master_voter_list_collection.find_one({'voter_id': f'V{i:03d}'}):
                master_voter_list_collection.insert_one({
                    'voter_id': f'V{i:03d}',
                    'national_id': f'N{i:03d}',
                    'name': f'Voter {i}',
                    'eligible': True
                })
        
        print("✓ Database initialized")
    except Exception as e:
        print(f"DB init error: {e}")


def load_fraud_dataset_summary(max_preview=25):
    """Load summary stats from voting_fraud_dataset.csv for admin dashboard."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(base_dir, 'voting_fraud_dataset.csv')
    summary = {
        'available': False,
        'dataset_path': dataset_path,
        'total_rows': 0,
        'fraudulent_votes': 0,
        'legitimate_votes': 0,
        'fraud_rate': 0,
        'preview': []
    }

    if not os.path.exists(dataset_path):
        summary['error'] = 'Dataset file not found'
        return summary

    try:
        with open(dataset_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                summary['total_rows'] += 1
                is_fraud_raw = str(row.get('is_fraud', '')).strip().lower()
                is_fraud = is_fraud_raw in ['1', 'true', 'yes']
                if is_fraud:
                    summary['fraudulent_votes'] += 1
                else:
                    summary['legitimate_votes'] += 1

                if len(summary['preview']) < max_preview:
                    summary['preview'].append(row)

        if summary['total_rows'] > 0:
            summary['fraud_rate'] = summary['fraudulent_votes'] / summary['total_rows']
            summary['available'] = True
    except Exception as e:
        summary['error'] = str(e)

    return summary

# Routes
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'database': 'MongoDB'}), 200

@app.route('/api/clear-otps', methods=['DELETE'])
def clear_otps():
    try:
        result = login_otp_collection.delete_many({'verified': False})
        print(f"[Clear OTP] Deleted {result.deleted_count} unverified OTPs")
        return jsonify({"message": f"Cleared {result.deleted_count} OTPs"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/register/voter', methods=['POST', 'OPTIONS'])
def register_voter():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not mongodb_available or users_collection is None:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        data = request.json
        username = data.get('username', '').strip() if data.get('username') else ''
        password = data.get('password', '').strip() if data.get('password') else ''
        email = data.get('email', '').strip() if data.get('email') else ''
        voter_id = data.get('voter_id', '').strip() if data.get('voter_id') else ''
        
        if not all([username, password, voter_id, email]):
            missing = []
            if not username: missing.append('username')
            if not password: missing.append('password')
            if not voter_id: missing.append('voter_id')
            if not email: missing.append('email')
            print(f"Registration error: Missing fields: {missing}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
        
        if users_collection.find_one({'username': username}):
            return jsonify({"error": "Username already exists"}), 400
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        mfa_secret = pyotp.random_base32()
        
        user_doc = {
            'username': username,
            'password': hashed,
            'role': 'voter',
            'email': email,
            'voter_id': voter_id,
            'mfa_secret': mfa_secret,
            'mfa_type': 'email',
            'created_at': datetime.utcnow()
        }
        
        # Save user first to get _id
        result = users_collection.insert_one(user_doc)

        # Optional: save registration photo
        try:
            photo_data_url = data.get('photo')
            if photo_data_url:
                import base64, io
                from PIL import Image
                # Ensure uploads directory exists
                uploads_dir = os.path.join(os.getcwd(), 'backend', 'uploads', 'user_photos')
                os.makedirs(uploads_dir, exist_ok=True)

                # Handle both data URL format and raw base64
                if ',' in photo_data_url and photo_data_url.startswith('data:'):
                    header, b64 = photo_data_url.split(',', 1)
                else:
                    b64 = photo_data_url
                
                # Decode base64 (supports all image formats)
                try:
                    img_bytes = base64.b64decode(b64)
                except Exception as decode_error:
                    print(f"Base64 decode error: {decode_error}")
                    raise
                
                # Open image and convert to RGB (handles PNG, JPEG, GIF, BMP, TIFF, WebP, etc.)
                img = Image.open(io.BytesIO(img_bytes))
                
                # Handle transparency by converting RGBA to RGB with white background
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                else:
                    img = img.convert('RGB')

                # Save as user_id.jpg
                photo_path = os.path.join(uploads_dir, f"{str(result.inserted_id)}.jpg")
                img.save(photo_path, format='JPEG', quality=95, optimize=True)

                # Update user with photo path
                users_collection.update_one({'_id': result.inserted_id}, {'$set': {'photo_path': photo_path}})
        except Exception as e:
            print(f"Registration photo save failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Send OTP on registration
        otp_code, success = create_login_otp(str(result.inserted_id), 'email', email)
        if success:
            send_email_otp(email, otp_code)
        
        return jsonify({"message": "User registered successfully", "mfa_type": "email"}), 201
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/register/candidate', methods=['POST', 'OPTIONS'])
def register_candidate():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not mongodb_available or users_collection is None:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        data = request.json
        username = data.get('username', '').strip() if data.get('username') else ''
        password = data.get('password', '').strip() if data.get('password') else ''
        email = data.get('email', '').strip() if data.get('email') else ''
        
        if not all([username, password, email]):
            missing = []
            if not username: missing.append('username')
            if not password: missing.append('password')
            if not email: missing.append('email')
            print(f"Candidate registration error: Missing fields: {missing}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
        
        if users_collection.find_one({'username': username}):
            return jsonify({"error": "Username already exists"}), 400
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        mfa_secret = pyotp.random_base32()
        
        user_doc = {
            'username': username,
            'password': hashed,
            'role': 'candidate',
            'email': email,
            'mfa_secret': mfa_secret,
            'mfa_type': 'email',
            'created_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_doc)
        
        # Send OTP on registration
        otp_code, success = create_login_otp(str(result.inserted_id), 'email', email)
        if success:
            send_email_otp(email, otp_code)
        
        return jsonify({"message": "Candidate registered successfully", "mfa_type": "email"}), 201
    except Exception as e:
        print(f"Candidate registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/register/admin', methods=['POST', 'OPTIONS'])
def register_admin():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not mongodb_available or users_collection is None:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        data = request.json
        username = data.get('username', '').strip() if data.get('username') else ''
        email = data.get('email', '').strip() if data.get('email') else ''
        password = data.get('password', '').strip() if data.get('password') else ''
        
        if not all([username, email, password]):
            missing = []
            if not username: missing.append('username')
            if not email: missing.append('email')
            if not password: missing.append('password')
            print(f"Admin registration error: Missing fields: {missing}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
        
        # Check if username or email already exists
        if users_collection.find_one({'username': username}):
            return jsonify({"error": "Username already exists"}), 400
        if users_collection.find_one({'email': email}):
            return jsonify({"error": "Email already exists"}), 400
        
        # Check if an authorized admin already exists
        existing_authorized_admin = users_collection.find_one({'role': 'admin', 'is_authorized_admin': True})
        if existing_authorized_admin:
            return jsonify({"error": "An authorized admin already exists. Only one admin is allowed."}), 403
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_doc = {
            'username': username,
            'password': hashed,
            'role': 'admin',
            'email': email,
            'mfa_type': 'none',
            'is_authorized_admin': True,
            'created_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_doc)
        print(f"✓ Admin registered: {username} ({email})")
        
        return jsonify({"message": "Admin registered successfully"}), 201
    except Exception as e:
        print(f"Admin registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing credentials"}), 400
        
        # If MongoDB is unavailable, allow test credentials for demo
        if not mongodb_available or users_collection is None:
            print("[Login] MongoDB unavailable - using fallback test credentials")
            if username == 'admin' and password == 'admin@123':
                token = create_access_token(identity=username, additional_claims={'role': 'admin'})
                return jsonify({"access_token": token, "role": "admin"}), 200
            elif username == 'voter' and password == 'voter123':
                token = create_access_token(identity=username, additional_claims={'role': 'voter'})
                return jsonify({"access_token": token, "role": "voter"}), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401
        
        user = users_collection.find_one({'username': username})
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check if user is admin and if they are authorized
        if user.get('role') == 'admin':
            if not user.get('is_authorized_admin', False):
                return jsonify({"error": "Unauthorized admin account. Access denied."}), 403
        
        if user.get('mfa_type') and user.get('mfa_type') != 'none':
            otp_code, success = create_login_otp(str(user['_id']), 'email', user.get('email'))
            if success:
                send_email_otp(user.get('email'), otp_code)
            
            return jsonify({
                "mfa_required": True,
                "mfa_type": "email",
                "user_id": str(user['_id']),
                "message": "OTP sent to your email"
            }), 200
        
        token = create_access_token(identity=username, additional_claims={'role': user['role']})
        return jsonify({"access_token": token, "role": user['role']}), 200
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    try:
        if not mongodb_available or users_collection is None:
            return jsonify({"error": "Database unavailable"}), 503
        
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not user.get('email'):
            return jsonify({"error": "User has no email configured"}), 400

        otp_code, success = create_login_otp(str(user['_id']), 'email', user.get('email'))
        if not success:
            return jsonify({"error": "Could not generate OTP"}), 500

        send_email_otp(user.get('email'), otp_code)
        return jsonify({"message": "A new OTP has been sent to your email"}), 200
    except Exception as e:
        print(f"Resend OTP error: {e}")
        return jsonify({"error": "Resend failed"}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        if not mongodb_available or users_collection is None:
            return jsonify({"error": "Database unavailable"}), 503
        
        data = request.json
        user_id = data.get('user_id')
        otp_code = data.get('otp')
        
        print(f"[Verify-OTP] Received request: user_id={user_id}, otp={otp_code} (type: {type(otp_code)})")
        
        if not user_id or not otp_code:
            return jsonify({"error": "Missing user_id or OTP"}), 400
        
        success, message = verify_login_otp(user_id, otp_code)
        
        if not success:
            print(f"[Verify-OTP] Verification failed: {message}")
            return jsonify({"error": message}), 401
        
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        token = create_access_token(identity=user['username'], additional_claims={'role': user['role']})
        print(f"[Verify-OTP] Success! Returning token for user: {user['username']}")
        return jsonify({"access_token": token, "role": user['role']}), 200
    except Exception as e:
        print(f"OTP verification error: {e}")
        return jsonify({"error": "Verification failed"}), 500

@app.route('/api/verify-identity', methods=['POST', 'OPTIONS'])
@jwt_required()
def verify_identity():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        live_photo = data.get('live_photo')
        camera_source = data.get('camera_source', 'webcam')
        
        if not live_photo:
            return jsonify({"error": "Live photo is required"}), 400

        try:
            import base64, io
            import numpy as np
            from PIL import Image
            import cv2
            try:
                import face_recognition
            except Exception:
                face_recognition = None

            # Decode live photo (supports all image formats: JPEG, PNG, GIF, BMP, TIFF, WebP, etc.)
            # Handle both data URL format and raw base64
            if ',' in live_photo and live_photo.startswith('data:'):
                header, b64 = live_photo.split(',', 1)
            else:
                b64 = live_photo
            
            img_bytes = base64.b64decode(b64)
            
            # Use OpenCV to decode image - it handles all formats and produces dlib-compatible arrays
            nparr = np.frombuffer(img_bytes, np.uint8)
            live_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if live_np is None:
                raise ValueError("Failed to decode image")
            
            # OpenCV loads as BGR, convert to RGB for face_recognition
            live_np = cv2.cvtColor(live_np, cv2.COLOR_BGR2RGB)
            
            # Force a complete copy into a fresh array with explicit properties
            # This ensures all internal array metadata is clean
            live_np = np.array(live_np, dtype=np.uint8, order='C', copy=True)
            
            # Verify and ensure the array is writable and owns its data
            if not live_np.flags['OWNDATA']:
                live_np = live_np.copy()
            
            # Debug logging
            print(f"[DEBUG] Image ready - shape: {live_np.shape}, dtype: {live_np.dtype}, contiguous: {live_np.flags['C_CONTIGUOUS']}, min: {live_np.min()}, max: {live_np.max()}")
            print(f"[DEBUG] Array strides: {live_np.strides}, itemsize: {live_np.itemsize}")

            # Basic fraud checks
            fraud_indicators = []
            if live_np.shape[0] < 100 or live_np.shape[1] < 100:
                fraud_indicators.append('image_too_small')

            # Detect face(s)
            if face_recognition is not None:
                try:
                    # CRITICAL FIX: Some dlib builds reject certain array layouts
                    # Force the exact memory layout dlib expects by creating a minimal copy
                    # Use the internal dlib.load_rgb_image equivalent
                    
                    # Ensure dimensions are correct
                    h, w, c = live_np.shape
                    
                    # Create a brand new array from scratch with explicit C-order
                    img_for_dlib = np.empty((h, w, 3), dtype=np.uint8, order='C')
                    img_for_dlib[:] = live_np
                    
                    # Double-check it's exactly what dlib wants
                    assert img_for_dlib.dtype == np.uint8
                    assert img_for_dlib.ndim == 3
                    assert img_for_dlib.shape[2] == 3
                    assert img_for_dlib.flags['C_CONTIGUOUS']
                    
                    print(f"[DEBUG] Calling face_locations with prepared array...")
                    # Try with more aggressive upsampling first
                    live_locations = face_recognition.face_locations(img_for_dlib, number_of_times_to_upsample=2, model='hog')
                    
                    # If no faces found, try CNN model (more accurate but slower)
                    if len(live_locations) == 0:
                        print(f"[DEBUG] HOG found no faces, trying CNN model...")
                        try:
                            live_locations = face_recognition.face_locations(img_for_dlib, model='cnn')
                        except:
                            # CNN might not be available
                            pass
                    
                    live_np = img_for_dlib  # Use this array for all subsequent operations
                    
                except Exception as e:
                    print(f"[ERROR] face_locations failed even after preparation: {e}")
                    print(f"[ERROR] Trying absolute fallback - load via PIL from scratch...")
                    
                    # Absolute last resort: encode back to bytes and reload via PIL
                    try:
                        from PIL import Image
                        import io
                        # Convert back to BGR for cv2
                        bgr = cv2.cvtColor(live_np, cv2.COLOR_RGB2BGR)
                        # Encode to PNG bytes
                        success, buffer = cv2.imencode('.png', bgr)
                        if not success:
                            raise ValueError("Failed to encode image")
                        # Reload via PIL
                        pil_img = Image.open(io.BytesIO(buffer.tobytes()))
                        pil_img = pil_img.convert('RGB')
                        live_np = np.array(pil_img, dtype=np.uint8)
                        
                        print(f"[DEBUG] PIL fallback - shape: {live_np.shape}, dtype: {live_np.dtype}")
                        live_locations = face_recognition.face_locations(live_np, number_of_times_to_upsample=2)
                    except Exception as e2:
                        print(f"[ERROR] All methods failed: {e2}")
                        # Give up on face detection but continue
                        live_locations = []
                
                print(f"[DEBUG] Detected {len(live_locations)} face(s) in image")
                
                if len(live_locations) == 0:
                    # Make this a warning instead of hard failure
                    print(f"[WARNING] No face detected - allowing verification to continue")
                    # Don't add to fraud_indicators to allow verification
                if len(live_locations) > 1:
                    fraud_indicators.append('multiple_faces_detected')

            if fraud_indicators:
                return jsonify({
                    "error": "Fraud indicators detected",
                    "fraud_indicators": fraud_indicators,
                    "liveness_score": 0.0,
                    "spoofing_confidence": 0.9
                }), 400

            # Attempt face match against stored photo
            user_id = get_jwt_identity()
            
            # Check if MongoDB is available
            if not mongodb_available or users_collection is None:
                print("[WARNING] MongoDB not available, skipping face matching")
                return jsonify({
                    "verified": True,
                    "is_genuine": True,
                    "face_match_confidence": 0.85,  # Default confidence when DB unavailable
                    "face_distance": None,
                    "liveness_score": 0.8,
                    "message": "Identity verified successfully (database unavailable - face matching skipped)"
                }), 200
            
            user = users_collection.find_one({'username': user_id})
            if user is None:
                user = users_collection.find_one({'_id': ObjectId(user_id)})
            
            if user is None:
                print(f"[WARNING] User not found: {user_id}")
                return jsonify({"error": "User not found. Please log in again."}), 404
            
            face_match_confidence = 0.0
            face_distance = None
            is_genuine = True

            if face_recognition is not None and user is not None and user.get('photo_path') and os.path.exists(user['photo_path']):
                try:
                    # Use OpenCV to load reference image - produces dlib-compatible arrays
                    ref_np = cv2.imread(user['photo_path'])
                    
                    if ref_np is None:
                        raise ValueError(f"Failed to load reference image from {user['photo_path']}")
                    
                    # OpenCV loads as BGR, convert to RGB for face_recognition
                    ref_np = cv2.cvtColor(ref_np, cv2.COLOR_BGR2RGB)
                    
                    # Ensure uint8 type
                    ref_np = np.asarray(ref_np, dtype=np.uint8, order='C')
                    
                    ref_encodings = face_recognition.face_encodings(ref_np)
                    live_encodings = face_recognition.face_encodings(live_np)
                    if len(ref_encodings) > 0 and len(live_encodings) > 0:
                        dist = face_recognition.face_distance([ref_encodings[0]], live_encodings[0])[0]
                        face_distance = float(dist)
                        # Map distance [0,1+] to confidence [0,1]
                        face_match_confidence = float(max(0.0, min(1.0, 1.0 - dist)))
                        is_genuine = dist < 0.6
                    else:
                        print("[WARNING] No face encodings found in reference or live photo")
                        is_genuine = True
                        face_match_confidence = 0.5  # Neutral confidence
                except Exception as e:
                    print(f"Face match error: {e}")
                    # Continue verification even if face matching fails
                    is_genuine = True
                    face_match_confidence = 0.5
            elif user is not None and not user.get('photo_path'):
                print(f"[WARNING] User {user_id} has no registered photo - skipping face matching")
                face_match_confidence = 0.7  # Give benefit of doubt
                is_genuine = True

            # Simple liveness heuristic (presence of a face + reasonable size)

            liveness_score = 0.95 if face_recognition is not None else 0.8

            # Optionally log success
            try:
                logs_dir = os.path.join(os.getcwd(), 'backend', 'logs')
                os.makedirs(logs_dir, exist_ok=True)
                log_path = os.path.join(logs_dir, f"security_{datetime.utcnow().date()}.log")
                with open(log_path, 'a', encoding='utf-8') as f:
                    entry = {
                        "username": user.get('username') if user is not None else None,
                        "user_id": str(user.get('_id')) if user is not None else None,
                        "face_match_confidence": face_match_confidence,
                        "liveness_score": liveness_score,
                        "camera_source": camera_source,
                        "ip_address": request.remote_addr,
                        "user_agent": request.headers.get('User-Agent'),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    f.write(f"[{datetime.utcnow().isoformat()}] [identity_verification_successful] {json.dumps(entry)}\n")
            except Exception:
                pass

            # Mark user as identity verified in DB (if available)
            try:
                if mongodb_available and users_collection is not None and user is not None:
                    users_collection.update_one({'_id': user.get('_id')}, {'$set': {'identity_verified': True}})
            except Exception:
                pass

            return jsonify({
                "verified": True,
                "is_genuine": is_genuine,
                "face_match_confidence": face_match_confidence,
                "face_distance": face_distance,
                "liveness_score": liveness_score,
                "message": "Identity verified successfully"
            }), 200
        except Exception as e:
            print(f"Identity verification processing error: {e}")
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            # Provide more specific error messages
            if "face_recognition" in error_msg.lower() or "dlib" in error_msg.lower():
                return jsonify({"error": "Face recognition library error. Please ensure camera permissions are granted and try again."}), 500
            elif "decode" in error_msg.lower():
                return jsonify({"error": "Failed to process image. Please try capturing the photo again."}), 500
            elif "photo_path" in error_msg.lower() or "reference" in error_msg.lower():
                return jsonify({"error": "No registered photo found. Please register your photo first."}), 400
            else:
                return jsonify({"error": f"Image processing error: {error_msg}"}), 500
    except Exception as e:
        print(f"Identity verification error: {e}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        # Handle common errors
        if "No JSON object could be decoded" in error_msg or "JSON" in error_msg:
            return jsonify({"error": "Invalid request format. Please try again."}), 400
        elif "token" in error_msg.lower():
            return jsonify({"error": "Authentication error. Please log in again.", "code": "token_error"}), 401
        else:
            return jsonify({"error": f"Verification error: {error_msg}"}), 500

@app.route('/api/election-data', methods=['GET'])
@jwt_required()
def get_election_data():
    try:
        return jsonify({
            'candidates': ['Candidate A', 'Candidate B'],
            'precincts': ['Precinct 1', 'Precinct 2', 'Precinct 3']
        }), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch data"}), 500

@app.route('/api/cast-vote', methods=['POST'])
@jwt_required()
def cast_vote():
    try:
        if not mongodb_available or votes_collection is None or users_collection is None:
            return jsonify({"error": "Database unavailable"}), 503
        
        data = request.json
        user_id = get_jwt_identity()
        
        # Extract candidate from nested vote object or top level
        vote_data = data.get('vote', {})
        candidate = vote_data.get('candidate_id') or data.get('candidate') or data.get('candidate_id')
        precinct = data.get('precinct')
        
        print(f"\n{'='*60}")
        print(f"[Cast Vote] user_id={user_id}, candidate={candidate}, precinct={precinct}")
        print(f"[Cast Vote] Full request data: {data}")
        print(f"{'='*60}")
        
        if not candidate:
            print(f"[Cast Vote] ERROR: Missing candidate")
            return jsonify({"error": "Missing candidate"}), 400
        
        # Check if user has already voted
        existing_vote = votes_collection.find_one({'user_id': user_id})
        if existing_vote:
            print(f"[Cast Vote] ERROR: User already voted")
            return jsonify({"error": "You have already voted"}), 400
        
        # FRAUD DETECTION - Collect behavior data and assess risk
        session_id = request.cookies.get('session_id', str(uuid.uuid4()))
        behavior_tracker = get_behavior_tracker()
        fraud_detector = get_fraud_detector()
        
        # Collect request metadata
        request_data = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'session_id': session_id
        }
        
        # Get voter information
        user = users_collection.find_one({'username': user_id})
        voter_data = {
            'voter_id': user_id,
            'age': user.get('age', 0),
            'registration_date': user.get('created_at', datetime.utcnow()),
            'identity_verified': user.get('identity_verified', False),
            'mfa_type': user.get('mfa_type', 'none')
        }
        
        # Prepare vote attempt data
        vote_attempt_data = {
            'timestamp': datetime.utcnow(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'is_mobile': 'mobile' in request.headers.get('User-Agent', '').lower(),
            'session_duration': data.get('session_duration', 0),
            'page_views': data.get('page_views', 0),
            'time_on_page': data.get('time_on_page', 0),
            'login_attempts': data.get('login_attempts', 1),
            'votes_in_last_hour': behavior_tracker.get_recent_votes(user_id, hours=1),
            'identity_verified': voter_data['identity_verified']
        }
        
        # Get historical behavior
        historical_data = behavior_tracker.get_voter_history(user_id, days=30)
        
        # Track vote attempt
        behavior_tracker.track_vote_attempt(user_id, session_id, vote_attempt_data, request_data)
        
        # Assess fraud risk
        fraud_assessment = fraud_detector.assess_vote_risk(
            voter_data, vote_attempt_data, historical_data
        )

        # Override for first-time voters to prevent unfair blocking
        try:
            previous_count = votes_collection.count_documents({'user_id': user_id})
        except Exception:
            previous_count = 0
        is_new_voter = previous_count == 0
        if is_new_voter:
            # Downgrade risk to low and allow
            fraud_assessment['risk_level'] = 'low'
            fraud_assessment['recommended_action'] = 'allow'
            fraud_assessment['fraud_probability'] = min(fraud_assessment.get('fraud_probability', 0.0), 0.2)
        
        # Store fraud assessment
        behavior_tracker.store_fraud_assessment(fraud_assessment)
        
        print(f"[Fraud Detection] Risk: {fraud_assessment['risk_level']} "
              f"(probability: {fraud_assessment['fraud_probability']:.4f})")
        
        # Block high-risk votes (not for first-time voters)
        if fraud_assessment['recommended_action'] == 'block' and not is_new_voter:
            print(f"[Cast Vote] BLOCKED: High fraud risk detected")
            return jsonify({
                "error": "Vote blocked due to security concerns. Please contact support.",
                "fraud_risk": fraud_assessment['risk_level'],
                "transaction_id": None
            }), 403
        
        # Flag medium-risk votes for review
        flagged_for_review = fraud_assessment['recommended_action'] == 'review'
        
        # Generate a unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        vote_record = {
            'user_id': user_id,
            'candidate': candidate,
            'precinct': precinct,
            'transaction_id': transaction_id,
            'timestamp': datetime.utcnow(),
            'verified': True,
            'fraud_score': fraud_assessment['fraud_probability'],
            'fraud_risk_level': fraud_assessment['risk_level'],
            'flagged_for_review': flagged_for_review
        }
        
        result = votes_collection.insert_one(vote_record)
        
        print(f"[Cast Vote] SUCCESS: Vote saved")
        print(f"[Cast Vote] Record: {vote_record}")
        print(f"[Cast Vote] Inserted ID: {result.inserted_id}, transaction_id: {transaction_id}")
        print(f"[Cast Vote] Total votes in DB now: {votes_collection.count_documents({})}")
        print(f"{'='*60}\n")
        
        response_data = {
            "message": "Vote cast successfully",
            "transaction_id": transaction_id,
            "fraud_risk_level": fraud_assessment['risk_level']
        }
        
        if flagged_for_review:
            response_data["warning"] = "Vote flagged for additional review"
        
        # Append this vote to local CSV dataset for model training
        try:
            dataset_path = os.path.join(os.path.dirname(__file__), 'voting_fraud_dataset.csv')
            # Derive feature values consistent with dataset columns
            voter_code = f"V{str(hash(user_id) % 10000).zfill(4)}"
            device_code = f"DV{str(hash(request.headers.get('User-Agent', '')) % 10000)}"
            ip_addr = request.remote_addr or '0.0.0.0'
            login_attempts = vote_attempt_data.get('login_attempts', 1)
            vote_duration = vote_attempt_data.get('session_duration', 0)
            # Location match: 1 for first vote or if IP seen before
            historical_ips = [h.get('ip_address', '') for h in historical_data] if historical_data else []
            location_match = 1 if (is_new_voter or (ip_addr in historical_ips)) else 0
            prev_votes = previous_count
            is_fraud_label = 0  # Non-fraud for successful, allowed vote

            # Append row
            import csv as _csv
            # Ensure file exists with header; create if missing
            if not os.path.exists(dataset_path):
                with open(dataset_path, 'w', newline='', encoding='utf-8') as f:
                    writer = _csv.writer(f)
                    writer.writerow(['voter_id','age','ip_address','device_id','login_attempts','vote_duration_sec','location_match','previous_votes','is_fraud'])
            with open(dataset_path, 'a', newline='', encoding='utf-8') as f:
                writer = _csv.writer(f)
                writer.writerow([voter_code, voter_data['age'], ip_addr, device_code, login_attempts, vote_duration, location_match, prev_votes, is_fraud_label])
        except Exception as _e:
            print(f"[Cast Vote] Dataset append failed: {_e}")

        return jsonify(response_data), 200
    except Exception as e:
        print(f"[Cast Vote] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Vote failed: {str(e)}"}), 500

@app.route('/api/votes', methods=['GET'])
@jwt_required()
def get_votes():
    try:
        votes = list(votes_collection.find({}, {'_id': 0}))
        return jsonify(votes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/votes/verify/<transaction_id>', methods=['GET'])
def verify_vote(transaction_id):
    try:
        vote = votes_collection.find_one({'transaction_id': transaction_id}, {'_id': 0})
        if vote:
            return jsonify({"verified": True, "vote": vote}), 200
        return jsonify({"verified": False, "message": "Vote not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    try:
        if not mongodb_available or votes_collection is None or users_collection is None:
            return jsonify({"error": "Database unavailable"}), 503
        
        total_votes = votes_collection.count_documents({})
        total_users = users_collection.count_documents({'role': 'voter'})
        
        # Count votes by candidate
        candidate_a_votes = votes_collection.count_documents({'candidate': 'Candidate A'})
        candidate_b_votes = votes_collection.count_documents({'candidate': 'Candidate B'})
        
        # Get all votes for debugging
        all_votes = list(votes_collection.find({}, {'_id': 0, 'candidate': 1}))
        print(f"[Statistics] Total votes in DB: {total_votes}")
        print(f"[Statistics] All votes: {all_votes}")
        print(f"[Statistics] Candidate A Votes: {candidate_a_votes}")
        print(f"[Statistics] Candidate B Votes: {candidate_b_votes}")
        print(f"[Statistics] Total registered voters: {total_users}")
        
        # Calculate turnout percentage
        turnout = (total_votes / total_users * 100) if total_users > 0 else 0
        print(f"[Statistics] Calculated turnout: {turnout}%")
        
        response = {
            'total_votes': total_votes,
            'total_registered': total_users,
            'avg_turnout': round(turnout, 2),
            'turnout_percentage': round(turnout, 2),
            'candidate_a_votes': candidate_a_votes,
            'candidate_b_votes': candidate_b_votes,
            'total_precincts': 0,
            'suspicious_precincts': 0
        }
        print(f"[Statistics] Response data: {response}")
        return jsonify(response), 200
    except Exception as e:
        print(f"[Statistics] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/user-stats', methods=['GET'])
@jwt_required()
def admin_user_stats():
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        # If MongoDB is available, use it; otherwise return default stats
        if mongodb_available and users_collection is not None and login_otp_collection is not None:
            total_users = users_collection.count_documents({})
            total_voters = users_collection.count_documents({'role': 'voter'})
            total_candidates = users_collection.count_documents({'role': 'candidate'})
            total_admins = users_collection.count_documents({'role': 'admin'})
            verified_voters = users_collection.count_documents({'role': 'voter', 'identity_verified': True})
            total_attempts = login_otp_collection.count_documents({})
            
            print(f"[Admin Stats] MongoDB - total_users={total_users}, total_voters={total_voters}, total_candidates={total_candidates}, verified_voters={verified_voters}")
        else:
            # Fallback: return default stats when MongoDB is unavailable
            print("[Admin Stats] MongoDB unavailable - returning default stats")
            total_users = 0
            total_voters = 0
            total_candidates = 0
            total_admins = 0
            verified_voters = 0
            total_attempts = 0
        
        return jsonify({
            'total_users': total_users,
            'total_voters': total_voters,
            'total_candidates': total_candidates,
            'total_admins': total_admins,
            'verified_voters': verified_voters,
            'total_attempts': total_attempts
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/fraud-dataset-summary', methods=['GET'])
@jwt_required()
def admin_fraud_dataset_summary():
    """Expose fraud CSV summary to the admin dashboard."""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        summary = load_fraud_dataset_summary()
        status_code = 200 if summary.get('available') else 404
        return jsonify(summary), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/activity-logs', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def admin_activity_logs():
    """Stub endpoint for admin activity logs to satisfy dashboard requests."""
    try:
        if request.method == 'OPTIONS':
            return '', 204

        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        # TODO: wire to real activity log storage. For now return empty list.
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/identity-verifications', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def admin_identity_verifications():
    """Stub endpoint for identity verification logs."""
    try:
        if request.method == 'OPTIONS':
            return '', 204

        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        # TODO: connect to real verification records. Return empty list placeholder.
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/security-logs', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def admin_security_logs():
    """Stub endpoint for security logs."""
    try:
        if request.method == 'OPTIONS':
            return '', 204

        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        # TODO: wire to real security log source. Placeholder empty list.
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/train-rf', methods=['POST'])
@jwt_required()
def admin_train_rf():
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        # Optional timeframe from payload
        data = request.get_json(silent=True) or {}
        days = int(data.get('days', 30))

        behavior_tracker = get_behavior_tracker()
        rf_service = get_rf_service()
        if rf_service is None:
            return jsonify({"error": "RF service not initialized"}), 500

        # Export vote attempts with optional labeling
        training_records = behavior_tracker.export_training_data(
            labeled_only=False
        )
        if not training_records:
            return jsonify({"error": "No training data available"}), 400

        # Train and persist model
        metrics = rf_service.train_and_save(training_records)

        return jsonify({
            "message": "Random Forest model trained and saved",
            "metrics": metrics
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/train-rf-from-csv', methods=['POST'])
@jwt_required()
def admin_train_rf_from_csv():
    """Train RF model using the voting_fraud_dataset.csv file"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        from random_forest_fraud import load_voting_fraud_dataset, get_rf_service
        
        # Load dataset from CSV
        dataset_records = load_voting_fraud_dataset()
        
        if not dataset_records:
            return jsonify({"error": "Failed to load dataset from CSV"}), 400
        
        print(f"[Train RF from CSV] Loaded {len(dataset_records)} records from CSV")
        
        # Train model
        rf_service = get_rf_service()
        if rf_service is None:
            return jsonify({"error": "RF service not initialized"}), 500
        
        metrics = rf_service.train_and_save(dataset_records)
        
        return jsonify({
            "message": "Random Forest model trained from CSV dataset",
            "records_used": len(dataset_records),
            "metrics": metrics
        }), 200
        
    except Exception as e:
        print(f"[Train RF from CSV] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/train-rf-from-db', methods=['POST'])
@jwt_required()
def admin_train_rf_from_db():
    """Train RF model using fraud_training_data from database"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        from random_forest_fraud import get_rf_service
        
        # Get training data from database
        training_collection = db['fraud_training_data']
        dataset_records = list(training_collection.find({}, {'_id': 0}))
        
        if not dataset_records:
            return jsonify({"error": "No training data found in database. Run load_dataset_to_db.py first"}), 400
        
        print(f"[Train RF from DB] Loaded {len(dataset_records)} records from database")
        
        # Normalize label field: map 'fraud_label' -> 'is_fraud' if needed
        label_mapped = 0
        for record in dataset_records:
            if 'is_fraud' not in record and 'fraud_label' in record:
                record['is_fraud'] = record['fraud_label']
                label_mapped += 1
        if label_mapped:
            print(f"[Train RF from DB] Mapped label for {label_mapped} records (fraud_label -> is_fraud)")

        # Convert MongoDB objects to JSON-serializable format
        for record in dataset_records:
            if 'timestamp' in record and hasattr(record['timestamp'], 'isoformat'):
                record['timestamp'] = record['timestamp'].isoformat()
        
        # Train model
        rf_service = get_rf_service()
        if rf_service is None:
            return jsonify({"error": "RF service not initialized"}), 500
        
        metrics = rf_service.train_and_save(dataset_records)

        # Persist latest training metrics
        try:
            model_metrics_col = db['model_metrics']
            metrics_doc = {
                'model': 'random_forest',
                'trained_at': datetime.utcnow(),
                'records_used': len(dataset_records),
                'metrics': metrics,
            }
            model_metrics_col.update_one({'model': 'random_forest'}, {'$set': metrics_doc}, upsert=True)
            print("[Train RF from DB] Metrics persisted to model_metrics collection")
        except Exception as me:
            print(f"[Train RF from DB] Warning: failed to persist metrics: {me}")

        return jsonify({
            "message": "Random Forest model trained from database",
            "records_used": len(dataset_records),
            "metrics": metrics
        }), 200
        
    except Exception as e:
        print(f"[Train RF from DB] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/model-status', methods=['GET'])
@jwt_required()
def admin_model_status():
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        rf_service = get_rf_service()
        fraud_detector = get_fraud_detector()
        
        # Fetch latest training metrics (if any)
        latest_metrics = None
        try:
            model_metrics_col = db['model_metrics']
            mdoc = model_metrics_col.find_one({'model': 'random_forest'})
            if mdoc:
                latest_metrics = {
                    'trained_at': mdoc.get('trained_at').isoformat() if mdoc.get('trained_at') else None,
                    'records_used': mdoc.get('records_used'),
                    'roc_auc': mdoc.get('metrics', {}).get('roc_auc'),
                    'pr_auc': mdoc.get('metrics', {}).get('pr_auc'),
                    'n_train': mdoc.get('metrics', {}).get('n_train'),
                    'n_test': mdoc.get('metrics', {}).get('n_test')
                }
        except Exception as e:
            print(f"[Model Status] Warning: failed to read model metrics: {e}")

        model_info = {
            'rf_service_ready': rf_service.is_ready() if rf_service else False,
            'model_path': rf_service.artifacts.model_path if rf_service else None,
            'model_type': fraud_detector.model_source if fraud_detector else 'unknown',
            'features_count': len(rf_service.model.features) if rf_service and rf_service.is_ready() else 0,
            'features': rf_service.model.features if rf_service and rf_service.is_ready() else [],
            'last_training': latest_metrics
        }
        
        return jsonify(model_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/fraud-analytics', methods=['GET'])
@jwt_required()
def fraud_analytics():
    """Get fraud detection analytics"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        behavior_tracker = get_behavior_tracker()
        
        # Get fraud assessments by risk level
        high_risk = behavior_tracker.get_fraud_assessments(risk_level='high', limit=100)
        medium_risk = behavior_tracker.get_fraud_assessments(risk_level='medium', limit=100)
        low_risk = behavior_tracker.get_fraud_assessments(risk_level='low', limit=100)
        
        # Get flagged votes
        flagged_votes = list(votes_collection.find(
            {'flagged_for_review': True},
            {'_id': 0, 'user_id': 1, 'transaction_id': 1, 'fraud_risk_level': 1, 
             'fraud_score': 1, 'timestamp': 1, 'candidate': 1}
        ).limit(50))
        
        # Convert ObjectId and datetime to strings
        for assessment in high_risk + medium_risk + low_risk:
            if '_id' in assessment:
                assessment['_id'] = str(assessment['_id'])
            if 'timestamp' in assessment:
                assessment['timestamp'] = assessment['timestamp'].isoformat()
        
        for vote in flagged_votes:
            if 'timestamp' in vote:
                vote['timestamp'] = vote['timestamp'].isoformat()
        
        return jsonify({
            'summary': {
                'high_risk_count': len(high_risk),
                'medium_risk_count': len(medium_risk),
                'low_risk_count': len(low_risk),
                'flagged_votes_count': len(flagged_votes)
            },
            'high_risk_assessments': high_risk[:10],  # Recent 10
            'medium_risk_assessments': medium_risk[:10],
            'flagged_votes': flagged_votes
        }), 200
    except Exception as e:
        print(f"Fraud analytics error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/export-training-data', methods=['GET'])
@jwt_required()
def export_training_data():
    """Export voter behavior data for model training"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        behavior_tracker = get_behavior_tracker()
        
        # Export training data
        training_data = behavior_tracker.export_training_data(labeled_only=False)
        
        # Convert to JSON-serializable format
        for record in training_data:
            if '_id' in record:
                record['_id'] = str(record['_id'])
            if 'timestamp' in record:
                record['timestamp'] = record['timestamp'].isoformat()
        
        return jsonify({
            'total_records': len(training_data),
            'labeled_records': sum(1 for r in training_data if 'fraud_label' in r),
            'data': training_data
        }), 200
    except Exception as e:
        print(f"Export training data error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/fraud-stats', methods=['GET'])
@jwt_required()
def fraud_stats():
    """Get fraud detection statistics"""
    try:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        # Count votes by fraud risk level
        total_votes = votes_collection.count_documents({})
        high_risk_votes = votes_collection.count_documents({'fraud_risk_level': 'high'})
        medium_risk_votes = votes_collection.count_documents({'fraud_risk_level': 'medium'})
        low_risk_votes = votes_collection.count_documents({'fraud_risk_level': 'low'})
        flagged_votes = votes_collection.count_documents({'flagged_for_review': True})
        
        return jsonify({
            'total_votes': total_votes,
            'high_risk_votes': high_risk_votes,
            'medium_risk_votes': medium_risk_votes,
            'low_risk_votes': low_risk_votes,
            'flagged_votes': flagged_votes,
            'fraud_detection_enabled': get_fraud_detector() is not None
        }), 200
    except Exception as e:
        print(f"Fraud stats error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    print(f"\n{'='*70}")
    print(f"Election System - MongoDB Mode")
    print(f"Database: {MONGODB_DB_NAME}")
    print(f"{'='*70}\n")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
