import os
import requests

class GrokClient:
    def __init__(self):
        self.api_key = os.environ.get("GROK_API_KEY", "")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def generate_audit_explanation(self, ip: str, resource_name: str, risk_score: int, at_risk_resource: str, action: str, profiler_context: str = "") -> str:
        fallback = f"Suspicious access from {ip} attempted credential harvesting on decoy asset {resource_name} — risk score {risk_score}/100 — {at_risk_resource} flagged as similar target and access {action} automatically."
        
        if not self.api_key:
            return fallback
            
        prompt = f"""
        You are a cloud security audit logger. Given an event object, write exactly one sentence in plain English describing what happened, what risk was detected, and what action the system took. Be specific about IP addresses, resource names, and risk scores. Never use technical jargon. Write as if explaining to a business executive.
        
        Event Details:
        - Attacker IP: {ip}
        - Decoy Asset: {resource_name}
        - Risk Score: {risk_score}/100
        - Real Asset at Risk: {at_risk_resource}
        - Action Taken: {action} (e.g., restricted automatically, rolled back)
        - Threat Intelligence Context: {profiler_context}
        """

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a cloud security audit logger."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 60,
                "temperature": 0.3
            }
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            return fallback
        except Exception as e:
            print(f"Grok API error: {e}")
            return fallback
