from flask import Flask, redirect, request, render_template, url_for, session
import boto3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# AWS Cognito Configuration
COGNITO_USER_POOL_ID = 'us-east-1_92fhsj2cM'
COGNITO_APP_CLIENT_ID = '33d5l6ooqfg4jnrohkv7r60sm9'
COGNITO_REGION = 'us-east-1'
COGNITO_DOMAIN = 'https://wealth-wave.auth.us-east-1.amazoncognito.com'
REDIRECT_URI = 'http://localhost:5000/home'

cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

def is_authenticated():
    return 'user_id' in session and 'user_name' in session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signin')
def signin():
    return redirect(f"{COGNITO_DOMAIN}/login?response_type=code&client_id={COGNITO_APP_CLIENT_ID}&redirect_uri={REDIRECT_URI}")

@app.route('/home')
def home():
    if is_authenticated():
        return render_template('home.html', user_id=session['user_id'], user_name=session['user_name'])

    code = request.args.get('code')
    if code:
        # ... existing code for Cognito authorization ...

        # Retrieve access token
        user_email = 'vv2289@nyu.edu'  # Replace with the user's email
        user_password = 'Vamshi@123'   # Replace with the user's password

        # Authenticate the user
        response = cognito_client.admin_initiate_auth(
            UserPoolId=COGNITO_USER_POOL_ID,
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': user_email,
                'PASSWORD': user_password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']

        # Get user information using the access token
        user_info = cognito_client.get_user(AccessToken=access_token)

        user_name = next((attribute['Value'] for attribute in user_info['UserAttributes'] if attribute['Name'] == 'name'), None)
        user_id = user_info['Username']  # or another unique identifier

        # Store user information in the session
        session['user_id'] = user_id
        session['user_name'] = user_name

        return render_template('home.html', user_id=user_id, user_name=user_name)

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
    return redirect(f"{COGNITO_DOMAIN}/logout?client_id={COGNITO_APP_CLIENT_ID}&logout_uri=http://localhost:5000/signin")

if __name__ == '__main__':
    app.run(debug=True)



# from flask import Flask, redirect, request, render_template, url_for, session
# import boto3

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# # AWS Cognito Configuration
# COGNITO_USER_POOL_ID = 'us-east-1_92fhsj2cM'
# COGNITO_APP_CLIENT_ID = '33d5l6ooqfg4jnrohkv7r60sm9'
# COGNITO_REGION = 'us-east-1'
# COGNITO_DOMAIN = 'https://wealth-wave.auth.us-east-1.amazoncognito.com'
# REDIRECT_URI = 'http://localhost:5000/home'

# cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

# def is_authenticated():
#     return 'user_id' in session and 'user_name' in session

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/signin')
# def signin():
#     return redirect(f"{COGNITO_DOMAIN}/login?response_type=code&client_id={COGNITO_APP_CLIENT_ID}&redirect_uri={REDIRECT_URI}")

# @app.route('/home')
# def home():
#     code = request.args.get('code')
#     if code:
#         # Example of getting email and password from a form or session
#         user_email = 'vv2289@nyu.edu'  # Replace with the user's email
#         user_password = 'Vamshi@123'   # Replace with the user's password

#         # Authenticate the user
#         response = cognito_client.admin_initiate_auth(
#             UserPoolId=COGNITO_USER_POOL_ID,
#             ClientId=COGNITO_APP_CLIENT_ID,
#             AuthFlow='ADMIN_NO_SRP_AUTH',
#             AuthParameters={
#                 'USERNAME': user_email,
#                 'PASSWORD': user_password
#             }
#         )

#         # Retrieve access token
#         access_token = response['AuthenticationResult']['AccessToken']

#         # Get user information using the access token
#         user_info = cognito_client.get_user(AccessToken=access_token)

#         user_name = next((attribute['Value'] for attribute in user_info['UserAttributes'] if attribute['Name'] == 'name'), None)

#         user_id = user_info['Username']  # or another unique identifier

#         # Store user information in the session
#         session['user_id'] = user_id
#         session['user_name'] = user_name

#         return render_template('home.html', user_id=user_id, user_name=user_name)
    
#     return redirect(url_for('signin'))

# @app.route('/uploadbill')
# def uploadbill():
#     user_name = session.get('user_name')
#     if not user_name:
#         return redirect(url_for('signin'))
    
#     return render_template('uploadbill.html', user_name=user_name)

# @app.route('/analytics')
# def analytics():
#     user_name = session.get('user_name')
#     if not user_name:
#         return redirect(url_for('signin'))
    
#     return render_template('analytics.html', user_name=user_name)

# @app.route('/exportdata')
# def exportdata():
#     user_name = session.get('user_name')
#     if not user_name:
#         return redirect(url_for('signin'))
    
#     return render_template('exportdata.html', user_name=user_name)

# @app.route('/settings')
# def settings():
#     user_name = session.get('user_name')
#     if not user_name:
#         return redirect(url_for('signin'))
    
#     return render_template('settings.html', user_name=user_name)

# @app.route('/signout')
# def signout():
#     # Clear the session and redirect to the sign-in page
#     session.clear()
#     return redirect(f"{COGNITO_DOMAIN}/logout?client_id={COGNITO_APP_CLIENT_ID}&logout_uri=http://localhost:5000/signin")

# if __name__ == '__main__':
#     app.run(debug=True)
