# Election System with AI-Powered Fraud Detection

A comprehensive web-based voting system with **Google Cloud Vertex AI** fraud detection using machine learning to ensure election integrity.

## Features

- **User Authentication**: Multi-factor authentication with email OTP
- **Identity Verification**: Facial recognition for voter verification
- **Secure Voting**: End-to-end encrypted vote casting
- **AI Fraud Detection**: Real-time fraud detection using Vertex AI (XGBoost/AutoML)
- **Behavioral Analysis**: Tracks 20+ voter behavior features
- **Admin Dashboard**: Comprehensive monitoring and fraud analytics
- **Real-time Alerts**: Automatic flagging of suspicious voting patterns
- **Audit Trail**: Complete transaction history with blockchain-ready architecture

## Tech Stack

- **Frontend**: React.js
- **Backend**: Python (Flask)
- **Database**: MongoDB
- **ML/AI**: Google Cloud Vertex AI (XGBoost, AutoML Tabular)
- **Security**: JWT, bcrypt, MFA, Data Encryption
- **Cloud**: Google Cloud Platform (Vertex AI, Cloud Storage)

## Quick Start
1. Navigate to the `backend` directory
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
### Frontend Setup
1. Navigate to the `frontend` directory
2. Install dependencies: `npm install`
3. Start the development server: `npm start`
See [VERTEX_AI_FRAUD_DETECTION.md](VERTEX_AI_FRAUD_DETECTION.md) for complete setup instructions.

**Quick setup:**
1. Set up Google Cloud project with Vertex AI API enabled
2. Create service account and download credentials
3. Configure environment variables in `.env`:
   ```
   GCP_PROJECT_ID=your-project-id
   GCP_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=./vertex-ai-key.json
   ```
4. Run setup verification: `python backend/setup_vertex_ai.py`

## Project Structure

```
election-fraud-detection/
├── backend/                      # Python Flask backend
│   ├── app_mongodb.py            # Main application
│   ├── fraud_detection.py        # Vertex AI fraud detection module
│   ├── behavior_tracker.py       # Voter behavior tracking service
│   ├── train_fraud_model.py      # Model training script
│   ├── setup_vertex_ai.py        # Vertex AI setup verification
│   ├── convert_training_data.py  # Training data converter
│   └── requirements.txt          # Python dependencies
├── frontend/                     # React frontend
│   ├── public/                   # Static files
│   ├── src/                      # Source code
│   │   ├── components/           # React components
│   │   │   ├── AdminDashboard.js # Admin fraud analytics
│   │   │   ├── VoterDashboard.js # Voter interface
│   │   │   └── Login.js          # Authentication
│   │   └── App.js                # Main component
├── ADMIN_LOGIN_GUIDE.md          # Admin monitoring guide
└── README.md                     # Project documentation
```

## Fraud Detection System

### How It Works

1. **Data Collection**: Tracks voter behavior (login patterns, session data, device info)
2. **Feature Extraction**: Analyzes 20+ behavioral features
3. **ML Prediction**: Ranndom Forest model predicts fraud probability (0.0 - 1.0)
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

```bash
# 1. Export training data
curl -X GET http://localhost:5000/api/admin/export-training-data \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -o training_data.json

# 2. Convert to CSV
  --training-data training_data.csv \
  --model-type automl \
echo "VERTEX_AI_ENDPOINT_ID=your-endpoint-id" >> .env
```
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
- Activity and security logs
- System configuration

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

