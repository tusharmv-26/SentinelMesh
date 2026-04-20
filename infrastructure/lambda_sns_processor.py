import json
import urllib.request
import os

# Set this to the public IP or domain of your EC2 FastAPI instance
FASTAPI_ENDPOINT = os.environ.get('FASTAPI_ENDPOINT', 'http://13.48.58.234:8000/events')

def lambda_handler(event, context):
    try:
        # Standard SNS wrapping S3 event structure
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        
        # Typically one record in an S3 Event Notification, but loop to be safe
        for record in sns_message.get('Records', []):
            s3_data = record['s3']
            request_parameters = record['requestParameters']
            timestamp = record['eventTime']
            
            attacker_ip = request_parameters['sourceIPAddress']
            bucket_name = s3_data['bucket']['name']
            object_key = s3_data['object']['key'] if 'object' in s3_data else ''
            
            # Form the resource name logically
            resource_name = bucket_name
            if object_key:
                resource_name += f"/{object_key}"
            
            # Map event name to HTTP roughly
            method = "GET" if "GetObject" in record['eventName'] else "UNKNOWN"
            
            payload = {
                "attacker_ip": attacker_ip,
                "resource_name": resource_name,
                "method": method
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                FASTAPI_ENDPOINT, 
                data=data, 
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=3) as response:
                print(f"Posted to FastAPI successfully: {response.getcode()}")
                
        return {
            'statusCode': 200,
            'body': json.dumps('Processed S3 event successfully')
        }
        
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        raise e
