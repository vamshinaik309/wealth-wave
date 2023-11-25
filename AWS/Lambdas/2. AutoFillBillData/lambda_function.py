import boto3
import json
from urllib.parse import unquote_plus
import gpt4_api_functions as gpt4_api

def lambda_handler(event, context):
    # Initialize AWS Textract client
    textract = boto3.client('textract')

    # Parse the JSON body from the event
    body = json.loads(event["body"])
    bucket_name = body['bucket_name']
    document_key = body['document_key']

    print('bucket_name:', bucket_name)
    print('document_key:', document_key)

    # Call Textract to analyze the document
    try:
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': document_key
                }
            }
        )

        # Process Textract response
        text_blocks = [block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE']
        
        # Check if text was extracted
        if not text_blocks:
            return {
                'statusCode': 400
            }
        
        extracted_text = ' '.join(text_blocks)
        print(f'extracted_text is: {extracted_text}')

        # Query GPT-4 with the extracted text
        gpt_response = gpt4_api.query_gpt4_json_mode(extracted_text)
        print(gpt_response)

        return {
            'statusCode': 200,
            'body': json.dumps(gpt_response)
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error extracting text.')
        }
