import datetime
from typing import Dict, List, Optional

_tracker = None

class BehaviorTracker:
    def __init__(self, db):
        self.db = db
        # Access MongoDB collections correctly (Database has no callable get; use bracket or get_collection)
        self.votes = db.get_collection('votes')
        self.vote_attempts = db.get_collection('vote_attempts')
        self.fraud_assessments = db.get_collection('fraud_assessments')

    def get_recent_votes(self, user_id: str, hours: int = 1) -> int:
        since = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        return self.votes.count_documents({
            'user_id': user_id,
            'timestamp': {'$gte': since}
        })

    def get_voter_history(self, user_id: str, days: int = 30) -> List[Dict]:
        since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        cursor = self.votes.find({
            'user_id': user_id,
            'timestamp': {'$gte': since}
        }).sort('timestamp', 1)
        return list(cursor)

    def track_vote_attempt(self, user_id: str, session_id: str, vote_attempt_data: Dict, request_data: Dict) -> None:
        doc = {
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': datetime.datetime.utcnow(),
            'vote_attempt': vote_attempt_data,
            'request': request_data
        }
        self.vote_attempts.insert_one(doc)

    def store_fraud_assessment(self, assessment: Dict) -> None:
        # Add a created_at for sorting
        assessment = dict(assessment)
        assessment['created_at'] = datetime.datetime.utcnow()
        self.fraud_assessments.insert_one(assessment)

    def export_training_data(self, labeled_only: bool = False) -> List[Dict]:
        # Join vote_attempts with fraud_assessments by voter_id and timestamp proximity
        attempts = list(self.vote_attempts.find().sort('timestamp', 1))
        assessments = list(self.fraud_assessments.find().sort('timestamp', 1))
        data: List[Dict] = []
        for a in attempts:
            label = None
            match = next((fa for fa in assessments if fa.get('voter_id') == a.get('user_id')), None)
            if match:
                label = match.get('risk_level')
            if labeled_only and label is None:
                continue
            data.append({
                'user_id': a.get('user_id'),
                'session_id': a.get('session_id'),
                'timestamp': a.get('timestamp'),
                'features': a.get('vote_attempt', {}),
                'label': label
            })
        return data

    def get_fraud_assessments(self, risk_level: Optional[str] = None, limit: int = 100) -> List[Dict]:
        query = {}
        if risk_level:
            query['risk_level'] = risk_level
        cursor = self.fraud_assessments.find(query).sort('created_at', -1).limit(limit)
        return list(cursor)


def initialize_behavior_tracker(db):
    global _tracker
    _tracker = BehaviorTracker(db)
    return _tracker


def get_behavior_tracker() -> BehaviorTracker:
    global _tracker
    return _tracker if _tracker else BehaviorTracker(None)
