from flask import Flask, render_template, request
import requests
from msal import ConfidentialClientApplication
import datetime
import os
from decouple import config

app = Flask(__name__)


client_id = config("client_id")
client_secret = config("client_secret")
tenant_id = config("tenant_id")
allowed_ObjectIDs = config("allowed_ObjectIDs")


scopes = ['https://graph.microsoft.com/.default']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        from_date = request.form['fromDateTime']
        to_date = request.form['toDateTime']

        app = ConfidentialClientApplication(
            client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )

        result = app.acquire_token_silent(scopes, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=scopes)

        if 'access_token' in result:
            access_token = result['access_token']

            graph_url = 'https://graph.microsoft.com/v1.0'
            endpoint = f'/communications/callRecords/getDirectRoutingCalls(fromDateTime={from_date},toDateTime={to_date})'
            url = f"{graph_url}{endpoint}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                pstn_usage = response.json()

                # Filter the data based on the allowed UPNs
                filtered_pstn_usage = [record for record in pstn_usage.get('value', []) if record.get('userId') in allowed_ObjectIDs]

                return render_template('index.html', pstn_usage=filtered_pstn_usage)
            else:
                error_message = f"Error: {response.status_code} - {response.text}"
                return render_template('index.html', error_message=error_message)
        else:
            return render_template('index.html', error_message=f"Authentication error: {result.get('error')}")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)