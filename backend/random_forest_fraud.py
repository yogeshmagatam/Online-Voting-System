"""
Random Forest Fraud Detection Module
- Train and serve a local RandomForestClassifier as an alternative to Vertex AI
- Uses behavior features already present in the app
"""

from __future__ import annotations

import os
import json
import joblib
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

logger = logging.getLogger(__name__)


DEFAULT_FEATURES = [
    'voter_id', 'age', 'ip_address', 'device_id', 
    'login_attempts', 'vote_duration_sec', 'location_match', 'previous_votes'
]


def load_voting_fraud_dataset(csv_path: Optional[str] = None) -> List[Dict]:
    """
    Load voting fraud dataset from CSV file
    
    Args:
        csv_path: Path to CSV file. If None, uses default path relative to this file
        
    Returns:
        List of dictionaries with voting fraud data
    """
    if csv_path is None:
        # Use default path: same directory as this module
        csv_path = os.path.join(os.path.dirname(__file__), 'voting_fraud_dataset.csv')
    
    if not os.path.exists(csv_path):
        logger.warning(f"Dataset not found at {csv_path}")
        return []
    
    try:
        df = pd.read_csv(csv_path)
        
        # Convert numeric features to appropriate types
        numeric_columns = ['voter_id', 'age', 'ip_address', 'device_id', 'login_attempts', 
                          'vote_duration_sec', 'location_match', 'previous_votes']
        
        # Handle voter_id: extract numeric part if it's text like "V0001"
        if 'voter_id' in df.columns and df['voter_id'].dtype == object:
            df['voter_id'] = df['voter_id'].str.extract(r'(\d+)').astype(int)
        
        # Handle ip_address: convert to hash or numeric representation
        if 'ip_address' in df.columns and df['ip_address'].dtype == object:
            df['ip_address'] = df['ip_address'].apply(lambda x: hash(str(x)) % (10 ** 8))
        
        # Handle device_id: convert to hash or numeric representation  
        if 'device_id' in df.columns and df['device_id'].dtype == object:
            df['device_id'] = df['device_id'].apply(lambda x: hash(str(x)) % (10 ** 8))
        
        # Ensure numeric columns are integers
        for col in ['age', 'login_attempts', 'vote_duration_sec', 'location_match', 'previous_votes']:
            if col in df.columns:
                df[col] = df[col].astype(int)
        
        # Map target column: is_fraud -> is_fraud (for compatibility with model training)
        if 'is_fraud' in df.columns:
            # Keep as is for model training
            pass
        elif 'fraud_label' in df.columns:
            df = df.rename(columns={'fraud_label': 'is_fraud'})
        
        logger.info(f"Loaded {len(df)} records from {csv_path}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        return records
        
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return []


@dataclass
class RFArtifacts:
    model_path: str
    features_path: str


class RandomForestFraudModel:
    def __init__(self, features: Optional[List[str]] = None):
        self.model: Optional[RandomForestClassifier] = None
        self.features = features or list(DEFAULT_FEATURES)

    def prepare_dataframe(self, records: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(records)
        # Timestamp derived features
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour_of_day'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        # Normalize booleans to ints
        for col in ['is_mobile', 'identity_verified']:
            if col in df.columns:
                df[col] = df[col].astype(int)
        # Ensure feature columns exist before type normalization
        for col in self.features:
            if col not in df.columns:
                df[col] = 0
        # Normalize expected numeric/text features
        # voter_id may be like "V0001" -> extract digits
        if 'voter_id' in df.columns and df['voter_id'].dtype == object:
            df['voter_id'] = df['voter_id'].astype(str).str.extract(r'(\d+)').fillna('0').astype(int)
        # Convert textual ip/device to stable numeric hashes
        if 'ip_address' in df.columns and df['ip_address'].dtype == object:
            df['ip_address'] = df['ip_address'].astype(str).apply(lambda x: hash(x) % (10 ** 8))
        if 'device_id' in df.columns and df['device_id'].dtype == object:
            df['device_id'] = df['device_id'].astype(str).apply(lambda x: hash(x) % (10 ** 8))
        # Cast remaining numeric features to int
        for col in ['age', 'login_attempts', 'vote_duration_sec', 'location_match', 'previous_votes']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df

    def train_from_records(self, records: List[Dict], target: str = 'is_fraud') -> Dict:
        df = self.prepare_dataframe(records)
        if target not in df.columns:
            # derive from probability if available
            if 'fraud_probability' in df.columns:
                df[target] = (df['fraud_probability'] > 0.5).astype(int)
            else:
                raise ValueError("No target label present in records (need 'is_fraud' or 'fraud_probability')")
        X = df[self.features]
        y = df[target].astype(int)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Balanced class weights
        import numpy as np
        classes = np.array([0, 1])
        class_weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_train)
        class_weight_dict = {c: w for c, w in zip(classes, class_weights)}

        rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_split=2,
            n_jobs=-1,
            class_weight=class_weight_dict,
            random_state=42,
        )
        rf.fit(X_train, y_train)

        y_prob = rf.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        metrics = {
            'classification_report': classification_report(y_test, y_pred, digits=4, output_dict=True),
            'roc_auc': float(roc_auc_score(y_test, y_prob)),
            'pr_auc': float(average_precision_score(y_test, y_prob)),
            'n_train': int(len(y_train)),
            'n_test': int(len(y_test)),
            'pos_rate_train': float(y_train.mean()),
            'pos_rate_test': float(y_test.mean()),
        }

        self.model = rf
        logger.info(f"RF trained: ROC AUC={metrics['roc_auc']:.4f} PR AUC={metrics['pr_auc']:.4f}")
        return metrics

    def predict_proba(self, features_dict: Dict) -> float:
        if self.model is None:
            raise RuntimeError('Model not loaded/trained')
        row = {k: features_dict.get(k, 0) for k in self.features}
        X = pd.DataFrame([row])[self.features].fillna(0)
        return float(self.model.predict_proba(X)[:, 1][0])

    def save(self, artifacts: RFArtifacts):
        if self.model is None:
            raise RuntimeError('No trained model to save')
        os.makedirs(os.path.dirname(artifacts.model_path), exist_ok=True)
        os.makedirs(os.path.dirname(artifacts.features_path), exist_ok=True)
        joblib.dump(self.model, artifacts.model_path)
        with open(artifacts.features_path, 'w') as f:
            json.dump(self.features, f)

    def load(self, artifacts: RFArtifacts):
        self.model = joblib.load(artifacts.model_path)
        if os.path.exists(artifacts.features_path):
            with open(artifacts.features_path, 'r') as f:
                self.features = json.load(f)
        return self


class RandomForestFraudService:
    def __init__(self, models_dir: str = './models/rf'):
        self.models_dir = models_dir
        # First try to load voting_fraud_model.pkl from backend directory
        backend_model_path = os.path.join(os.path.dirname(__file__), 'voting_fraud_model.pkl')
        
        self.artifacts = RFArtifacts(
            model_path=backend_model_path if os.path.exists(backend_model_path) else os.path.join(models_dir, 'rf_fraud_model.pkl'),
            features_path=os.path.join(models_dir, 'rf_features.json'),
        )
        self.model = RandomForestFraudModel()
        self._ready = False
        self._try_load()

    def _try_load(self):
        try:
            if os.path.exists(self.artifacts.model_path):
                # Load the pre-trained model
                self.model.model = joblib.load(self.artifacts.model_path)
                
                # Try to load features if available
                if os.path.exists(self.artifacts.features_path):
                    with open(self.artifacts.features_path, 'r') as f:
                        self.model.features = json.load(f)
                
                self._ready = True
                logger.info(f'Loaded RandomForest model from: {self.artifacts.model_path}')
            else:
                logger.warning(f'Model file not found at: {self.artifacts.model_path}')
        except Exception as e:
            logger.warning(f'RF load failed: {e}')
            self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    def train_and_save(self, records: List[Dict]) -> Dict:
        metrics = self.model.train_from_records(records)
        self.model.save(self.artifacts)
        self._ready = True
        return metrics

    def predict_proba(self, feature_dict: Dict) -> float:
        if not self._ready:
            raise RuntimeError('RandomForest model not ready')
        return self.model.predict_proba(feature_dict)


# Global service instance
_rf_service: Optional[RandomForestFraudService] = None


def initialize_rf_service(models_dir: Optional[str] = None) -> RandomForestFraudService:
    global _rf_service
    models_dir = models_dir or os.environ.get('RF_MODELS_DIR', './models/rf')
    _rf_service = RandomForestFraudService(models_dir=models_dir)
    return _rf_service


def get_rf_service() -> Optional[RandomForestFraudService]:
    return _rf_service
