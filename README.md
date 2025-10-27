# Election Fraud Detection System

A web-based system for detecting election fraud using cybersecurity and machine learning techniques.

## Features

- User authentication and authorization
- Secure data upload and management
- Machine learning-based fraud detection
- Real-time monitoring and alerts
- Comprehensive dashboard for visualization
- Secure API with encryption

## Tech Stack

- **Frontend**: React.js
- **Backend**: Python (Flask)
- **Database**: SQLite (development), PostgreSQL (production)
- **ML Libraries**: Scikit-learn, TensorFlow
- **Security**: JWT, HTTPS, Data Encryption

## Setup Instructions

### Backend Setup
1. Navigate to the `backend` directory
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the server: `python app.py`

### Frontend Setup
1. Navigate to the `frontend` directory
2. Install dependencies: `npm install`
3. Start the development server: `npm start`

## Project Structure

```
election-fraud-detection/
├── backend/                # Python Flask backend
│   ├── app.py              # Main application entry
│   ├── config.py           # Configuration settings
│   ├── models/             # Database models
│   ├── routes/             # API routes
│   ├── services/           # Business logic
│   ├── ml_models/          # Machine learning models
│   └── utils/              # Utility functions
├── frontend/               # React frontend
│   ├── public/             # Static files
│   ├── src/                # Source code
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── utils/          # Utility functions
│   │   └── App.js          # Main component
└── README.md               # Project documentation
```