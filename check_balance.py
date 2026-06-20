import os
import requests
from dotenv import load_dotenv

# 1. 打开 .env 保险箱拿到密钥
load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 2.  DeepSeek 专门用来查余额的 API 路径
URL = "https://api.deepseek.com/user/balance"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

print("正在向服务器查询账户余额...")

try:
    # 注意：查数据通常用 GET 请求
    response = requests.get(URL, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # 解析返回的 JSON 数据
        is_available = data.get("is_available", False)
        balance_infos = data.get("balance_infos", [])
        
        print("\n✅ [账户状态]:", "可用" if is_available else "欠费/不可用")
        
        # 遍历各个币种的余额（通常会返回 CNY 人民币余额）
        for info in balance_infos:
            currency = info.get("currency")
            total_balance = info.get("total_balance")
            print(f"💰 [剩余金额]: {total_balance} {currency}")
            
    else:
        print(f"❌ 查询失败，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")

except Exception as e:
    print(f"代码运行出错: {e}")