import os
import requests
from ipwhois import IPWhois
from concurrent.futures import ThreadPoolExecutor

# Preload Tor exit nodes exactly once at module startup
TOR_EXIT_NODES = set()
tor_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tor_exit_nodes.txt')

try:
    if os.path.exists(tor_file_path):
        with open(tor_file_path, 'r') as f:
            for line in f:
                if line.startswith('ExitAddress'):
                    parts = line.strip().split(' ')
                    if len(parts) >= 2:
                        TOR_EXIT_NODES.add(parts[1])
except Exception as e:
    print(f"Warning: Failed to load Tor exit nodes: {e}")

DATACENTER_ASNS = {"AS14061", "AS16276", "AS24940", "AS63023", "AS8100"}

def _get_geo(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("country", "UNKNOWN"), data.get("city", "UNKNOWN")
    except:
        pass
    return "UNKNOWN", "UNKNOWN"

def _get_asn(ip):
    try:
        obj = IPWhois(ip)
        result = obj.lookup_rdap(depth=1)
        return result.get("asn", "UNKNOWN"), result.get("asn_description", "UNKNOWN")
    except:
        return "UNKNOWN", "UNKNOWN"

def enrich_ip(ip):
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127.") or ip.startswith("172."):
        return {
            "is_tor": False, "asn": "PRIVATE", "org": "LOCAL_NETWORK", 
            "country": "LOCAL", "city": "LOCAL", "is_datacenter": False, 
            "risk_label": "PRIVATE_NETWORK"
        }

    is_tor = ip in TOR_EXIT_NODES
    
    # Run API calls in parallel to preserve <3s latency constraint
    with ThreadPoolExecutor(max_workers=2) as executor:
        geo_future = executor.submit(_get_geo, ip)
        asn_future = executor.submit(_get_asn, ip)
        
        country, city = geo_future.result()
        asn, org = asn_future.result()

    is_datacenter = f"AS{asn}" in DATACENTER_ASNS if asn != "UNKNOWN" else False

    if is_tor:
        risk_label = "TOR_EXIT_NODE"
    elif is_datacenter:
        risk_label = "DATACENTER_SCANNER"
    else:
        risk_label = "RESIDENTIAL_IP"

    return {
        "is_tor": is_tor,
        "asn": f"AS{asn}" if asn != "UNKNOWN" else "UNKNOWN",
        "org": org,
        "country": country,
        "city": city,
        "is_datacenter": is_datacenter,
        "risk_label": risk_label
    }
