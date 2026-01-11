"""
Script to load voting_fraud_dataset.csv into MongoDB
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# MongoDB connection
from urllib.parse import quote_plus
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')

# Handle special characters in MongoDB URI
if '@' in MONGO_URI and '://' in MONGO_URI:
    # Parse and re-encode if needed
    parts = MONGO_URI.split('://')
    if len(parts) == 2:
        protocol = parts[0]
        rest = parts[1]
        if '@' in rest:
            auth, host = rest.rsplit('@', 1)
            if ':' in auth:
                username, password = auth.split(':', 1)
                # Encode special characters
                username = quote_plus(username)
                password = quote_plus(password)
                MONGO_URI = f"{protocol}://{username}:{password}@{host}"

mongo_client = MongoClient(MONGO_URI)
db = mongo_client['election_db']

def load_dataset_to_db():
    """Load voting_fraud_dataset.csv into MongoDB"""
    
    csv_path = os.path.join(os.path.dirname(__file__), 'voting_fraud_dataset.csv')
    
    if not os.path.exists(csv_path):
        print(f"✗ CSV file not found: {csv_path}")
        return False
    
    try:
        print(f"Loading CSV from: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} records from CSV")
        
        # Convert numeric features
        numeric_columns = ['age', 'login_attempts', 'vote_duration_sec', 'location_match', 'previous_votes']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(int)
        
        # Handle voter_id: extract numeric part if text
        if 'voter_id' in df.columns and df['voter_id'].dtype == object:
            df['voter_id'] = df['voter_id'].str.extract(r'(\d+)').astype(int)
        
        # Handle ip_address: keep as string for now
        if 'ip_address' in df.columns and df['ip_address'].dtype != object:
            df['ip_address'] = df['ip_address'].astype(str)
        
        # Handle device_id: keep as string for now
        if 'device_id' in df.columns and df['device_id'].dtype != object:
            df['device_id'] = df['device_id'].astype(str)
        
        # Rename is_fraud to fraud_label if needed
        if 'is_fraud' in df.columns:
            df = df.rename(columns={'is_fraud': 'fraud_label'})
        
        # Add timestamp
        df['timestamp'] = datetime.utcnow()
        df['source'] = 'voting_fraud_dataset.csv'
        
        # Convert to dictionaries
        records = df.to_dict('records')
        
        print(f"\n✓ Converted to {len(records)} database records")
        print(f"Sample record: {records[0]}")
        
        # Insert into MongoDB
        collection = db['fraud_training_data']
        
        # Clear existing data from this source (optional)
        print("\nClearing existing data from this source...")
        result = collection.delete_many({'source': 'voting_fraud_dataset.csv'})
        print(f"✓ Deleted {result.deleted_count} existing records")
        
        # Insert new data
        print("\nInserting new records into MongoDB...")
        insert_result = collection.insert_many(records)
        print(f"✓ Inserted {len(insert_result.inserted_ids)} records")
        
        # Verify insertion
        count = collection.count_documents({'source': 'voting_fraud_dataset.csv'})
        print(f"\n✓ Total records in database: {count}")
        
        # Show distribution
        print("\nFraud label distribution in database:")
        pipeline = [
            {'$match': {'source': 'voting_fraud_dataset.csv'}},
            {'$group': {'_id': '$fraud_label', 'count': {'$sum': 1}}}
        ]
        distribution = list(collection.aggregate(pipeline))
        for item in distribution:
            label = "Fraud" if item['_id'] == 1 else "Legitimate"
            pct = (item['count'] / count) * 100
            print(f"  {label}: {item['count']} ({pct:.1f}%)")
        
        print("\n" + "="*60)
        print("✓ Dataset successfully loaded into MongoDB!")
        print("="*60)
        print(f"Collection: fraud_training_data")
        print(f"Records: {count}")
        print(f"Ready for model training!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        mongo_client.close()

if __name__ == "__main__":
    success = load_dataset_to_db()
    sys.exit(0 if success else 1)
