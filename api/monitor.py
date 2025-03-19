from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import re
import time

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://www.serv00.com/"
URL2 = "https://www.ct8.pl/"

def get_numbers(url, retries=3, timeout=15):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            span = soup.find("span", class_="button is-large is-flexible")
            if not span:
                raise ValueError(f"無法找到指定的 span 標籤，URL: {url}")
            text = span.get_text(strip=True)
            match = re.search(r"(\d+)\s*/\s*(\d+)", text)
            if not match:
                raise ValueError(f"無法從文本中提取數字，URL: {url}")
            xxxxx = int(match.group(1))
            ooooo = int(match.group(2))
            return xxxxx, ooooo
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise e

def send_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    response.raise_for_status()

@app.route('/')
def monitor():
    try:
        xxxxx, ooooo = get_numbers(URL)
        xx, oo = get_numbers(URL2)
        difference = ooooo - xxxxx
        dif = oo - xx
        send_message(dif)
        if difference > 2:
            message = f"警告：ooooo - xxxxx = {difference} > 2\n當前值：{xxxxx} / {ooooo}"
            send_message(message)
        if dif > 2:
            message = f"警告：oo - xx = {dif} > 2\n當前值：{xx} / {oo}"
            send_message(message)
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
        send_message(error_message)
        return jsonify({"status": "error", "message": str(e)}), 500
