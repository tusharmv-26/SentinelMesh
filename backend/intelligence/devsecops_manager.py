"""
DevSecOps Bridge Components
Integrates security into CI/CD pipelines and tracks honeypot coverage for deployed services.
"""

import time
from typing import Dict, List


class DevSecOpsManager:
    """
    Tracks deployed services and their security coverage status.
    Integrates with CI/CD systems via webhook.
    """
    
    def __init__(self):
        self.deployments = {}  # {service_name: deployment_record}
        self.coverage_map = {}  # {service_name: covered_honeypots}
        self.alerts = []
    
    def record_deployment(self, deployment_data: Dict) -> Dict:
        """
        Record a deployment event from CI/CD system.
        
        Args:
            deployment_data: {
                "service_name": str,
                "version": str,
                "deployed_by": str (github-actions, jenkins, etc),
                "environment": str (production, staging),
                "repository": str,
                "timestamp": float,
                "assets": [list of asset names]
            }
        
        Returns: Coverage analysis
        """
        
        service_name = deployment_data.get("service_name", "unknown")
        version = deployment_data.get("version", "unknown")
        environment = deployment_data.get("environment", "unknown")
        assets = deployment_data.get("assets", [])
        timestamp = deployment_data.get("timestamp", time.time())
        
        # Store deployment record
        self.deployments[service_name] = {
            "service_name": service_name,
            "version": version,
            "environment": environment,
            "deployed_by": deployment_data.get("deployed_by", "unknown"),
            "timestamp": timestamp,
            "assets": assets
        }
        
        # Analyze honeypot coverage
        coverage_status = self._analyze_coverage(service_name, assets)
        
        self.coverage_map[service_name] = coverage_status
        
        # Generate alerts for unmonitored assets
        if coverage_status["coverage"] == "UNMONITORED":
            alert = {
                "timestamp": timestamp,
                "service": service_name,
                "severity": "MEDIUM",
                "message": f"Service '{service_name}' deployed without honeypot coverage",
                "suggested_honeypot": coverage_status.get("suggested_honeypot")
            }
            self.alerts.append(alert)
        
        return coverage_status
    
    def _analyze_coverage(self, service_name: str, assets: List[str]) -> Dict:
        """
        Analyze whether deployed assets are covered by honeypots.
        
        Returns: {
            "service": str,
            "coverage": "MONITORED" / "PARTIAL" / "UNMONITORED",
            "covered_assets": [list],
            "uncovered_assets": [list],
            "suggested_honeypot": str
        }
        """
        
        # Honeypot coverage mapping
        known_honeypots = {
            "s3-customer-backups": ["s3://", "backup"],
            "rds-credentials": ["rds", "database", "connection"],
            "api-keys-endpoint": ["api", "endpoint", "keys"],
            "env-config-file": [".env", "config"],
            "ec2-metadata": ["metadata", "instance"]
        }
        
        covered_assets = []
        uncovered_assets = []
        
        for asset in assets:
            asset_lower = asset.lower()
            is_covered = False
            
            for honeypot_name, keywords in known_honeypots.items():
                if any(kw in asset_lower for kw in keywords):
                    covered_assets.append(asset)
                    is_covered = True
                    break
            
            if not is_covered:
                uncovered_assets.append(asset)
        
        # Determine coverage status
        if not uncovered_assets:
            coverage = "MONITORED"
        elif not covered_assets:
            coverage = "UNMONITORED"
        else:
            coverage = "PARTIAL"
        
        # Suggest honeypot for uncovered assets
        suggested_honeypot = ""
        if uncovered_assets:
            first_asset = uncovered_assets[0].lower()
            if "database" in first_asset or "rds" in first_asset:
                suggested_honeypot = "rds-credentials"
            elif "api" in first_asset or "endpoint" in first_asset:
                suggested_honeypot = "api-keys-endpoint"
            elif "config" in first_asset or "env" in first_asset:
                suggested_honeypot = "env-config-file"
            else:
                suggested_honeypot = "s3-customer-backups"
        
        return {
            "service": service_name,
            "coverage": coverage,
            "covered_assets": covered_assets,
            "uncovered_assets": uncovered_assets,
            "suggested_honeypot": suggested_honeypot
        }
    
    def get_coverage_report(self) -> List[Dict]:
        """
        Get coverage report for all known services.
        
        Returns: List of coverage entries for dashboard
        """
        report = []
        
        for service_name, deployment in self.deployments.items():
            coverage_info = self.coverage_map.get(service_name, {})
            
            report.append({
                "service_name": service_name,
                "version": deployment.get("version"),
                "environment": deployment.get("environment"),
                "deployed_by": deployment.get("deployed_by"),
                "last_deployed": deployment.get("timestamp"),
                "coverage_status": coverage_info.get("coverage", "UNKNOWN"),
                "covered_assets_count": len(coverage_info.get("covered_assets", [])),
                "uncovered_assets_count": len(coverage_info.get("uncovered_assets", [])),
                "suggested_honeypot": coverage_info.get("suggested_honeypot"),
                "assets": deployment.get("assets", [])
            })
        
        return sorted(report, key=lambda x: x["last_deployed"], reverse=True)
    
    def get_coverage_summary(self) -> Dict:
        """
        Get summary statistics for coverage.
        """
        report = self.get_coverage_report()
        
        total_services = len(report)
        monitored = len([r for r in report if r["coverage_status"] == "MONITORED"])
        partial = len([r for r in report if r["coverage_status"] == "PARTIAL"])
        unmonitored = len([r for r in report if r["coverage_status"] == "UNMONITORED"])
        
        return {
            "total_services": total_services,
            "monitored": monitored,
            "partial": partial,
            "unmonitored": unmonitored,
            "coverage_percentage": (monitored / total_services * 100) if total_services > 0 else 0
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent coverage alerts"""
        return self.alerts[-limit:]
    
    def create_honeypot_for_service(self, service_name: str, asset_name: str) -> Dict:
        """
        Simulate creating a new honeypot for an uncovered asset.
        In production, this would actually deploy to AWS.
        
        Returns: New honeypot metadata
        """
        
        honeypot_id = f"honeypot-{service_name}-{int(time.time())}"
        
        new_honeypot = {
            "id": honeypot_id,
            "name": f"{service_name} honeypot",
            "type": "S3_BUCKET",
            "resource_name": asset_name,
            "created_at": time.time(),
            "created_for_service": service_name,
            "total_hits": 0
        }
        
        # Log alert that coverage gap was closed
        alert = {
            "timestamp": time.time(),
            "service": service_name,
            "severity": "LOW",
            "message": f"Honeypot deployed for service '{service_name}' - coverage gap closed",
            "honeypot_created": honeypot_id
        }
        self.alerts.append(alert)
        
        return new_honeypot
