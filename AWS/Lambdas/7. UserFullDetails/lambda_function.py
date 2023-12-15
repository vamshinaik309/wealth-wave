import boto3
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    print(event)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('UserBills')  # Your DynamoDB table name

    # Parse incoming data
    data = json.loads(event['body'])
    user_id = data['user_id']

    # Query DynamoDB to get the last 10 items
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        ScanIndexForward=False,  # Set to False for descending order (assuming timestamp is used for sorting)
        # IndexName='your_index_name'  # Optional: If you're using a global secondary index
    )

    # Extract last 10 items
    last_10_items = response.get('Items', [])

    # Prepare the response using the custom encoder
    response_body = {
        'statusCode': 200,
        'body': json.dumps(last_10_items, cls=DecimalEncoder)
    }

    return response_body
