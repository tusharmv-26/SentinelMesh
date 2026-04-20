import boto3
import os
import random
import time
from botocore.exceptions import ClientError

class MutationEngine:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name='eu-north-1')
        self.sns_arn = os.environ.get('HONEYPOT_SNS_ARN', '')
        self.created_honeypots = []
        
        self.category_keywords = {
            "payment": ["payment", "billing", "stripe", "gateway"],
            "credential": ["key", "secret", "token", "auth", "iam"],
            "database": ["database", "db", "sql", "rds", "postgres"],
            "backup": ["backup", "snapshot", "restore", "archive"],
            "employee": ["employee", "salary", "hr", "personnel"]
        }
        
        self.templates = {
            "payment": [
                "stripe-api-credentials-backup-{year}",
                "payment-gateway-prod-keys-{year}"
            ],
            "credential": [
                "admin-ssh-keys-backup-{year}",
                "service-account-tokens-prod-{year}"
            ],
            "database": [
                "rds-prod-snapshot-restore-{year}",
                "db-master-password-backup-{year}"
            ],
            "backup": [
                "prod-system-full-backup-{year}",
                "disaster-recovery-archives-{year}"
            ],
            "employee": [
                "employee-salary-records-hr-{year}",
                "personnel-files-confidential-{year}"
            ]
        }

    def _determine_category(self, profile):
        combined = " ".join(profile.get("resources_probed", [])).lower()
        if not combined:
            return None
            
        best_cat = None
        max_hits = 0
        
        for category, keywords in self.category_keywords.items():
            hits = sum(1 for kw in keywords if kw in combined)
            if hits > max_hits:
                max_hits = hits
                best_cat = category
                
        return best_cat if max_hits > 0 else None

    def mutate(self, profile):
        category = self._determine_category(profile)
        if not category:
            return None
            
        year = time.strftime("%Y")
        bucket_name = None
        
        # Shuffle templates to avoid predicting
        templates = self.templates[category][:]
        random.shuffle(templates)
        
        for template in templates:
            candidate = template.format(year=year)
            # Ensure we haven't already made it
            if not any(h['bucket_name'] == candidate for h in self.created_honeypots):
                bucket_name = candidate
                break
                
        if not bucket_name:
            return None # Ran out of templates for this category
            
        # 1. Create the Bucket
        try:
            print(f"[MUTATION ENGINE] Deploying adaptive honeypot: {bucket_name}")
            self.s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'eu-north-1'}
            )
        except ClientError as e:
            print(f"Mutation Engine Error creating bucket: {e}")
            return None
            
        # 2. Wire the SNS Notification
        if self.sns_arn:
            try:
                self.s3_client.put_bucket_notification_configuration(
                    Bucket=bucket_name,
                    NotificationConfiguration={
                        'TopicConfigurations': [
                            {
                                'TopicArn': self.sns_arn,
                                'Events': ['s3:ObjectCreated:*', 's3:ObjectRemoved:*']
                            }
                        ]
                    }
                )
            except ClientError as e:
                print(f"Mutation Engine Error setting SNS: {e}")
                
        # 3. Drop the fake README payload
        payload_content = f"CONFIDENTIAL - {time.strftime('%Y-%m-%d')}\n\nRESTRICTED ACCESS ONLY.\n"
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key='README.txt',
                Body=payload_content.encode('utf-8')
            )
        except Exception:
            pass
            
        # 4. Record mutation
        mutation_record = {
            "bucket_name": bucket_name,
            "category": category,
            "trigger_ip": profile["ip"],
            "trigger_intent": profile["intent"],
            "timestamp": time.time()
        }
        self.created_honeypots.insert(0, mutation_record)
        return mutation_record

    def get_created_honeypots(self):
        return self.created_honeypots
