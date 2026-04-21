import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class AWSController:
    def __init__(self):
        try:
            self.ec2 = boto3.client('ec2', region_name='eu-north-1')
            self.has_credentials = True
        except Exception:
            self.has_credentials = False
            
        self.saved_rules = {}

    def fetch_my_ip(self) -> str:
        import urllib.request
        try:
            return urllib.request.urlopen('https://checkip.amazonaws.com').read().decode('utf-8').strip() + '/32'
        except:
            return '0.0.0.0/0'

    def restrict_security_group(self, instance_id: str) -> bool:
        if not self.has_credentials or instance_id.startswith('i-mock') or instance_id.startswith('mock-'):
            print(f"[MOCK AWS] Restricting security group for {instance_id}")
            self.saved_rules[instance_id] = "mock_rules"
            return True

        try:
            # 1. Get instance to find its security group
            reservations = self.ec2.describe_instances(InstanceIds=[instance_id])
            instance = reservations['Reservations'][0]['Instances'][0]
            sg_id = instance['SecurityGroups'][0]['GroupId']
            
            # 2. Save current rules
            sg_info = self.ec2.describe_security_groups(GroupIds=[sg_id])
            current_rules = sg_info['SecurityGroups'][0]['IpPermissions']
            self.saved_rules[instance_id] = {
                'sg_id': sg_id,
                'rules': current_rules
            }
            
            # 3. Remove all inbound rules
            if current_rules:
                self.ec2.revoke_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=current_rules
                )
                
            # 4. Add restricted SSH rule (only from your IP)
            my_ip = self.fetch_my_ip()
            self.ec2.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': my_ip, 'Description': 'CloudSentinel Auto-Lock'}]
                    }
                ]
            )
            
            # 5. Tag the instance
            self.ec2.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': 'CloudSentinel-Status', 'Value': 'Restricted'}]
            )
            return True
            
        except Exception as e:
            print(f"Error restricting SG: {str(e)}")
            return False

    def rollback_security_group(self, instance_id: str) -> bool:
        if not self.has_credentials or instance_id.startswith('i-mock') or instance_id.startswith('mock-'):
            print(f"[MOCK AWS] Rolling back security group for {instance_id}")
            if instance_id in self.saved_rules:
                del self.saved_rules[instance_id]
            return True

        if instance_id not in self.saved_rules:
            return False
            
        try:
            sg_id = self.saved_rules[instance_id]['sg_id']
            original_rules = self.saved_rules[instance_id]['rules']
            
            # Remove the auto-lock rule
            my_ip = self.fetch_my_ip()
            try:
                self.ec2.revoke_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpRanges': [{'CidrIp': my_ip}]
                        }
                    ]
                )
            except ClientError:
                pass
                
            # Restore original rules
            if original_rules:
                self.ec2.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=original_rules
                )
                
            # Remove tag
            self.ec2.delete_tags(
                Resources=[instance_id],
                Tags=[{'Key': 'CloudSentinel-Status'}]
            )
            
            del self.saved_rules[instance_id]
            return True
            
        except Exception as e:
            print(f"Error rolling back SG: {str(e)}")
            return False
