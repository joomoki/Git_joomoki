
import sys
import os
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web.main import app

def test_endpoints():
    with TestClient(app) as client:
        print("Testing / (Redirect) ...")
        response = client.get("/", follow_redirects=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 307:
            print(f"Redirects to: {response.headers.get('location')}")
        else:
            print(f"Expected 307, got {response.status_code}")
            print(response.text)

        print("\nTesting /market ...")
        try:
            response = client.get("/market?page=2&sort=per")
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(response.text)
        except Exception as e:
            print(f"Error testing /market: {e}")

        stock_code = "005930" # Samsung Electronics
        print(f"\nTesting /stock/{stock_code} ...")
        try:
            response = client.get(f"/stock/{stock_code}")
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(response.text)
        except Exception as e:
            print(f"Error testing /stock/{stock_code}: {e}")

        print("\nTesting /api/screener ...")
        try:
            payload = {"trend": "UP", "min_market_cap": 10000}
            response = client.post("/api/screener", json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(response.text)
            else:
                data = response.json()
                print(f"Returned {len(data)} items")
        except Exception as e:
            print(f"Error testing /api/screener: {e}")

if __name__ == "__main__":
    test_endpoints()
