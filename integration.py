#!/usr/bin/env python3
"""
Automated Backend-Frontend Integration Script
This script monitors Railway deployment and updates Vercel with the backend URL
"""

import subprocess
import time
import json
import re
from datetime import datetime

def run_command(cmd):
    """Run a command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_railway_domain():
    """Get the public domain from Railway"""
    output, _, _ = run_command("npx railway domain")
    # Extract URL from output
    if "http" in output:
        # Find all HTTP URLs
        urls = re.findall(r'https?://[^\s\)]+', output)
        if urls:
            return urls[0]
    return None

def check_deployment_status():
    """Check if deployment is ready"""
    output, _, code = run_command("npx railway status")
    if code == 0:
        return output
    return None

def wait_for_deployment(timeout_minutes=7):
    """Wait for Railway deployment to complete"""
    print("⏳ Waiting for Railway deployment to complete...")
    print(f"⏱️  Timeout: {timeout_minutes} minutes")
    print()
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    check_interval = 15  # Check every 15 seconds
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            print("❌ Deployment timeout exceeded")
            return False
        
        status = check_deployment_status()
        if status:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Deployment status available")
            return True
        
        remaining = int(timeout_seconds - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - Still building... ({minutes}m {seconds}s remaining)")
        time.sleep(check_interval)

def get_backend_url():
    """Get the backend URL from Railway"""
    print("\n🔍 Retrieving backend URL from Railway...")
    
    domain = get_railway_domain()
    if domain:
        print(f"✅ Backend URL found: {domain}")
        return domain
    
    print("⚠️  Could not retrieve domain automatically")
    print("Go to: https://railway.app/dashboard")
    print("Click the Python service → Settings → Domains")
    print("Copy the public URL and use it in next step")
    return None

def update_vercel_env(backend_url):
    """Create a guide for updating Vercel"""
    if not backend_url:
        print("\n⚠️  Cannot update Vercel without backend URL")
        return False
    
    print("\n📝 Steps to Update Vercel:")
    print("=" * 60)
    print()
    print("1. Go to: https://vercel.com/yogeshmagatams-projects/online-voting-system")
    print("2. Click: Settings")
    print("3. Click: Environment Variables")
    print("4. Find: REACT_APP_API_URL")
    print(f"5. Update value to: {backend_url}")
    print("6. Click: Save")
    print("7. Go to: Deployments")
    print("8. Click latest deployment")
    print("9. Click: Redeploy")
    print()
    print("=" * 60)
    
    return True

def main():
    """Main integration flow"""
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "BACKEND-FRONTEND INTEGRATION SCRIPT" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    print()
    
    # Step 1: Wait for deployment
    print("📍 Step 1: Waiting for Railway Backend Deployment")
    print("-" * 60)
    if not wait_for_deployment(7):
        return False
    
    # Step 2: Get backend URL
    print("\n📍 Step 2: Getting Backend URL")
    print("-" * 60)
    backend_url = get_backend_url()
    
    # Step 3: Guide for updating Vercel
    print("\n📍 Step 3: Update Vercel with Backend URL")
    print("-" * 60)
    update_vercel_env(backend_url)
    
    # Step 4: Final instructions
    print("\n📍 Step 4: After Vercel Redeploy")
    print("-" * 60)
    print("\n✅ Testing the Integration:")
    print()
    print("1. Go to: https://online-voting-system-six-flax.vercel.app")
    print("2. Register a new account")
    print("3. Check email for OTP")
    print("4. Login with OTP")
    print("5. Complete identity verification")
    print("6. Cast a vote")
    print("7. Check admin dashboard")
    print()
    print("If all steps work → 🎉 Integration is complete!")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
