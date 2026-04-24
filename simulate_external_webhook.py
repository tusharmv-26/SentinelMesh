import urllib.request
import json
import time
import random

WEBHOOK_URL = "http://127.0.0.1:8000/webhooks/external-honeypot"

def send_webhook(honeypot_id, technique, name):
    print(f"\n--- Simulating {name} ---")
    payload = {
        "src_ip": f"192.168.100.{random.randint(10,250)}",
        "honeypot_id": honeypot_id,
        "technique": technique
    }
    
    req = urllib.request.Request(
        WEBHOOK_URL, 
        json.dumps(payload).encode('utf-8'), 
        {'Content-Type': 'application/json'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        print(f"Success: {result['message']}")
        print(f"Attacker IP {payload['src_ip']} logged into ML Risk Engine.")
    except Exception as e:
        print(f"Failed to send webhook: {e}")

if __name__ == "__main__":
    print("SentinelMesh Third-Party Integration Demo\n")
    
    # 1. Simulate Cowrie SSH Brute Force
    send_webhook("cowrie-ssh-01", "T1110", "Cowrie SSH Attack")
    time.sleep(2)
    
    # 2. Simulate Thinkst Canary Token Trigger
    send_webhook("canary-aws-token", "T1552", "Thinkst Canary AWS Token Exfiltration")
    time.sleep(2)
    
    # 3. Simulate Dionaea SMB Malware Capture
    send_webhook("dionaea-smb-trap", "T1562", "Dionaea SMB Trap")
    
    print("\nDone. Check your SentinelMesh Dashboard (Honeypots & Live Events)!")
