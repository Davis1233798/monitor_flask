from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_message(message):
    if not TOKEN or not CHAT_ID:
        return False, "TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID 未設置"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": str(message)}
    response = requests.post(url, json=payload)
    if response.ok:
        return True, "訊息發送成功"
    return False, f"Telegram 失敗: {response.status_code} - {response.text}"

@app.route('/')
def monitor():
    success, msg = send_message("測試訊息：端點已觸發")
    return jsonify({"status": "success" if success else "error", "message": msg})
