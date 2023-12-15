import json
import boto3
import base64

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    table = dynamodb.Table('User-Preferences')
    bucket_name = 'wealthwave-user-images'

    try:
        user_id = event['user_id']
        email_frequency = event['email_frequency']
        file_content = event.get('file_content', '')
        content_type = event.get('contentType', 'application/octet-stream')  # Default content type

        # S3 object key pattern
        s3_object_key = f'user-profiles/{user_id}'

        # Upload file to S3 if provided
        if file_content:
            file_data = base64.b64decode(file_content)
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_object_key,
                Body=file_data,
                ContentType=content_type,  # Adjust based on actual content type
                CacheControl='max-age=86400'  # Example cache control header
            )

        # Update DynamoDB with email frequency and S3 object key
        update_expression = 'SET emailFrequency = :ef, s3ObjectKey = :ok'
        expression_attribute_values = {
            ':ef': email_frequency,
            ':ok': s3_object_key  # Store only the user_id-based key
        }
        
        print(f'update_expression: {update_expression}')
        print(f'expression_attribute_values: {expression_attribute_values}')

        table.update_item(
            Key={'user_id': user_id},  # Ensure the key matches your DynamoDB table's primary key
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        print(f'table is updated!')
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User preferences updated successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error: {str(e)}'})
        }
