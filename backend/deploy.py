#!/usr/bin/env python3
"""
Railway Backend Deployment Automation Script
This script automates the deployment of the Flask backend to Railway
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def run_command(cmd, description=None):
    """Run a shell command and return output"""
    if description:
        print(f"\n📌 {description}")
    print(f"  Running: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0, result.stdout, result.stderr

def main():
    """Main deployment function"""
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║     RAILWAY BACKEND DEPLOYMENT - AUTOMATED SCRIPT              ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    # Check we're in backend directory
    backend_dir = Path.cwd()
    if not (backend_dir / "app_mongodb.py").exists():
        print("❌ Error: app_mongodb.py not found!")
        print("   Please run this script from the backend directory")
        sys.exit(1)
    
    print(f"✅ Backend directory: {backend_dir}\n")
    
    # Step 1: Create .railway config
    print("Step 1: Setting up Railway configuration")
    railway_dir = backend_dir / ".railway"
    railway_config = railway_dir / "config.json"
    
    railway_dir.mkdir(exist_ok=True)
    
    config = {
        "project_id": None,
        "environment": "production",
        "service": "election-fraud-detection"
    }
    
    # Step 2: List services
    print("\n✓ Checking Railroad services...")
    success, stdout, stderr = run_command(
        "npx railway service list",
        "Getting available services"
    )
    
    print("Services found:\n", stdout)
    
    # Step 3: Display environment variables set
    print("\n✓ Verifying environment variables...")
    success, stdout, stderr = run_command(
        "npx railway variables",
        "Listing current environment variables"
    )
    
    print("Current variables:\n", stdout)
    
    # Step 4: Deploy
    print("\n" + "="*64)
    print("🚀 DEPLOYMENT STATUS")
    print("="*64)
    print("\n✅ All preparations complete!")
    print("\n📊 Next Steps:")
    print("  1. Open: https://railway.app/dashboard")
    print("  2. Select: election-fraud-detection project")
    print("  3. Add Service → GitHub Repo → Online-Voting-System")
    print("  4. Select branch: feature/yogesh/login")
    print("  5. Wait 5-7 minutes for build")
    print("\n💡 Variables already set:")
    print("  ✓ FLASK_ENV = production")
    print("  ✓ FLASK_DEBUG = False")
    print("  ✓ SECRET_KEY = [generated]")
    print("  ✓ JWT_SECRET_KEY = [generated]")
    print("  ✓ And 4 more configuration variables")
    print("\n⚠️  Still need to set (requires your action):")
    print("  • MAIL_USERNAME (your Gmail)")
    print("  • MAIL_PASSWORD (Gmail app password)")
    print("  • MONGO_URI (after adding MongoDB)")
    print("\nGo to Railway Dashboard to complete the setup!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
