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

# 初始化標誌，確保首次部署時發送測試訊息
INITIALIZED = False

def send_message(message):
    """發送訊息到 Telegram，若失敗則拋出異常"""
    if not TOKEN or not CHAT_ID:
        raise ValueError("TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID 未設置")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": str(message)}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True, "訊息發送成功"
    except requests.exceptions.RequestException as e:
        error_msg = f"Telegram 發送失敗: {str(e)}"
        raise Exception(error_msg)

def get_numbers(url, retries=3, timeout=15):
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
    """主監控函數，首次部署發送測試訊息，並執行監控邏輯"""
    global INITIALIZED
    try:
        # 首次部署發送測試訊息
        if not INITIALIZED:
            success, msg = send_message("測試訊息：程式碼已成功部署到 Vercel！")
            INITIALIZED = True

        xxxxx, ooooo = get_numbers(URL)
        xx, oo = get_numbers(URL2)
        difference = ooooo - xxxxx
        dif = oo - xx

        # 測試模式：發送 dif 值
        success, msg = send_message(f"Test mode: dif = {dif}")

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
        try:
            send_message(error_message)
        except Exception as telegram_error:
            return jsonify({"status": "error", "message": f"{str(e)} - Telegram failed: {str(telegram_error)}"}), 500
        return jsonify({"status": "error", "message": str(e)}), 500

# 啟動時運行測試（可選，若 Vercel 不允許啟動時執行則移除）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
