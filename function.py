import boto3
import json

def lambda_handler(event, context):
    # Initialize the S3 and Config clients
    s3_client = boto3.client('s3')
    config_client = boto3.client('config')
    
    # Assume non-compliant by default
    compliance_status = "NON-COMPLIANT"
    
    # Extract the bucket name from the invokingEvent
    config = json.loads(event['invokingEvent'])
    configuration_item = config["configurationItem"]
    bucket_name = configuration_item['configuration']['name']
    
    # Get the bucket's public access block configuration
    try:
        public_access_block = s3_client.get_public_access_block(Bucket=bucket_name)
        public_access_settings = public_access_block['PublicAccessBlockConfiguration']
        
        # Check if any public access block settings are enabled
        if any(public_access_settings.values()):
            compliance_status = "COMPLIANT"
            annotation = "Block Public Access is ON."
        else:
            annotation = "Block Public Access is OFF."
            
    except s3_client.exceptions.NoSuchPublicAccessBlockConfiguration:
        # If there is no Public Access Block configuration, consider it compliant
        annotation = "No Block Public Access configuration found; assuming public access is allowed."
    
    # Prepare the evaluation object
    evaluation = {
        'ComplianceResourceType': 'AWS::S3::Bucket',
        'ComplianceResourceId': bucket_name,
        'ComplianceType': compliance_status,
        'Annotation': annotation,
        'OrderingTimestamp': configuration_item['configurationItemCaptureTime']
    }
    
    # Submit the evaluation to AWS Config
    response = config_client.put_evaluations(
        Evaluations=[evaluation],
        ResultToken=event['resultToken']
    )
    
    return response
