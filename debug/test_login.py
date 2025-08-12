#!/usr/bin/env python3

import requests
import json

def test_login():
    url = "http://127.0.0.1:8000/api/auth/login/json"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("Login successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Login failed: {response.text}")
            
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_login()