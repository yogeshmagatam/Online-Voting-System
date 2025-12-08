# Role-Based Authentication Implementation Guide

## Overview
This document describes the role-based authentication system implemented for the Online Voting System. The system supports three distinct user roles: **Voter**, **Candidate**, and **Admin**, each with specific permissions and features.

## Architecture

### Backend (Python/Flask)

#### 1. Role-Based Decorator
A new `@role_required()` decorator has been added to protect endpoints based on user roles.

**Location:** `backend/app.py` (after security headers)

```python
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
                log_security_event('unauthorized_role_access', {...})
                return jsonify({"error": "Unauthorized: insufficient permissions"}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

#### 2. Role Claims in JWT
When a user logs in successfully, the JWT includes their role in the claims:

```python
additional_claims = {
    'role': user['role'],
    'session_id': session_id,
    'jti': str(uuid.uuid4())
}

access_token = create_access_token(
    identity=username,
    additional_claims=additional_claims
)
```

#### 3. Protected Endpoints by Role

**Admin-Only Endpoints:**
- `POST /api/election-data` - Add election data
- `POST /api/analyze` - Run fraud detection
- `GET /api/anomaly-detection` - View behavioral logs
- `POST /api/anomaly-detection/analyze` - Analyze anomalies
- `GET /api/votes` - View all votes
- `GET /api/statistics/benford` - Benford's Law analysis

**Voter-Only Endpoints:**
- `POST /api/cast-vote` - Cast a vote

**All Authenticated Users:**
- `GET /api/election-data` - View election data
- `GET /api/statistics` - View statistics
- `POST /api/verify-identity` - Identity verification
- `GET /api/health` - Health check

### Frontend (React)

#### 1. RoleProtectedRoute Component
A new component (`frontend/src/components/RoleProtectedRoute.js`) provides client-side route protection:

```javascript
<RoleProtectedRoute 
  userRole={userRole} 
  requiredRoles={['admin']}
  fallback={<AccessDeniedPage />}
>
  <AdminDashboard />
</RoleProtectedRoute>
```

#### 2. Role-Specific Dashboards

**VoterDashboard** (`frontend/src/components/VoterDashboard.js`)
- Identity verification via face recognition
- Vote casting interface
- Candidate selection
- Precinct selection
- Vote confirmation

**CandidateDashboard** (`frontend/src/components/CandidateDashboard.js`)
- Vote distribution charts
- Precinct-level statistics
- Turnout analysis
- Vote tallies by candidate

**AdminDashboard** (`frontend/src/components/AdminDashboard.js`)
- Election data entry
- Fraud detection (ML analysis)
- Benford's Law analysis
- Suspicious precinct flagging
- Comprehensive analytics

#### 3. App.js Routing
The main App component now renders different dashboards based on user role:

```javascript
const renderDashboard = () => {
  switch (userRole) {
    case 'admin':
      return <AdminDashboard token={token} onLogout={handleLogout} />;
    case 'voter':
      return <VoterDashboard token={token} onLogout={handleLogout} />;
    case 'candidate':
      return <CandidateDashboard token={token} onLogout={handleLogout} />;
    default:
      return <Dashboard token={token} userRole={userRole} onLogout={handleLogout} />;
  }
};
```

#### 4. Enhanced Login Flow
The Login component now supports MFA verification:

- Initial login with username/password
- Optional MFA requirement (email or app-based)
- MFA code verification before accessing dashboard

## User Registration by Role

### Voter Registration
```
POST /api/register/voter
Required Fields:
- username
- password (12+ chars, letters, numbers, special chars)
- voter_id (from master voter list)
- email
- phone (optional)
- photo (face capture)
- captcha
```

### Candidate Registration
```
POST /api/register/candidate
Required Fields:
- username
- password (12+ chars, letters, numbers, special chars)
- email
- phone (optional)
- photo (face capture)
- captcha
```

### Admin User
- Created automatically during database initialization
- Default credentials: admin/admin123 (CHANGE IN PRODUCTION)

## Security Features by Role

### Voter Security
1. **Identity Verification**: Face recognition verification before voting
2. **Single Vote Enforcement**: Prevents duplicate votes
3. **Voter Master List**: Validates voter eligibility
4. **Vote Encryption**: Homomorphic encryption for vote data
5. **Transaction ID**: Unique identifier for each vote
6. **Account Lockout**: After 5 failed login attempts (30 minutes)
7. **MFA Support**: App-based or email-based two-factor authentication

### Candidate Security
1. **Limited Dashboard Access**: View-only access to election statistics
2. **Personal Data Protection**: Cannot modify election data
3. **Session Tracking**: All actions are logged
4. **Token Expiration**: 1-hour JWT token lifespan

### Admin Security
1. **Full System Access**: Can add and modify election data
2. **Fraud Detection**: Run ML-based anomaly detection
3. **Behavioral Analysis**: Track user actions for suspicious patterns
4. **Audit Trails**: All admin actions are logged with timestamps and IP
5. **Benford's Law Analysis**: Statistical validation of vote counts
6. **Rate Limiting**: Enhanced rate limiting for sensitive endpoints

## Authentication Flow

### Login Process
1. User submits username/password
2. Backend validates credentials
3. If MFA enabled:
   - Generate/send OTP
   - Return `mfa_required: true`
   - User enters code
   - Backend verifies code
4. On success:
   - Generate JWT with role claim
   - Return access token and role
5. Frontend stores token and role in localStorage
6. Frontend routes to appropriate dashboard

### Access Control Flow
1. User attempts to access protected resource
2. Frontend sends JWT in Authorization header
3. Backend validates JWT signature
4. Backend extracts user role from JWT claims
5. If role not in required roles:
   - Return 403 Unauthorized
   - Log security event
6. If role matches:
   - Execute endpoint logic

## Testing the System

### Test as Voter
```bash
# Register as voter
- Username: voter1
- Voter ID: VID12345 (from master list)
- Password: SecurePass123!
- Photo: Upload face photo

# Login
- Username: voter1
- Password: SecurePass123!
- MFA Code: (if enabled)

# Verify Identity
- Take live photo for face verification

# Cast Vote
- Select candidate
- Select precinct
- Submit vote
```

### Test as Candidate
```bash
# Register as candidate
- Username: candidate1
- Password: SecurePass123!
- Photo: Upload face photo

# Login
- Username: candidate1
- Password: SecurePass123!

# Access Dashboard
- View only election statistics
- Cannot modify data
```

### Test as Admin
```bash
# Default Admin Account
- Username: admin
- Password: admin123

# Access Dashboard
- Add election data
- Run fraud detection
- Analyze anomalies
- View all votes
- Run Benford's analysis
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password BLOB NOT NULL,
    role TEXT NOT NULL,  -- 'voter', 'candidate', 'admin'
    photo_path TEXT,
    face_encoding BLOB,
    mfa_secret TEXT,
    mfa_type TEXT,  -- 'app', 'email', 'none'
    email TEXT,
    phone TEXT,
    verified BOOLEAN,
    voter_id TEXT UNIQUE,
    national_id TEXT UNIQUE,
    failed_login_attempts INTEGER,
    account_locked BOOLEAN,
    lock_expiration TEXT,
    salt BLOB,
    last_password_change TEXT,
    require_password_change BOOLEAN
);
```

## Configuration & Environment Variables

### Backend Configuration
```python
# Security
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secret-key')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

# Feature Flags
ALLOW_VOTER_VALIDATION_BYPASS = True  # Dev only
ALLOW_ID_VERIFICATION_BYPASS = True   # Dev only
ALLOW_AUTO_FACE_ENROLLMENT = True     # Dev only

# Rate Limiting
default_limits=["200 per day", "50 per hour"]
```

### Frontend Configuration
```javascript
// API Endpoint
const API_URL = 'http://localhost:5000'

// Token Storage
localStorage.setItem('token', access_token)
localStorage.setItem('userRole', role)
```

## Security Best Practices

1. **Change Default Admin Password** in production
2. **Enable HTTPS** for all communications
3. **Disable Development Flags** in production:
   - ALLOW_VOTER_VALIDATION_BYPASS
   - ALLOW_ID_VERIFICATION_BYPASS
   - ALLOW_AUTO_FACE_ENROLLMENT
4. **Use Strong JWT Secrets**
5. **Enable MFA** for all user types
6. **Regular Audit Logs Review**
7. **Database Encryption** for sensitive data
8. **Rate Limiting** on all authentication endpoints

## Troubleshooting

### User Cannot Login After Role Assignment
- Check JWT is properly including role in claims
- Verify role matches expected values: 'voter', 'candidate', 'admin'
- Check localStorage for correct role storage

### Dashboard Not Loading
- Verify JWT token is valid
- Check token expiration time
- Clear localStorage and re-login
- Verify role claim exists in JWT

### Access Denied Errors
- Confirm user role matches endpoint requirements
- Check role_required decorator on endpoint
- Review security logs for authorization attempts

### MFA Not Working
- Verify MAIL_SERVER configuration if using email MFA
- Check mfa_secret is properly generated
- Verify timestamp synchronization for app-based MFA

## Future Enhancements

1. **Role Hierarchy**: Sub-roles for election observers, auditors
2. **Permission Granularity**: Specific permissions instead of role-based
3. **OAuth Integration**: Third-party authentication providers
4. **Biometric Authentication**: Fingerprint/iris recognition
5. **Delegation**: Admin role delegation for specific tasks
6. **Audit Dashboard**: Comprehensive activity monitoring
7. **Role-Based API**: Dynamic role and permission management

## Support & Documentation

For additional help, refer to:
- Backend security logs in `logs/security_*.log`
- Database security_logs table
- JWT token decoding at jwt.io
- Flask-JWT-Extended documentation
