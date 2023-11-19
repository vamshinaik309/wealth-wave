from flask import Flask, redirect, request, render_template, url_for, session
import boto3, requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# AWS Cognito Configuration
COGNITO_USER_POOL_ID = 'us-east-1_mV9RmoPzS'
COGNITO_APP_CLIENT_ID = '2g6k88qolbqpalkvtb828v7nj6'
COGNITO_APP_CLIENT_SECRET = '1jlii3adeqpodqd4ag1apabtsbts2h5civsl4ahut6le4g3skh3h'
COGNITO_REGION = 'us-east-1'
COGNITO_DOMAIN = 'https://wealthwave.auth.us-east-1.amazoncognito.com'
REDIRECT_URI = 'http://localhost:5001/home'

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
        # Decode the access token to get its claims, including the expiration time
        decoded_token = cognito_client.decode_jwt_token(JWToken=access_token)

        # Extract the expiration time from the decoded token
        expiration_time = decoded_token['exp']

        # Convert the expiration time to a datetime object
        expiration_datetime = datetime.utcfromtimestamp(expiration_time)

        # Check if the token has expired by comparing with the current time
        return expiration_datetime < datetime.utcnow()

    except Exception as e:
        # Log the error for further analysis
        app.logger.error(f"Error checking token expiration: {e}")
        return False  # Return False in case of any error; you may choose to handle errors differently based on your requirements

@app.route('/home')
def home():
    print("Entering /home route")
    
    if is_authenticated():
        print("User is authenticated")
        access_token = session['access_token']

        # Check if the access token is expired (simplified check)
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

            # Parse the response, which should contain access_token, refresh_token, and id_token
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

    return render_template('uploadbill.html', user_name=session['user_name'])

@app.route('/analytics')
def analytics():
    if not is_authenticated():
        return redirect(url_for('signin'))

    return render_template('analytics.html', user_name=session['user_name'])

@app.route('/exportdata')
def exportdata():
    if not is_authenticated():
        return redirect(url_for('signin'))

    return render_template('exportdata.html', user_name=session['user_name'])

@app.route('/settings')
def settings():
    if not is_authenticated():
        return redirect(url_for('signin'))

    return render_template('settings.html', user_name=session['user_name'])

@app.route('/signout')
def signout():
    session.clear()
    return render_template('index.html')

# ... (Other routes remain unchanged)

if __name__ == '__main__':
    app.run(debug=True,port = 5001)
