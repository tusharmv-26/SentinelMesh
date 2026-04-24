"""
Honeypot Management System
Tracks all honeypots across the system with their status, hit counts, and access patterns.
"""

import time
from typing import Dict, List


class HoneypotManager:
    """Manages honeypot registry, hit tracking, and mode transitions"""
    
    def __init__(self):
        import hashlib
        canary_hash = hashlib.md5(f"apex-trap-{time.time()}".encode()).hexdigest()[:8]
        
        self.honeypots = {
            "sentinelmesh-apex-trap": {
                "id": "sentinelmesh-apex-trap",
                "name": "SentinelMesh Apex Trap",
                "type": "DYNAMIC_TRAP",
                "resource_name": "unified-core-trap-endpoint",
                "description": "Unified Super-Honeypot handling all threat vectors simultaneously.",
                "created_at": time.time(),
                "total_hits": 0,
                "last_accessed": None,
                "mode": "ACTIVE",
                "threat_level": "HIGH",
                "integration_type": "native",
                "canary_token": f"canary_{canary_hash}",
                "intent_analysis": "Full Payload & Keystroke Logging",
                "vuln_profile": "Adaptive Exploit Baiting"
            }
        }
        
        # Track per-IP access to honeypots for progressive revelation
        self.ip_access_counts = {}  # {ip: {honeypot_id: access_count}}
    
    def record_hit(self, honeypot_id: str, attacker_ip: str):
        """Record a hit on a honeypot"""
        if honeypot_id in self.honeypots:
            self.honeypots[honeypot_id]["total_hits"] += 1
            self.honeypots[honeypot_id]["last_accessed"] = time.time()
            
            # Track per-IP access for progressive revelation
            if attacker_ip not in self.ip_access_counts:
                self.ip_access_counts[attacker_ip] = {}
            
            if honeypot_id not in self.ip_access_counts[attacker_ip]:
                self.ip_access_counts[attacker_ip][honeypot_id] = 0
            
            self.ip_access_counts[attacker_ip][honeypot_id] += 1
    
    def get_honeypot(self, honeypot_id: str) -> Dict:
        """Get single honeypot details"""
        return self.honeypots.get(honeypot_id)
    
    def get_all_honeypots(self) -> List[Dict]:
        """Get all honeypots with current status"""
        honeypots_list = []
        for hp_id, hp_data in self.honeypots.items():
            honeypots_list.append(hp_data.copy())
        return honeypots_list
    
    def set_mode(self, honeypot_id: str, mode: str):
        """Change honeypot mode: PASSIVE, ACTIVE, DECEPTION_MODE"""
        if honeypot_id in self.honeypots:
            self.honeypots[honeypot_id]["mode"] = mode
            if mode == "DECEPTION_MODE":
                self.honeypots[honeypot_id]["threat_level"] = "CRITICAL"
            elif mode == "ACTIVE":
                self.honeypots[honeypot_id]["threat_level"] = "HIGH"
            else:
                self.honeypots[honeypot_id]["threat_level"] = "LOW"
    
    def get_access_tier(self, honeypot_id: str, attacker_ip: str) -> int:
        """
        Get progressive revelation tier (1-3) based on access count
        Tier 1: First access - generic response
        Tier 2: Second access - slightly more specific
        Tier 3: Third+ access - most sensitive data
        """
        if attacker_ip not in self.ip_access_counts:
            return 1
        
        access_count = self.ip_access_counts[attacker_ip].get(honeypot_id, 0)
        
        if access_count <= 1:
            return 1
        elif access_count == 2:
            return 2
        else:
            return 3
    
    def get_honeypot_status(self) -> Dict:
        """Get summary statistics for all honeypots"""
        total_hits = sum(hp["total_hits"] for hp in self.honeypots.values())
        active_honeypots = len([hp for hp in self.honeypots.values() if hp["mode"] != "PASSIVE"])
        deception_mode = len([hp for hp in self.honeypots.values() if hp["mode"] == "DECEPTION_MODE"])
        
        return {
            "total_honeypots": len(self.honeypots),
            "total_hits": total_hits,
            "active_honeypots": active_honeypots,
            "deception_mode_count": deception_mode,
            "honeypots": self.get_all_honeypots()
        }

    def trigger_apex_honeypot(self, technique_id: str, technique_name: str, tactic: str) -> Dict:
        """
        Routes the attacker to the unified Apex Trap and generates contextual
        threat intelligence based on the specific MITRE technique used.
        """
        apex_id = "sentinelmesh-apex-trap"
        if apex_id in self.honeypots:
            self.honeypots[apex_id]["total_hits"] += 1
            self.honeypots[apex_id]["last_accessed"] = time.time()
            base_trap = self.honeypots[apex_id]
        else:
            base_trap = {}

        # Determine contextual vulnerability based on tactic
        vuln_map = {
            "Initial Access": "CVE-2024-3094 (XZ Utils)",
            "Execution": "CVE-2021-44228 (Log4Shell)",
            "Persistence": "SMBv1 Auth Bypass",
            "Privilege Escalation": "CVE-2021-3156 (Sudo)",
            "Defense Evasion": "EDR EDR-Bypass Script",
            "Credential Access": "Cleartext SAM Backup",
            "Discovery": "Exposed AD LDAP",
            "Lateral Movement": "Open RDP (No NLA)",
            "Collection": "Unauthenticated S3",
            "Exfiltration": "Unrestricted Outbound DNS"
        }
        
        # Return the intel package to the caller
        return {
            "resource_name": base_trap.get("resource_name", "unified-core-trap-endpoint"),
            "canary_token": base_trap.get("canary_token", "canary_default"),
            "intent_detected": f"Attempting {technique_name} via {tactic}",
            "vuln_profile": vuln_map.get(tactic, "Generic Misconfiguration")
        }
