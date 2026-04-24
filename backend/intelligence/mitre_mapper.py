"""
MITRE ATT&CK Framework Mapping
Maps detected attack patterns to MITRE TTP (Tactic, Technique, Procedure) IDs
"""

from typing import List, Dict


class MITREMapper:
    """Maps detected attacks to MITRE ATT&CK techniques"""
    
    # Complete MITRE technique database
    MITRE_TECHNIQUES = {
        "T1580": {
            "id": "T1580",
            "name": "Cloud Infrastructure Discovery",
            "tactic": "Discovery (TA0007)",
            "description": "Adversary enumerates cloud resources to find targets"
        },
        "T1619": {
            "id": "T1619",
            "name": "Cloud Storage Object Discovery",
            "tactic": "Discovery (TA0007)",
            "description": "Adversary discovers S3 buckets and their contents"
        },
        "T1087": {
            "id": "T1087",
            "name": "Account Discovery",
            "tactic": "Discovery (TA0007)",
            "description": "Adversary probes for IAM roles and service accounts"
        },
        "T1552": {
            "id": "T1552",
            "name": "Unsecured Credentials",
            "tactic": "Credential Access (TA0006)",
            "description": "Adversary discovers exposed secrets in code or config files"
        },
        "T1528": {
            "id": "T1528",
            "name": "Steal Application Access Token",
            "tactic": "Credential Access (TA0006)",
            "description": "Adversary steals API keys, OAuth tokens, or JWT tokens"
        },
        "T1530": {
            "id": "T1530",
            "name": "Data from Cloud Storage Object",
            "tactic": "Collection (TA0009)",
            "description": "Adversary exfiltrates data from S3 buckets or cloud storage"
        },
        "T1550": {
            "id": "T1550",
            "name": "Use Alternate Authentication Material",
            "tactic": "Lateral Movement (TA0008)",
            "description": "Adversary uses stolen credentials for lateral movement"
        },
        "T1078": {
            "id": "T1078",
            "name": "Valid Accounts",
            "tactic": "Persistence (TA0003)",
            "description": "Adversary uses legitimate credentials to maintain access"
        },
        "T1098": {
            "id": "T1098",
            "name": "Account Manipulation",
            "tactic": "Persistence (TA0003)",
            "description": "Adversary modifies or creates accounts for persistence"
        }
    }
    
    # APT group patterns (best-effort attribution)
    APT_PATTERNS = {
        "APT29_COZY_BEAR": {
            "name": "APT-29 / Cozy Bear",
            "description": "Russian state-sponsored APT targeting cloud infrastructure",
            "techniques": ["T1580", "T1552", "T1530", "T1078"],
            "confidence": "MEDIUM"
        },
        "APT33_ELFIN": {
            "name": "APT-33 / Elfin",
            "description": "Iranian state-sponsored APT with cloud targeting",
            "techniques": ["T1087", "T1528", "T1550"],
            "confidence": "MEDIUM"
        },
        "LAPSUS": {
            "name": "LAPSUS Group",
            "description": "Extortion-focused group targeting cloud infrastructure",
            "techniques": ["T1619", "T1552", "T1530"],
            "confidence": "MEDIUM"
        }
    }
    
    def __init__(self):
        self.detected_techniques = {}  # Track technique hits
    
    def map_to_mitre(self, event: Dict, profile: Dict) -> List[Dict]:
        """
        Map event and profile to MITRE techniques
        
        Args:
            event: Attack event data
            profile: Attacker behavioral profile
        
        Returns:
            List of MITRE technique matches with confidence scores
        """
        techniques = []
        resource_name = event.get("resource_name", "").lower()
        intent = profile.get("intent", "").upper()
        behavior_type = profile.get("behavior_type", "").upper()
        is_tor = event.get("ip_enrichment", {}).get("is_tor", False)
        
        # Discovery Tactic (TA0007)
        # T1580: Cloud Infrastructure Discovery - any cloud resource probe
        if "s3" in resource_name or "ec2" in resource_name or "rds" in resource_name or "bucket" in resource_name:
            techniques.append(self._create_match(
                "T1580",
                confidence="HIGH" if not is_tor else "MEDIUM",
                reason="Cloud resource enumeration detected"
            ))
        
        # T1619: Cloud Storage Object Discovery - specific S3 access
        if "s3" in resource_name or "bucket" in resource_name:
            techniques.append(self._create_match(
                "T1619",
                confidence="HIGH",
                reason="S3 bucket access indicates object discovery"
            ))
        
        # T1087: Account Discovery - IAM/user/role keywords
        iam_keywords = ["iam", "role", "user", "account", "credentials", "principal"]
        if any(kw in resource_name for kw in iam_keywords):
            techniques.append(self._create_match(
                "T1087",
                confidence="HIGH",
                reason="IAM resource probing indicates account discovery"
            ))
        
        # Credential Access Tactic (TA0006)
        # T1552: Unsecured Credentials - sensitive keywords in resource
        credential_keywords = ["password", "secret", "key", "token", "credential", ".env", "config", "database.yml"]
        if any(kw in resource_name for kw in credential_keywords):
            techniques.append(self._create_match(
                "T1552",
                confidence="HIGH",
                reason="Access attempt to credential-bearing resource"
            ))
        
        # T1528: Steal Application Access Token - API key specific
        api_keywords = ["api_key", "token", "oauth", "jwt", "bearer", "api-key"]
        if any(kw in resource_name for kw in api_keywords):
            techniques.append(self._create_match(
                "T1528",
                confidence="HIGH",
                reason="API key or token theft attempt detected"
            ))
        
        # T1530: Data from Cloud Storage Object - S3 with exfiltration intent
        if ("s3" in resource_name or "bucket" in resource_name) and intent == "DATA_EXFILTRATION":
            techniques.append(self._create_match(
                "T1530",
                confidence="HIGH",
                reason="S3 data exfiltration intent detected"
            ))
        
        # Lateral Movement Tactic (TA0008)
        # T1550: Use Alternate Authentication Material - EC2 metadata SSRF
        if "metadata" in resource_name or "ec2-metadata" in resource_name:
            techniques.append(self._create_match(
                "T1550",
                confidence="HIGH",
                reason="EC2 metadata SSRF indicates credential theft for lateral movement"
            ))
        
        # Persistence Tactic (TA0003)
        # T1078: Valid Accounts - repeated access with valid creds
        if behavior_type == "MANUAL_ATTACKER" and profile.get("access_count", 0) > 5:
            techniques.append(self._create_match(
                "T1078",
                confidence="MEDIUM",
                reason="Repeated legitimate-looking access patterns"
            ))
        
        # T1098: Account Manipulation - high escalation probability
        if profile.get("escalation_probability", 0) > 70:
            techniques.append(self._create_match(
                "T1098",
                confidence="MEDIUM",
                reason="High escalation probability suggests account manipulation"
            ))
        
        # Track detected techniques
        for tech in techniques:
            tech_id = tech["technique_id"]
            if tech_id not in self.detected_techniques:
                self.detected_techniques[tech_id] = 0
            self.detected_techniques[tech_id] += 1
        
        # Remove duplicates by technique ID
        unique_techniques = {}
        for tech in techniques:
            tech_id = tech["technique_id"]
            if tech_id not in unique_techniques:
                unique_techniques[tech_id] = tech
        
        return list(unique_techniques.values())
    
    def _create_match(self, technique_id: str, confidence: str = "MEDIUM", reason: str = "") -> Dict:
        """Create a MITRE match object"""
        tech = self.MITRE_TECHNIQUES.get(technique_id, {})
        return {
            "technique_id": technique_id,
            "technique_name": tech.get("name", "Unknown"),
            "tactic": tech.get("tactic", "Unknown"),
            "confidence": confidence,
            "description": reason or tech.get("description", "")
        }
    
    def get_technique_summary(self) -> Dict[str, int]:
        """Get count of how many times each technique was triggered"""
        return self.detected_techniques.copy()
    
    def attempt_apt_attribution(self, techniques: List[Dict]) -> str:
        """
        Attempt APT group attribution based on technique clusters
        Returns APT group name or empty string if no match
        """
        technique_ids = [t["technique_id"] for t in techniques]
        
        # Check against known APT patterns
        for apt_key, apt_pattern in self.APT_PATTERNS.items():
            pattern_techniques = set(apt_pattern["techniques"])
            detected_techniques = set(technique_ids)
            
            # If at least 3 techniques match the pattern, flag it
            if len(pattern_techniques.intersection(detected_techniques)) >= 3:
                return apt_pattern["name"]
        
        return ""
