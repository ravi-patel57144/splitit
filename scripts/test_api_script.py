#!/usr/bin/env python3
"""
Test script to demonstrate the Split It API functionality
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_api():
    """Test the Split It API functionality"""
    
    # Test data
    test_users = [
        {"username": "alice", "password": "testpass123"},
        {"username": "bob", "password": "testpass123"},
        {"username": "charlie", "password": "testpass123"}
    ]
    
    # Create test users
    print("Creating test users...")
    for user_data in test_users:
        try:
            response = requests.post(f"{BASE_URL}/auth/token/", json=user_data)
            if response.status_code == 200:
                print(f"✓ User {user_data['username']} authenticated successfully")
            else:
                print(f"✗ Failed to authenticate user {user_data['username']}: {response.text}")
        except requests.exceptions.ConnectionError:
            print("✗ Could not connect to the API. Make sure the server is running.")
            return
    
    # Get token for alice
    response = requests.post(f"{BASE_URL}/auth/token/", json=test_users[0])
    if response.status_code != 200:
        print("✗ Failed to get authentication token")
        return
    
    token = response.json()['access']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*50)
    print("TESTING SPLIT IT API FUNCTIONALITY")
    print("="*50)
    
    # 1. Create an occasion
    print("\n1. Creating an occasion...")
    occasion_data = {
        "name": "Weekend Trip",
        "description": "Splitting expenses for a weekend trip"
    }
    response = requests.post(f"{BASE_URL}/occasions/", json=occasion_data, headers=headers)
    if response.status_code == 201:
        occasion = response.json()
        print(f"✓ Created occasion: {occasion['name']} (ID: {occasion['id']})")
    else:
        print(f"✗ Failed to create occasion: {response.text}")
        return
    
    # 2. Create an event
    print("\n2. Creating an event...")
    event_data = {
        "name": "Dinner",
        "description": "Group dinner at restaurant",
        "occasion": occasion['id']
    }
    response = requests.post(f"{BASE_URL}/events/", json=event_data, headers=headers)
    if response.status_code == 201:
        event = response.json()
        print(f"✓ Created event: {event['name']} (ID: {event['id']})")
    else:
        print(f"✗ Failed to create event: {response.text}")
        return
    
    # 3. Create an expenditure with equal split
    print("\n3. Creating an expenditure with equal split...")
    expenditure_data = {
        "event": event['id'],
        "amount": "120.00",
        "description": "Restaurant bill",
        "split_type": "equal",
        "split_user_ids": [2, 3]  # Assuming bob and charlie have IDs 2 and 3
    }
    response = requests.post(f"{BASE_URL}/expenditures/", json=expenditure_data, headers=headers)
    if response.status_code == 201:
        expenditure = response.json()
        print(f"✓ Created expenditure: {expenditure['description']} - ${expenditure['amount']}")
        print(f"  Split equally among users: {expenditure_data['split_user_ids']}")
    else:
        print(f"✗ Failed to create expenditure: {response.text}")
        return
    
    # 4. Create an expenditure with custom split
    print("\n4. Creating an expenditure with custom split...")
    custom_expenditure_data = {
        "event": event['id'],
        "amount": "100.00",
        "description": "Hotel room",
        "split_type": "custom",
        "split_user_ids": [2, 3],
        "custom_amounts": ["60.00", "40.00"]
    }
    response = requests.post(f"{BASE_URL}/expenditures/", json=custom_expenditure_data, headers=headers)
    if response.status_code == 201:
        custom_expenditure = response.json()
        print(f"✓ Created custom expenditure: {custom_expenditure['description']} - ${custom_expenditure['amount']}")
        print(f"  Custom split: ${custom_expenditure_data['custom_amounts'][0]} and ${custom_expenditure_data['custom_amounts'][1]}")
    else:
        print(f"✗ Failed to create custom expenditure: {response.text}")
        return
    
    # 5. Get user balance
    print("\n5. Getting user balance...")
    response = requests.get(f"{BASE_URL}/user/balance/", headers=headers)
    if response.status_code == 200:
        balance = response.json()
        print(f"✓ User balance:")
        print(f"  Total owed: ${balance['total_owed']}")
        print(f"  Total owes: ${balance['total_owes']}")
        print(f"  Balance: ${balance['balance']}")
    else:
        print(f"✗ Failed to get user balance: {response.text}")
    
    # 6. Get occasion summary
    print("\n6. Getting occasion summary...")
    response = requests.get(f"{BASE_URL}/occasions/{occasion['id']}/summary/", headers=headers)
    if response.status_code == 200:
        summary = response.json()
        print(f"✓ Occasion summary:")
        print(f"  Total expenditures: ${summary['total_expenditures']}")
        print(f"  Total events: {summary['total_events']}")
        print(f"  Users involved: {len(summary['user_balances'])}")
    else:
        print(f"✗ Failed to get occasion summary: {response.text}")
    
    # 7. Create a payment
    print("\n7. Creating a payment...")
    payment_data = {
        "to_user_id": 2,  # Assuming bob has ID 2
        "amount": "40.00",
        "description": "Settlement payment"
    }
    response = requests.post(f"{BASE_URL}/payments/", json=payment_data, headers=headers)
    if response.status_code == 201:
        payment = response.json()
        print(f"✓ Created payment: ${payment['amount']} to user {payment['to_user_id']}")
    else:
        print(f"✗ Failed to create payment: {response.text}")
    
    print("\n" + "="*50)
    print("API TEST COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nYou can now:")
    print("1. Visit http://localhost:8000/api/docs/ for interactive API documentation")
    print("2. Visit http://localhost:8000/admin/ to manage data through Django admin")
    print("3. Use the API endpoints to create and manage expenses")

if __name__ == "__main__":
    test_api()
