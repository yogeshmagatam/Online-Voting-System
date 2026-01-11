# Election System with AI-Powered Fraud Detection

A comprehensive web-based voting system with **Random Forest** fraud detection using machine learning to ensure election integrity.

## Features

- **User Authentication**: Multi-factor authentication with email OTP
- **Identity Verification**: Facial recognition for voter verification using face_recognition library
- **Secure Voting**: End-to-end encrypted vote casting with behavioral tracking
- **AI Fraud Detection**: Real-time fraud detection using Random Forest algorithm
- **Behavioral Analysis**: Tracks 20+ voter behavior features
- **Admin Dashboard**: Comprehensive monitoring and fraud analytics with Chart.js visualizations
- **Voter Dashboard**: Identity verification, candidate selection, and voting interface
- **Public Information Pages**: Accessible mission, security, privacy, FAQ, support, and accessibility pages
- **Real-time Alerts**: Automatic flagging of suspicious voting patterns
- **React Router v6**: Client-side routing with protected routes for role-based access
- **Audit Trail**: Complete transaction history with blockchain-ready architecture

## Tech Stack

- **Frontend**: React 17 with React Router v6, Bootstrap, Chart.js
- **Backend**: Python (Flask)
- **Database**: MongoDB
- **ML/AI**: Random Forest (scikit-learn)
- **Security**: JWT, bcrypt, MFA, Face Recognition, Data Encryption

## Quick Start
1. NBackend Setup
1. Navigate to the `backend` directory
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment (Windows): `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start MongoDB (see MONGODB_LOCAL_SETUP.md)
6. Run the application: `python app_mongodb.py`

### Frontend Setup
1. Navigate to the `frontend` directory
2. Install dependencies: `npm install`
3. Start the development server: `npm start`
4. Open browser to `http://localhost:3000`

**Quick setup:**
1. Random Forest model will be automatically trained on first run
2. Model is saved locally and used for real-time fraud detection
3. All React components use .jsx extensions
4. React Router v6 handles all naviga
1. Install required dependencies: `pip install -r backend/requirements.txt`
2. Random Forest model will be automatically trained on first run
3. Model is saved locally and used for real-time fraud detection

## Project Structure

```
election-fraud-detection/
├── backend/                        # Python Flask backend
│   ├── app_mongodb.py              # Main application
│   ├── random_forest_fraud.py      # Random Forest fraud detection module
│   ├── behavior_tracker.py         # Voter behavior tracking service
│   └── requirements.txt            # Python dependencies
├── frontend/                       # React frontend
│   ├── public/                     # Static files
│   │   └── index.html              # HTML template
│   ├── src/                        # Source code
│   │   ├── components/             # React components (.jsx)
│   │   │   ├── AdminDashboard.jsx  # Admin fraud analytics
│   │   │   ├── VoterDashboard.jsx  # Voter interface with identity verification
│   │   │   ├── Dashboard.jsx       # Generic dashboard
│   │   │   ├── Login.jsx           # Authentication with OTP
│   │   │   ├── Register.jsx        # Voter registration
│   │   │   ├── RegisterAdmin.jsx   # Admin registration
│   │   │   ├── IdentityVerification.jsx # Face recognition verification
│   │   │   ├── RoleProtectedRoute.jsx   # Route protection
│   │   │   ├── public/             # Public information pages
│   │   │   │   ├── Home.jsx
│   │   │   │   ├── Mission.jsx
│   │   │   │   ├── Security.jsx
│   │   │   │   ├── Privacy.jsx
│   │   │   │   ├── FAQ.jsx
│   │   │   │   ├── Support.jsx
│   │   │   │   ├── Accessibility.jsx
│   │   │   │   └── About.jsx
│   │   │   └── layout/
│   │   │       └── SiteLayout.jsx  # Shared layout component
│   │   ├── index.jsx               # React entry point
│   │   └── App.jsx                 # Main app with routing
│   └── package.json                # NPM dependencies
├── ADMIN_LOGIN_GUIDE.md            # Admin monitoring guide
└── README.md                       # Project documentation
```

## Fraud Detection System

### How It Works

1. **Data Collection**: Tracks voter behavior (login patterns, session data, device info)
2. **Feature Extraction**: Analyzes 20+ behavioral features
3. **ML Prediction**: Random Forest model predicts fraud probability (0.0 - 1.0)
4. **Risk Assessment**: Categorizes as Low/Medium/High risk
5. **Action**: Allows, flags for review, or blocks suspicious votes

### Fraud Detection Features

**Input Features:**
- Temporal patterns (time of day, day of week)
- Voter profile (age, registration date, verification status)
- Behavioral metrics (session duration, page views, login attempts)
- Device consistency (IP address, user agent, mobile vs desktop)
- Historical patterns (previous votes, device changes)

**Output:**
- Fraud probability score (0.0 - 1.0)
- Risk level (Low < 0.3 < Medium < 0.6 < High)
- Recommended action (Allow / Review / Block)

### Training Your Own Model

The Random Forest model is automatically trained and updated:
- Model trains on existing voting data when the application starts
- Continuously improves as more voting data is collected
- Model is saved locally in `backend/models/random_forest_model.pkl`
- No cloud services or API keys required
├── frontend/               # React frontend
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── utils/          # Utility functions
│   │   └── App.js          # Main component
├── ADMIN_LOGIN_GUIDE.md    # Admin monitoring guide
└── README.md               # Project documentation
```

## Admin Dashboard

**Default Admin Credentials:**
- **Username**: `admin`
- **Password**: `admin123`

> ⚠️ **IMPORTANT**: Change the default admin password immediately in production!

### Admin Features:
- Real-time election statistics
- Voter and candidate oversight
- **Fraud Detection Analytics Dashboard**
  - View high/medium/low risk votes
  - Review flagged transactions
  - Export fraud assessment reports
  - Monitor fraud detection model performance
  - Dataset summary and model status
- Election outcome visualization with charts
- User statistics and activity monitoring

### Fraud Analytics API Endpoints

```bash
# Get fraud analytics (admin only)
GET /api/admin/fraud-analytics

# Get fraud statistics
GET /api/admin/fraud-stats

# Export training data
GET /api/admin/export-training-data
```

See [ADMIN_LOGIN_GUIDE.md](ADMIN_LOGIN_GUIDE.md) for detailed admin panel features.

## Documentation

- **[ADMIN_LOGIN_GUIDE.md](ADMIN_LOGIN_GUIDE.md)**: Admin dashboard and monitoring guide
- **[SECURITY_FEATURES.md](SECURITY_FEATURES.md)**: Security architecture documentation
- **[MONGODB_LOCAL_SETUP.md](MONGODB_LOCAL_SETUP.md)**: MongoDB installation guide

## Cost Estimation

### Random Forest (Local)
- Training: Free (runs locally)
- Deployment: Free (no cloud services)
- Predictions: Free (unlimited)
- **Total**: $0/month

*All fraud detection runs locally with no external API costs.*

## License

This project is for educational purposes.

## Support

For issues or questions about fraud detection, check the logs in `backend/logs/` or review the Random Forest implementation in `backend/random_forest_fraud.py`.
