import difflib
import time

class RiskEngine:
    def __init__(self):
        # In-memory stores for hackathon demo purposes
        self.ip_history = {} # ip -> [timestamps]
        
    def calculate_score(self, ip: str, resource_name: str) -> int:
        score = 0
        current_time = time.time()
        
        # Rule 1: IP is new (no history)
        if ip not in self.ip_history:
            score += 10
            self.ip_history[ip] = []
        
        self.ip_history[ip].append(current_time)
        
        # Clean up old history (keep last 10 minutes)
        ten_mins_ago = current_time - 600
        self.ip_history[ip] = [ts for ts in self.ip_history[ip] if ts > ten_mins_ago]
        
        # Rule 2: Repeated access from same IP within 10-minute window
        if len(self.ip_history[ip]) > 1:
            score += 40
            
        # Rule 3: Resource name contains sensitive keywords
        keywords = ['credentials', 'password', 'secret', 'key', 'prod', 'backup', 'db']
        resource_lower = resource_name.lower()
        if any(kw in resource_lower for kw in keywords):
            score += 30
            
        # Rule 4: Access time between 10pm and 6am local time
        # Using simple local time heuristic for demo
        lt = time.localtime(current_time)
        if lt.tm_hour >= 22 or lt.tm_hour <= 6:
            score += 20
            
        return min(score, 100)

class SimilarityEngine:
    def __init__(self):
        # We simulate the list of real resources for the demo.
        # Ideally, we would fetch this via boto3 EC2 list.
        self.real_resources = [
            {"id": "i-mockdbserver1", "name": "prod-db-server"},
            {"id": "i-mockappserver1", "name": "app-backend-live"},
            {"id": "mock-bucket-1", "name": "company-internal-assets"}
        ]
        
    def find_at_risk_resource(self, honeypot_name: str) -> dict:
        best_match = None
        best_ratio = 0.0
        
        for resource in self.real_resources:
            ratio = difflib.SequenceMatcher(None, honeypot_name.lower(), resource['name'].lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = resource
                
        # Return match if similarity is >= 0.3 to ensure it catches during fast demo
        if best_ratio >= 0.3:
            return best_match
        return None

# Import submodules so they're available
from .attacker_profiler import AttackerProfiler
from .ip_enricher import enrich_ip
from .mutation_engine import MutationEngine
from .mitre_mapper import MITREMapper
from .apt_detector import APTDetector
from .devsecops_manager import DevSecOpsManager
from .honeypot_manager import HoneypotManager
from .employee_tracker import EmployeeActivityTracker
from .correlation_engine import InsiderExternalCorrelationEngine

__all__ = [
    'RiskEngine', 'SimilarityEngine', 'AttackerProfiler', 'enrich_ip', 'MutationEngine',
    'MITREMapper', 'APTDetector', 'DevSecOpsManager', 'HoneypotManager', 
    'EmployeeActivityTracker', 'InsiderExternalCorrelationEngine'
]
