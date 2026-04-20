import time

class AttackerProfiler:
    def __init__(self):
        self.profiles = {}

    def update(self, ip, resource, timestamp=None, enrichment=None):
        if timestamp is None:
            timestamp = time.time()
            
        if ip not in self.profiles:
            self.profiles[ip] = {
                "ip": ip,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "access_count": 0,
                "resources_probed": [],
                "intervals": [],
                "behavior_type": "INITIAL_PROBE",
                "intent": "UNKNOWN",
                "escalation_probability": 0,
                "threat_level": "LOW",
                "session_duration": 0,
                "is_tor": False,
                "is_datacenter": False,
                "org": "UNKNOWN"
            }
            
        profile = self.profiles[ip]
        if enrichment:
            profile["is_tor"] = enrichment.get("is_tor", False)
            profile["is_datacenter"] = enrichment.get("is_datacenter", False)
            profile["org"] = enrichment.get("org", "UNKNOWN")
        
        # Timing calculations
        if profile["access_count"] > 0:
            interval = timestamp - profile["last_seen"]
            profile["intervals"].append(interval)
            
        profile["last_seen"] = timestamp
        profile["access_count"] += 1
        profile["resources_probed"].append(resource)
        profile["session_duration"] = int(profile["last_seen"] - profile["first_seen"])
        
        # Run classification modules
        profile["behavior_type"] = self._classify_behavior(profile)
        profile["intent"] = self._classify_intent(profile)
        profile["escalation_probability"] = self._calculate_escalation(profile)
        profile["threat_level"] = self._assign_threat_level(profile["escalation_probability"])
        
        return profile

    def _classify_behavior(self, profile):
        intervals = profile["intervals"]
        access_count = profile["access_count"]
        
        if len(intervals) == 0:
            return "INITIAL_PROBE"
            
        avg_int = sum(intervals) / len(intervals)
        variance = max(intervals) - min(intervals)
        
        if avg_int < 2 and variance < 0.5:
            return "AUTOMATED_SCANNER"
        if avg_int > 10 and variance > 5:
            return "MANUAL_ATTACKER"
        if access_count > 5 and avg_int < 3:
            return "AGGRESSIVE_ENUMERATION"
        if access_count <= 3 and avg_int > 5:
            return "RECONNAISSANCE"
            
        return "UNKNOWN_PATTERN"

    def _classify_intent(self, profile):
        combined_resources = " ".join(profile["resources_probed"]).lower()
        
        # Categorized Keywords
        cred_kws = ['key', 'secret', 'password', 'token', 'credential', 'auth', 'api', 'iam', 'cert', 'private', 'pem']
        exfil_kws = ['backup', 'dump', 'export', 'archive', 'snapshot', 'restore', 'prod', 'database', 'db', 'sql']
        fin_kws = ['payment', 'billing', 'invoice', 'stripe', 'gateway', 'wallet', 'transaction', 'bank']
        
        cred_hits = sum(1 for w in cred_kws if w in combined_resources)
        exfil_hits = sum(1 for w in exfil_kws if w in combined_resources)
        fin_hits = sum(1 for w in fin_kws if w in combined_resources)
        
        # Targeted rule: Same resource > 2 times in a row sequentially
        if len(profile["resources_probed"]) > 2:
            unique_recent = set(profile["resources_probed"][-3:])
            if len(unique_recent) == 1:
                return "TARGETED_ATTACK"
                
        if cred_hits == 0 and exfil_hits == 0 and fin_hits == 0:
            return "BROAD_RECONNAISSANCE"
            
        max_hits = max(cred_hits, exfil_hits, fin_hits)
        
        if fin_hits == max_hits and fin_hits > 0:
            return "FINANCIAL_TARGETING"
        if cred_hits == max_hits and cred_hits > 0:
            return "CREDENTIAL_HARVESTING"
        if exfil_hits == max_hits and exfil_hits > 0:
            return "DATA_EXFILTRATION"
            
        return "BROAD_RECONNAISSANCE"

    def _calculate_escalation(self, profile):
        score = 0
        
        # Access Count
        score += min(profile["access_count"] * 7, 35)
        
        # Dangerous keyword hits
        dangerous = ['key', 'secret', 'password', 'payment', 'prod', 'gateway', 'token', 'credential']
        combined = " ".join(profile["resources_probed"]).lower()
        danger_hits = sum(1 for w in dangerous if w in combined)
        score += min(danger_hits * 10, 30)
        
        # Behavior bonuses
        b_type = profile["behavior_type"]
        if b_type == "AGGRESSIVE_ENUMERATION": score += 20
        elif b_type == "MANUAL_ATTACKER": score += 15
        elif b_type == "AUTOMATED_SCANNER": score += 10
        
        # Intent bonuses
        i_type = profile["intent"]
        if i_type == "TARGETED_ATTACK": score += 20
        elif i_type == "FINANCIAL_TARGETING": score += 15
        
        return min(score, 100)

    def _assign_threat_level(self, score):
        if score >= 75: return "CRITICAL"
        if score >= 50: return "HIGH"
        if score >= 25: return "MEDIUM"
        return "LOW"
        
    def get_profile(self, ip):
        return self.profiles.get(ip)
        
    def get_all_profiles(self):
        return sorted(list(self.profiles.values()), key=lambda x: x["escalation_probability"], reverse=True)
        
    def get_plain_english_summary(self, ip):
        p = self.profiles.get(ip)
        if not p: return "No profile exists."
        return f"Attacker at {ip} probed {p['access_count']} resources over {p['session_duration']} seconds exhibiting {p['behavior_type']} behavior indicating {p['intent']} intent, reaching {p['escalation_probability']}% escalation probability ({p['threat_level']} threat level)."
