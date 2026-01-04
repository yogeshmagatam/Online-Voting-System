"""
Script to fix admin users in the database
Only the first admin created will be marked as authorized
"""
from pymongo import MongoClient
from urllib.parse import quote_plus
from datetime import datetime

# MongoDB connection
username = 'admin'
password = 'admin@123'
escaped_password = quote_plus(password)
MONGODB_URI = f'mongodb://{username}:{escaped_password}@localhost:27017/election_db?authSource=admin'
MONGODB_DB_NAME = 'election_db'

try:
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db = mongo_client[MONGODB_DB_NAME]
    users_collection = db['users']
    print(f"✓ Connected to MongoDB: {MONGODB_DB_NAME}")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    exit(1)

print("\n" + "="*70)
print("FIXING ADMIN USERS")
print("="*70)

# Get all admin users sorted by creation date
all_admins = list(users_collection.find({'role': 'admin'}).sort('created_at', 1))

if not all_admins:
    print("\n✗ No admin users found in database")
    print("Run the backend server to create the default admin user")
else:
    print(f"\nFound {len(all_admins)} admin user(s)")
    print("\nCurrent admin users:")
    for i, admin in enumerate(all_admins, 1):
        authorized = admin.get('is_authorized_admin', False)
        created = admin.get('created_at', 'Unknown')
        print(f"{i}. Username: {admin.get('username')}")
        print(f"   Email: {admin.get('email', 'N/A')}")
        print(f"   Authorized: {authorized}")
        print(f"   Created: {created}")
        print()
    
    # Fix: Only first admin should be authorized
    first_admin = all_admins[0]
    
    print("Applying fix...")
    
    # Mark first admin as authorized
    result = users_collection.update_one(
        {'_id': first_admin['_id']},
        {'$set': {'is_authorized_admin': True}}
    )
    if result.modified_count > 0:
        print(f"✓ Marked '{first_admin.get('username')}' as AUTHORIZED admin")
    else:
        print(f"✓ '{first_admin.get('username')}' already authorized")
    
    # Mark all other admins as unauthorized
    if len(all_admins) > 1:
        for admin in all_admins[1:]:
            result = users_collection.update_one(
                {'_id': admin['_id']},
                {'$set': {'is_authorized_admin': False}}
            )
            if result.modified_count > 0:
                print(f"✓ Marked '{admin.get('username')}' as UNAUTHORIZED")
    
    print("\n" + "="*70)
    print("FINAL STATE")
    print("="*70)
    
    all_admins = list(users_collection.find({'role': 'admin'}).sort('created_at', 1))
    for i, admin in enumerate(all_admins, 1):
        authorized = admin.get('is_authorized_admin', False)
        status = "✓ AUTHORIZED (Can access admin dashboard)" if authorized else "✗ UNAUTHORIZED (Cannot login)"
        print(f"{i}. {admin.get('username')}: {status}")
    
    print("\n✓ Admin users have been fixed!")
    print(f"✓ Only '{first_admin.get('username')}' can access the admin dashboard")
    print("✓ No new admin registrations will be allowed")

mongo_client.close()
