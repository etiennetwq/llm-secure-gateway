import os
import requests
from dotenv import load_dotenv

# 1. 打开同目录下的 .env 保险柜，加载环境变量
load_dotenv()

# 2. 安全地取出 API Key，代码里再也看不到密钥明文了！
API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好，这是一次环境变量读取测试。"}],
    "temperature": 0.7
}

print("正在安全读取本地密钥并发送请求...")

try:
    response = requests.post(API_URL, headers=headers, json=data)
    
    # 我们先检查一下 HTTP 状态码，如果不是 200 (成功)，就直接打印服务器的真实报错
    if response.status_code != 200:
        print(f"\n❌ [请求被服务器拒绝] 状态码: {response.status_code}")
        print(f"服务器真实返回信息: {response.text}")
    else:
        ai_reply = response.json()['choices'][0]['message']['content']
        print(f"\n✅ [验证成功]: {ai_reply}")

except Exception as e:
    print(f"\n❌ [代码执行报错]: {e}")