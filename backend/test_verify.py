#!/usr/bin/env python
"""Test identity verification in dev mode without FR installed.
1) Register a user (if needed)
2) Login and get JWT
3) Call /api/verify-identity with a dummy base64 image and expect success (bypass or auto-enroll)
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

username = f"verify{datetime.now().strftime('%H%M%S')}"
password = "Password@1234"

# 1) Register
reg_payload = {
    "username": username,
    "password": password,
    "voter_id": "VID24680",
    "national_id": "NID24680",
    "email": f"{username}@example.com",
    "phone": "",
    "captcha": "dev-ok",
    "photo": "data:image/jpeg;base64,ZmFrZQ=="
}
print("Registering:", username)
requests.post(f"{BASE_URL}/api/register", json=reg_payload)

# 2) Login
print("Logging in...")
login = requests.post(f"{BASE_URL}/api/login", json={"username": username, "password": password})
if login.status_code != 200:
    print("Login failed:", login.text)
    raise SystemExit(1)
access_token = login.json().get("access_token")

# 3) Verify identity (dev bypass/auto-enroll)
print("Verifying identity...")
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
verify_payload = {"live_photo": "data:image/jpeg;base64,ZmFrZQ=="}
resp = requests.post(f"{BASE_URL}/api/verify-identity", headers=headers, json=verify_payload)
print("Status:", resp.status_code)
print("Body:", resp.text)
if resp.status_code != 200:
    raise SystemExit(1)
print("OK: Verification success in development mode")
