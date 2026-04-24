"""
Generate synthetic training data for ML MITRE Technique Classification
Trains a separate model to predict MITRE ATT&CK techniques from attack patterns.
"""

import random
import numpy as np
import os


def generate_mitre_training_data(num_samples=1500):
    """
    Generate synthetic training data for MITRE technique classification.
    
    This model predicts which MITRE techniques are being used based on attack characteristics.
    
    Features:
    - resource_type: 0=S3, 1=EC2_metadata, 2=API, 3=RDS, 4=CONFIG
    - keywords_present: bitmask of keyword types
    - access_pattern: 0=scanner, 1=human, 2=systematic
    - repetition_count: how many times same resource hit
    - behavior_duration: seconds of activity
    - is_tor: 0 or 1
    - is_datacenter: 0 or 1
    - intent_score: 0=reconnaissance, 50=credential_theft, 100=exfiltration
    
    Labels: MITRE technique IDs as integers
    - 0: T1580 (Cloud Infrastructure Discovery)
    - 1: T1619 (Cloud Storage Object Discovery)
    - 2: T1087 (Account Discovery)
    - 3: T1552 (Unsecured Credentials)
    - 4: T1528 (Steal Application Access Token)
    - 5: T1530 (Data from Cloud Storage Object)
    - 6: T1550 (Use Alternate Authentication Material)
    - 7: T1078 (Valid Accounts)
    - 8: T1098 (Account Manipulation)
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
    
    X = []
    y = []
    
    # T1580: Cloud Infrastructure Discovery (generic cloud probing)
    for _ in range(num_samples // 9):
        resource_type = random.randint(0, 4)
        keywords = random.randint(0, 3)  # Few keywords
        access_pattern = 0  # Scanner
        repetition = random.randint(1, 3)
        duration = random.randint(60, 600)
        is_tor = random.randint(0, 1)
        is_datacenter = random.randint(0, 1)
        intent = random.randint(0, 50)
        
        X.append([resource_type, keywords, access_pattern, repetition, duration, 
                 is_tor, is_datacenter, intent])
        y.append(0)  # T1580
    
    # T1619: Cloud Storage Object Discovery (S3 specific)
    for _ in range(num_samples // 9):
        resource_type = 0  # S3
        keywords = random.randint(0, 2)
        access_pattern = 0
        repetition = random.randint(1, 5)
        duration = random.randint(120, 1200)
        is_tor = random.randint(0, 1)
        is_datacenter = 0
        intent = random.randint(0, 50)
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(1)  # T1619
    
    # T1087: Account Discovery (IAM/user keywords)
    for _ in range(num_samples // 9):
        resource_type = random.randint(0, 4)
        keywords = 4  # IAM keywords bitmask
        access_pattern = 0
        repetition = random.randint(2, 8)
        duration = random.randint(300, 1800)
        is_tor = 0
        is_datacenter = 0
        intent = 25
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(2)  # T1087
    
    # T1552: Unsecured Credentials (password/secret keywords)
    for _ in range(num_samples // 9):
        resource_type = random.randint(0, 4)
        keywords = 8  # Credential keywords bitmask
        access_pattern = random.randint(0, 1)
        repetition = random.randint(1, 4)
        duration = random.randint(60, 900)
        is_tor = random.randint(0, 1)
        is_datacenter = random.randint(0, 1)
        intent = random.randint(50, 100)
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(3)  # T1552
    
    # T1528: Steal Application Access Token (API keywords)
    for _ in range(num_samples // 9):
        resource_type = 2  # API
        keywords = 16  # API keywords bitmask
        access_pattern = 1  # Human
        repetition = random.randint(1, 3)
        duration = random.randint(120, 600)
        is_tor = 1  # Often over TOR
        is_datacenter = 0
        intent = random.randint(50, 100)
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(4)  # T1528
    
    # T1530: Data from Cloud Storage Object (S3 exfiltration)
    for _ in range(num_samples // 9):
        resource_type = 0  # S3
        keywords = random.randint(8, 16)
        access_pattern = 1
        repetition = random.randint(3, 10)
        duration = random.randint(600, 3600)
        is_tor = random.randint(0, 1)
        is_datacenter = random.randint(0, 1)
        intent = 100  # Full exfiltration
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(5)  # T1530
    
    # T1550: Use Alternate Authentication Material (lateral movement)
    for _ in range(num_samples // 9):
        resource_type = 1  # EC2 metadata
        keywords = 8
        access_pattern = 0
        repetition = random.randint(2, 6)
        duration = random.randint(300, 1800)
        is_tor = 0
        is_datacenter = 0
        intent = random.randint(50, 100)
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(6)  # T1550
    
    # T1078: Valid Accounts (repeated legitimate access)
    for _ in range(num_samples // 9):
        resource_type = random.randint(0, 4)
        keywords = random.randint(0, 5)
        access_pattern = 1  # Human pattern
        repetition = random.randint(5, 20)
        duration = random.randint(3600, 86400)  # Long sessions
        is_tor = 0
        is_datacenter = 0
        intent = 50
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(7)  # T1078
    
    # T1098: Account Manipulation (escalation)
    for _ in range(num_samples // 9):
        resource_type = 1  # EC2/IAM
        keywords = 12  # Account keywords
        access_pattern = 1
        repetition = random.randint(3, 8)
        duration = random.randint(1800, 7200)
        is_tor = random.randint(0, 1)
        is_datacenter = random.randint(0, 1)
        intent = random.randint(70, 100)
        
        X.append([resource_type, keywords, access_pattern, repetition, duration,
                 is_tor, is_datacenter, intent])
        y.append(8)  # T1098
    
    return np.array(X), np.array(y)


def train_and_save_mitre_model():
    """Train MITRE technique classification model and save it"""
    try:
        from sklearn.ensemble import RandomForestClassifier
        import joblib
    except ImportError:
        print("ERROR: scikit-learn or joblib not installed")
        return False
    
    print("Generating 1500 synthetic MITRE training samples...")
    X, y = generate_mitre_training_data(1500)
    
    print("Training RandomForestClassifier for MITRE technique prediction...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X, y)
    
    # Save model
    model_path = os.path.join(os.path.dirname(__file__), "mitre_model.joblib")
    joblib.dump(model, model_path)
    
    print(f"✅ MITRE model trained and saved to {model_path}")
    
    # Get feature importance
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
    
    importances = model.feature_importances_
    feature_importance_dict = dict(zip(feature_names, importances))
    
    print("\nFeature Importance (MITRE Model):")
    for name, importance in sorted(feature_importance_dict.items(),
                                   key=lambda x: x[1], reverse=True):
        print(f"  {name}: {importance:.4f}")
    
    return True


if __name__ == "__main__":
    train_and_save_mitre_model()
