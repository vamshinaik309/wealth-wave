import json
import boto3
import base64
from datetime import datetime

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    table = dynamodb.Table('User-Preferences')
    bucket_name = 'wealthwave-user-images'

    try:
        # Retrieve additional data from the event
        user_id = event['user_id']
        email_frequency = event['email_frequency']
        username = event['username']
        user_email = event['user_email']
        last_email = event['last_email']  # Assuming last_email is passed in the event
        file_content = event.get('file_content', '')
        content_type = event.get('contentType', 'application/octet-stream')

        # S3 object key pattern
        s3_object_key = f'user-profiles/{user_id}'

        # Upload file to S3 if provided
        if file_content:
            file_data = base64.b64decode(file_content)
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_object_key,
                Body=file_data,
                ContentType=content_type,
                CacheControl='max-age=86400'
            )

        # Update DynamoDB
        update_expression = 'SET emailFrequency = :ef, s3ObjectKey = :ok, username = :un, user_email = :ue, last_email = :le'
        expression_attribute_values = {
            ':ef': email_frequency,
            ':ok': s3_object_key,
            ':un': username,
            ':ue': user_email,
            ':le': last_email
        }

        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User preferences updated successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error: {str(e)}'})
        }
        