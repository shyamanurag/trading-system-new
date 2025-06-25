#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://algoauto-9gx56.ondigitalocean.app"

def main():
    print("Setting up paper trading user...")
    
    # Get existing users
    response = requests.get(f"{BASE_URL}/api/v1/control/users/broker")
    data = response.json()
    users = data.get('users', [])
    
    print(f"Found {len(users)} existing users")
    for user in users:
        user_id = user.get('user_id')
        paper_trading = user.get('paper_trading', 'Unknown')
        print(f"  - {user_id}: Paper Trading = {paper_trading}")
        
        # If not paper trading, delete the user
        if not paper_trading:
            print(f"  Deleting live trading user: {user_id}")
            delete_response = requests.delete(f"{BASE_URL}/api/v1/control/users/broker/{user_id}")
            print(f"  Delete status: {delete_response.status_code}")
    
    # Add paper trading user
    paper_user = {
        "user_id": "PAPER_TRADER_MAIN",
        "name": "Paper Trading Account",
        "broker": "zerodha",
        "api_key": "sylcoq492qz6f7ej",
        "api_secret": "jm3h4iejwnxr4ngmma2qxccpkhevo8sy",
        "client_id": "QSW899",
        "initial_capital": 100000.0,
        "risk_tolerance": "medium",
        "paper_trading": True
    }
    
    print("Adding paper trading user...")
    response = requests.post(f"{BASE_URL}/api/v1/control/users/broker", json=paper_user)
    if response.status_code == 200:
        print("✅ Paper trading user added successfully!")
        result = response.json()
        user_data = result.get('user', {})
        print(f"User ID: {user_data.get('user_id')}")
        print(f"Paper Trading: {user_data.get('paper_trading')}")
        print(f"Capital: ₹{user_data.get('initial_capital'):,.2f}")
    else:
        print(f"❌ Failed to add user: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main() 