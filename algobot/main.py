import requests
import hmac
import json
import base64
import hashlib
import datetime, time
import calendar
from twilio.rest import Client
from dotenv import load_dotenv
import os

now = datetime.datetime.now()
day = calendar.day_name[now.weekday()]

base_url = "https://api.gemini.com"
endpoint = "/v1/order/new"
url = base_url + endpoint

load_dotenv()
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
MY_NUMBER = os.getenv("MY_NUMBER")
gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_api_secret = os.getenv("GEMINI_SECRET").encode()

t = datetime.datetime.now()
payload_nonce = str(int(time.mktime(t.timetuple())*1000))


def buyBTC():
    # get current price and buy specific amount in usd
    base_url = "https://api.gemini.com/v2"
    response = requests.get(base_url + "/ticker/btcusd")
    btc_data = response.json()
    # round to 8 because BTC breaks to 8 decimals
    amount = round(4.98 / float(btc_data['close']), 8)

    payload = {
       "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": "btcgusd",
        "amount": amount,
        "price": "100000",
        "side": "buy",
        "type": "exchange limit",
        "options": ["immediate-or-cancel"]
    }

    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

    request_headers = {'Content-Type': "text/plain",
                        'Content-Length': "0",
                        'X-GEMINI-APIKEY': gemini_api_key,
                        'X-GEMINI-PAYLOAD': b64,
                        'X-GEMINI-SIGNATURE': signature,
                        'Cache-Control': "no-cache"}

    response = requests.post(url, data=None, headers=request_headers)

    new_order = response.json()
    print(new_order)
    price = round(float(new_order['avg_execution_price']) * float(new_order['executed_amount']), 2)

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    message = client.messages \
        .create(
        body=f"Bought {new_order['executed_amount']} {new_order['symbol'].replace('gusd', '').upper()} "
             f"at ${new_order['avg_execution_price']} for ${price} \n"
             f"Order id: {new_order['order_id']}",
        from_=TWILIO_NUMBER,
        to=MY_NUMBER
    )

    print(message.status)


def lambda_handler(event, context):
    buyBTC()
    return {
        'statusCode': 200,
        'body': json.dumps('End of script')
    }

buyBTC()