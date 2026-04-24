import json
import random
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

def generate_training_data(num_samples=2500):
    """
    Generates synthetic training data for the Risk ML model.
    Features:
    0: access_count (int)
    1: avg_interval (float)
    2: interval_variance (float)
    3: keyword_hit_count (int)
    4: is_tor (int 0/1)
    5: is_datacenter (int 0/1)
    6: hour_of_day (int 0-23)
    7: unique_honeypots_hit (int)
    
    Target: risk_score (0-100)
    """
    X = []
    y = []
    
    for _ in range(num_samples):
        # 1. Low risk (Scanners, noise, regular traffic) - 40% of data
        if random.random() < 0.4:
            access_count = random.randint(1, 3)
            avg_interval = random.uniform(30, 300)
            interval_variance = random.uniform(0, 10)
            keyword_hit_count = random.randint(0, 1)
            is_tor = 0
            is_datacenter = random.randint(0, 1)
            hour_of_day = random.randint(8, 18) # Business hours
            unique_honeypots_hit = random.randint(0, 1)
            
            base_score = random.uniform(5, 25)
            
        # 2. Medium risk (Aggressive scanners, script kiddies) - 30% of data
        elif random.random() < 0.8:
            access_count = random.randint(4, 10)
            avg_interval = random.uniform(5, 30)
            interval_variance = random.uniform(10, 50)
            keyword_hit_count = random.randint(1, 3)
            is_tor = random.choices([0, 1], weights=[0.8, 0.2])[0]
            is_datacenter = random.randint(0, 1)
            hour_of_day = random.randint(0, 23)
            unique_honeypots_hit = random.randint(1, 2)
            
            base_score = random.uniform(30, 65)
            
        # 3. High risk / APT / "Smart Catch" scenarios - 30% of data
        else:
            # We specifically train the model to be "smart" by giving very high
            # risk to things that hit multiple honeypots or use Tor/Datacenters
            # and target sensitive keywords (like the interactive MITRE paths).
            access_count = random.randint(5, 50)
            avg_interval = random.uniform(0.1, 5) # Very fast (automated attack) OR very slow (APT)
            if random.random() < 0.5:
                avg_interval = random.uniform(3600, 7200) # APT slow
                
            interval_variance = random.uniform(0, 100)
            keyword_hit_count = random.randint(3, 8)
            is_tor = random.choices([0, 1], weights=[0.3, 0.7])[0]
            is_datacenter = random.choices([0, 1], weights=[0.2, 0.8])[0]
            hour_of_day = random.choices([1, 2, 3, 4, 22, 23], k=1)[0] # Off hours
            unique_honeypots_hit = random.randint(3, 6) # Multi-target
            
            base_score = random.uniform(75, 95)

        # Add noise to target
        score = base_score + (random.uniform(-5, 5))
        
        # Absolute rule: if they hit multiple honeypots + keywords (like our Simulator), guarantee high score
        if unique_honeypots_hit >= 2 and keyword_hit_count >= 2:
            score = max(score, random.uniform(85, 99))
            
        # Cap score at 100, floor at 0
        score = min(max(score, 0), 100)
        
        features = [
            access_count,
            avg_interval,
            interval_variance,
            keyword_hit_count,
            is_tor,
            is_datacenter,
            hour_of_day,
            unique_honeypots_hit
        ]
        
        X.append(features)
        y.append(score)
        
    return np.array(X), np.array(y)

def train_and_save():
    print("Generating 2500 synthetic attack records...")
    X, y = generate_training_data(2500)
    
    print("Training RandomForestRegressor...")
    # Train regressor to output continuous risk score 0-100
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)
    
    # Calculate feature importances
    importances = model.feature_importances_
    feature_names = [
        "access_count", "avg_interval", "interval_variance", 
        "keyword_hit_count", "is_tor", "is_datacenter", 
        "hour_of_day", "unique_honeypots_hit"
    ]
    
    importance_dict = {name: float(imp) for name, imp in zip(feature_names, importances)}
    print("Feature Importances learned by model:")
    for k, v in sorted(importance_dict.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v:.4f}")
        
    # Save the model
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'risk_model.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_save()
