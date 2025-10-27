#!/usr/bin/env python
"""Register a test user to verify backend register flow"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

if __name__ == "__main__":
    suffix = datetime.now().strftime("%H%M%S")
    username = f"user{suffix}"
    payload = {
        "username": username,
        "password": "Password@1234",
        "voter_id": "VID67890",
        "national_id": "NID67890",
        "email": f"{username}@example.com",
        "phone": "",
        "captcha": "dev-ok",
        # small dummy jpg bytes ("fake") as base64; backend skips encoding if face_recognition unavailable
        "photo": "data:image/jpeg;base64,ZmFrZQ=="
    }

    print("Registering:", username)
    r = requests.post(f"{BASE_URL}/api/register", json=payload)
    print("Status:", r.status_code)
    try:
        print("Response:", json.dumps(r.json(), indent=2))
    except Exception:
        print("Response text:", r.text)
    
    if r.status_code in (200, 201):
        print("OK: Registration success")
    else:
        raise SystemExit(1)
