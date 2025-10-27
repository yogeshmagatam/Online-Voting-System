@echo off
echo Starting Election Fraud Detection System...

echo Starting Python Backend...
start cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python app.py"

echo Starting React Frontend...
start cmd /k "cd frontend && npm install && npm start"

echo System started! Access the application at http://localhost:3000