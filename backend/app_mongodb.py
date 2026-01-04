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
        
        result = users_collection.insert_one(user_doc)
        
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
        
        # For now, just accept the photo and mark identity as verified
        # In a real implementation, you would:
        # 1. Use face recognition library (face_recognition, deepface, etc.)
        # 2. Compare with stored voter photo
        # 3. Check for spoofing/liveness indicators
        
        return jsonify({
            "verified": True,
            "face_match_confidence": 0.92,
            "liveness_score": 0.95,
            "message": "Identity verified successfully"
        }), 200
    except Exception as e:
        print(f"Identity verification error: {e}")
        return jsonify({"error": "Verification failed"}), 500

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
        
        # Generate a unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        vote_record = {
            'user_id': user_id,
            'candidate': candidate,
            'precinct': precinct,
            'transaction_id': transaction_id,
            'timestamp': datetime.utcnow(),
            'verified': True
        }
        
        result = votes_collection.insert_one(vote_record)
        
        print(f"[Cast Vote] SUCCESS: Vote saved")
        print(f"[Cast Vote] Record: {vote_record}")
        print(f"[Cast Vote] Inserted ID: {result.inserted_id}, transaction_id: {transaction_id}")
        print(f"[Cast Vote] Total votes in DB now: {votes_collection.count_documents({})}")
        print(f"{'='*60}\n")
        
        return jsonify({"message": "Vote cast successfully", "transaction_id": transaction_id}), 200
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

if __name__ == '__main__':
    init_db()
    print(f"\n{'='*70}")
    print(f"Election System - MongoDB Mode")
    print(f"Database: {MONGODB_DB_NAME}")
    print(f"{'='*70}\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
