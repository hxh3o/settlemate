#!/usr/bin/env python3
"""
Test script for SettleMate Backend API

This script tests the main API endpoints to ensure they're working correctly.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_api_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, json=data, headers=headers)
        
        print(f"{method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"  Error: {response.text}")
        else:
            try:
                json_response = response.json()
                print(f"  Response: {json.dumps(json_response, indent=2)[:200]}...")
            except:
                print(f"  Response: {response.text[:200]}...")
        
        return response
        
    except requests.exceptions.ConnectionError:
        print(f"{method} {endpoint} - Connection Error: Server not running")
        return None
    except Exception as e:
        print(f"{method} {endpoint} - Error: {str(e)}")
        return None

def main():
    """Run API tests"""
    print("Testing SettleMate Backend API")
    print("=" * 50)
    
    # Test server connection
    print("\n1. Testing server connection...")
    response = test_api_endpoint("/")
    if not response:
        print("Server is not running. Please start the Django server first.")
        print("Run: python manage.py runserver")
        sys.exit(1)
    
    # Test authentication endpoints
    print("\n2. Testing authentication endpoints...")
    
    # Test signup
    signup_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123",
        "password_confirm": "testpassword123"
    }
    signup_response = test_api_endpoint("/signup/", "POST", signup_data)
    
    # Test login
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    login_response = test_api_endpoint("/login/", "POST", login_data)
    
    # Extract auth token if login successful
    auth_token = None
    if login_response and login_response.status_code == 200:
        try:
            login_data = login_response.json()
            if login_data.get('success'):
                auth_token = login_data.get('authToken')
                print(f"  Auth token received: {auth_token[:20]}...")
        except:
            pass
    
    # Test authenticated endpoints
    if auth_token:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        print("\n3. Testing authenticated endpoints...")
        
        # Test get user data
        test_api_endpoint("/getUserData/", "GET", headers=headers)
        
        # Test create trip
        trip_data = {
            "name": "Test Trip",
            "description": "A test trip for API testing"
        }
        trip_response = test_api_endpoint("/createtrip/", "POST", trip_data, headers)
        
        # Test get trips data
        test_api_endpoint("/getTripsData/", "GET", headers=headers)
        
        # Test logout
        test_api_endpoint("/logout/", "POST", headers=headers)
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    main()
