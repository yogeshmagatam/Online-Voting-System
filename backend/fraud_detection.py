"""
Fraud Detection Module (Local)
Uses a local Random Forest model if available, otherwise rule-based heuristics.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
try:
    # Optional local RandomForest model service
    from random_forest_fraud import get_rf_service
except Exception:
    get_rf_service = None
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FraudDetector:
    """Fraud detection using local model or rules"""
    def __init__(self):
        self.model_source = "random_forest_local" if (get_rf_service and get_rf_service()) else "rule_based"
    
    def extract_model_features(self, voter_data: Dict, vote_data: Dict, historical_data: List[Dict]) -> Dict:
        """
        Extract features compatible with the voting_fraud_model.pkl
        Expected features: ['voter_id', 'age', 'ip_address', 'device_id', 
                          'login_attempts', 'vote_duration_sec', 'location_match', 'previous_votes']
        
        Args:
            voter_data: Current voter information
            vote_data: Current vote attempt data
            historical_data: Historical voting patterns
            
        Returns:
            Dictionary of extracted features for the model
        """
        features = {}
        
        # Voter ID (hash to numeric)
        features['voter_id'] = hash(voter_data.get('voter_id', '')) % (10 ** 8)
        
        # Age
        features['age'] = voter_data.get('age', 0)
        
        # IP address (hash to numeric)
        features['ip_address'] = hash(vote_data.get('ip_address', '')) % (10 ** 8)
        
        # Device ID (hash of user agent to numeric)
        features['device_id'] = hash(vote_data.get('user_agent', '')) % (10 ** 8)
        
        # Login attempts
        features['login_attempts'] = vote_data.get('login_attempts', 1)
        
        # Vote duration (session duration)
        features['vote_duration_sec'] = vote_data.get('session_duration', 0)
        
        # Location match (1 if IP is consistent with history, 0 otherwise)
        if historical_data:
            historical_ips = [h.get('ip_address', '') for h in historical_data]
            current_ip = vote_data.get('ip_address', '')
            features['location_match'] = 1 if current_ip in historical_ips else 0
        else:
            features['location_match'] = 1  # First vote, assume match
        
        # Previous votes count
        features['previous_votes'] = len(historical_data)
        
        return features
    
    def extract_voter_behavior_features(self, voter_data: Dict, 
                                       vote_data: Dict, 
                                       historical_data: List[Dict]) -> Dict:
        """
        Extract features from voter behavior for fraud detection
        
        Args:
            voter_data: Current voter information
            vote_data: Current vote attempt data
            historical_data: Historical voting patterns
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Temporal features
        now = datetime.utcnow()
        vote_time = vote_data.get('timestamp', now)
        
        features['hour_of_day'] = vote_time.hour
        features['day_of_week'] = vote_time.weekday()
        features['is_weekend'] = 1 if vote_time.weekday() >= 5 else 0
        
        # Voter profile features
        features['voter_age'] = voter_data.get('age', 0)
        features['voter_registration_days'] = (now - voter_data.get('registration_date', now)).days
        features['has_verified_identity'] = 1 if voter_data.get('identity_verified') else 0
        features['has_mfa_enabled'] = 1 if voter_data.get('mfa_type', 'none') != 'none' else 0
        
        # Behavioral features from current session
        features['login_attempts_today'] = vote_data.get('login_attempts', 0)
        features['session_duration_seconds'] = vote_data.get('session_duration', 0)
        features['page_views_before_vote'] = vote_data.get('page_views', 0)
        features['time_on_voting_page_seconds'] = vote_data.get('time_on_page', 0)
        
        # Device and location features
        features['ip_address_hash'] = hash(vote_data.get('ip_address', '')) % (10 ** 8)
        features['user_agent_hash'] = hash(vote_data.get('user_agent', '')) % (10 ** 8)
        features['is_mobile_device'] = 1 if vote_data.get('is_mobile') else 0
        
        # Historical pattern features
        if historical_data:
            # Calculate average time between votes for this voter
            vote_times = [h.get('timestamp', now) for h in historical_data]
            if len(vote_times) > 1:
                time_diffs = [(vote_times[i] - vote_times[i-1]).total_seconds() 
                             for i in range(1, len(vote_times))]
                features['avg_time_between_votes'] = np.mean(time_diffs)
                features['std_time_between_votes'] = np.std(time_diffs)
            else:
                features['avg_time_between_votes'] = 0
                features['std_time_between_votes'] = 0
            
            # Historical voting count
            features['total_previous_votes'] = len(historical_data)
            
            # IP address changes
            unique_ips = len(set([h.get('ip_address', '') for h in historical_data]))
            features['unique_ip_addresses_used'] = unique_ips
            
            # Device consistency
            unique_devices = len(set([h.get('user_agent', '') for h in historical_data]))
            features['unique_devices_used'] = unique_devices
        else:
            features['avg_time_between_votes'] = 0
            features['std_time_between_votes'] = 0
            features['total_previous_votes'] = 0
            features['unique_ip_addresses_used'] = 1
            features['unique_devices_used'] = 1
        
        # Anomaly indicators
        features['rapid_consecutive_votes'] = 1 if vote_data.get('votes_in_last_hour', 0) > 3 else 0
        features['unusual_voting_time'] = 1 if vote_time.hour < 6 or vote_time.hour > 22 else 0
        features['session_too_short'] = 1 if features['session_duration_seconds'] < 30 else 0
        features['session_too_long'] = 1 if features['session_duration_seconds'] > 3600 else 0
        
        return features
    
    def predict_fraud_probability(self, features: Dict) -> Tuple[float, Dict]:
        """Predict fraud probability using local RF if available, else rules"""
        if get_rf_service is not None:
            try:
                rf_service = get_rf_service()
                if rf_service and rf_service.is_ready():
                    fraud_prob = rf_service.predict_proba(features)
                    details = {
                        'model_type': 'random_forest_local',
                        'timestamp': datetime.utcnow().isoformat(),
                        'features_used': list(features.keys())
                    }
                    logger.info(f"RF fraud prediction: {fraud_prob:.4f}")
                    return fraud_prob, details
            except Exception as e:
                logger.warning(f"Local RF prediction failed: {e}")
        logger.info("Using rule-based detection")
        return self._rule_based_detection(features)
    
    def _rule_based_detection(self, features: Dict) -> Tuple[float, Dict]:
        """
        Fallback rule-based fraud detection when Vertex AI is unavailable
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Tuple of (fraud_probability, prediction_details)
        """
        fraud_score = 0.0
        triggered_rules = []
        
        # Rule 1: Rapid consecutive votes
        if features.get('rapid_consecutive_votes', 0) == 1:
            fraud_score += 0.3
            triggered_rules.append('rapid_consecutive_votes')
        
        # Rule 2: Too many login attempts
        if features.get('login_attempts_today', 0) > 5:
            fraud_score += 0.2
            triggered_rules.append('excessive_login_attempts')
        
        # Rule 3: Session too short (rushed voting)
        if features.get('session_too_short', 0) == 1:
            fraud_score += 0.15
            triggered_rules.append('session_too_short')
        
        # Rule 4: Multiple unique IPs (suspicious)
        if features.get('unique_ip_addresses_used', 1) > 3:
            fraud_score += 0.2
            triggered_rules.append('multiple_ip_addresses')
        
        # Rule 5: Multiple devices (suspicious)
        if features.get('unique_devices_used', 1) > 3:
            fraud_score += 0.15
            triggered_rules.append('multiple_devices')
        
        # Rule 6: No MFA enabled
        if features.get('has_mfa_enabled', 0) == 0:
            fraud_score += 0.1
            triggered_rules.append('no_mfa')
        
        # Rule 7: Identity not verified
        if features.get('has_verified_identity', 0) == 0:
            fraud_score += 0.15
            triggered_rules.append('identity_not_verified')
        
        # Rule 8: Unusual voting time
        if features.get('unusual_voting_time', 0) == 1:
            fraud_score += 0.05
            triggered_rules.append('unusual_voting_time')
        
        # Normalize to [0, 1]
        fraud_probability = min(fraud_score, 1.0)
        
        prediction_details = {
            'model_type': 'rule_based',
            'timestamp': datetime.utcnow().isoformat(),
            'triggered_rules': triggered_rules,
            'rule_count': len(triggered_rules)
        }
        
        logger.info(f"Rule-based fraud score: {fraud_probability:.4f} "
                   f"(triggered {len(triggered_rules)} rules)")
        return fraud_probability, prediction_details
    
    def assess_vote_risk(self, voter_data: Dict, vote_data: Dict, 
                        historical_data: List[Dict]) -> Dict:
        """
        Complete fraud risk assessment for a vote attempt
        
        Args:
            voter_data: Current voter information
            vote_data: Current vote attempt data
            historical_data: Historical voting patterns
            
        Returns:
            Dictionary containing risk assessment results
        """
        # Extract model-compatible features for ML prediction
        model_features = self.extract_model_features(
            voter_data, vote_data, historical_data
        )
        
        # Extract behavior features for rule-based fallback
        behavior_features = self.extract_voter_behavior_features(
            voter_data, vote_data, historical_data
        )
        
        # Try ML prediction first with model features, fallback to rules with behavior features
        rf_service = get_rf_service() if get_rf_service else None
        if rf_service and rf_service.is_ready():
            try:
                fraud_prob = rf_service.predict_proba(model_features)
                prediction_details = {
                    'model_type': 'random_forest_local',
                    'timestamp': datetime.utcnow().isoformat(),
                    'features_used': list(model_features.keys())
                }
                logger.info(f"RF fraud prediction: {fraud_prob:.4f}")
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}, falling back to rules")
                fraud_prob, prediction_details = self._rule_based_detection(behavior_features)
        else:
            # Use rule-based detection with behavior features
            fraud_prob, prediction_details = self._rule_based_detection(behavior_features)
        
        # Determine risk level
        if fraud_prob < 0.3:
            risk_level = 'low'
            action = 'allow'
        elif fraud_prob < 0.6:
            risk_level = 'medium'
            action = 'review'
        else:
            risk_level = 'high'
            action = 'block'
        
        # Compile assessment
        assessment = {
            'fraud_probability': fraud_prob,
            'risk_level': risk_level,
            'recommended_action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'voter_id': voter_data.get('voter_id'),
            'features': model_features,
            'behavior_features': behavior_features,
            'prediction_details': prediction_details
        }
        
        logger.info(f"Vote risk assessment: {risk_level} risk (prob={fraud_prob:.4f})")
        return assessment


# Global instance (will be initialized in app)
fraud_detector = None


def initialize_fraud_detector():
    """Initialize the global fraud detector instance (local only)"""
    global fraud_detector
    fraud_detector = FraudDetector()
    logger.info("Fraud detector initialized (local)")
    return fraud_detector


def get_fraud_detector() -> FraudDetector:
    """Get the global fraud detector instance"""
    global fraud_detector
    if fraud_detector is None:
        initialize_fraud_detector()
    return fraud_detector
