"""
Dynamic Honeypot Content Generation
Adapts honeypot responses based on attacker type, behavior, and access tier.
"""

from typing import Dict
import json


class DynamicContentGenerator:
    """
    Generates honeypot responses that adapt to attacker characteristics.
    Different content for scanners vs humans vs APTs.
    Progressive revelation: more valuable data on repeated access.
    """
    
    def generate_ec2_metadata_response(self, attacker_type: str, access_tier: int) -> Dict:
        """
        Generate EC2 metadata endpoint response.
        Attacker type affects specificity and believability.
        Access tier affects how complete the credentials are.
        """
        
        if attacker_type == "AUTOMATED_SCANNER":
            # Scanners don't verify - give them everything at once
            if access_tier >= 2:
                return {
                    "iam": {
                        "security-credentials": {
                            "ec2-role": {
                                "Code": "Success",
                                "LastUpdated": "2026-04-24T10:30:00Z",
                                "Type": "AWS-HMAC",
                                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE1",
                                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2",
                                "Token": "AQoDYXdzEJr...<token>...//////////",
                                "Expiration": "2026-04-24T16:30:00Z"
                            }
                        }
                    }
                }
            else:
                return {
                    "iam": {
                        "security-credentials": {
                            "ec2-role": {
                                "Code": "Success",
                                "Type": "AWS-HMAC",
                                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE1"
                            }
                        }
                    }
                }
        
        elif attacker_type == "MANUAL_ATTACKER":
            # Humans verify - give convincing but specific fake creds
            if access_tier >= 2:
                return {
                    "iam": {
                        "security-credentials": {
                            "ec2-role": {
                                "Code": "Success",
                                "LastUpdated": "2026-04-22T14:15:00Z",
                                "Type": "AWS-HMAC",
                                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE1",
                                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2",
                                "Token": "AQoDYXdzEJr.../token/with/canary/embedded/...",
                                "Expiration": "2026-04-25T14:15:00Z"
                            }
                        }
                    }
                }
            else:
                # First access: just show the AccessKeyId
                return {
                    "iam": {
                        "security-credentials": {
                            "ec2-role": {
                                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE1"
                            }
                        }
                    }
                }
        
        else:  # RECONNAISSANCE
            # APT-like slow probing: partial credentials to keep them engaged
            if access_tier == 1:
                return {"iam": {"security-credentials": {"ec2-role": {"AccessKeyId": "AKIAIOSFODNN7EXAMPLE1"}}}}
            elif access_tier == 2:
                return {
                    "iam": {
                        "security-credentials": {
                            "ec2-role": {
                                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE1",
                                "Type": "AWS-HMAC"
                            }
                        }
                    }
                }
            else:
                return {
                    "iam": {
                        "security-credentials": {
                            "ec2-role": {
                                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE1",
                                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY2",
                                "Token": "CANARY_TOKEN_EMBEDDED_HERE"
                            }
                        }
                    }
                }
    
    def generate_api_key_response(self, attacker_type: str, access_tier: int) -> Dict:
        """
        Generate fake API keys endpoint response.
        """
        
        base_keys = {
            "api_keys": [
                {
                    "key_id": "key_prod_1a2b3c4d5e6f7g8h",
                    "type": "authentication",
                    "environment": "production"
                }
            ]
        }
        
        if attacker_type == "AUTOMATED_SCANNER":
            # Give full key immediately for scanners
            base_keys["api_keys"][0]["secret"] = "sk_prod_abcdefghijklmnopqrstuvwxyz123456"
            return base_keys
        
        elif attacker_type == "MANUAL_ATTACKER":
            # Humans: partial key first, full key on retry
            if access_tier >= 2:
                base_keys["api_keys"][0]["secret"] = "sk_prod_abcdefghijklmnopqrstuvwxyz123456"
                base_keys["api_keys"][0]["note"] = "Production credentials - use with caution"
            return base_keys
        
        else:  # RECONNAISSANCE
            # APT: progressive info release
            if access_tier >= 3:
                base_keys["api_keys"][0]["secret"] = "sk_prod_abcdefghijklmnopqrstuvwxyz123456"
                base_keys["api_keys"][0]["permissions"] = ["admin", "write", "delete"]
            return base_keys
    
    def generate_rds_connection_string(self, attacker_type: str, access_tier: int) -> str:
        """
        Generate fake RDS connection string for .yml file
        """
        
        base_config = """production:
  adapter: postgresql
  host: prod-rds.cluster-xxxxx.eu-north-1.rds.amazonaws.com
  port: 5432
  database: payment_gateway_prod
"""
        
        if attacker_type == "AUTOMATED_SCANNER":
            # Full credentials for scanners
            return base_config + """  username: admin
  password: Pr0d_RDS_S3cr3t!2026
  pool: 5
"""
        
        elif attacker_type == "MANUAL_ATTACKER":
            if access_tier >= 2:
                return base_config + """  username: postgres_prod
  password: C0mpl3xP@ssw0rd_2026_Prod
  pool: 20
  ssl: true
"""
            else:
                return base_config + "  # credentials require additional access\n"
        
        else:  # RECONNAISSANCE
            if access_tier >= 3:
                return base_config + """  username: rds_superuser
  password: MASTER_PASSWORD_EMBEDDED_CANARY_TOKEN
  ssl: true
  backup_retention: 30
"""
            else:
                return base_config + "  # partial configuration\n"
    
    def generate_env_file_content(self, attacker_type: str, access_tier: int) -> str:
        """
        Generate fake .env file with secrets
        """
        
        base_env = """# SentinelMesh Environment Configuration
# PRODUCTION - DO NOT SHARE

APP_ENV=production
DEBUG=false
LOG_LEVEL=warning
"""
        
        secrets = f"""
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE{access_tier}
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY{access_tier}
AWS_REGION=eu-north-1

# Database
DATABASE_URL=postgresql://admin:Pr0d_RDS_S3cr3t!{2026}@prod-rds.cluster-xxxxx.eu-north-1.rds.amazonaws.com:5432/payment_db
"""
        
        if attacker_type == "AUTOMATED_SCANNER":
            # Full secrets immediately
            secrets += f"""
# API Keys  
STRIPE_SECRET_KEY=sk_prod_abcdefghijklmnopqrstuvwxyz{123456 + access_tier}
STRIPE_PUBLISHABLE_KEY=pk_prod_abc123def456

# OAuth
GITHUB_OAUTH_SECRET=gho_abcdefghijklmnopqrstuvwxyz123456789
GOOGLE_OAUTH_SECRET=ya29_token_string_here

# Internal Secrets
MASTER_API_KEY=master_key_with_canary_token_{access_tier}
JWT_SECRET=jwt_secret_key_production_{2026}
"""
            return base_env + secrets
        
        elif attacker_type == "MANUAL_ATTACKER":
            if access_tier >= 2:
                return base_env + secrets + f"\n# Last modified: 2026-04-{24 - access_tier}\n"
            else:
                return base_env + "# Partial secrets - require higher access tier\n"
        
        else:  # RECONNAISSANCE
            if access_tier >= 3:
                return base_env + secrets + "\n# SENSITIVE: Contains master credentials\n"
            else:
                return base_env
    
    def get_deception_mode_response(self, resource_type: str) -> Dict:
        """
        Get response for deception mode (APT-level threat detected)
        Maximum honey value with embedded canary tokens
        """
        
        if resource_type == "EC2_METADATA":
            return {
                "iam": {
                    "security-credentials": {
                        "MASTER_ROLE": {
                            "Code": "Success",
                            "AccessKeyId": "AKIAIOSFODNN7MASTER_CANARY",
                            "SecretAccessKey": "MASTER_SECRET_WITH_EMBEDDED_CANARY_TOKEN_WILL_TRIGGER_ALERT",
                            "Token": "DECEPTION_MODE_ACTIVATED_CANARY_EMBEDDED",
                            "Expiration": "2099-12-31T23:59:59Z",
                            "note": "Master role credentials - extremely sensitive"
                        }
                    }
                }
            }
        
        elif resource_type == "API_ENDPOINT":
            return {
                "api_keys": [
                    {
                        "key_id": "key_master_deception_mode",
                        "type": "master_admin",
                        "secret": "sk_master_deception_with_embedded_canary_will_trigger",
                        "permissions": ["*"],
                        "environment": "production",
                        "note": "DECEPTION_MODE: This key will be tracked"
                    }
                ]
            }
        
        else:  # S3
            return {
                "file": "MASTER_CREDENTIALS_DO_NOT_SHARE.txt",
                "content": "MASTER_DECRYPTION_KEYS=canary_token_embedded_trigger_on_use\nAWS_MASTER_ROLE=arn:aws:iam::123456789012:role/master\nMESSAGE: This file is being monitored with embedded canary tokens"
            }
