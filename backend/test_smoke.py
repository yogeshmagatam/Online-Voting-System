#!/usr/bin/env python
"""Quick smoke test for auth flow and API endpoints"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_login():
    """Test admin login without MFA"""
    print("1. Testing login...")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "admin", "password": "admin123"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Token received: {data['access_token'][:20]}...")
        print(f"   Role: {data['role']}")
        return data['access_token']
    else:
        print(f"   Error: {response.text}")
        return None

def test_add_election_data(token):
    """Test adding election data"""
    print("\n2. Testing add election data...")
    payload = {
        "precinct": "Test Precinct Alpha",
        "votes_candidate_a": 450,
        "votes_candidate_b": 350,
        "registered_voters": 1000,
        "turnout_percentage": 80.0,
        "timestamp": datetime.now().isoformat()
    }
    response = requests.post(
        f"{BASE_URL}/api/election-data",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Data added successfully: {response.json()}")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_analyze(token):
    """Test fraud detection analysis"""
    print("\n3. Testing fraud detection analysis...")
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Analysis complete - Flagged: {data.get('flagged_count', 0)}")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_statistics(token):
    """Test statistics endpoint"""
    print("\n4. Testing statistics...")
    response = requests.get(
        f"{BASE_URL}/api/statistics",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"   Total precincts: {stats.get('total_precincts', 0)}")
        print(f"   Total votes: {stats.get('total_votes', 0)}")
        print(f"   Avg turnout: {stats.get('avg_turnout', 0):.2f}%")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_face_verification_guard(token):
    """Test face verification returns 501 when deps not installed"""
    print("\n5. Testing face verification guard (should return 501)...")
    payload = {
        "live_photo": "data:image/jpeg;base64,ZmFrZWltYWdlZGF0YQ=="
    }
    response = requests.post(
        f"{BASE_URL}/api/verify-identity",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 501:
        print(f"   ✓ Guard working: {response.json()}")
        return True
    else:
        print(f"   Unexpected response: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SMOKE TEST - Election System API")
    print("=" * 60)
    
    # Run tests
    token = test_login()
    if not token:
        print("\n✗ Login failed - cannot continue tests")
        exit(1)
    
    test_add_election_data(token)
    test_analyze(token)
    test_statistics(token)
    test_face_verification_guard(token)
    
    print("\n" + "=" * 60)
    print("✓ Smoke test completed")
    print("=" * 60)
