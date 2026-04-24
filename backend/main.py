from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import datetime
import random
import urllib.request
import json

from intelligence import (
    RiskEngine, SimilarityEngine, AttackerProfiler, enrich_ip, MutationEngine,
    MITREMapper, APTDetector, DevSecOpsManager, HoneypotManager,
    EmployeeActivityTracker, InsiderExternalCorrelationEngine
)
from aws_client import AWSController
from grok_client import GrokClient

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize engines
risk_engine = RiskEngine()
similarity_engine = SimilarityEngine()
attacker_profiler = AttackerProfiler()
mutation_engine = MutationEngine()
mitre_mapper = MITREMapper()
apt_detector = APTDetector()
devsecops_manager = DevSecOpsManager()
honeypot_manager = HoneypotManager()
employee_tracker = EmployeeActivityTracker()
correlation_engine = InsiderExternalCorrelationEngine()

aws_client = AWSController()
grok_client = GrokClient()

# In-memory stores
events = [] # Event feed
audit_log = [] # Audit logs
system_status = {"status": "Monitoring", "peak_score": 0, "total_events": 0, "total_healing": 0}

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})

@app.route("/events", methods=["POST", "GET"])
def handle_events():
    if request.method == "GET":
        return jsonify(events[:50])
        
    payload = request.get_json() or {}
    req_ip = payload.get("attacker_ip", "0.0.0.0")
    req_res_name = payload.get("resource_name", "unknown")
    req_method = payload.get("method", "GET")
    ts = payload.get("timestamp") or time.time()
    
    # 1. Calculate risk score
    score = risk_engine.calculate_score(req_ip, req_res_name)
    
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

    # Profile attacker
    enrichment = enrich_ip(req_ip)
    profile = attacker_profiler.update(req_ip, req_res_name, ts, enrichment)

    # Add to main event feed
    event_record = {
        "id": len(events) + 1,
        "timestamp": datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S'),
        "attacker_ip": req_ip,
        "resource_name": req_res_name,
        "method": req_method,
        "risk_score": score,
        "status_badge": status_badge,
        "attack_type": profile.get("behavior_type", "UNKNOWN"),
        "intent": profile.get("intent", "UNKNOWN"),
        "escalation_probability": profile.get("escalation_probability", 0),
        "threat_level": profile.get("threat_level", "LOW"),
        "ip_enrichment": enrichment
    }
    
    events.insert(0, event_record)

    # Feed to intelligence modules
    mitre_mapper.map_to_mitre(event_record, profile)
    apt_detector.analyze_profile(profile, mitre_mapper.detected_techniques)
    correlation_engine.correlate_threats(employee_tracker.get_all_activities(), events)

    # 2. If score >= 70, trigger intelligence matching and self-healing
    if score >= 70:
        at_risk = similarity_engine.find_at_risk_resource(req_res_name)
        if at_risk:
            # Check if already mitigated
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
                    
                    # Post-heal action: Adaptive Mutation
                    mutation_record = mutation_engine.mutate(profile)
                    if mutation_record:
                        events[0]["mutation"] = mutation_record

    return jsonify({"status": "success", "record": event_record})

@app.route("/audit", methods=["GET"])
def get_audit():
    return jsonify(audit_log[:50])

@app.route("/status", methods=["GET"])
def get_status():
    return jsonify(system_status)

# MITRE, APT, Honeypots, DevSecOps Endpoints
@app.route("/mitre/summary", methods=["GET"])
def get_mitre_summary():
    return jsonify(mitre_mapper.get_technique_summary())

@app.route("/apt/suspects", methods=["GET"])
def get_apt_suspects():
    return jsonify(apt_detector.get_suspects())

@app.route("/devsecops/coverage", methods=["GET"])
def get_devsecops_coverage():
    return jsonify(devsecops_manager.get_coverage())

@app.route("/devsecops/coverage-summary", methods=["GET"])
def get_devsecops_summary():
    return jsonify(devsecops_manager.get_coverage_summary())

@app.route("/honeypots", methods=["GET"])
def get_honeypots():
    return jsonify(honeypot_manager.get_active_honeypots())

@app.route("/profiles", methods=["GET"])
def get_profiles():
    # Helper to return all profiler summaries
    profs = []
    for ip, profile in attacker_profiler.profiles.items():
        summary = profile.copy()
        summary["ip"] = ip
        profs.append(summary)
    return jsonify(profs)

# Insider + External Correlation Endpoints
@app.route("/employee-access", methods=["POST"])
def post_employee_access():
    payload = request.get_json() or {}
    employee_id = payload.get("employee_id")
    resource = payload.get("resource")
    access_type = payload.get("type", "read")
    timestamp = payload.get("timestamp", time.time())
    
    if not employee_id or not resource:
        return jsonify({"status": "error", "message": "Missing employee_id or resource"}), 400
        
    record = employee_tracker.log_employee_access(employee_id, resource, access_type, timestamp)
    correlations = correlation_engine.correlate_threats(employee_tracker.get_all_activities(), events)
    
    high_risk_count = len([c for c in correlations if c.get("correlation_score", 0) >= 60])
    
    return jsonify({"status": "success", "record": record, "high_risk_correlations": high_risk_count})

@app.route("/correlations", methods=["GET"])
def get_correlations():
    min_score = int(request.args.get("min_score", 0))
    if min_score > 0:
        return jsonify(correlation_engine.get_high_risk_correlations(min_score))
    return jsonify(correlation_engine.correlations)

@app.route("/employees", methods=["GET"])
def get_employees():
    return jsonify(employee_tracker.get_all_employees())

@app.route("/employee/<employee_id>", methods=["GET"])
def get_employee(employee_id):
    return jsonify(employee_tracker.get_employee_profile(employee_id))

@app.route("/rollback", methods=["POST"])
def post_rollback():
    payload = request.get_json() or {}
    resource_id = payload.get("resource_id", "")
    success = aws_client.rollback_security_group(resource_id)
    if success:
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
        
        if system_status["status"] == "Healing active":
            system_status["status"] = "Monitoring"
            
        return jsonify({"status": "success"})
    return jsonify({"status": "failed", "reason": "Could not rollback or resource not found in saved states."})

@app.route("/heal", methods=["POST"])
def post_heal():
    payload = request.get_json() or {}
    resource_id = payload.get("resource_id", "")
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
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"})

@app.route("/demo", methods=["POST"])
def post_demo():
    ts = time.time()
    ip = f"185.220.101.{random.randint(10,200)}"
    
    e1 = {
        "attacker_ip": ip,
        "resource_name": "company-prod-db-backup-2024",
        "method": "GET",
        "timestamp": ts
    }
    urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000/events", json.dumps(e1).encode('utf-8'), {'Content-Type': 'application/json'}))
    
    e2 = {
        "attacker_ip": ip,
        "resource_name": "company-prod-db-backup-2024/credentials",
        "method": "GET",
        "timestamp": ts + 2
    }
    urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8000/events", json.dumps(e2).encode('utf-8'), {'Content-Type': 'application/json'}))
    return jsonify({"status": "demo sequence triggered"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
