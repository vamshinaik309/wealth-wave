import os
import boto3
import base64
import json
from datetime import datetime
import uuid

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Print the received event for debugging
        # print("Received event:", event)
        
        # Parse the JSON body from the event
        body = json.loads(event["body"])
        
        # Extract the user_id, filename, and base64-encoded file content from the body
        user_id = body['user_id']
        print(f'user_id extracted is: {user_id}')
        
        # Extract bucket_name
        bucket_name = body['bucket_name']
        
        original_filename = body['filename']
        file_content_base64 = body['body']
        
        # Decode the base64-encoded file content
        file_content = base64.b64decode(file_content_base64)
        print(f'file_content extracted')
        
        # Extract the file extension
        _, file_extension = os.path.splitext(original_filename)
        
        # Generate the file key
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex
        file_key = f'uploads/{user_id}/{timestamp}_{unique_id}{file_extension}'  # Append file extension

        # Upload the file to S3
        s3_client.put_object(Body=file_content, Bucket=bucket_name, Key=file_key)

        # Return a success response
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'File uploaded successfully', 'file_key': file_key})
        }
    except Exception as e:
        # Log the exception and return an error response
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error in uploading file: {str(e)}")
        }
