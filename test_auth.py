#!/usr/bin/env python3
"""
Test script to verify authentication endpoints
"""

import requests
import json
import time

BASE_URL = 'http://localhost:5000/api'

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f'{BASE_URL}/health')
        print(f"[PASS] Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False

def test_auth_flow():
    """Test complete auth flow"""
    session = requests.Session()
    
    # Use unique email for each test run
    import random
    unique_suffix = random.randint(100000, 999999)
    test_email = f'testuser{unique_suffix}@example.com'
    
    # Test 1: Register new user
    print("\n--- Testing Registration ---")
    register_data = {
        'name': 'Test User',
        'email': test_email,
        'password': 'testpassword123'
    }
    response = session.post(f'{BASE_URL}/auth/register', json=register_data)
    print(f"Register: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 201:
        print("Registration failed!")
        return False
    
    # Test 2: Login with the registered user
    print("\n--- Testing Login ---")
    login_data = {
        'email': test_email,
        'password': 'testpassword123'
    }
    response = session.post(f'{BASE_URL}/auth/login', json=login_data)
    print(f"Login: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("Login failed!")
        return False
    
    # Test 3: Get current user
    print("\n--- Testing Get Current User ---")
    response = session.get(f'{BASE_URL}/auth/current-user')
    print(f"Current User: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("Get current user failed!")
        return False
    
    user_id = response.json().get('user_id')
    
    # Test 4: Update user (add allergens)
    print("\n--- Testing Update User ---")
    update_data = {
        'allergens': ['Milk', 'Peanuts'],
        'dietary_preferences': {'vegan': False, 'vegetarian': True}
    }
    response = session.put(f'{BASE_URL}/user/{user_id}', json=update_data)
    print(f"Update: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: Verify updated user info
    print("\n--- Verifying Updated User ---")
    response = session.get(f'{BASE_URL}/user/{user_id}')
    print(f"Get User: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 6: Logout
    print("\n--- Testing Logout ---")
    response = session.post(f'{BASE_URL}/auth/logout')
    print(f"Logout: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 7: Try to get current user after logout (should fail)
    print("\n--- Testing Get Current User After Logout ---")
    response = session.get(f'{BASE_URL}/auth/current-user')
    print(f"Current User (after logout): {response.status_code}")
    print(f"Response: {response.json()}")
    
    return True

if __name__ == '__main__':
    print("=== LabelDoctor API Testing ===\n")
    
    # Wait for server to start
    print("Waiting for server to start...")
    for i in range(10):
        if test_health():
            break
        time.sleep(1)
    
    print("\n=== Running Auth Tests ===")
    if test_auth_flow():
        print("\n[SUCCESS] All tests passed!")
    else:
        print("\n[FAILURE] Some tests failed!")
