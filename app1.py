from flask import Flask, redirect, request, render_template, url_for, session, jsonify
import boto3, requests
from datetime import datetime
import base64
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# AWS Cognito Configuration
COGNITO_USER_POOL_ID = 'us-east-1_mV9RmoPzS'
COGNITO_APP_CLIENT_ID = '2g6k88qolbqpalkvtb828v7nj6'
COGNITO_APP_CLIENT_SECRET = '1jlii3adeqpodqd4ag1apabtsbts2h5civsl4ahut6le4g3skh3h'
COGNITO_REGION = 'us-east-1'
COGNITO_DOMAIN = 'https://wealthwave.auth.us-east-1.amazoncognito.com'
REDIRECT_URI = 'http://localhost:5001/home'


#API Gateway Endpoints
API_GATEWAY_UPLOAD_ENDPOINT = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/testStage/upload'
API_GATEWAY_AUTOFILL_ENDPOINT = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/testStage/autofill'
API_GATEWAY_SAVEBILL_ENDPOINT = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/testStage/savebill'

#S3 Configurations
BUCKET_NAME = 'wealthwave-bills-data'

cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

def is_authenticated():
    return 'user_id' in session and 'user_name' in session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signin')
def signin():
    return redirect(f"{COGNITO_DOMAIN}/login?response_type=code&client_id={COGNITO_APP_CLIENT_ID}&redirect_uri={REDIRECT_URI}")


def get_authenticated_user(access_token):
    try:
        # Get user information using the access token
        user_info = cognito_client.get_user(AccessToken=access_token)
        user_name = next((attribute['Value'] for attribute in user_info['UserAttributes'] if attribute['Name'] == 'given_name'), None)
        user_id = user_info['Username']  # or another unique identifier

        return {'user_id': user_id, 'user_name': user_name}

    except Exception as e:
        print(f"Error getting user information: {e}")
        # Log the error for further analysis
        app.logger.error(f"Error getting user information: {e}")
        return None


def is_token_expired(access_token):
    try:
       
        decoded_token = cognito_client.decode_jwt_token(JWToken=access_token)
        expiration_time = decoded_token['exp']
        expiration_datetime = datetime.utcfromtimestamp(expiration_time)

        return expiration_datetime < datetime.utcnow()

    except Exception as e:
        app.logger.error(f"Error checking token expiration: {e}")
        return False  

@app.route('/home')
def home():
    print("Entering /home route")
    
    if is_authenticated():
        print("User is authenticated")
        access_token = session['access_token']

        if is_token_expired(access_token):
            print("Access token expired")
            return render_template('error.html', error_message="Access token expired. Please reauthenticate.")

        user_info = get_authenticated_user(access_token)
        if user_info:
            print("Rendering home.html")
            return render_template('home.html', user_id=user_info['user_id'], user_name=user_info['user_name'])
        else:
            print("Error retrieving user information")
            # Handle error retrieving user information
            return render_template('error.html', error_message="Error retrieving user information.")

    code = request.args.get('code')
    if code:
        try:
            print(f"Received code: {code}")

            # Exchange authorization code for tokens using Authorization Code Grant
            token_url = f'{COGNITO_DOMAIN}/oauth2/token'
            redirect_uri = 'http://localhost:5001/home'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            data = {
                'grant_type': 'authorization_code',
                'client_id': COGNITO_APP_CLIENT_ID,
                'client_secret': COGNITO_APP_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'code': code # Include the necessary scopes here
            }

            response = requests.post(token_url,headers=headers, data=data)

            tokens = response.json()
            access_token = tokens['access_token']
            refresh_token = tokens['refresh_token']
            id_token = tokens['id_token']

            # Store access token and refresh token in the session
            session['access_token'] = access_token
            session['refresh_token'] = refresh_token
            user_info = get_authenticated_user(access_token)
            session['user_id'] = user_info['user_id']
            session['user_name'] = user_info['user_name']
            print(session)
            if user_info:
                print("Rendering home.html")
                return render_template('home.html', user_id=user_info['user_id'], user_name=user_info['user_name'])
            else:
                print("Error retrieving user information")
                # Handle error retrieving user information
                return render_template('error.html', error_message="Error retrieving user information.")

        except Exception as e:
            print(f"Authentication error: {e}")
            # Log the error for further analysis
            app.logger.error(f"Authentication error: {e}")
            print("Rendering error.html")
            # Handle authentication failure gracefully, e.g., redirect to a specific error page
            return render_template('error.html', error_message="Authentication failed. Please try again.")

    print("Redirecting to /signin")
    return redirect(url_for('signin'))

@app.route('/uploadbill')
def uploadbill():
    if not is_authenticated():
        return redirect(url_for('signin'))
    return render_template('uploadbill.html', user_id=session['user_id'])

# @app.route('/analytics')
# def analytics():
#     if not is_authenticated():
#         return redirect(url_for('signin'))

#     return render_template('analytics.html', user_id=session['user_id'])

@app.route('/analytics')
def analytics():
    if not is_authenticated():
        return redirect(url_for('signin'))

   # Define the API URL
    api_url = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/stage1/home/lasttendays'

   # Define the request payload (data to be sent in the request body)
    payload = {'body': json.dumps({'user_id': session['user_id']})}

    # Make a request to the API
    response = requests.get(api_url, data=json.dumps(payload))


    print(response)
    print("---------------------")

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        api_data = response.json()
        print(api_data)  # Print the API data in your Flask console for debugging
    else:
        # Print an error message if the request was not successful
        print(f"Error fetching API data. Status code: {response.status_code}")

    return render_template('analytics.html', user_id=session['user_id'], api_data=api_data)


@app.route('/exportdata')
def exportdata():
    if not is_authenticated():
        return redirect(url_for('signin'))

    return render_template('exportdata.html', user_id=session['user_id'])

@app.route('/settings')
def settings():
    if not is_authenticated():
        return redirect(url_for('signin'))

    return render_template('settings.html', user_id=session['user_id'])

@app.route('/signout')
def signout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    user_id = request.form.get('user_id')  # Assuming the user ID is sent as part of the form data

    # Read the file content and encode it in base64
    file_content_base64 = base64.b64encode(file.read()).decode('utf-8')

    # Prepare the payload for the API Gateway
    payload = json.dumps({
        'user_id': user_id,
        'filename': file.filename,
        'body': file_content_base64,
        'bucket_name': BUCKET_NAME
    })

    # Send the request to API Gateway
    response = requests.post(API_GATEWAY_UPLOAD_ENDPOINT, data=payload, headers={'Content-Type': 'application/json'})

    # Handle the response from API Gateway
    if response.status_code == 200:
        # Process was successful, forward the response
        return jsonify(response.json()), 200
    else:
        # There was an error, forward the error message
        return jsonify(response.json()), response.status_code

@app.route('/autofill', methods=['POST'])
def auto_fill():
    data = request.json
    s3_file_key = data.get('s3_file_key')

    # Prepare the payload for the API Gateway request
    payload = {
        'bucket_name': BUCKET_NAME,  # Replace with your bucket name
        'document_key': s3_file_key
    }

    # Send the request to the API Gateway endpoint
    response = requests.post(API_GATEWAY_AUTOFILL_ENDPOINT, json=payload)

    # Return the response to the frontend
    return jsonify(response.json()), response.status_code

@app.route('/saveBillData', methods=['POST'])
def save_bill_data():
    # Get the data from the request
    data = request.json

    # Send the request to the Lambda function via API Gateway
    response = requests.post(API_GATEWAY_SAVEBILL_ENDPOINT, json=data)

    # Forward the response from the Lambda function
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(debug=True,port = 5001)
