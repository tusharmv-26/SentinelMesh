"""
Honeypot Management System
Tracks all honeypots across the system with their status, hit counts, and access patterns.
"""

import time
from typing import Dict, List


class HoneypotManager:
    """Manages honeypot registry, hit tracking, and mode transitions"""
    
    def __init__(self):
        self.honeypots = {
            "s3-customer-backups": {
                "id": "s3-customer-backups",
                "name": "Customer Database Backups",
                "type": "S3_BUCKET",
                "resource_name": "company-prod-db-backup-2024",
                "description": "S3 bucket with fake customer database backups",
                "created_at": time.time(),
                "total_hits": 0,
                "last_accessed": None,
                "mode": "PASSIVE",
                "threat_level": "LOW"
            },
            "ec2-metadata": {
                "id": "ec2-metadata",
                "name": "EC2 Metadata Endpoint",
                "type": "EC2_METADATA",
                "resource_name": "ec2-metadata-ssrf-honeypot",
                "description": "Fake AWS EC2 instance metadata service endpoint",
                "created_at": time.time(),
                "total_hits": 0,
                "last_accessed": None,
                "mode": "PASSIVE",
                "threat_level": "LOW"
            },
            "rds-credentials": {
                "id": "rds-credentials",
                "name": "RDS Connection String",
                "type": "S3_BUCKET",
                "resource_name": "internal-db-connection-strings-2026",
                "description": "S3 bucket with fake RDS database connection strings",
                "created_at": time.time(),
                "total_hits": 0,
                "last_accessed": None,
                "mode": "PASSIVE",
                "threat_level": "LOW"
            },
            "api-keys-endpoint": {
                "id": "api-keys-endpoint",
                "name": "API Keys Endpoint",
                "type": "API_ENDPOINT",
                "resource_name": "api-keys-honeypot",
                "description": "Fake internal API endpoint with exposed API keys",
                "created_at": time.time(),
                "total_hits": 0,
                "last_accessed": None,
                "mode": "PASSIVE",
                "threat_level": "LOW"
            },
            "env-config-file": {
                "id": "env-config-file",
                "name": ".env Configuration File",
                "type": "S3_BUCKET",
                "resource_name": "dev-environment-configs-backup-2026",
                "description": "S3 bucket with fake .env file containing secrets",
                "created_at": time.time(),
                "total_hits": 0,
                "last_accessed": None,
                "mode": "PASSIVE",
                "threat_level": "LOW"
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
