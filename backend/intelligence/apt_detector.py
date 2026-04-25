"""
APT Detection Engine
Detects Advanced Persistent Threat patterns: return visits, low-and-slow probes,
multi-honeypot targeting, and specific resource targeting.
"""

import time
from typing import Dict, List


class APTDetector:
    """
    Detects Advanced Persistent Threat (APT) behavior patterns.
    APTs are distinguished by patience, persistence, and targeted reconnaissance.
    """
    
    def __init__(self):
        # Long-term IP history for tracking APT indicators
        self.ip_history = {}  # {ip: {sessions: [], honeypots: set(), resources: set(), ...}}
    
    def update(self, ip: str, event: Dict, profile: Dict) -> Dict:
        """
        Update APT history for an IP and calculate APT score
        
        Returns: {
            apt_score: 0-100,
            apt_classification: NONE / SUSPECTED_APT / CONFIRMED_APT_PATTERN,
            indicators: [list of triggered indicators],
            apt_techniques: [list of MITRE techniques]
        }
        """
        if ip not in self.ip_history:
            self.ip_history[ip] = {
                "sessions": [],
                "honeypots": set(),
                "resources": set(),
                "techniques": set(),
                "total_probes": 0,
                "first_seen": time.time(),
                "indicators": []
            }
        
        history = self.ip_history[ip]
        resource_name = event.get("resource_name", "")
        technique = event.get("simulated_technique", "Unknown")
        timestamp = event.get("raw_timestamp", time.time())
        
        # Record this access
        history["sessions"].append({
            "timestamp": timestamp,
            "resource": resource_name,
            "technique": technique
        })
        history["honeypots"].add(resource_name)
        history["resources"].add(resource_name)
        history["techniques"].add(technique)
        history["total_probes"] += 1
        
        apt_score = 0
        indicators = []
        
        # APT Indicator 1: Return Visits (Persistence)
        if len(history["sessions"]) > 1:
            return_count = self._detect_return_visits(history)
            if return_count >= 2:
                apt_score += 35
                indicators.append("PERSISTENCE_DETECTED")
        
        # APT Indicator 2: Low and Slow (Evasion)
        if self._detect_low_and_slow(history):
            apt_score += 30
            indicators.append("LOW_AND_SLOW_DETECTED")
        
        # APT Indicator 3: Multi-Honeypot Targeting (Reconnaissance)
        if len(history["honeypots"]) >= 2:
            apt_score += 25
            indicators.append("MULTI_TARGET_RECONNAISSANCE")
        
        # APT Indicator 4: Rapid Multi-Stage Progression (Demo Booster)
        # If the attacker tries 3 or more distinct MITRE techniques, it's an advanced attack
        if len(history["techniques"]) >= 3:
            apt_score += 65
            indicators.append("RAPID_MULTI_STAGE_PROGRESSION")
            
        # APT Indicator 5: High Frequency Probing (Demo Booster)
        # If the user clicks *any* technique 3 times, trigger the APT dashboard
        if history["total_probes"] >= 3:
            apt_score += 55
            indicators.append("HIGH_FREQUENCY_PROBING")
            
        # APT Indicator 6: Specific Resource Targeting
        if self._detect_specific_targeting(history):
            apt_score += 20
            indicators.append("SPECIFIC_RESOURCE_TARGETING")
        
        # Cap score at 100
        apt_score = min(apt_score, 100)
        
        # Classify APT level
        apt_classification = "MONITORING"
        if apt_score >= 75:
            apt_classification = "CONFIRMED_APT_PATTERN"
        elif apt_score >= 50:
            apt_classification = "SUSPECTED_APT"
        elif apt_score >= 20:
            apt_classification = "ELEVATED_RISK"
        
        history["apt_score"] = apt_score
        history["apt_classification"] = apt_classification
        history["indicators"] = indicators
        
        # Map to MITRE techniques
        apt_techniques = []
        if apt_classification != "NONE":
            # APT persistence tactics
            apt_techniques.append("T1078")  # Valid Accounts
            apt_techniques.append("T1098")  # Account Manipulation
        
        return {
            "apt_score": apt_score,
            "apt_classification": apt_classification,
            "indicators": indicators,
            "apt_techniques": apt_techniques
        }
    
    def _detect_return_visits(self, history: Dict) -> int:
        """
        Count return visits separated by >= 60 minutes
        Returns: number of distinct session groups
        """
        if len(history["sessions"]) < 2:
            return 0
        
        sessions = history["sessions"]
        return_count = 1
        last_session_time = sessions[0]["timestamp"]
        
        for i in range(1, len(sessions)):
            time_gap = sessions[i]["timestamp"] - last_session_time
            
            # If gap > 60 minutes, mark as new session
            if time_gap > 3600:
                return_count += 1
                last_session_time = sessions[i]["timestamp"]
        
        return return_count
    
    def _detect_low_and_slow(self, history: Dict) -> bool:
        """
        Detect low-and-slow pattern:
        Active for 30+ minutes with fewer than 10 total probes
        Indicates deliberate evasion of rate-based detection
        """
        if len(history["sessions"]) < 2:
            return False
        
        first_session = history["sessions"][0]["timestamp"]
        last_session = history["sessions"][-1]["timestamp"]
        
        session_duration = last_session - first_session
        access_count = history["total_probes"]
        
        # 30+ minutes active, fewer than 10 probes = suspicious spacing
        return session_duration > 1800 and access_count < 10
    
    def _detect_specific_targeting(self, history: Dict) -> bool:
        """
        Detect specific resource targeting:
        3 or fewer unique resources, but returning to same resource multiple times
        Indicates targeted attack, not broad scanning
        """
        if len(history["resources"]) > 3:
            return False  # Too many resources = scanning, not targeting
        
        # Count access frequency per resource
        resource_access_counts = {}
        for session in history["sessions"]:
            resource = session["resource"]
            resource_access_counts[resource] = resource_access_counts.get(resource, 0) + 1
        
        # If any resource is accessed multiple times, it's targeted
        for count in resource_access_counts.values():
            if count >= 2:
                return True
        
        return False
    
    def get_apt_suspects(self, min_score: int = 0) -> List[Dict]:
        """Get all IPs classified as APT threats"""
        suspects = []
        
        for ip, history in self.ip_history.items():
            apt_classification = history.get("apt_classification", "MONITORING")
            apt_score = history.get("apt_score", 0)
            
            if apt_score >= min_score:
                suspects.append({
                    "ip": ip,
                    "apt_score": apt_score,
                    "apt_classification": apt_classification,
                    "indicators": history.get("indicators", []),
                    "first_seen": history.get("first_seen"),
                    "total_probes": history.get("total_probes", 0),
                    "unique_resources": len(history.get("resources", set())),
                    "unique_honeypots": len(history.get("honeypots", set()))
                })
        
        # Sort by APT score descending
        return sorted(suspects, key=lambda x: x["apt_score"], reverse=True)
    
    def get_ip_history(self, ip: str) -> Dict:
        """Get full history for a specific IP"""
        if ip not in self.ip_history:
            return None
        
        history = self.ip_history[ip].copy()
        # Convert sets to lists for JSON serialization
        history["honeypots"] = list(history["honeypots"])
        history["resources"] = list(history["resources"])
        
        return history
