"""
register_webhook.py
====================
Run this ONCE after deploying to Render to tell Telegram
where to send updates.

Usage:
    python register_webhook.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
RENDER_URL  = "https://sportsbetai-f2tw.onrender.com"
WEBHOOK_URL = f"{RENDER_URL}/api/webhook/telegram/"

def register():
    url      = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.post(url, json={"url": WEBHOOK_URL})
    data     = response.json()

    if data.get("ok"):
        print(f"✅ Webhook registered: {WEBHOOK_URL}")
    else:
        print(f"❌ Failed: {data}")

def check():
    url      = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    data     = response.json()
    print(f"\nCurrent webhook info:\n{data.get('result', data)}")

if __name__ == "__main__":
    register()
    check()