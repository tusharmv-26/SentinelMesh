"""
Generate synthetic training data for ML Risk Scoring Model
Creates 2000 synthetic attack scenarios with varying severity levels.
"""

import random
import numpy as np
import os


def generate_risk_training_data(num_samples=2000):
    """
    Generate synthetic training data for risk scoring model.
    
    Features:
    - access_count: number of probes by this IP
    - avg_interval: average seconds between probes
    - interval_variance: max - min interval
    - keyword_hit_count: danger keywords found
    - is_tor: 0 or 1
    - is_datacenter: 0 or 1
    - hour_of_day: 0-23
    - unique_honeypots_hit: number of honeypots targeted
    
    Labels:
    - 0-30: Low risk
    - 31-69: Medium risk
    - 70-100: High risk
    """
    
    X = []
    y = []
    
    # Low risk examples (label 0-30)
    for _ in range(num_samples // 3):
        access_count = random.randint(1, 3)
        avg_interval = random.uniform(30, 300)
        interval_variance = random.uniform(0, 50)
        keyword_hits = random.randint(0, 1)
        is_tor = 0
        is_datacenter = random.randint(0, 1)
        hour_of_day = random.randint(6, 18)  # Business hours
        unique_honeypots = 1
        
        X.append([access_count, avg_interval, interval_variance, keyword_hits, 
                 is_tor, is_datacenter, hour_of_day, unique_honeypots])
        
        # Low risk score (0-30)
        risk_score = random.randint(5, 30)
        y.append(risk_score)
    
    # Medium risk examples (label 31-69)
    for _ in range(num_samples // 3):
        access_count = random.randint(3, 7)
        avg_interval = random.uniform(5, 30)
        interval_variance = random.uniform(10, 100)
        keyword_hits = random.randint(1, 3)
        is_tor = random.randint(0, 1)
        is_datacenter = random.randint(0, 1)
        hour_of_day = random.randint(0, 23)
        unique_honeypots = random.randint(1, 2)
        
        X.append([access_count, avg_interval, interval_variance, keyword_hits,
                 is_tor, is_datacenter, hour_of_day, unique_honeypots])
        
        # Medium risk score (31-69)
        risk_score = random.randint(31, 69)
        y.append(risk_score)
    
    # High risk examples (label 70-100)
    for _ in range(num_samples // 3):
        access_count = random.randint(7, 20)
        avg_interval = random.uniform(0.5, 5)
        interval_variance = random.uniform(50, 200)
        keyword_hits = random.randint(3, 8)
        is_tor = random.randint(0, 1)  # High TOR probability
        is_datacenter = random.randint(0, 1)
        hour_of_day = random.choice([0, 1, 2, 3, 4, 5, 22, 23])  # Off-hours
        unique_honeypots = random.randint(2, 5)
        
        X.append([access_count, avg_interval, interval_variance, keyword_hits,
                 is_tor, is_datacenter, hour_of_day, unique_honeypots])
        
        # High risk score (70-100)
        risk_score = random.randint(70, 100)
        y.append(risk_score)
    
    return np.array(X), np.array(y)


def train_and_save_risk_model():
    """Train RandomForest model and save it"""
    try:
        from sklearn.ensemble import RandomForestRegressor
        import joblib
    except ImportError:
        print("ERROR: scikit-learn or joblib not installed")
        print("Install with: pip install scikit-learn joblib --break-system-packages")
        return False
    
    print("Generating 2000 synthetic risk training samples...")
    X, y = generate_risk_training_data(2000)
    
    print("Training RandomForestRegressor for risk scoring...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X, y)
    
    # Save model
    model_path = os.path.join(os.path.dirname(__file__), "risk_model.joblib")
    joblib.dump(model, model_path)
    
    print(f"✅ Risk model trained and saved to {model_path}")
    
    # Get feature importance
    feature_names = [
        "access_count",
        "avg_interval",
        "interval_variance",
        "keyword_hit_count",
        "is_tor",
        "is_datacenter",
        "hour_of_day",
        "unique_honeypots_hit"
    ]
    
    importances = model.feature_importances_
    feature_importance_dict = dict(zip(feature_names, importances))
    
    print("\nFeature Importance (Risk Model):")
    for name, importance in sorted(feature_importance_dict.items(), 
                                   key=lambda x: x[1], reverse=True):
        print(f"  {name}: {importance:.4f}")
    
    return True


if __name__ == "__main__":
    train_and_save_risk_model()
