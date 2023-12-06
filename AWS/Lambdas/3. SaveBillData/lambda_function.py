import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('UserBills')  # Your DynamoDB table name

    # Parse incoming data
    data = json.loads(event['body'])
    user_id = data['user_id']
    # Generate a timestamp for sorting
    timestamp = datetime.now().isoformat()
    date = data['date']
    total_amount = data['totalAmount']
    category = data['category']
    uploaded_file_key = data['uploadedFileKey']

    # Save data to DynamoDB
    table.put_item(Item={
        'user_id': user_id,
        'timestamp': timestamp,
        'date': date,
        'totalAmount': total_amount,
        'category': category,
        'uploadedFileKey': uploaded_file_key
    })

    return {
        'statusCode': 200,
        'body': json.dumps('Data saved successfully')
    }
