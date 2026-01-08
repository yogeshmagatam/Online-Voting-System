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
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ["headers", "cookies"]
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
jwt = JWTManager(app)

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
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db = mongo_client[MONGODB_DB_NAME]
    print(f"✓ MongoDB connected: {MONGODB_DB_NAME}")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    exit(1)

users_collection = db['users']
login_otp_collection = db['login_otp']
master_voter_list_collection = db['master_voter_list']
votes_collection = db['votes']

# Initialize fraud detection and behavior tracking (local only)
initialize_fraud_detector()
initialize_behavior_tracker(db)
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
        # Mark all previous unverified OTPs as invalid (but don't delete them)
        login_otp_collection.update_many(
            {
                'user_id': user_id,
                'verified': False
            },
            {'$set': {'invalid': True}}
        )
        
        otp_code = generate_4digit_otp()
        now = datetime.utcnow()
        
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
        
        otp_record = login_otp_collection.find_one({
            'user_id': user_id,
            'verified': False,
            'invalid': {'$ne': True}
        }, sort=[('created_at', -1)])
        
        if not otp_record:
            print(f"[OTP Verify] No valid OTP found for user_id={user_id}")
            return False, "No OTP found"
        
        print(f"[OTP Verify] Found OTP record: code={otp_record['otp_code']}, expires_at={otp_record['expires_at']}, now={datetime.utcnow()}")
        
        if datetime.utcnow() > otp_record['expires_at']:
            print(f"[OTP Verify] OTP expired")
            login_otp_collection.update_one(
                {'_id': otp_record['_id']},
                {'$set': {'invalid': True}}
            )
            return False, "OTP expired"
        
        stored_code = str(otp_record['otp_code']).strip()
        provided_code = str(otp_code).strip()
        print(f"[OTP Verify] Comparing: stored='{stored_code}' vs provided='{provided_code}'")
        
        if stored_code != provided_code:
            print(f"[OTP Verify] OTP mismatch!")
            login_otp_collection.update_one(
                {'_id': otp_record['_id']},
                {'$inc': {'attempts': 1}}
            )
            return False, "Invalid OTP"
        
        print(f"[OTP Verify] OTP matched! Marking as verified")
        login_otp_collection.update_one(
            {'_id': otp_record['_id']},
            {'$set': {'verified': True}}
        )
        return True, "OTP verified"
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

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
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
            img = Image.open(io.BytesIO(img_bytes))
            
            # Force convert to RGB mode (simplest approach - always works)
            img = img.convert('RGB')
            
            # Convert to numpy array with explicit 8-bit unsigned integer type
            live_np = np.array(img, dtype=np.uint8)
            
            # Ensure contiguous memory layout (required by dlib)
            if not live_np.flags['C_CONTIGUOUS']:
                live_np = np.ascontiguousarray(live_np, dtype=np.uint8)
            
            # Final validation
            if len(live_np.shape) != 3 or live_np.shape[2] != 3:
                raise ValueError(f"Invalid image shape: {live_np.shape}, expected (H, W, 3)")
            if live_np.dtype != np.uint8:
                live_np = live_np.astype(np.uint8)

            # Basic fraud checks
            fraud_indicators = []
            if live_np.shape[0] < 100 or live_np.shape[1] < 100:
                fraud_indicators.append('image_too_small')

            # Detect face(s)
            if face_recognition:
                live_locations = face_recognition.face_locations(live_np)
                if len(live_locations) == 0:
                    fraud_indicators.append('no_face_detected')
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
            user = users_collection.find_one({'username': user_id}) or users_collection.find_one({'_id': ObjectId(user_id)})
            face_match_confidence = 0.0
            face_distance = None
            is_genuine = True

            if face_recognition and user and user.get('photo_path') and os.path.exists(user['photo_path']):
                try:
                    ref_img = Image.open(user['photo_path'])
                    # Force convert to RGB
                    ref_img = ref_img.convert('RGB')
                    
                    # Convert to numpy array with explicit 8-bit unsigned integer type
                    ref_np = np.array(ref_img, dtype=np.uint8)
                    
                    # Ensure contiguous memory layout
                    if not ref_np.flags['C_CONTIGUOUS']:
                        ref_np = np.ascontiguousarray(ref_np, dtype=np.uint8)
                    
                    # Validate shape
                    if len(ref_np.shape) != 3 or ref_np.shape[2] != 3:
                        raise ValueError(f"Invalid reference image shape: {ref_np.shape}")
                    if ref_np.dtype != np.uint8:
                        ref_np = ref_np.astype(np.uint8)
                    
                    ref_encodings = face_recognition.face_encodings(ref_np)
                    live_encodings = face_recognition.face_encodings(live_np)
                    if ref_encodings and live_encodings:
                        dist = face_recognition.face_distance([ref_encodings[0]], live_encodings[0])[0]
                        face_distance = float(dist)
                        # Map distance [0,1+] to confidence [0,1]
                        face_match_confidence = float(max(0.0, min(1.0, 1.0 - dist)))
                        is_genuine = dist < 0.6
                    else:
                        is_genuine = True
                except Exception as e:
                    print(f"Face match error: {e}")

            # Simple liveness heuristic (presence of a face + reasonable size)
            liveness_score = 0.95 if face_recognition else 0.8

            # Optionally log success
            try:
                logs_dir = os.path.join(os.getcwd(), 'backend', 'logs')
                os.makedirs(logs_dir, exist_ok=True)
                log_path = os.path.join(logs_dir, f"security_{datetime.utcnow().date()}.log")
                with open(log_path, 'a', encoding='utf-8') as f:
                    entry = {
                        "username": user.get('username') if user else None,
                        "user_id": str(user.get('_id')) if user else None,
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
            return jsonify({"error": f"Verification failed: {str(e)}"}), 500
    except Exception as e:
        print(f"Identity verification error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Verification failed: {str(e)}"}), 500

@app.route('/api/election-data', methods=['GET'])
@jwt_required()
def get_election_data():
    try:
        return jsonify({
            'candidates': ['Narendra Modi ji', 'Rahul Gandhi ji'],
            'precincts': ['Precinct 1', 'Precinct 2', 'Precinct 3']
        }), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch data"}), 500

@app.route('/api/cast-vote', methods=['POST'])
@jwt_required()
def cast_vote():
    try:
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
        
        # Store fraud assessment
        behavior_tracker.store_fraud_assessment(fraud_assessment)
        
        print(f"[Fraud Detection] Risk: {fraud_assessment['risk_level']} "
              f"(probability: {fraud_assessment['fraud_probability']:.4f})")
        
        # Block high-risk votes
        if fraud_assessment['recommended_action'] == 'block':
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
        total_votes = votes_collection.count_documents({})
        total_users = users_collection.count_documents({'role': 'voter'})
        
        # Count votes by candidate
        candidate_a_votes = votes_collection.count_documents({'candidate': 'Narendra Modi ji'})
        candidate_b_votes = votes_collection.count_documents({'candidate': 'Rahul Gandhi ji'})
        
        # Get all votes for debugging
        all_votes = list(votes_collection.find({}, {'_id': 0, 'candidate': 1}))
        print(f"[Statistics] Total votes in DB: {total_votes}")
        print(f"[Statistics] All votes: {all_votes}")
        print(f"[Statistics] Narendra Modi ji votes: {candidate_a_votes}")
        print(f"[Statistics] Rahul Gandhi ji votes: {candidate_b_votes}")
        
        # Calculate turnout percentage
        turnout = (total_votes / total_users * 100) if total_users > 0 else 0
        
        return jsonify({
            'total_votes': total_votes,
            'total_registered': total_users,
            'avg_turnout': turnout,
            'turnout_percentage': turnout,
            'candidate_a_votes': candidate_a_votes,
            'candidate_b_votes': candidate_b_votes,
            'total_precincts': 0,
            'suspicious_precincts': 0
        }), 200
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
        
        total_users = users_collection.count_documents({})
        total_voters = users_collection.count_documents({'role': 'voter'})
        total_candidates = users_collection.count_documents({'role': 'candidate'})
        total_admins = users_collection.count_documents({'role': 'admin'})
        verified_voters = users_collection.count_documents({'role': 'voter', 'identity_verified': True})
        total_attempts = login_otp_collection.count_documents({})
        
        print(f"[Admin Stats] total_users={total_users}, total_voters={total_voters}, total_candidates={total_candidates}, verified_voters={verified_voters}")
        
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
    app.run(debug=True, host='0.0.0.0', port=5000)
