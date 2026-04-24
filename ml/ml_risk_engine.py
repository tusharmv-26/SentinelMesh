import os
import time
import joblib

class MLRiskEngine:
    def __init__(self):
        self.model = None
        self.ip_history = {}  # Store access histories for feature extraction
        
        # Load model
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'risk_model.joblib')
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                print("MLRiskEngine: Successfully loaded RandomForest model.")
            except Exception as e:
                print(f"MLRiskEngine Error: Could not load model - {e}")
        else:
            print("MLRiskEngine Warning: risk_model.joblib not found. Run generate_training_data.py first.")

    def calculate_score(self, ip: str, resource_name: str, event: dict = None, profile: dict = None, honeypot_manager = None) -> int:
        """
        Calculate ML risk score using the trained Random Forest model.
        Falls back to a heuristic if the model isn't loaded.
        """
        if not event:
            event = {}
            
        current_time = time.time()
        
        # Update internal history for this IP
        if ip not in self.ip_history:
            self.ip_history[ip] = {
                "timestamps": [],
                "honeypots_hit": set(),
                "keywords_hit": 0
            }
            
        history = self.ip_history[ip]
        history["timestamps"].append(current_time)
        
        # Check honeypot manager
        if honeypot_manager:
            for hp in honeypot_manager.get_all_honeypots():
                if hp["resource_name"] == resource_name:
                    history["honeypots_hit"].add(hp["id"])
        else:
            # Fallback heuristic for honeypot count
            history["honeypots_hit"].add(resource_name)
            
        # Count keywords
        keywords = ['credentials', 'password', 'secret', 'key', 'prod', 'backup', 'db', 'admin', 'role', 'env']
        resource_lower = resource_name.lower()
        if any(kw in resource_lower for kw in keywords):
            history["keywords_hit"] += 1
            
        # Extract the 8 features
        # 1. access_count
        access_count = len(history["timestamps"])
        
        # 2 & 3. avg_interval, interval_variance
        if access_count > 1:
            intervals = [history["timestamps"][i] - history["timestamps"][i-1] for i in range(1, access_count)]
            avg_interval = sum(intervals) / len(intervals)
            interval_variance = max(intervals) - min(intervals)
        else:
            avg_interval = 60.0 # default baseline
            interval_variance = 0.0
            
        # 4. keyword_hit_count
        keyword_hit_count = history["keywords_hit"]
        
        # 5 & 6. is_tor, is_datacenter
        enrichment = event.get("ip_enrichment", {}) if event else {}
        is_tor = 1 if enrichment.get("is_tor", False) else 0
        is_datacenter = 1 if enrichment.get("is_datacenter", False) else 0
        
        # 7. hour_of_day
        lt = time.localtime(current_time)
        hour_of_day = lt.tm_hour
        
        # 8. unique_honeypots_hit
        unique_honeypots_hit = len(history["honeypots_hit"])
        
        # If model is loaded, predict
        if self.model:
            features = [[
                access_count,
                avg_interval,
                interval_variance,
                keyword_hit_count,
                is_tor,
                is_datacenter,
                hour_of_day,
                unique_honeypots_hit
            ]]
            
            try:
                base_score = self.model.predict(features)[0]
                # Ensure the score strictly increases with each step in the MITRE path!
                path_booster = (unique_honeypots_hit - 1) * 15
                final_score = max(base_score, 20 + path_booster)
                return int(min(max(final_score, 0), 100))
            except Exception as e:
                print(f"ML Prediction failed: {e}")
                
        # Fallback to heuristic if model is unavailable
        score = 10
        if access_count > 1: score += 20
        if unique_honeypots_hit > 1: score += 30
        if keyword_hit_count > 0: score += 20
        if is_tor or is_datacenter: score += 20
        
        return min(score, 100)
    
    def get_feature_importance(self) -> dict:
        """Returns the feature importance learned by the Random Forest"""
        if not self.model:
            return {}
            
        feature_names = [
            "access_count", "avg_interval", "interval_variance", 
            "keyword_hit_count", "is_tor", "is_datacenter", 
            "hour_of_day", "unique_honeypots_hit"
        ]
        importances = self.model.feature_importances_
        return {name: float(imp) for name, imp in zip(feature_names, importances)}
