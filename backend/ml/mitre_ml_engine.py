"""
MITRE ML Technique Classification Engine
Predicts which MITRE techniques are being used based on attack patterns.
Separate model from risk scoring for specialized technique classification.
"""

import os
import joblib
import datetime
from typing import Dict, List


class MITREMLEngine:
    """
    Classifies attacks to MITRE techniques using a trained ML model
    Complements the rule-based MITRE mapper with learned patterns
    """
    
    TECHNIQUE_MAP = {
        0: "T1580",  # Cloud Infrastructure Discovery
        1: "T1619",  # Cloud Storage Object Discovery
        2: "T1087",  # Account Discovery
        3: "T1552",  # Unsecured Credentials
        4: "T1528",  # Steal Application Access Token
        5: "T1530",  # Data from Cloud Storage Object
        6: "T1550",  # Use Alternate Authentication Material
        7: "T1078",  # Valid Accounts
        8: "T1098"   # Account Manipulation
    }
    
    TECHNIQUE_NAMES = {
        "T1580": "Cloud Infrastructure Discovery",
        "T1619": "Cloud Storage Object Discovery",
        "T1087": "Account Discovery",
        "T1552": "Unsecured Credentials",
        "T1528": "Steal Application Access Token",
        "T1530": "Data from Cloud Storage Object",
        "T1550": "Use Alternate Authentication Material",
        "T1078": "Valid Accounts",
        "T1098": "Account Manipulation"
    }
    
    TACTIC_MAP = {
        "T1580": "Discovery (TA0007)",
        "T1619": "Discovery (TA0007)",
        "T1087": "Discovery (TA0007)",
        "T1552": "Credential Access (TA0006)",
        "T1528": "Credential Access (TA0006)",
        "T1530": "Collection (TA0009)",
        "T1550": "Lateral Movement (TA0008)",
        "T1078": "Persistence (TA0003)",
        "T1098": "Persistence (TA0003)"
    }
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "mitre_model.joblib")
        
        self.model = None
        self._load_model(model_path)
    
    def _load_model(self, model_path: str):
        """Load trained MITRE classification model"""
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                print(f"✅ Loaded MITRE ML model from {model_path}")
            except Exception as e:
                print(f"❌ Failed to load MITRE model: {e}")
                self.model = None
        else:
            print(f"⚠️  MITRE model not found at {model_path}")
            print("   Run: python backend/ml/mitre_training_data.py")
            self.model = None
    
    def predict_techniques(self, event: Dict, profile: Dict, enrichment: Dict) -> List[Dict]:
        """
        Predict which MITRE techniques are being used (ML-based)
        
        Returns: List of predicted techniques with confidence scores
        """
        if self.model is None:
            return []
        
        try:
            features = self._extract_features(event, profile, enrichment)
            
            # Get predictions and probabilities
            predictions = self.model.predict([features])[0]
            probabilities = self.model.predict_proba([features])[0]
            
            # Filter to techniques with high confidence
            techniques = []
            threshold = 0.3  # 30% confidence threshold
            
            for technique_idx, prob in enumerate(probabilities):
                if prob > threshold:
                    technique_id = self.TECHNIQUE_MAP.get(technique_idx)
                    if technique_id:
                        techniques.append({
                            "technique_id": technique_id,
                            "technique_name": self.TECHNIQUE_NAMES.get(technique_id),
                            "tactic": self.TACTIC_MAP.get(technique_id),
                            "confidence": "HIGH" if prob > 0.7 else "MEDIUM",
                            "ml_probability": float(prob),
                            "source": "ML_CLASSIFIER"
                        })
            
            # Sort by probability
            techniques.sort(key=lambda x: x["ml_probability"], reverse=True)
            
            return techniques
        
        except Exception as e:
            print(f"MITRE ML prediction error: {e}")
            return []
    
    def _extract_features(self, event: Dict, profile: Dict, enrichment: Dict) -> list:
        """Extract 8-element feature vector for MITRE classifier"""
        
        resource_name = event.get("resource_name", "").lower()
        
        # 1. resource_type (0=S3, 1=EC2_metadata, 2=API, 3=RDS, 4=CONFIG)
        if "s3" in resource_name or "bucket" in resource_name:
            resource_type = 0
        elif "metadata" in resource_name or "ec2" in resource_name:
            resource_type = 1
        elif "api" in resource_name or "endpoint" in resource_name:
            resource_type = 2
        elif "rds" in resource_name or "database" in resource_name:
            resource_type = 3
        else:
            resource_type = 4
        
        # 2. keywords_present (bitmask of keyword types)
        keywords_bitmask = 0
        if any(kw in resource_name for kw in ["iam", "role", "user", "account"]):
            keywords_bitmask |= 4
        if any(kw in resource_name for kw in ["password", "secret", "key", "token", "credential", ".env", "config"]):
            keywords_bitmask |= 8
        if any(kw in resource_name for kw in ["api_key", "oauth", "jwt"]):
            keywords_bitmask |= 16
        if any(kw in resource_name for kw in ["backup", "database", "data"]):
            keywords_bitmask |= 2
        
        # 3. access_pattern (0=scanner, 1=human, 2=systematic)
        behavior_type = profile.get("behavior_type", "")
        if behavior_type == "AUTOMATED_SCANNER":
            access_pattern = 0
        elif behavior_type == "MANUAL_ATTACKER":
            access_pattern = 1
        else:
            access_pattern = 2
        
        # 4. repetition_count
        repetition = profile.get("access_count", 1)
        
        # 5. behavior_duration (seconds of observed activity)
        intervals = profile.get("intervals", [])
        if intervals:
            duration = max(intervals) - min(intervals) if len(intervals) > 1 else 0
        else:
            duration = 0
        
        # 6. is_tor
        is_tor = 1 if enrichment.get("is_tor", False) else 0
        
        # 7. is_datacenter
        is_datacenter = 1 if enrichment.get("is_datacenter", False) else 0
        
        # 8. intent_score (0=reconnaissance, 50=credential_theft, 100=exfiltration)
        intent = profile.get("intent", "RECONNAISSANCE")
        if intent == "DATA_EXFILTRATION":
            intent_score = 100
        elif intent == "CREDENTIAL_HARVESTING":
            intent_score = 50
        else:
            intent_score = 0
        
        return [
            resource_type,
            keywords_bitmask,
            access_pattern,
            repetition,
            duration,
            is_tor,
            is_datacenter,
            intent_score
        ]
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from MITRE classifier"""
        if self.model is None:
            return {}
        
        try:
            feature_names = [
                "resource_type",
                "keywords_present",
                "access_pattern",
                "repetition_count",
                "behavior_duration",
                "is_tor",
                "is_datacenter",
                "intent_score"
            ]
            importances = self.model.feature_importances_
            return dict(zip(feature_names, importances))
        except:
            return {}
