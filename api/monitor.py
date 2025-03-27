from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import re
import time

app = Flask(__name__)

# 從環境變數獲取 Telegram 配置
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://www.serv00.com/"
URL2 = "https://www.ct8.pl/"

# Discord配置
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
WEBCRAWLER_DISCORD_WEBHOOK_URL = os.environ.get("WEBCRAWLER_DISCORD_WEBHOOK_URL")

def send_discord_message(message):
    """發送訊息到Discord頻道"""
    # 優先使用專用頻道Webhook
    webhook_url = WEBCRAWLER_DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL
    
    if not webhook_url:
        print("Discord Webhook URL 未設置")
        return False, "Discord Webhook URL 未設置"
    
    payload = {"content": str(message)}
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        if WEBCRAWLER_DISCORD_WEBHOOK_URL:
            print("訊息已發送至Web爬蟲專用頻道")
        return True, "Discord訊息發送成功"
    except requests.exceptions.RequestException as e:
        error_msg = f"Discord發送失敗: {str(e)}"
        print(error_msg)
        return False, error_msg

def send_message(message):
    """發送訊息到 Telegram，若失敗則拋出異常"""
    if not TOKEN or not CHAT_ID:
        raise ValueError("TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID 未設置")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": str(message)}  # 確保 message 是字串
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        # 嘗試也發送到Discord
        send_discord_message(message)
        return True, "訊息發送成功"
    except requests.exceptions.RequestException as e:
        error_msg = f"Telegram 發送失敗: {str(e)}"
        # 嘗試發送到Discord作為備用
        discord_success, _ = send_discord_message(message)
        if not discord_success:
            raise Exception(error_msg)
        return discord_success, "Telegram失敗但Discord發送成功"

def get_numbers(url, retries=3, timeout=5):  # 縮短 timeout 以避免超時
    """獲取網站數字，若失敗則發送錯誤訊息到 Telegram"""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            span = soup.find("span", class_="button is-large is-flexible")
            if not span:
                error_msg = f"無法找到 span 標籤，URL: {url}"
                send_message(error_msg)
                raise ValueError(error_msg)
            text = span.get_text(strip=True)
            match = re.search(r"(\d+)\s*/\s*(\d+)", text)
            if not match:
                error_msg = f"無法從文本中提取數字，URL: {url}"
                send_message(error_msg)
                raise ValueError(error_msg)
            xxxxx = int(match.group(1))
            ooooo = int(match.group(2))
            return xxxxx, ooooo
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            error_msg = f"請求失敗，URL: {url} - {str(e)}"
            send_message(error_msg)
            raise Exception(error_msg)

@app.route('/')
def monitor():
    """主監控函數，執行監控邏輯並發送測試訊息"""
    try:
        # 測試Discord是否可用
        discord_success, discord_msg = send_discord_message("🔍 Web爬蟲監控服務啟動")
        if not discord_success:
            print(f"Discord發送失敗: {discord_msg}")

        xxxxx, ooooo = get_numbers(URL)
        xx, oo = get_numbers(URL2)
        difference = ooooo - xxxxx
        dif = oo - xx

        if difference > 2:
            send_message(f"警告：ooooo - xxxxx = {difference} > 2\n當前值：{xxxxx} / {ooooo}")
        if dif > 2:
            send_message(f"警告：oo - xx = {dif} > 2\n當前值：{xx} / {oo}")
        if difference > 2 or dif > 2:
            message = (
                f"Respority:Davis1233798/monitor.py\n"
                f"cron-job.org\n"
                f"網站網址: {URL}\n"
                f"網站網址: {URL2}\n"
                f"{URL} 目前可註冊數量: {difference}\n"
                f"{URL2} 目前可註冊數量: {dif}"
            )
            send_message(message)
        return jsonify({"status": "success"})
    except Exception as e:
        error_message = f"監測腳本出現錯誤：{str(e)}"
        try:
            send_message(error_message)
        except Exception as telegram_error:
            # 如果Telegram也失敗，嘗試發送到Discord
            try:
                send_discord_message(f"監測腳本錯誤: {str(e)} - Telegram失敗: {str(telegram_error)}")
            except:
                pass
            return jsonify({"status": "error", "message": f"{str(e)} - Telegram failed: {str(telegram_error)}"}), 500
        return jsonify({"status": "error", "message": str(e)}), 500
