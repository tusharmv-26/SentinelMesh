import time
from typing import Dict, List

class EmployeeActivityTracker:
    """Track employee access patterns for insider threat detection"""
    
    def __init__(self):
        self.employee_logs = {}  # employee_id -> list of access records
        self.suspicious_patterns = {
            "mass_export": [],
            "off_hours_access": [],
            "unusual_resources": [],
            "vpn_usage": []
        }
    
    def log_employee_access(self, employee_id: str, resource: str, 
                           access_type: str, timestamp: float = None):
        """
        Log employee accessing a resource
        
        Args:
            employee_id: Email or ID of employee
            resource: What they accessed (file, database, S3 bucket)
            access_type: "read", "download", "export", "modify", "delete"
            timestamp: When it happened
        """
        if timestamp is None:
            timestamp = time.time()
        
        if employee_id not in self.employee_logs:
            self.employee_logs[employee_id] = []
        
        access_record = {
            "employee_id": employee_id,
            "resource": resource,
            "access_type": access_type,
            "timestamp": timestamp,
            "is_suspicious": self._classify_suspicion(access_type, resource),
            "risk_score": self._calculate_risk(access_type, resource)
        }
        
        self.employee_logs[employee_id].append(access_record)
        
        # Check for suspicious patterns
        self._detect_suspicious_patterns(employee_id)
        
        return access_record
    
    def _classify_suspicion(self, access_type: str, resource: str) -> bool:
        """Determine if access pattern is suspicious"""
        
        suspicious_types = ["export", "download", "delete", "modify"]
        sensitive_resources = ["password", "credential", "secret", "database", 
                             "backup", "config", "key", "token", "admin"]
        
        is_suspicious_type = access_type in suspicious_types
        is_sensitive_resource = any(word in resource.lower() for word in sensitive_resources)
        
        return is_suspicious_type or is_sensitive_resource
    
    def _calculate_risk(self, access_type: str, resource: str) -> int:
        """Calculate risk score 0-100"""
        
        risk = 0
        
        # Export/Download is riskier than read
        if access_type == "export":
            risk += 40
        elif access_type == "download":
            risk += 30
        elif access_type == "delete":
            risk += 50
        elif access_type == "modify":
            risk += 20
        elif access_type == "read":
            risk += 10
        
        # Sensitive resources are riskier
        sensitive_words = ["password", "credential", "secret", "key", "token", "database"]
        if any(word in resource.lower() for word in sensitive_words):
            risk += 30
        
        return min(risk, 100)
    
    def _detect_suspicious_patterns(self, employee_id: str):
        """Detect suspicious behavior patterns"""
        
        logs = self.employee_logs[employee_id]
        
        if len(logs) < 2:
            return
        
        # Pattern 1: Mass export (5+ exports in 1 hour)
        recent_exports = [l for l in logs[-10:] 
                         if l["access_type"] == "export" and 
                         time.time() - l["timestamp"] < 3600]
        
        if len(recent_exports) >= 5:
            self.suspicious_patterns["mass_export"].append({
                "employee_id": employee_id,
                "count": len(recent_exports),
                "timestamp": time.time()
            })
        
        # Pattern 2: Off-hours access (after 6pm or before 6am)
        latest_log = logs[-1]
        hour = time.localtime(latest_log["timestamp"]).tm_hour
        
        if hour < 6 or hour > 18:
            self.suspicious_patterns["off_hours_access"].append({
                "employee_id": employee_id,
                "hour": hour,
                "timestamp": time.time()
            })
    
    def get_employee_profile(self, employee_id: str) -> Dict:
        """Get risk profile for an employee"""
        
        if employee_id not in self.employee_logs:
            return {
                "employee_id": employee_id,
                "total_accesses": 0,
                "suspicious_accesses": 0,
                "avg_risk_score": 0,
                "threat_level": "LOW"
            }
        
        logs = self.employee_logs[employee_id]
        suspicious_count = sum(1 for l in logs if l["is_suspicious"])
        avg_risk = sum(l["risk_score"] for l in logs) / len(logs) if logs else 0
        
        threat_level = "LOW"
        if avg_risk > 50:
            threat_level = "CRITICAL"
        elif avg_risk > 30:
            threat_level = "HIGH"
        elif avg_risk > 10:
            threat_level = "MEDIUM"
        
        return {
            "employee_id": employee_id,
            "total_accesses": len(logs),
            "suspicious_accesses": suspicious_count,
            "avg_risk_score": int(avg_risk),
            "threat_level": threat_level,
            "latest_access": logs[-1] if logs else None
        }

    def get_all_activities(self) -> List[Dict]:
        all_activities = []
        for logs in self.employee_logs.values():
            all_activities.extend(logs)
        return all_activities

    def get_all_employees(self) -> List[Dict]:
        profiles = [self.get_employee_profile(emp_id) for emp_id in self.employee_logs.keys()]
        return sorted(profiles, key=lambda x: x['avg_risk_score'], reverse=True)
