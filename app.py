from flask import Flask, redirect, request, render_template, url_for, session, jsonify
import boto3, requests
import base64
import json
import jwt
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
from flask import flash
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from collections import defaultdict
import numpy as np



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# AWS Cognito Configuration
COGNITO_USER_POOL_ID = 'us-east-1_mV9RmoPzS'
COGNITO_APP_CLIENT_ID = '2g6k88qolbqpalkvtb828v7nj6'
COGNITO_APP_CLIENT_SECRET = '1jlii3adeqpodqd4ag1apabtsbts2h5civsl4ahut6le4g3skh3h'
COGNITO_REGION = 'us-east-1'
COGNITO_DOMAIN = 'https://wealthwave.auth.us-east-1.amazoncognito.com'

REDIRECT_URI = 'http://localhost:5001/home'
# If you are using the domain, then make this the redirect url instead of localhost.
# REDIRECT_URI = 'https://wealthwavenyu.net/home'



#API Gateway Endpoints
API_GATEWAY_BASE_URL = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/testStage'
API_GATEWAY_UPLOAD_ENDPOINT = API_GATEWAY_BASE_URL + '/upload'
API_GATEWAY_AUTOFILL_ENDPOINT = API_GATEWAY_BASE_URL + '/autofill'
API_GATEWAY_SAVEBILL_ENDPOINT = API_GATEWAY_BASE_URL + '/savebill'

API_GATEWAY_UPDATE_USER_PREF_ENDPOINT = API_GATEWAY_BASE_URL + '/updateUserPref'
API_GATEWAY_GET_PROFILE_PIC_URL_ENDPOINT = API_GATEWAY_BASE_URL + '/getProfilePicUrl'

#S3 Configurations
BUCKET_NAME = 'wealthwave-bills-data'

cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

def is_authenticated():
    return 'user_id' in session and 'user_name' in session and 'user_email' in session

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
        print(user_info)
        user_name = next((attribute['Value'] for attribute in user_info['UserAttributes'] if attribute['Name'] == 'given_name'), None)
        user_id = user_info['Username']  # or another unique identifier
        user_email = next((attribute['Value'] for attribute in user_info['UserAttributes'] if attribute['Name'] == 'email'), None)

        return {'user_id': user_id, 'user_name': user_name, 'user_email' : user_email}

    except Exception as e:
        print(f"Error getting user information: {e}")
        # Log the error for further analysis
        app.logger.error(f"Error getting user information: {e}")
        return None


def is_token_expired(access_token):
    try:
        # Decode the token (without verifying, as we just want the expiry time)
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
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
            # Retrieve last 10 transactions data (similar to the /analytics route)
            api_url = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/stage1/home/lasttendays'
            payload = {'body': json.dumps({'user_id': session['user_id']})}
            response = requests.get(api_url, data=json.dumps(payload))

            if response.status_code == 200:
                api_data = response.json()
                body_data = json.loads(api_data.get('body', '[]'))
                transactions = body_data[:10]  # Take the first 10 transactions

                # Calculate total amount
                total_amount = sum(float(entry.get('totalAmount', 0)) for entry in transactions)

                # Render home.html with user information, last 10 transactions, and total amount
                return render_template('home.html', user_id=user_info['user_id'],
                                           user_name=user_info['user_name'],
                                           user_email=user_info['user_email'],
                                           transactions=transactions,
                                           total_amount=total_amount)
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
            redirect_uri = REDIRECT_URI
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
            session['user_email']= user_info['user_email']
            print(session)
            if user_info:
                api_url = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/stage1/home/lasttendays'
                payload = {'body': json.dumps({'user_id': session['user_id']})}
                response = requests.get(api_url, data=json.dumps(payload))

                if response.status_code == 200:
                    api_data = response.json()
                    body_data = json.loads(api_data.get('body', '[]'))
                    transactions = body_data[:10]  # Take the first 10 transactions

                    # Calculate total amount
                    total_amount = sum(float(entry.get('totalAmount', 0)) for entry in transactions)

                    # Render home.html with user information, last 10 transactions, and total amount
                    return render_template('home.html', user_id=user_info['user_id'],
                                            user_name=user_info['user_name'],
                                            user_email=user_info['user_email'],
                                            transactions=transactions,
                                            total_amount=total_amount)    
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

@app.route('/analytics')
def analytics():
    # Check if the user is authenticated
    if not is_authenticated():
        return redirect(url_for('signin'))

    # Define the API URL
    api_url = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/stage1/home/UserFullDetailsApi'

    # Define the request payload (data to be sent in the request body)
    payload = {'body': json.dumps({'user_id': session['user_id']})}

    try:
        # Make a request to the API
        response = requests.get(api_url, data=json.dumps(payload))

        # print(response)
        # print("---------------------")

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            api_data = response.json()
            print(api_data)  # Print the API data in your Flask console for debugging
            print(type(api_data))

            # Extract 'body' from api_data or provide an empty list as a default
            body_data = json.loads(api_data.get('body', '[]'))
            print(body_data)

            # Calculate the sum of totalAmount values
            total_amount_sum = sum(float(entry.get('totalAmount', 0)) for entry in body_data)
            print(f"Total Amount Sum: {total_amount_sum}")

            # Combine values for the same category
            category_totals = defaultdict(float)
            for entry in body_data:
                category_totals[entry['category']] += float(entry.get('totalAmount', 0))

            # Prepare data for pie chart
            pie_chart_data = [{'category': category, 'totalAmount': total} for category, total in category_totals.items()]


            ##################line graph for last 30 days##########
            # Sort the data by date
            sorted_body_data = sorted(body_data, key=lambda x: x['date'])

            # Filter data for the last 30 days
            last_30_days_data = [entry for entry in sorted_body_data if datetime.now() - datetime.strptime(entry['date'], '%Y-%m-%d') <= timedelta(days=30)]

            # Use a defaultdict to accumulate totalAmount values for each date
            date_totals = defaultdict(float)
            for entry in last_30_days_data:
                date_totals[entry['date']] += float(entry['totalAmount'])

            # Prepare data for line graph (last 30 days)
            line_chart_data_30_days = {
                'labels': list(date_totals.keys()),
                'data': list(date_totals.values())
            }

            ##################line graph for last 12 months##########
            # Filter data for the last 12 months
            last_12_months_data = [entry for entry in sorted_body_data if datetime.now() - datetime.strptime(entry['date'], '%Y-%m-%d') <= timedelta(days=365)]

            # Use a defaultdict to accumulate totalAmount values for each month
            month_totals = defaultdict(float)
            for entry in last_12_months_data:
                year_month = entry['date'][:7]  # Extract the year and month part
                month_totals[year_month] += float(entry['totalAmount'])

            # Prepare data for line graph (last 12 months)
            line_chart_data_12_months = {
                'labels': [datetime.strptime(date, '%Y-%m').strftime('%b %Y') for date in month_totals.keys()],
                'data': list(month_totals.values())
            }

            ##################total amount for the current month##########
            # Filter data for the current month
            current_month_data = [entry for entry in sorted_body_data if datetime.now().strftime('%Y-%m') == entry['date'][:7]]

            # Calculate the total amount spent in the current month
            total_amount_current_month = sum(float(entry['totalAmount']) for entry in current_month_data)

            ##################percentage increase from last month to the month before##########
            # Calculate the total amount spent in the last month
            total_amount_last_month = line_chart_data_12_months['data'][-2] if line_chart_data_12_months['data'] else 0

            # Calculate the total amount spent in the month before the last month
            total_amount_last_last_month = line_chart_data_12_months['data'][-3] if len(line_chart_data_12_months['data']) > 1 else 0
            
            # Calculate the percentage increase
            percentage_increase = ((total_amount_last_month - total_amount_last_last_month) / total_amount_last_last_month) * 100 if total_amount_last_last_month != 0 else 0
            
            
            #####################calculate last 12 months category wise data##################################
            current_month_year = datetime.now().strftime('%Y-%m')
            
            category_totals_12_months = defaultdict(lambda: set())
            for entry in last_12_months_data:
                # Skip the current month's data
                if entry['date'][:7] == current_month_year:
                    continue
                
                category_totals_12_months[entry['category']].add(float(entry['totalAmount']))

            

            # Convert the sets to lists for easier serialization to JSON
            category_totals_12_months = {category: list(total_amounts) for category, total_amounts in category_totals_12_months.items()}

            # print(total_amount_last_month)
            # print(total_amount_last_last_month)
            # print(line_chart_data_12_months)
            # print("----------------------")
            # print(category_totals_12_months)

            pie_chart_data = sorted(pie_chart_data, key=lambda x: x['category'].lower())
            # print(pie_chart_data)
            # Include all necessary data in a single variable
            frontend_data = {
                'user_id': session['user_id'],
                'total_amount_sum': total_amount_sum,
                'total_amount_current_month': total_amount_current_month,
                'percentage_increase_last_month': percentage_increase,
                'pie_chart_data': pie_chart_data,
                'line_chart_data_30_days': line_chart_data_30_days,
                'line_chart_data_12_months': line_chart_data_12_months
            }
            return render_template('analytics.html', **frontend_data)
        
        else:
            # Print an error message if the request was not successful
            print(f"Error fetching API data. Status code: {response.status_code}")
            return render_template('analytics.html', user_id=session['user_id'], total_amount_sum=0, pie_chart_data="[]", transactions=[])

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")







@app.route('/predictions')
def predictions():
    # Check if the user is authenticated
    if not is_authenticated():
        return redirect(url_for('signin'))

    # Define the API URL
    api_url = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/stage1/home/UserFullDetailsApi'

    # Define the request payload (data to be sent in the request body)
    payload = {'body': json.dumps({'user_id': session['user_id']})}

    try:
        # Make a request to the API
        response = requests.get(api_url, data=json.dumps(payload))

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            api_data = response.json()

            # Extract 'body' from api_data or provide an empty list as a default
            body_data = json.loads(api_data.get('body', '[]'))
            # print(body_data)

            # Calculate the sum of totalAmount values
            total_amount_sum = sum(float(entry.get('totalAmount', 0)) for entry in body_data)
            print(f"Total Amount Sum: {total_amount_sum}")

           
            ##################line graph for last 30 days##########
            # Sort the data by date
            sorted_body_data = sorted(body_data, key=lambda x: x['date'])


            ##################line graph for last 12 months##########
            # Filter data for the last 12 months
            last_12_months_data = [entry for entry in sorted_body_data if datetime.now() - datetime.strptime(entry['date'], '%Y-%m-%d') <= timedelta(days=365)]

            
            #####################calculate last 12 months category wise data##################################
            # Use a defaultdict to accumulate totalAmount values for each month and category
            # Use a defaultdict to accumulate totalAmount values for each category over the last 12 months
            current_month_year = datetime.now().strftime('%Y-%m')
            
            category_totals_12_months = defaultdict(lambda: set())
            for entry in last_12_months_data:
                # Skip the current month's data
                if entry['date'][:7] == current_month_year:
                    continue
                
                category_totals_12_months[entry['category']].add(float(entry['totalAmount']))

            # Convert the sets to lists for easier serialization to JSON
            category_totals_12_months = {category: list(total_amounts) for category, total_amounts in category_totals_12_months.items()}

            pred_cat_list =[]
            for category, values in category_totals_12_months.items():
                list_cat = category_totals_12_months[category]
                 
                x = np.arange(1,len(list_cat) + 1).reshape(-1,1)
                y = np.array(list_cat)

                # x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.2,random_state=42)
                 
                model = LinearRegression()

                model.fit(x,y)

                #  mse = mean_squared_error(y_test)
                next_month_number = len(list_cat)+1
                next_month_prediction = model.predict(np.array([[next_month_number]]))
                if next_month_prediction[0] < 0 :
                    next_month_prediction[0] = 0
                
                # pred_cat_list[category] = next_month_prediction
                pred_cat_list.append({'category': category, 'predicted_amount': next_month_prediction[0]})

            pred_cat_list = sorted(pred_cat_list, key=lambda x: x['category'].lower())
            print(pred_cat_list)
            # Include all necessary data in a single variable
            frontend_data = {
                'user_id': session['user_id'],
                'pred_cat_list' : pred_cat_list
            }
            return render_template('predictions.html', **frontend_data)
        
        else:
            # Print an error message if the request was not successful
            print(f"Error fetching API data. Status code: {response.status_code}")
            return render_template('predictions.html', user_id=session['user_id'], total_amount_sum=0, pie_chart_data="[]", transactions=[])

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

# api_url = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/stage1/export/daterange'
@app.route('/exportdata', methods=['GET', 'POST'])
def exportdata():
    if not is_authenticated():
        return redirect(url_for('signin'))
    
    if request.method == 'POST':
        # Get the selected date range from the form
        date_range = request.form.get('dateRange')

        # Initialize payload with date_range
        payload = {'date_range': date_range, 'user_id': session['user_id'], 'user_email' : session['user_email'], 'user_name' : session['user_name']}


        # If the selected date range is 'custom', add start and end dates to the payload
        if date_range == 'custom':
            start_date = request.form.get('startDate')
            end_date = request.form.get('endDate')
            payload['start_date'] = start_date
            payload['end_date'] = end_date
        else:
            # Calculate start and end dates based on the selected option
            end_date = datetime.now().strftime('%Y-%m-%d')  # End date is always today

            if date_range == '1_week':
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            elif date_range == '1_month':
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif date_range == '1_year':
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            else:
                # Handle additional date range options if needed
                start_date = end_date

            payload['start_date'] = start_date
            payload['end_date'] = end_date

        # Make a POST request to your API with the payload
        api_url = 'https://qqhx04wws7.execute-api.us-east-1.amazonaws.com/stage1/export/daterange'
        response = requests.post(api_url, json=payload)

        if response.status_code == 200:
            # Display a success message on the frontend
            flash('Check your mail in some time for the exported data.', 'success')
        else:
            # Display an error message on the frontend
            flash('Error exporting data. Please try again later.', 'error')

    return render_template('exportdata.html', user_id=session['user_id'])

@app.route('/settings')
def settings():
    if not is_authenticated():
        return redirect(url_for('signin'))

    return render_template('settings.html', user_id=session['user_id'], user_name=session['user_name'], user_email=session['user_email'])

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
    
@app.route('/updateUserPreferences', methods=['POST'])
def update_user_preferences():
    # Handle file upload if present
    file_content_base64 = ""
    if 'file' in request.files:
        file = request.files['file']
        file_content_base64 = base64.b64encode(file.read()).decode('utf-8')

    # Get email frequency preference
    email_frequency = request.form.get('emailFrequency')
    user_id = request.form.get('user_id') 

    user_id = request.form.get('user_id') 
    username = request.form.get('username') 
    user_email = request.form.get('user_email') 
    last_email = datetime.now().isoformat() 

    print(user_id)
    print(f'username: {username}')
    print(f'user_email: {user_email}')

    # Prepare the payload for the API Gateway
    payload = json.dumps({
        'user_id': user_id,  # assuming user_id is sent as part of the form data
        'email_frequency': email_frequency,
        'username': username,
        'user_email': user_email,
        'last_email': last_email,
        'file_content': file_content_base64,  # Send the base64 encoded file content
        'filename': file.filename if 'file' in request.files else "",
        'contentType': request.form.get('contentType')
    })

    # Send the request to API Gateway
    response = requests.post(API_GATEWAY_UPDATE_USER_PREF_ENDPOINT, data=payload, headers={'Content-Type': 'application/json'})

    # Handle the response from API Gateway
    if response.status_code == 200:
        # Process was successful, forward the response
        return jsonify(response.json()), 200
    else:
        # There was an error, forward the error message
        return jsonify(response.json()), response.status_code
    
@app.route('/getUserProfilePic/<user_id>')
def get_user_profile_pic(user_id):
    try:
        response = requests.get(API_GATEWAY_GET_PROFILE_PIC_URL_ENDPOINT, params={'user_id': user_id})

        if response.status_code == 200:
            return response.json()  # Return the JSON response from the Lambda function
        else:
            return {'exists': False, 'url': ''}, response.status_code
    except requests.exceptions.RequestException as e:
        return {'message': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port = 5001)
