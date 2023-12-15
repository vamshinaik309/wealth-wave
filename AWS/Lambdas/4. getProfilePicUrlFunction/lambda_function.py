import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    bucket_name = 'wealthwave-user-images'
    
    print(f'event: {event}')
    user_id = event.get('user_id')
    object_key = f'user-profiles/{user_id}'

    try:
        # Check if the object exists in S3
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        image_url = f'https://{bucket_name}.s3.amazonaws.com/{object_key}'
        return {
            'statusCode': 200,
            'body': json.dumps({'exists': True, 'url': image_url})
        }
    except ClientError as e:
        return {
            'statusCode': 404,
            'body': json.dumps({'exists': False, 'url': ''})
        }
