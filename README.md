# Election System with ML-Powered Fraud Detection

A comprehensive web-based voting system with **Random Forest** fraud detection using machine learning to ensure election integrity. Built with React, Flask, MongoDB, and scikit-learn for a secure, scalable voting platform.

## Features

- **User Authentication**: Multi-factor authentication (MFA) with email OTP, password hashing with bcrypt
- **Identity Verification**: Photo capture and verification system for voter identity validation
- **Secure Voting**: End-to-end vote casting with behavioral tracking and transaction IDs
- **ML Fraud Detection**: Real-time fraud detection using Random Forest algorithm (no cloud dependency)
- **Behavioral Analysis**: Tracks 20+ voter behavior features (login patterns, session data, device info)
- **Admin Dashboard**: Comprehensive monitoring and fraud analytics with Chart.js visualizations
- **Voter Dashboard**: Vote casting interface with identity verification
- **Public Information Pages**: Accessible mission, security, privacy, FAQ, support, and accessibility pages
- **Real-time Alerts**: Automatic flagging of suspicious voting patterns with risk categorization (Low/Medium/High)
- **React Router v6**: Client-side routing with protected routes for role-based access (Voter/Admin)
- **MongoDB Integration**: Persistent data storage with CSV dataset support for model training
- **Audit Trail**: Complete transaction history with logging and monitoring capabilities

## Tech Stack

- **Frontend**: React 17+ with React Router v6, Bootstrap, Chart.js
- **Backend**: Python with Flask and Flask-CORS
- **Database**: MongoDB (local setup with optional Docker support)
- **ML**: Random Forest (scikit-learn), scikit-learn-based fraud detection
- **Security**: JWT (flask-jwt-extended), bcrypt password hashing, email OTP, CORS protection
- **Deployment**: Docker support, Gunicorn-ready
- **Development**: Node.js/npm, Python venv

## Quick Start

### Backend Setup
1. Navigate to the `backend` directory
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment (Windows): `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start MongoDB (see [MONGODB_LOCAL_SETUP.md](MONGODB_LOCAL_SETUP.md))
6. Run the application: `python app_mongodb.py`

The application will:
- Automatically train the Random Forest model on startup
- Load the CSV dataset if available (`voting_fraud_dataset.csv`)
- Save the trained model to `backend/models/rf/`
- Start the Flask server on `http://localhost:5000`

### Frontend Setup
1. Navigate to the `frontend` directory
2. Install dependencies: `npm install`
3. Start the development server: `npm start`
4. Open browser to `http://localhost:3000`

### Quick Setup Notes
- Random Forest model will be automatically trained on first run
- Model is saved locally in `backend/models/rf/` and used for real-time fraud detection
- All React components use `.jsx` extensions
- React Router v6 handles all navigation with protected routes
- CSV dataset integration is fully supported

## Project Structure

```
Major_Project_clg/
├── backend/                              # Python Flask backend
│   ├── app_mongodb.py                    # Main Flask application with MongoDB
│   ├── fraud_detection.py                # Fraud detection module
│   ├── random_forest_fraud.py            # Random Forest ML implementation
│   ├── behavior_tracker.py               # Voter behavior tracking service
│   ├── load_dataset_to_db.py             # CSV dataset loader
│   ├── update_dataset_distribution.py    # Dataset utilities
│   ├── requirements.txt                  # Python dependencies
│   ├── models/
│   │   └── rf/                           # Saved Random Forest models
│   ├── logs/                             # Application logs
│   ├── uploads/                          # User photo storage
│   │   └── user_photos/                  # Photo directory
│   └── voting_fraud_dataset.csv          # Training dataset (3000 records)
│
├── frontend/                             # React frontend
│   ├── src/                              # Source code
│   │   ├── components/                   # React components (.jsx)
│   │   │   ├── AdminDashboard.jsx        # Admin fraud analytics
│   │   │   ├── VoterDashboard.jsx        # Voter voting interface
│   │   │   ├── Dashboard.jsx             # Generic dashboard
│   │   │   ├── Login.jsx                 # Authentication with OTP
│   │   │   ├── Register.jsx              # Voter registration
│   │   │   ├── RegisterAdmin.jsx         # Admin registration
│   │   │   ├── IdentityVerification.jsx  # Identity verification
│   │   │   ├── RoleProtectedRoute.jsx    # Route protection
│   │   │   ├── public/                   # Public information pages
│   │   │   │   ├── Home.jsx
│   │   │   │   ├── Mission.jsx
│   │   │   │   ├── Security.jsx
│   │   │   │   ├── Privacy.jsx
│   │   │   │   ├── FAQ.jsx
│   │   │   │   ├── Support.jsx
│   │   │   │   ├── Accessibility.jsx
│   │   │   │   └── About.jsx
│   │   │   └── layout/
│   │   │       └── SiteLayout.jsx        # Shared layout component
│   │   ├── index.jsx                     # React entry point
│   │   ├── App.jsx                       # Main app with routing
│   │   ├── App.css                       # Application styles
│   │   └── index.css                     # Global styles
│   ├── public/
│   │   └── index.html                    # HTML template
│   ├── package.json                      # NPM dependencies
│   └── build/                            # Production build
│
├── Documentation Files
│   ├── README.md                         # This file
│   ├── SECURITY_FEATURES.md              # Security architecture
│   ├── MONGODB_LOCAL_SETUP.md            # MongoDB setup guide
│   ├── DATASET_INTEGRATION_SUMMARY.md    # Dataset integration details
│   ├── VERIFICATION_FLOW_DIAGRAM.md      # Registration & verification flow
│   └── INSTALL_FACE_RECOGNITION.md       # Face recognition setup (optional)
│
├── Configuration & Deployment
│   ├── docker-compose.yml                # Docker configuration
│   ├── Dockerfile                        # Docker build file
│   ├── run_app.bat                       # Quick start script (Windows)
│   ├── setup_gmail_otp.bat               # Gmail OTP setup (Windows)
│   └── .env.example                      # Environment variables template
│
└── Miscellaneous
    ├── model.pkl                         # Saved model (legacy)
    └── voting_fraud_model.pkl            # Saved Random Forest model
```

## Fraud Detection System

### How It Works

1. **Data Collection**: Tracks voter behavior including:
   - Login patterns and session data
   - Device information (IP address, user agent)
   - Temporal patterns (time of day, day of week)
   - Voter profile data (age, registration date)
   - Historical patterns (previous votes, device changes)

2. **Feature Extraction**: Analyzes 20+ behavioral features for each vote

3. **ML Prediction**: Random Forest model predicts fraud probability (0.0 - 1.0)

4. **Risk Assessment**: Categorizes votes as:
   - **Low Risk**: Score < 0.3 (Allow)
   - **Medium Risk**: 0.3 < Score < 0.6 (Review)
   - **High Risk**: Score > 0.6 (Flag for review/blocking)

5. **Action**: System recommends Allow, Review, or Block based on risk level

### Fraud Detection Features

**Input Features (20+):**
- Temporal patterns (time of day, day of week)
- Voter profile (age, registration date, verification status)
- Behavioral metrics (session duration, page views, login attempts)
- Device consistency (IP address, user agent, mobile vs desktop)
- Historical patterns (previous votes, device changes)

**Output:**
- Fraud probability score (0.0 - 1.0)
- Risk level (Low/Medium/High)
- Recommended action (Allow / Review / Block)
- Confidence metrics and feature importance

### Training Your Own Model

The Random Forest model is automatically trained and updated:
- Model trains on existing voting data when the application starts
- Uses CSV dataset if available (`voting_fraud_dataset.csv` with 3,000 records)
- Continuously improves as more voting data is collected
- Model is saved locally in `backend/models/rf/`
- No cloud services or API keys required - completely offline

**API Endpoint for Training:**
```bash
# Train model from CSV dataset (admin only)
POST /api/admin/train-rf-from-csv
```

## Admin Dashboard

**Default Admin Credentials:**
- **Username**: `admin`
- **Password**: `admin123`

> ⚠️ **IMPORTANT**: Change the default admin password immediately in production!

### Admin Features:
- Real-time election statistics and voter oversight
- **Fraud Detection Analytics Dashboard**
  - View high/medium/low risk votes with visualizations
  - Review flagged and suspicious transactions
  - Export fraud assessment reports
  - Monitor fraud detection model performance
  - Dataset summary and model training status
  - Real-time fraud detection metrics
- User statistics and activity monitoring
- Comprehensive audit logs and transaction history

### Fraud Analytics API Endpoints

```bash
# Get fraud analytics (admin only)
GET /api/admin/fraud-analytics

# Get fraud statistics and overview
GET /api/admin/fraud-stats

# Train model from CSV dataset
POST /api/admin/train-rf-from-csv

# Export training data
GET /api/admin/export-training-data
```

## Documentation

- **[SECURITY_FEATURES.md](SECURITY_FEATURES.md)**: Comprehensive security architecture and authentication details
- **[MONGODB_LOCAL_SETUP.md](MONGODB_LOCAL_SETUP.md)**: MongoDB installation and configuration guide
- **[DATASET_INTEGRATION_SUMMARY.md](DATASET_INTEGRATION_SUMMARY.md)**: CSV dataset integration and training details
- **[VERIFICATION_FLOW_DIAGRAM.md](VERIFICATION_FLOW_DIAGRAM.md)**: Complete registration and verification flow
- **[INSTALL_FACE_RECOGNITION.md](INSTALL_FACE_RECOGNITION.md)**: Optional face recognition setup guide

## Cost Estimation

### Random Forest (Local)
- Training: **Free** (runs locally on your machine)
- Deployment: **Free** (no cloud services required)
- Predictions: **Free** (unlimited real-time fraud detection)
- **Total**: $0/month

All fraud detection runs completely offline with no external API costs or cloud dependencies.

## Security & Compliance

### Authentication & Authorization
- Multi-factor authentication (MFA) with email OTP
- JWT-based session management
- Role-based access control (Voter/Admin)
- Bcrypt password hashing with salt

### Data Protection
- Input validation and sanitization (XSS prevention)
- CORS protection and secure headers
- Transaction logging and audit trails
- Encrypted sensitive data storage
- User photo secure storage

See [SECURITY_FEATURES.md](SECURITY_FEATURES.md) for detailed security architecture.

## Getting Help

### Troubleshooting

**MongoDB Connection Issues:**
- See [MONGODB_LOCAL_SETUP.md](MONGODB_LOCAL_SETUP.md) for setup instructions
- Check `backend/logs/` for connection errors
- Ensure MongoDB service is running

**Model Training Issues:**
- Check `backend/logs/` for training errors
- Verify CSV dataset is in `backend/voting_fraud_dataset.csv`
- See [DATASET_INTEGRATION_SUMMARY.md](DATASET_INTEGRATION_SUMMARY.md) for data format

**Frontend Issues:**
- Clear browser cache and local storage
- Check browser console for React errors
- Ensure backend server is running on port 5000

**Email OTP Issues:**
- Verify Gmail OTP setup in [setup_gmail_otp.bat](setup_gmail_otp.bat)
- Check `.env` file has correct Gmail credentials
- Review Flask email configuration in app_mongodb.py
