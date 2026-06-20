import os
import requests
from dotenv import load_dotenv

# 1. Load environment variables from the .env file
load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 2. DeepSeek API endpoint for balance inquiries
URL = "https://api.deepseek.com/user/balance"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

print("Querying account balance from the server...")

try:
    # Note: GET requests are typically used for data retrieval
    response = requests.get(URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Parse the returned JSON payload
        is_available = data.get("is_available", False)
        balance_infos = data.get("balance_infos", [])
        
        print("\n✅ [Account Status]:", "Available" if is_available else "Arrears/Unavailable")
        
        # Iterate through the balances of various currencies (usually returns CNY)
        for info in balance_infos:
            currency = info.get("currency")
            total_balance = info.get("total_balance")
            print(f"💰 [Remaining Balance]: {total_balance} {currency}")
            
    else:
        print(f"❌ Query failed, status code: {response.status_code}")
        print(f"Error message: {response.text}")

except Exception as e:
    print(f"Execution error: {e}")

    