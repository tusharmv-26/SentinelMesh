"""
ML Risk Scoring Engine
Predicts risk scores using a trained RandomForest model
"""

import os
import joblib
from typing import Dict, Tuple


class MLRiskEngine:
    """
    Predicts attack risk scores using a trained ML model
    Replaces the heuristic RiskEngine with learned patterns
    """
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "risk_model.joblib")
        
        self.model = None
        self.feature_names = [
            "access_count",
            "avg_interval",
            "interval_variance",
            "keyword_hit_count",
            "is_tor",
            "is_datacenter",
            "hour_of_day",
            "unique_honeypots_hit"
        ]
        
        self._load_model(model_path)
    
    def _load_model(self, model_path: str):
        """Load trained model from disk"""
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                print(f"✅ Loaded ML risk model from {model_path}")
            except Exception as e:
                print(f"❌ Failed to load model: {e}")
                self.model = None
        else:
            print(f"⚠️  Model not found at {model_path}")
            print("   Run: python backend/ml/generate_training_data.py")
            self.model = None
    
    def predict(self, event: Dict, profile: Dict, enrichment: Dict) -> int:
        """
        Predict risk score (0-100) from event/profile/enrichment data
        
        Args:
            event: Attack event data
            profile: Attacker behavioral profile
            enrichment: IP enrichment data
        
        Returns:
            Risk score 0-100
        """
        if self.model is None:
            # Fallback to simple heuristic if model not available
            return self._fallback_score(event, profile, enrichment)
        
        try:
            features = self._extract_features(event, profile, enrichment)
            score = self.model.predict([features])[0]
            return int(max(0, min(100, score)))  # Clamp to 0-100
        except Exception as e:
            print(f"ML prediction error: {e}, falling back to heuristic")
            return self._fallback_score(event, profile, enrichment)
    
    def _extract_features(self, event: Dict, profile: Dict, enrichment: Dict) -> list:
        """Extract 8-element feature vector for model prediction"""
        
        # 1. access_count
        access_count = profile.get("access_count", 1)
        
        # 2. avg_interval
        intervals = profile.get("intervals", [])
        avg_interval = sum(intervals) / len(intervals) if intervals else 30
        
        # 3. interval_variance
        if intervals and len(intervals) > 1:
            interval_variance = max(intervals) - min(intervals)
        else:
            interval_variance = 0
        
        # 4. keyword_hit_count
        resource_name = event.get("resource_name", "").lower()
        danger_keywords = [
            "password", "secret", "key", "token", "credential", ".env",
            "config", "database", "backup", "admin", "api", "oauth",
            "jwt", "iam", "role", "user"
        ]
        keyword_hits = sum(1 for kw in danger_keywords if kw in resource_name)
        
        # 5. is_tor
        is_tor = 1 if enrichment.get("is_tor", False) else 0
        
        # 6. is_datacenter
        is_datacenter = 1 if enrichment.get("is_datacenter", False) else 0
        
        # 7. hour_of_day
        import datetime
        timestamp = event.get("timestamp", 0)
        if timestamp:
            hour_of_day = datetime.datetime.fromtimestamp(timestamp).hour
        else:
            hour_of_day = 12
        
        # 8. unique_honeypots_hit
        unique_honeypots = profile.get("resources_probed_count", 1)
        
        return [
            access_count,
            avg_interval,
            interval_variance,
            keyword_hits,
            is_tor,
            is_datacenter,
            hour_of_day,
            unique_honeypots
        ]
    
    def _fallback_score(self, event: Dict, profile: Dict, enrichment: Dict) -> int:
        """
        Simple heuristic scoring when model unavailable
        Based on behavior and keyword matching
        """
        score = 20  # Base score
        
        # Increase by access frequency
        score += min(profile.get("access_count", 1) * 5, 30)
        
        # Increase by keyword density
        resource_name = event.get("resource_name", "").lower()
        keywords = [
            "password", "secret", "key", "token", "credential", ".env",
            "config", "database", "backup", "admin", "api"
        ]
        keyword_hits = sum(1 for kw in keywords if kw in resource_name)
        score += min(keyword_hits * 10, 30)
        
        # Increase by behavioral indicators
        if profile.get("behavior_type") == "MANUAL_ATTACKER":
            score += 15
        
        if profile.get("escalation_probability", 0) > 50:
            score += 20
        
        # Increase by enrichment data
        if enrichment.get("is_tor"):
            score += 20
        if enrichment.get("is_datacenter"):
            score += 10
        
        return min(score, 100)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance from trained model"""
        if self.model is None:
            return {}
        
        try:
            importances = self.model.feature_importances_
            return dict(zip(self.feature_names, importances))
        except:
            return {}
