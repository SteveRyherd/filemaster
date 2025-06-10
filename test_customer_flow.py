#!/usr/bin/env python3
"""Quick test script to create a request and test the customer interface."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_customer_flow():
    # 1. Create a request
    print("Creating request...")
    response = requests.post(f"{BASE_URL}/requests", 
                           json={"nickname": "Test Customer - 2025 Camry", "expires_days": 7})
    request = response.json()
    print(f"Request created with ID: {request['id']}, Token: {request['token']}")
    
    # 2. Add SSN module
    print("\nAdding SSN module...")
    response = requests.post(f"{BASE_URL}/requests/{request['id']}/modules",
                           json={"kind": "ssn", "label": "Social Security Number"})
    module = response.json()
    print(f"SSN module added with ID: {module['id']}")
    
    # 3. Print customer URL
    customer_url = f"{BASE_URL}/customer?token={request['token']}"
    print("\n" + "="*60)
    print("SUCCESS! Request created successfully")
    print("="*60)
    print(f"\nCUSTOMER URL (copy and share this):\n")
    print(f"  {customer_url}")
    print("\n" + "="*60)
    print("\nWhat to do next:")
    print("1. Copy the URL above")
    print("2. Open it in your browser to see the customer experience")
    print("3. Or share it with a customer via email/SMS")
    print("\n" + "="*60)
    
    # 4. Test direct submission
    print("\nTesting direct API submission...")
    response = requests.post(f"{BASE_URL}/modules/{module['id']}/submit",
                           json={"ssn": "123-45-6789"})
    if response.status_code == 200:
        print("✓ SSN submitted successfully!")
        print(f"Module status: {response.json()}")
    else:
        print(f"✗ Error: {response.text}")

if __name__ == "__main__":
    test_customer_flow()
