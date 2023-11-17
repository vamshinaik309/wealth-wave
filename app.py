from flask import Flask, redirect, request, render_template, url_for
import boto3

app = Flask(__name__)

# AWS Cognito Configuration
COGNITO_USER_POOL_ID = 'us-east-1_92fhsj2cM'
COGNITO_APP_CLIENT_ID = '33d5l6ooqfg4jnrohkv7r60sm9'
COGNITO_REGION = 'us-east-1'
COGNITO_DOMAIN = 'https://wealth-wave.auth.us-east-1.amazoncognito.com'
REDIRECT_URI = 'http://localhost:5000/home'

cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signin')
def signin():
    return redirect(f"{COGNITO_DOMAIN}/login?response_type=code&client_id={COGNITO_APP_CLIENT_ID}&redirect_uri={REDIRECT_URI}")


@app.route('/home')
def callback():
    code = request.args.get('code')
    if code:
        # Example of getting email and password from a form or session
        user_email = 'vv2289@nyu.edu'  # Replace with the user's email
        user_password = 'Vamshi@123'   # Replace with the user's password

        response = cognito_client.admin_initiate_auth(
            UserPoolId=COGNITO_USER_POOL_ID,
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': user_email,
                'PASSWORD': user_password
            }
        )
        # Handle the response, such as creating a session
    return render_template('home.html')


@app.route('/signout')
def signout():
    return redirect(f"{COGNITO_DOMAIN}/logout?client_id={COGNITO_APP_CLIENT_ID}&logout_uri=http://localhost:5000/signin")


# Add other routes and logic here

if __name__ == '__main__':
    app.run(debug=True)
