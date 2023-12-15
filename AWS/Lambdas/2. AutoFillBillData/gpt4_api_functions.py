import boto3
from botocore.exceptions import ClientError
from openai import OpenAI
import json

# Function to retrieve the OpenAI API key from AWS Secrets Manager
def get_openai_api_key():
    secret_name = "WealthWaveProjectKey"  # Updated secret name
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e
    else:
        # Decrypts secret using the associated KMS key.
        secret = get_secret_value_response['SecretString']
        parsed_secret = json.loads(secret)
        return parsed_secret["OpenAI_API_Key"]

# Function to query GPT-4 to process the extracted text
def query_gpt4_json_mode(extracted_text):
    # Initialize OpenAI client
    client = OpenAI(api_key=get_openai_api_key())

    # Create system and user messages
    system_message = """
You are a helpful assistant designed to output JSON.
Analyze the following receipt and extract the specified details.
Structure the output as a JSON object with the following keys:
- 'date': The date of the transaction in the format "yyyy-MM-dd".
- 'time': The time of the transaction in 24-hour format 'HH:mm'.
- 'total_amount': The total amount paid, as a numerical value without the currency symbol.
- 'currency_type': The type of currency used (e.g., dollar, rupee).
- 'category': The category of the purchase from the following options: groceries/food, dining, utilities, housing, transportation, healthcare, entertainment, clothing, education, alcohol/beverages, travel.
If the category does not match the predefined options, default to 'miscellaneous'.
If a specific value cannot be inferred from the receipt, set the corresponding field to null.
"""

    user_message = extracted_text

    # Call the OpenAI API in JSON mode
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )

        # Extract and return the JSON content from the response
        json_output = response.choices[0].message.content
        return json_output
    except Exception as e:
        print(f"Error querying GPT-4 in JSON mode: {e}")
        raise e
