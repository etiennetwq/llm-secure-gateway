import os
import requests
from dotenv import load_dotenv

# 1. Load environment variables from the local .env file
load_dotenv()

# 2. Securely retrieve the API Key without hardcoding it
API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello, this is an environment variable reading test."}],
    "temperature": 0.7
}

print("Securely reading local key and dispatching request...")

try:
    response = requests.post(API_URL, headers=headers, json=data)
    
    # Check the HTTP status code; print the raw server error if not 200 (Success)
    if response.status_code != 200:
        print(f"\n❌ [Request rejected by server] Status code: {response.status_code}")
        print(f"Raw server response: {response.text}")
    else:
        ai_reply = response.json()['choices'][0]['message']['content']
        print(f"\n✅ [Validation successful]: {ai_reply}")

except Exception as e:
    print(f"\n❌ [Execution error]: {e}")