from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import datetime

from intelligence import RiskEngine, SimilarityEngine
from intelligence.attacker_profiler import AttackerProfiler
from intelligence.ip_enricher import enrich_ip
from intelligence.mutation_engine import MutationEngine
from intelligence.employee_tracker import EmployeeActivityTracker
from intelligence.correlation_engine import InsiderExternalCorrelationEngine
from intelligence.honeypot_manager import HoneypotManager
from intelligence.mitre_mapper import MITREMapper
from intelligence.apt_detector import APTDetector
from intelligence.dynamic_content import DynamicContentGenerator
from intelligence.devsecops_manager import DevSecOpsManager
from ml.ml_risk_engine import MLRiskEngine
from ml.mitre_ml_engine import MITREMLEngine
from aws_client import AWSController
from grok_client import GrokClient
from reports.report_generator import generate_incident_report
import os
import json

app = FastAPI(title="Cloud Sentinel API")

# Setup CORS as requested
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
risk_engine = RiskEngine()
similarity_engine = SimilarityEngine()
aws_client = AWSController()
grok_client = GrokClient()
attacker_profiler = AttackerProfiler()
mutation_engine = MutationEngine()
employee_tracker = EmployeeActivityTracker()
correlation_engine = InsiderExternalCorrelationEngine()
honeypot_manager = HoneypotManager()
mitre_mapper = MITREMapper()
apt_detector = APTDetector()
dynamic_content = DynamicContentGenerator()
devsecops_manager = DevSecOpsManager()
ml_risk_engine = MLRiskEngine()
mitre_ml_engine = MITREMLEngine()

# In-memory stores
events = [] # Event feed
audit_log = [] # Audit logs
system_status = {"status": "Monitoring", "peak_score": 0, "total_events": 0, "total_healing": 0}

# Feature 3: Canary Tokens
CANARY_TOKENS = {
    "ab937-2910-cdea-f19b": {
        "source_file": "payment_gateway_config.json",
        "description": "Embedded inside production mock payments file."
    }
}

# Removed Pydantic base models completely for raw async Request decoding to bypass Python 3.14 type hint parsing crashes


@app.get("/health")
def health_check():
    return JSONResponse(
        content={"status": "healthy"},
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/events")
async def post_event(request: Request):
    payload = await request.json()
    req_ip = payload.get("attacker_ip")
    req_res_name = payload.get("resource_name")
    req_method = payload.get("method")
    ts = payload.get("timestamp") or time.time()
    
    # 1. Enrich IP with Global Intel
    enrichment = enrich_ip(req_ip)
    
    # 2. Calculate risk score using ML model (replaces heuristic RiskEngine)
    profile = attacker_profiler.update(req_ip, req_res_name, ts, enrichment)
    score = ml_risk_engine.predict({"timestamp": ts, "resource_name": req_res_name}, profile, enrichment)
    
    # 3. Record honeypot hit (tracks which honeypots are being targeted)
    honeypot_manager.record_hit(req_res_name, req_ip)
    
    # 4. Map to MITRE ATT&CK techniques (both rule-based and ML)
    mitre_techniques_rules = mitre_mapper.map_to_mitre(
        {"timestamp": ts, "resource_name": req_res_name, "ip_enrichment": enrichment},
        profile
    )
    mitre_techniques_ml = mitre_ml_engine.predict_techniques(
        {"timestamp": ts, "resource_name": req_res_name, "ip_enrichment": enrichment},
        profile,
        enrichment
    )
    # Combine techniques and deduplicate
    all_techniques = {}
    for tech in mitre_techniques_rules + mitre_techniques_ml:
        tech_id = tech["technique_id"]
        if tech_id not in all_techniques:
            all_techniques[tech_id] = tech
    mitre_techniques = list(all_techniques.values())
    
    # 5. Detect APT patterns
    apt_analysis = apt_detector.update(req_ip, {"timestamp": ts, "resource_name": req_res_name}, profile)
    
    # Update system tracking
    system_status["total_events"] += 1
    if score > system_status["peak_score"]:
        system_status["peak_score"] = score
        
    status_badge = "Healthy"
    if score >= 70:
        system_status["status"] = "Healing active"
        status_badge = "Critical"
    elif score >= 40:
        system_status["status"] = "Alert"
        status_badge = "Elevated"
    else:
        system_status["status"] = "Monitoring"
        status_badge = "Low"

    # Add to main event feed with all new intelligence
    event_record = {
        "id": len(events) + 1,
        "timestamp": datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'),
        "attacker_ip": req_ip,
        "resource_name": req_res_name,
        "method": req_method,
        "risk_score": score,
        "status_badge": status_badge,
        "attack_type": profile["behavior_type"],
        "intent": profile["intent"],
        "escalation_probability": profile["escalation_probability"],
        "threat_level": profile["threat_level"],
        "ip_enrichment": enrichment,
        "mitre_techniques": mitre_techniques,
        "apt_analysis": apt_analysis
    }
    events.insert(0, event_record)  # Reverse-chronological

    # 6. If score >= 70, trigger intelligence matching and self-healing
    if score >= 70:
        at_risk = similarity_engine.find_at_risk_resource(req_res_name)
        if at_risk:
            # Check if we already mitigated it recently
            already_healed = any(
                log for log in audit_log 
                if log['resource_id'] == at_risk['id'] and log['action'] == 'Restricted'
            )
            
            if not already_healed:
                print(f"[HEAL TRIGGER] Protecting {at_risk['name']} ({at_risk['id']})")
                success = aws_client.restrict_security_group(at_risk['id'])
                
                if success:
                    system_status["total_healing"] += 1
                    explanation = grok_client.generate_audit_explanation(
                        req_ip,
                        req_res_name,
                        score,
                        at_risk['name'],
                        "restricted",
                        profiler_context=attacker_profiler.get_plain_english_summary(req_ip)
                    )
                    
                    audit_record = {
                        "id": len(audit_log) + 1,
                        "timestamp": datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'),
                        "resource_id": at_risk['id'],
                        "resource_name": at_risk['name'],
                        "action": "Restricted",
                        "explanation": explanation
                    }
                    audit_log.insert(0, audit_record)
                    
                    # 7. Post-Heal Action: Adaptive Mutation
                    mutation_record = mutation_engine.mutate(profile)
                    if mutation_record:
                        events[0]["mutation"] = mutation_record
    
    # 8. If APT detected and score crosses 50, activate deception mode
    if apt_analysis["apt_score"] >= 50:
        honeypot_manager.set_mode(req_res_name, "DECEPTION_MODE")

    return {"status": "success", "record": event_record}

@app.get("/events")
def get_events():
    return JSONResponse(
        content=events[:50],
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/canary/track")
def track_canary(request: Request, token: str = None, type: str = "access"):
    if not token or token not in CANARY_TOKENS:
        return JSONResponse(
            content={},
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        ) # Stealth return, act exactly like a 404/blank healthcheck
        
    ts = time.time()
    real_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    forwarded = request.headers.get("x-forwarded-for")
    
    canary_data = CANARY_TOKENS[token]
    
    event_record = {
        "id": len(events) + 1,
        "timestamp": datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'),
        "attacker_ip": real_ip,
        "resource_name": "CANARY: " + canary_data["source_file"],
        "method": "CANARY",
        "risk_score": 100,
        "status_badge": "Critical",
        "type": "CANARY_TOKEN_HIT",
        "user_agent": user_agent,
        "forwarded_for": forwarded,
        "note": "Attacker opened exfiltrated file — tracking beyond cloud boundary."
    }
    
    events.insert(0, event_record)
    
    if system_status["peak_score"] < 100:
        system_status["peak_score"] = 100
        
    system_status["status"] = "Healing active"
    system_status["total_events"] += 1
    
    return JSONResponse(
        content={},
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    ) # Always return empty 200 OK so attacker tool doesn't crash or notice

@app.get("/mutations")
def get_mutations():
    return JSONResponse(
        content=mutation_engine.get_created_honeypots(),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/report/{ip}")
def download_report(ip: str):
    profile = attacker_profiler.get_profile(ip)
    if not profile:
        return {"error": "Profile not found for this IP"}
        
    my_events = [e for e in events if e.get("attacker_ip") == ip and e.get("type", "") != "CANARY_TOKEN_HIT"]
    canaries = [e for e in events if e.get("attacker_ip") == ip and e.get("type", "") == "CANARY_TOKEN_HIT"]
    
    actions = []
    for a in audit_log:
        expl = a.get("explanation", "")
        if ip in expl:
            actions.append(f"{a['action']} - {expl}")
            
    # Also include mutations as actions
    for h in mutation_engine.get_created_honeypots():
        if h["trigger_ip"] == ip:
            actions.append(f"Deployed Honey Bucket s3://{h['bucket_name']} mimicking {h['category']}")
            
    groq_sum = f"Autonomous Intelligence flagged IP {ip} exhibiting {profile.get('behavior_type')} patterns indicating {profile.get('intent')}."
            
    session_data = {
        "profile": profile,
        "enrichment": {"is_tor": profile.get("is_tor"), "city": "N/A", "country": "N/A", "org": profile.get("org")}, # using simplified enrichment
        "events": my_events,
        "canary_events": canaries,
        "actions": actions,
        "peak_score": max([e["risk_score"] for e in my_events]) if my_events else 0,
        "groq_summary": groq_sum
    }
    
    # Since we saved full enrichment in events occasionally, try extracting full geo
    for e in my_events:
        if "ip_enrichment" in e:
            session_data["enrichment"] = e["ip_enrichment"]
            break
            
    output_path = os.path.join(os.path.dirname(__file__), "reports", f"Report_{ip.replace('.','_')}.pdf")
    generate_incident_report(session_data, output_path)
    
    return FileResponse(path=output_path, filename=f"SentinelMesh_Report_{ip}.pdf", media_type='application/pdf')

@app.get("/audit")
def get_audit():
    return JSONResponse(
        content=audit_log[:50],
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/status")
def get_status():
    return JSONResponse(
        content=system_status,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/rollback")
async def post_rollback(request: Request):
    payload = await request.json()
    resource_id = payload.get("resource_id")
    success = aws_client.rollback_security_group(resource_id)
    if success:
        # Add to audit log
        ts = time.time()
        explanation = f"Manual rollback executed. Access to {resource_id} has been restored."
        
        audit_record = {
            "id": len(audit_log) + 1,
            "timestamp": datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'),
            "resource_id": resource_id,
            "resource_name": resource_id,
            "action": "Rolled Back",
            "explanation": explanation
        }
        audit_log.insert(0, audit_record)
        
        # Reset system status if this was the last locked resource (simplification)
        if system_status["status"] == "Healing active":
            system_status["status"] = "Monitoring"
            
        return {"status": "success"}
    return {"status": "failed", "reason": "Could not rollback or resource not found in saved states."}

@app.post("/heal")
async def post_heal(request: Request):
    payload = await request.json()
    resource_id = payload.get("resource_id")
    # Manual heal endpoint as requested
    success = aws_client.restrict_security_group(resource_id)
    if success:
        system_status["total_healing"] += 1
        ts = time.time()
        audit_record = {
            "id": len(audit_log) + 1,
            "timestamp": datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'),
            "resource_id": resource_id,
            "resource_name": resource_id,
            "action": "Restricted",
            "explanation": f"Manual restriction executed. Access to {resource_id} restricted."
        }
        audit_log.insert(0, audit_record)
        return {"status": "success"}
    return {"status": "failed"}

# Simple demo endpoint to populate fake data for testing without attacker script
@app.post("/demo")
def post_demo():
    import random
    ts = time.time()
    ip = f"185.220.101.{random.randint(10,200)}"
        
    import urllib.request
    import json
    
    e1 = {
        "attacker_ip": ip,
        "resource_name": "company-prod-db-backup-2024",
        "method": "GET",
        "timestamp": ts
    }
    urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000/events", json.dumps(e1).encode('utf-8'), {'Content-Type': 'application/json'}))
    
    # 2 seconds later
    e2 = {
        "attacker_ip": ip,
        "resource_name": "company-prod-db-backup-2024/credentials",
        "method": "GET",
        "timestamp": ts + 2
    }
    urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000/events", json.dumps(e2).encode('utf-8'), {'Content-Type': 'application/json'}))
    return {"status": "demo sequence triggered"}

@app.get("/profiles")
def get_profiles():
    return JSONResponse(
        content=attacker_profiler.get_all_profiles(),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/profiles/{ip}")
def get_profile(ip: str):
    return JSONResponse(
        content=attacker_profiler.get_profile(ip),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/employee-access")
async def log_employee_access(request: Request):
    """Log employee accessing a resource (for insider threat tracking)"""
    payload = await request.json()
    
    employee_id = payload.get("employee_id")
    resource = payload.get("resource")
    access_type = payload.get("type")
    timestamp = payload.get("timestamp") or time.time()
    
    # Log the access
    access_record = employee_tracker.log_employee_access(
        employee_id, resource, access_type, timestamp
    )
    
    # Check for correlations with external attacks
    correlations = correlation_engine.correlate_threats(
        [access_record],
        events
    )
    
    high_risk_count = len([c for c in correlations if c["correlation_score"] >= 70])
    
    if high_risk_count > 0:
        system_status["status"] = "Insider Threat Detected"
        system_status["total_healing"] += 1
    
    return {
        "status": "logged",
        "record": access_record,
        "correlations_detected": high_risk_count
    }

@app.get("/correlations")
def get_correlations(min_score: int = 70):
    """Get insider + external threat correlations"""
    high_risk = correlation_engine.get_high_risk_correlations(min_score)
    return JSONResponse(
        content=high_risk,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/employee/{employee_id}")
def get_employee_profile(employee_id: str):
    """Get risk profile for specific employee"""
    profile = employee_tracker.get_employee_profile(employee_id)
    return JSONResponse(
        content=profile,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/employees")
def get_all_employees():
    """Get all tracked employees and their risk levels"""
    employees = []
    for emp_id in employee_tracker.employee_logs.keys():
        profile = employee_tracker.get_employee_profile(emp_id)
        employees.append(profile)
    
    return JSONResponse(
        content=sorted(employees, key=lambda x: x["avg_risk_score"], reverse=True),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# ============================================================================
# NEW FEATURE ENDPOINTS: Honeypots, MITRE, APT, ML, DevSecOps
# ============================================================================

# Feature 1: Multiple Honeypots
@app.get("/honeypots")
def get_honeypots():
    """Get all honeypots and their status"""
    return JSONResponse(
        content=honeypot_manager.get_all_honeypots(),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/honeypots/mode")
async def set_honeypot_mode(request: Request):
    """Change honeypot mode: PASSIVE, ACTIVE, DECEPTION_MODE"""
    payload = await request.json()
    honeypot_name = payload.get("honeypot_name")
    mode = payload.get("mode", "PASSIVE")
    
    honeypot_manager.set_mode(honeypot_name, mode)
    
    return {
        "status": "success",
        "honeypot": honeypot_name,
        "mode": mode
    }

# Feature 2: MITRE ATT&CK Mapping
@app.get("/mitre/summary")
def get_mitre_summary():
    """Get summary of detected MITRE techniques"""
    techniques = {}
    
    for event in events:
        for tech in event.get("mitre_techniques", []):
            tech_id = tech["technique_id"]
            if tech_id not in techniques:
                techniques[tech_id] = {
                    "technique_id": tech_id,
                    "name": tech.get("name", "Unknown"),
                    "tactic": tech.get("tactic", "Unknown"),
                    "count": 0,
                    "highest_confidence": 0.0
                }
            techniques[tech_id]["count"] += 1
            techniques[tech_id]["highest_confidence"] = max(
                techniques[tech_id]["highest_confidence"],
                tech.get("confidence", 0.0)
            )
    
    sorted_techniques = sorted(
        techniques.values(),
        key=lambda x: (x["count"], x["highest_confidence"]),
        reverse=True
    )
    
    return JSONResponse(
        content=sorted_techniques,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Feature 3: APT Detection Engine
@app.get("/apt/suspects")
def get_apt_suspects():
    """Get list of IPs classified as APT with analysis"""
    apt_ips = {}
    
    for event in events:
        ip = event.get("attacker_ip")
        apt_data = event.get("apt_analysis", {})
        
        if apt_data.get("classification") in ["SUSPECTED_APT", "CONFIRMED_APT_PATTERN"]:
            if ip not in apt_ips:
                apt_ips[ip] = {
                    "ip": ip,
                    "classification": apt_data.get("classification"),
                    "apt_score": apt_data.get("apt_score", 0),
                    "indicators": apt_data.get("indicators", []),
                    "first_seen": event.get("timestamp"),
                    "event_count": 0
                }
            apt_ips[ip]["event_count"] += 1
    
    sorted_apts = sorted(
        apt_ips.values(),
        key=lambda x: x["apt_score"],
        reverse=True
    )
    
    return JSONResponse(
        content=sorted_apts,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Feature 4: ML Risk Model (Feature Importance)
@app.get("/ml/feature-importance")
def get_ml_feature_importance():
    """Get ML model feature importance for risk scoring and MITRE classification"""
    return JSONResponse(
        content={
            "risk_model": ml_risk_engine.get_feature_importance(),
            "mitre_model": mitre_ml_engine.get_feature_importance()
        },
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Feature 5: Dynamic Honeypots (Content Generation)
@app.get("/honeypots/{honeypot_name}/content")
def get_dynamic_content(honeypot_name: str):
    """Get dynamically generated content for a honeypot based on attacker profile"""
    # Find the attacker who most recently accessed this honeypot
    recent_attacker_ip = None
    for event in events:
        if honeypot_name in event.get("resource_name", ""):
            recent_attacker_ip = event.get("attacker_ip")
            break
    
    if not recent_attacker_ip:
        return {"content": "No recent attacker found"}
    
    profile = attacker_profiler.get_profile(recent_attacker_ip)
    access_tier = honeypot_manager.get_access_tier(recent_attacker_ip, honeypot_name)
    
    # Generate appropriate response based on honeypot type
    if "ec2" in honeypot_name:
        content = dynamic_content.generate_ec2_metadata_response(profile, access_tier)
    elif "rds" in honeypot_name or "database" in honeypot_name:
        content = dynamic_content.generate_rds_connection_string(profile, access_tier)
    elif "api" in honeypot_name or "key" in honeypot_name:
        content = dynamic_content.generate_api_key_response(profile, access_tier)
    elif "env" in honeypot_name or "config" in honeypot_name:
        content = dynamic_content.generate_env_file_content(profile, access_tier)
    else:
        content = "Generic honeypot content"
    
    return JSONResponse(
        content={"content": content, "attacker_ip": recent_attacker_ip, "access_tier": access_tier},
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Feature 6: DevSecOps Bridge
@app.post("/devsecops/deployment-event")
async def record_deployment(request: Request):
    """Record a deployment event from CI/CD system"""
    payload = await request.json()
    
    coverage = devsecops_manager.record_deployment(payload)
    
    return {
        "status": "success",
        "coverage_analysis": coverage
    }

@app.get("/devsecops/coverage")
def get_devsecops_coverage():
    """Get deployment coverage report"""
    return JSONResponse(
        content=devsecops_manager.get_coverage_report(),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/devsecops/coverage-summary")
def get_coverage_summary():
    """Get deployment coverage summary"""
    return JSONResponse(
        content=devsecops_manager.get_coverage_summary(),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/devsecops/alerts")
def get_devsecops_alerts():
    """Get recent DevSecOps alerts"""
    return JSONResponse(
        content=devsecops_manager.get_recent_alerts(),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/devsecops/honeypot-create")
async def create_honeypot_for_service(request: Request):
    """Create a honeypot for an uncovered service asset"""
    payload = await request.json()
    service_name = payload.get("service_name")
    asset_name = payload.get("asset_name")
    
    new_honeypot = devsecops_manager.create_honeypot_for_service(service_name, asset_name)
    
    return {
        "status": "success",
        "honeypot": new_honeypot
    }
