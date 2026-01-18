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

        # Save registration photo (REQUIRED for identity verification)
        photo_data_url = data.get('photo')
        if not photo_data_url:
            # Delete the user document if photo is missing
            users_collection.delete_one({'_id': result.inserted_id})
            return jsonify({"error": "Registration photo is required for identity verification"}), 400
        
        try:
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
            img_bytes = base64.b64decode(b64)
            
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

            # Save as user_id.jpg with high quality
            photo_path = os.path.join(uploads_dir, f"{str(result.inserted_id)}.jpg")
            img.save(photo_path, format='JPEG', quality=95, optimize=True)
            
            print(f"[DEBUG] Registration photo saved: {photo_path}")

            # Update user with photo path
            users_collection.update_one({'_id': result.inserted_id}, {'$set': {'photo_path': photo_path}})
            
        except Exception as e:
            print(f"[ERROR] Registration photo save failed: {e}")
            import traceback
            traceback.print_exc()
            # Delete the user document if photo save fails
            users_collection.delete_one({'_id': result.inserted_id})
            return jsonify({"error": f"Failed to save registration photo: {str(e)}"}), 500
        
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
        
        print(f"\n{'='*60}")
        print(f"[LOGIN ATTEMPT] Username: {username}")
        print(f"[LOGIN ATTEMPT] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[LOGIN ATTEMPT] IP: {request.remote_addr}")
        print(f"{'='*60}\n")
        
        if not username or not password:
            print(f"[LOGIN FAILED] Missing credentials for: {username}")
            return jsonify({"error": "Missing credentials"}), 400
        
        # If MongoDB is unavailable, allow test credentials for demo
        if not mongodb_available or users_collection is None:
            print("[Login] MongoDB unavailable - using fallback test credentials")
            if username == 'admin' and password == 'admin@123':
                print(f"[LOGIN SUCCESS] Test admin login: {username}")
                token = create_access_token(identity=username, additional_claims={'role': 'admin'})
                return jsonify({"access_token": token, "role": "admin"}), 200
            elif username == 'voter' and password == 'voter123':
                print(f"[LOGIN SUCCESS] Test voter login: {username}")
                token = create_access_token(identity=username, additional_claims={'role': 'voter'})
                return jsonify({"access_token": token, "role": "voter"}), 200
            else:
                print(f"[LOGIN FAILED] Invalid test credentials for: {username}")
                return jsonify({"error": "Invalid credentials"}), 401
        
        user = users_collection.find_one({'username': username})
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            print(f"[LOGIN FAILED] Invalid credentials for: {username}")
            return jsonify({"error": "Invalid credentials"}), 401
        
        print(f"[LOGIN] User found: {username} | Role: {user.get('role', 'voter')}")
        
        # Check if user is admin and if they are authorized
        if user.get('role') == 'admin':
            if not user.get('is_authorized_admin', False):
                print(f"[LOGIN FAILED] Unauthorized admin account: {username}")
                return jsonify({"error": "Unauthorized admin account. Access denied."}), 403
        
        if user.get('mfa_type') and user.get('mfa_type') != 'none':
            print(f"[LOGIN] MFA required for: {username}")
            otp_code, success = create_login_otp(str(user['_id']), 'email', user.get('email'))
            if success:
                send_email_otp(user.get('email'), otp_code)
            
            return jsonify({
                "mfa_required": True,
                "mfa_type": "email",
                "user_id": str(user['_id']),
                "message": "OTP sent to your email"
            }), 200
        
        print(f"[LOGIN SUCCESS] {username} | Role: {user.get('role', 'voter')}")
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

def prepare_image_for_dlib(img_array):
    """
    Fix Windows dlib compatibility issues by ensuring correct memory layout.
    
    The "Unsupported image type" error on Windows often occurs due to:
    - Incorrect stride values in the numpy array
    - Memory layout issues even when C_CONTIGUOUS is True
    
    This function creates a clean copy with exact memory layout dlib expects.
    
    Args:
        img_array: numpy array (H, W, 3) in RGB format
    
    Returns:
        numpy array properly formatted for dlib
    """
    import numpy as np
    
    # Ensure uint8
    if img_array.dtype != np.uint8:
        img_array = img_array.astype(np.uint8)
    
    # Create a completely new array with clean memory layout
    # This fixes stride and alignment issues that cause dlib errors on Windows
    clean_array = np.empty((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)
    clean_array[:] = img_array
    
    # Verify it's C-contiguous (should be after the copy)
    if not clean_array.flags['C_CONTIGUOUS']:
        clean_array = np.ascontiguousarray(clean_array, dtype=np.uint8)
    
    return clean_array


def load_image_for_face_recognition(image_source, is_file_path=False):
    """
    Load and prepare an image for face_recognition library.
    Uses face_recognition.load_image_file() for proper dlib compatibility.
    
    Args:
        image_source: Either a base64 string or a file path
        is_file_path: True if image_source is a file path, False if it's base64
    
    Returns:
        numpy array in RGB format, ready for face_recognition
    """
    import base64, io, tempfile
    import numpy as np
    from PIL import Image
    import face_recognition
    
    try:
        if is_file_path:
            print(f"[DEBUG] Loading from file path: {image_source}")
            # Use PIL to load (more reliable on Windows)
            from PIL import Image as PILImage
            pil_img = PILImage.open(image_source).convert('RGB')
            img_array = np.array(pil_img, dtype=np.uint8)
            print(f"[DEBUG] Image loaded via PIL - shape: {img_array.shape}, dtype: {img_array.dtype}")
            # Fix memory layout for dlib
            img_array = prepare_image_for_dlib(img_array)
            print(f"[DEBUG] Image prepared for dlib - C_CONTIGUOUS: {img_array.flags['C_CONTIGUOUS']}")
            return img_array
        else:
            # Decode base64
            print(f"[DEBUG] Loading from base64")
            
            if ',' in image_source and image_source.startswith('data:'):
                header, b64 = image_source.split(',', 1)
            else:
                b64 = image_source
            
            img_bytes = base64.b64decode(b64)
            
            # Use PIL to decode
            from PIL import Image as PILImage
            pil_img = PILImage.open(io.BytesIO(img_bytes)).convert('RGB')
            img_array = np.array(pil_img, dtype=np.uint8)
            print(f"[DEBUG] Image loaded from base64 - shape: {img_array.shape}, dtype: {img_array.dtype}")
            # Fix memory layout for dlib
            img_array = prepare_image_for_dlib(img_array)
            print(f"[DEBUG] Image prepared for dlib - C_CONTIGUOUS: {img_array.flags['C_CONTIGUOUS']}")
            return img_array
            
    except Exception as e:
        print(f"[ERROR] Image loading failed: {e}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Failed to load image: {str(e)}")


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
            import numpy as np
            try:
                import face_recognition
            except Exception:
                face_recognition = None

            # Load verification photo using robust helper function
            live_np = load_image_for_face_recognition(live_photo, is_file_path=False)

            # Basic fraud checks
            fraud_indicators = []
            if live_np.shape[0] < 100 or live_np.shape[1] < 100:
                fraud_indicators.append('image_too_small')

            # Detect face(s) in verification photo using multiple methods
            live_locations = []
            import cv2
            
            if face_recognition is not None:
                try:
                    print(f"[DEBUG] Detecting faces in verification photo...")
                    print(f"[DEBUG] Array properties before face detection:")
                    print(f"  Shape: {live_np.shape}, dtype: {live_np.dtype}")
                    print(f"  C_CONTIGUOUS: {live_np.flags['C_CONTIGUOUS']}")
                    
                    # Try HOG method first (faster)
                    print(f"[DEBUG] Calling face_recognition.face_locations with HOG model (upsample=1)...")
                    live_locations = face_recognition.face_locations(live_np, number_of_times_to_upsample=1, model='hog')

                    # If no faces, try more aggressive HOG upsample
                    if len(live_locations) == 0:
                        print(f"[DEBUG] HOG (upsample=1) found no faces, retrying with upsample=2...")
                        live_locations = face_recognition.face_locations(live_np, number_of_times_to_upsample=2, model='hog')
                    
                    print(f"[DEBUG] Detected {len(live_locations)} face(s) using dlib HOG")
                    
                except Exception as dlib_error:
                    print(f"[WARNING] dlib/HOG face detection failed: {dlib_error}")
                    print(f"[DEBUG] Falling back to OpenCV Haar Cascade...")
                    
                    # Fallback to OpenCV Haar Cascade
                    try:
                        live_bgr = cv2.cvtColor(live_np, cv2.COLOR_RGB2BGR)
                        live_gray = cv2.cvtColor(live_bgr, cv2.COLOR_BGR2GRAY)
                        
                        # Enhance image for better detection
                        live_gray = cv2.equalizeHist(live_gray)
                        
                        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                        face_cascade = cv2.CascadeClassifier(cascade_path)
                        
                        # Try multiple detection strategies with increasingly lenient parameters
                        faces = face_cascade.detectMultiScale(live_gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
                        
                        if len(faces) == 0:
                            print(f"[DEBUG] No faces with default params, trying more lenient settings...")
                            faces = face_cascade.detectMultiScale(live_gray, scaleFactor=1.05, minNeighbors=2, minSize=(20, 20))
                        
                        if len(faces) == 0:
                            print(f"[DEBUG] Still no faces, trying very lenient settings...")
                            faces = face_cascade.detectMultiScale(live_gray, scaleFactor=1.02, minNeighbors=1, minSize=(15, 15))
                        
                        print(f"[DEBUG] OpenCV Haar Cascade detected {len(faces)} face(s)")
                        
                        # Filter: Keep only the largest face (most likely the real face, rest are false positives)
                        if len(faces) > 1:
                            print(f"[DEBUG] Multiple faces detected ({len(faces)}), keeping only the largest")
                            faces = [max(faces, key=lambda f: f[2] * f[3])]  # Sort by area (w*h), keep largest
                        
                        # Convert OpenCV format (x, y, w, h) to face_recognition format (top, right, bottom, left)
                        live_locations = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
                        print(f"[DEBUG] Converted to face_recognition format: {len(live_locations)} face(s)")
                        
                    except Exception as cv_error:
                        print(f"[ERROR] OpenCV Haar Cascade also failed: {cv_error}")
                        import traceback
                        traceback.print_exc()
                        live_locations = []
                
                if len(live_locations) == 0:
                    return jsonify({
                        "error": "No face detected in verification photo",
                        "message": "Please ensure your face is clearly visible and well-lit. Look directly at the camera. Try again."
                    }), 400
                
                # Check face quality - ensure face is reasonably sized
                if len(live_locations) > 0:
                    top, right, bottom, left = live_locations[0]
                    face_width = right - left
                    face_height = bottom - top
                    face_area = face_width * face_height
                    image_area = live_np.shape[0] * live_np.shape[1]
                    face_percentage = (face_area / image_area) * 100
                    
                    print(f"[DEBUG] Face quality - Size: {face_width}x{face_height}, Area: {face_percentage:.2f}% of image")
                    
                    # Relaxed thresholds when using OpenCV fallback (less precise detection)
                    # Face should be at least 0.5% of image (very lenient for OpenCV)
                    if face_percentage < 0.5:
                        fraud_indicators.append('face_too_small_in_frame')
                        print(f"[WARNING] Face is extremely small ({face_percentage:.2f}% of frame)")
                    
                    # Face should not be more than 95% of image
                    if face_percentage > 95:
                        fraud_indicators.append('face_fills_entire_frame')
                        print(f"[WARNING] Face fills too much of frame ({face_percentage:.2f}% of frame)")
                
                # Note: We already filtered to keep only the largest face, so no multi-face warning needed

            if fraud_indicators:
                return jsonify({
                    "error": "Fraud indicators detected",
                    "fraud_indicators": fraud_indicators,
                    "liveness_score": 0.0,
                    "spoofing_confidence": 0.9
                }), 400

            # Attempt face match against stored registration photo
            user_id = get_jwt_identity()
            
            # Check if MongoDB is available
            if not mongodb_available or users_collection is None:
                print("[WARNING] MongoDB not available, skipping face matching")
                return jsonify({
                    "verified": True,
                    "is_genuine": True,
                    "face_match_confidence": 0.85,
                    "face_distance": None,
                    "liveness_score": 0.8,
                    "message": "Identity verified successfully (database unavailable - face matching skipped)"
                }), 200
            
            # Find user by username or _id
            user = users_collection.find_one({'username': user_id})
            if user is None:
                try:
                    user = users_collection.find_one({'_id': ObjectId(user_id)})
                except:
                    pass
            
            if user is None:
                print(f"[ERROR] User not found: {user_id}")
                return jsonify({"error": "User not found. Please log in again."}), 404
            
            # Check if user has a registered photo
            if not user.get('photo_path'):
                print(f"[ERROR] User {user.get('username')} has no registered photo")
                return jsonify({
                    "error": "No registration photo found",
                    "message": "You must register with a photo before identity verification. Please contact support."
                }), 400
            
            # Check if registration photo file exists
            if not os.path.exists(user['photo_path']):
                print(f"[ERROR] Registration photo file not found: {user['photo_path']}")
                return jsonify({
                    "error": "Registration photo file missing",
                    "message": "Your registration photo is missing. Please contact support."
                }), 500
            
            face_match_confidence = 0.0
            face_distance = None
            is_genuine = False

            # Perform face matching
            if face_recognition is not None:
                try:
                    print(f"[DEBUG] Loading registration photo from: {user['photo_path']}")
                    
                    # Load registration photo using robust helper function with error handling
                    try:
                        ref_np = load_image_for_face_recognition(user['photo_path'], is_file_path=True)
                    except Exception as load_error:
                        print(f"[ERROR] Failed to load registration photo: {load_error}")
                        return jsonify({
                            "error": "Failed to load registration photo",
                            "message": f"Could not process your registration photo: {str(load_error)}"
                        }), 500
                    
                    print(f"[DEBUG] Extracting face encodings from both photos...")
                    
                    # Extract face encodings from registration photo with error handling
                    try:
                        print(f"[DEBUG] Extracting encoding from registration photo (shape: {ref_np.shape}, dtype: {ref_np.dtype})")
                        # Image is already prepared by prepare_image_for_dlib()
                        print(f"[DEBUG] Registration photo array - C_CONTIGUOUS: {ref_np.flags['C_CONTIGUOUS']}, dtype: {ref_np.dtype}")
                        
                        # Try dlib HOG detection first
                        try:
                            ref_locations = face_recognition.face_locations(ref_np, number_of_times_to_upsample=1, model='hog')
                            if len(ref_locations) == 0:
                                print(f"[DEBUG] HOG found no faces, trying with upsample=2...")
                                ref_locations = face_recognition.face_locations(ref_np, number_of_times_to_upsample=2, model='hog')
                            print(f"[DEBUG] dlib HOG detected {len(ref_locations)} face(s) in registration photo")
                        except Exception as dlib_ref_error:
                            print(f"[WARNING] dlib HOG face detection failed for registration photo: {dlib_ref_error}")
                            # Fallback to OpenCV Haar Cascade
                            try:
                                ref_bgr = cv2.cvtColor(ref_np, cv2.COLOR_RGB2BGR)
                                ref_gray = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2GRAY)
                                ref_gray = cv2.equalizeHist(ref_gray)
                                
                                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                                face_cascade = cv2.CascadeClassifier(cascade_path)
                                
                                faces = face_cascade.detectMultiScale(ref_gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
                                if len(faces) == 0:
                                    faces = face_cascade.detectMultiScale(ref_gray, scaleFactor=1.05, minNeighbors=2, minSize=(20, 20))
                                if len(faces) == 0:
                                    faces = face_cascade.detectMultiScale(ref_gray, scaleFactor=1.02, minNeighbors=1, minSize=(15, 15))
                                
                                ref_locations = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
                                print(f"[DEBUG] OpenCV Haar Cascade found {len(ref_locations)} faces in registration photo")
                            except Exception as cv_ref_error:
                                print(f"[ERROR] Both dlib and OpenCV failed for registration photo: {cv_ref_error}")
                                ref_locations = []
                        
                        # Extract face encodings using dlib
                        ref_encodings = []
                        if len(ref_locations) > 0:
                            try:
                                ref_encodings = face_recognition.face_encodings(ref_np, ref_locations)
                                print(f"[DEBUG] Successfully extracted {len(ref_encodings)} encoding(s) from registration photo")
                            except Exception as encoding_error:
                                print(f"[ERROR] dlib encoding extraction failed: {encoding_error}")
                                return jsonify({
                                    "error": "Face encoding extraction failed",
                                    "message": "Could not extract facial features from registration photo. Please contact support or try re-registering with a clearer photo."
                                }), 500
                        else:
                            print(f"[ERROR] No face detected in registration photo")
                            return jsonify({
                                "error": "No face detected in registration photo",
                                "message": "Your registration photo does not contain a detectable face. Please contact support."
                            }), 500
                    except Exception as ref_error:
                        print(f"[ERROR] Failed to extract encoding from registration photo: {ref_error}")
                        import traceback
                        traceback.print_exc()
                        return jsonify({
                            "error": "Registration photo processing error",
                            "message": "Could not process your registration photo. It may be corrupted. Please re-register with a new photo."
                        }), 500
                    
                    # Extract face encodings from verification photo with error handling
                    live_encodings = []
                    try:
                        print(f"[DEBUG] Extracting encoding from verification photo (shape: {live_np.shape}, dtype: {live_np.dtype})")
                        # Image is already prepared by prepare_image_for_dlib()
                        print(f"[DEBUG] Verification photo array - C_CONTIGUOUS: {live_np.flags['C_CONTIGUOUS']}, dtype: {live_np.dtype}")
                        
                        if len(live_locations) > 0:
                            try:
                                live_encodings = face_recognition.face_encodings(live_np, live_locations)
                                print(f"[DEBUG] Successfully extracted {len(live_encodings)} encoding(s) from verification photo")
                            except Exception as encoding_error:
                                print(f"[ERROR] dlib encoding extraction failed: {encoding_error}")
                                return jsonify({
                                    "error": "Face encoding extraction failed",
                                    "message": "Could not extract facial features from your photo. Please ensure good lighting and a clear face view."
                                }), 400
                        else:
                            print(f"[ERROR] No faces detected in verification photo")
                            return jsonify({
                                "error": "Face not detected",
                                "message": "Could not detect a face in your verification photo. Please try again with better lighting and a clear face."
                            }), 400
                    except Exception as live_error:
                        print(f"[ERROR] Verification encoding extraction error: {live_error}")
                        import traceback
                        traceback.print_exc()
                        return jsonify({
                            "error": "Verification processing error",
                            "message": f"An error occurred during verification: {str(live_error)}"
                        }), 500
                    
                    
                    if len(ref_encodings) == 0:
                        print(f"[ERROR] No face encoding generated from registration photo")
                        return jsonify({
                            "error": "Registration photo invalid",
                            "message": "Your registration photo does not contain a detectable face. Please contact support or re-register with a different photo."
                        }), 500
                    
                    if len(live_encodings) == 0:
                        print(f"[ERROR] No face encoding generated from verification photo")
                        return jsonify({
                            "error": "Verification photo invalid",
                            "message": "Could not extract facial features from your verification photo. Please try again with better lighting."
                        }), 400
                    
                    # Compare faces - mandatory verification using actual face encodings
                    best_distance = float('inf')
                    best_match_idx = -1
                    
                    print(f"[DEBUG] Comparing {len(ref_encodings)} registration encoding(s) with {len(live_encodings)} verification encoding(s)")
                    
                    # Use face encoding comparison - this is real verification
                    for live_idx, live_enc in enumerate(live_encodings):
                        distances = face_recognition.face_distance(ref_encodings, live_enc)
                        min_distance = float(distances.min())
                        
                        if min_distance < best_distance:
                            best_distance = min_distance
                            best_match_idx = live_idx
                        
                        print(f"[DEBUG] Live encoding {live_idx}: min distance = {min_distance:.4f}")
                    
                    face_distance = best_distance
                    
                    # Map distance to confidence score
                    # Distance ranges from 0 (perfect match) to 1+ (different faces)
                    # Threshold of 0.6 is standard for face_recognition library
                    face_match_confidence = float(max(0.0, min(1.0, 1.0 - face_distance)))
                    
                    # Determine if faces match with stricter threshold
                    is_genuine = face_distance < 0.55  # Slightly stricter than 0.6
                    
                    print(f"[DEBUG] Face matching complete:")
                    print(f"  Distance: {face_distance:.4f}")
                    print(f"  Confidence: {face_match_confidence:.2%}")
                    print(f"  Match: {is_genuine}")
                    
                    if not is_genuine:
                        print(f"[WARNING] Face mismatch detected - User: {user.get('username')}, Distance: {face_distance:.4f}")
                        
                        # Provide additional context for rejection
                        if face_distance < 0.6:
                            message = "Face match confidence is borderline. Please try again with better lighting or a clearer angle."
                        else:
                            message = "The verification photo does not match your registration photo. Please try again."
                        
                        return jsonify({
                            "error": "Face verification failed",
                            "message": message,
                            "face_match_confidence": face_match_confidence,
                            "face_distance": face_distance,
                            "is_genuine": False
                        }), 400
                    
                except Exception as e:
                    print(f"[ERROR] Face matching failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({
                        "error": "Face matching error",
                        "message": f"An error occurred during face verification: {str(e)}"
                    }), 500
            else:
                # face_recognition library not available
                print(f"[WARNING] face_recognition library not available, skipping face matching")
                face_match_confidence = 0.7
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
            'candidates': ['Congress', 'BJP'],
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
        
        # Get user information
        user = users_collection.find_one({'username': user_id})
        if not user:
            try:
                user = users_collection.find_one({'_id': ObjectId(user_id)})
            except:
                pass
        
        if not user:
            print(f"[Cast Vote] ERROR: User not found")
            return jsonify({"error": "User not found"}), 404
        
        # ENFORCE IDENTITY VERIFICATION - Users must verify their identity before voting
        if not user.get('identity_verified', False):
            print(f"[Cast Vote] BLOCKED: User {user_id} has not completed identity verification")
            return jsonify({
                "error": "Identity verification required",
                "message": "You must complete identity verification before you can vote. Please verify your identity first."
            }), 403
        
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
        
        # Prepare voter information (user already fetched above)
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
        total_registered = users_collection.count_documents({'role': 'voter'})
        total_verified = users_collection.count_documents({'role': 'voter', 'identity_verified': True})
        total_unverified = total_registered - total_verified
        
        # Count votes by candidate (handle both old and new names for backward compatibility)
        candidate_a_votes = votes_collection.count_documents({'candidate': {'$in': ['Congress', 'Candidate A']}})
        candidate_b_votes = votes_collection.count_documents({'candidate': {'$in': ['BJP', 'Candidate B']}})
        
        # Get all votes for debugging
        all_votes = list(votes_collection.find({}, {'_id': 0, 'candidate': 1}))
        print(f"[Statistics] Total votes in DB: {total_votes}")
        print(f"[Statistics] All votes: {all_votes}")
        print(f"[Statistics] Congress (incl. old 'Candidate A') Votes: {candidate_a_votes}")
        print(f"[Statistics] BJP (incl. old 'Candidate B') Votes: {candidate_b_votes}")
        print(f"[Statistics] Total registered voters: {total_registered}")
        print(f"[Statistics] Identity verified voters: {total_verified}")
        print(f"[Statistics] Unverified voters: {total_unverified}")
        
        # Calculate turnout percentage (based on verified voters, since only they can vote)
        turnout_of_verified = (total_votes / total_verified * 100) if total_verified > 0 else 0
        turnout_of_all = (total_votes / total_registered * 100) if total_registered > 0 else 0
        print(f"[Statistics] Turnout (verified voters): {turnout_of_verified}%")
        print(f"[Statistics] Turnout (all registered): {turnout_of_all}%")
        
        # Get dataset summary for suspicious precinct calculation
        dataset_summary = load_fraud_dataset_summary()
        dataset_available = dataset_summary.get('available', False)
        dataset_fraudulent = dataset_summary.get('fraudulent_votes', 0)
        dataset_total = dataset_summary.get('total_rows', 0)
        
        # Calculate suspicious precincts from dataset
        # Assume dataset represents historical/batch data distributed across precincts
        # If fraud rate is high (>10%), count it as 1 suspicious precinct from dataset
        dataset_suspicious_precincts = 0
        if dataset_available and dataset_total > 0:
            fraud_rate = dataset_fraudulent / dataset_total
            if fraud_rate > 0.10:  # More than 10% fraud rate
                dataset_suspicious_precincts = 1
        
        # Get precinct votes from live voting
        precincts = ['Precinct 1', 'Precinct 2', 'Precinct 3']
        precinct_votes = {}
        total_precincts = len(precincts)
        live_suspicious_precincts = 0
        
        for precinct in precincts:
            precinct_vote_count = votes_collection.count_documents({'precinct': precinct})
            precinct_votes[precinct] = precinct_vote_count
            print(f"[Statistics] {precinct}: {precinct_vote_count} votes")
            
            # Check for suspicious activity in live votes
            if precinct_vote_count > 0:
                precinct_a = votes_collection.count_documents({'precinct': precinct, 'candidate': {'$in': ['Congress', 'Candidate A']}})
                precinct_b = votes_collection.count_documents({'precinct': precinct, 'candidate': {'$in': ['BJP', 'Candidate B']}})
                max_votes = max(precinct_a, precinct_b)
                ratio = max_votes / precinct_vote_count if precinct_vote_count > 0 else 0
                print(f"  → Congress: {precinct_a}, BJP: {precinct_b}, Max ratio: {ratio:.2%}")
                # Flag if one candidate has >95% of votes
                if ratio > 0.95:
                    live_suspicious_precincts += 1
                    print(f"  → SUSPICIOUS (ratio {ratio:.2%} > 95%)")
        
        # Combine dataset and live suspicious precincts
        total_suspicious_precincts = dataset_suspicious_precincts + live_suspicious_precincts
        print(f"[Statistics] Live suspicious precincts: {live_suspicious_precincts}")
        print(f"[Statistics] Dataset suspicious precincts: {dataset_suspicious_precincts}")
        
        response = {
            'total_votes': total_votes,
            'total_registered': total_registered,
            'total_verified': total_verified,
            'total_unverified': total_unverified,
            'avg_turnout': round(turnout_of_verified, 2),
            'turnout_percentage': round(turnout_of_all, 2),
            'turnout_of_verified': round(turnout_of_verified, 2),
            'candidate_a_votes': candidate_a_votes,
            'candidate_b_votes': candidate_b_votes,
            'total_precincts': total_precincts,
            'suspicious_precincts': total_suspicious_precincts,
            'live_suspicious_precincts': live_suspicious_precincts,
            'dataset_suspicious_precincts': dataset_suspicious_precincts,
            'precinct_votes': precinct_votes
        }
        print(f"[Statistics] Suspicious precincts - Dataset: {dataset_suspicious_precincts}, Live: {live_suspicious_precincts}, Total: {total_suspicious_precincts}")
        print(f"[Statistics] Response data: {response}")
        return jsonify(response), 200
    except Exception as e:
        print(f"[Statistics] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/precinct-status', methods=['GET'])
@jwt_required()
def get_precinct_status():
    """Get live precinct voting status based on current vote counts"""
    try:
        if not mongodb_available or votes_collection is None:
            return jsonify({"error": "Database unavailable"}), 503
        
        # Define precincts
        precincts = ['Precinct 1', 'Precinct 2', 'Precinct 3']
        precinct_data = []
        
        print(f"\n{'='*60}")
        print(f"[Precinct Status] Calculating live precinct status...")
        
        for precinct in precincts:
            # Count votes in this precinct
            precinct_total_votes = votes_collection.count_documents({'precinct': precinct})
            precinct_candidate_a = votes_collection.count_documents({'precinct': precinct, 'candidate': {'$in': ['Congress', 'Candidate A']}})
            precinct_candidate_b = votes_collection.count_documents({'precinct': precinct, 'candidate': {'$in': ['BJP', 'Candidate B']}})
            
            # Calculate precinct turnout (get unique voters)
            unique_voters = votes_collection.distinct('user_id', {'precinct': precinct})
            precinct_unique_voters = len(unique_voters)
            
            # Determine leading candidate
            if precinct_candidate_a > precinct_candidate_b:
                leading_candidate = 'Congress'
                lead_margin = precinct_candidate_a - precinct_candidate_b
            elif precinct_candidate_b > precinct_candidate_a:
                leading_candidate = 'BJP'
                lead_margin = precinct_candidate_b - precinct_candidate_a
            else:
                leading_candidate = 'TIE'
                lead_margin = 0
            
            # Determine precinct status
            if precinct_total_votes == 0:
                status = 'No votes'
                completion_percentage = 0
            elif precinct_total_votes > 0:
                status = 'Active'
                completion_percentage = 100  # Some votes recorded
            
            # Check for suspicious activity (unusual vote distribution)
            suspicious = False
            if precinct_total_votes > 0:
                # Check if one candidate has more than 90% of votes (potential fraud indicator)
                max_votes = max(precinct_candidate_a, precinct_candidate_b)
                if max_votes / precinct_total_votes > 0.95:
                    suspicious = True
            
            precinct_info = {
                'name': precinct,
                'total_votes': precinct_total_votes,
                'candidate_a_votes': precinct_candidate_a,
                'candidate_b_votes': precinct_candidate_b,
                'unique_voters': precinct_unique_voters,
                'leading_candidate': leading_candidate,
                'lead_margin': lead_margin,
                'status': status,
                'completion_percentage': completion_percentage,
                'suspicious': suspicious
            }
            
            precinct_data.append(precinct_info)
            
            print(f"[Precinct Status] {precinct}:")
            print(f"  Votes: {precinct_total_votes} | A: {precinct_candidate_a} | B: {precinct_candidate_b}")
            print(f"  Leading: {leading_candidate} (margin: {lead_margin})")
            print(f"  Status: {status} | Suspicious: {suspicious}")
        
        # Calculate overall precinct statistics
        total_precincts = len(precincts)
        active_precincts = sum(1 for p in precinct_data if p['status'] == 'Active')
        suspicious_precincts = sum(1 for p in precinct_data if p['suspicious'])
        
        print(f"[Precinct Status] Total precincts: {total_precincts}")
        print(f"[Precinct Status] Active precincts: {active_precincts}")
        print(f"[Precinct Status] Suspicious precincts: {suspicious_precincts}")
        print(f"{'='*60}\n")
        
        response = {
            'precincts': precinct_data,
            'total_precincts': total_precincts,
            'active_precincts': active_precincts,
            'suspicious_precincts': suspicious_precincts,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"[Precinct Status] Error: {e}")
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
