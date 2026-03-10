
import sys
import os
import requests
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.secrets import KIS_AUTH
except ImportError:
    print("config/secrets.py not found.")
    sys.exit(1)

def test_token():
    base_url = KIS_AUTH.get("URL_BASE")
    app_key = KIS_AUTH.get("APP_KEY")
    app_secret = KIS_AUTH.get("APP_SECRET")
    
    print(f"URL_BASE: {base_url}")
    print(f"APP_KEY: {app_key[:5]}... (masked)")
    
    url = f"{base_url}/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }
    
    try:
        print(f"Requesting token from {url}...")
        res = requests.post(url, json=body)
        print(f"Status Code: {res.status_code}")
        if res.status_code != 200:
            print(f"Response: {res.text}")
        else:
            print("Token generation successful!")
            print(f"Token: {res.json()['access_token'][:10]}...")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_token()
