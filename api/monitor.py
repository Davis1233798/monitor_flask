from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import re
import time
import traceback

app = Flask(__name__)

# 全局變量來追踪服務啟動通知是否已發送
startup_message_sent = False

# 網站配置
URL = "https://www.serv00.com/"
URL2 = "https://www.ct8.pl/"

# Discord配置
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
WEBCRAWLER_DISCORD_WEBHOOK_URL = os.environ.get("WEBCRAWLER_DISCORD_WEBHOOK_URL")

def send_message(message):
    """發送訊息到Discord頻道"""
    # 優先使用專用頻道Webhook
    webhook_url = WEBCRAWLER_DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL
    
    if not webhook_url:
        print("Discord Webhook URL 未設置")
        return False, "Discord Webhook URL 未設置"
    
    payload = {"content": str(message)}
    try:
        response = requests.post(webhook_url, json=payload, timeout=3)  # 減少超時時間
        response.raise_for_status()
        if WEBCRAWLER_DISCORD_WEBHOOK_URL:
            print("訊息已發送至Web爬蟲專用頻道")
        return True, "Discord訊息發送成功"
    except requests.exceptions.RequestException as e:
        error_msg = f"Discord發送失敗: {str(e)}"
        print(error_msg)
        return False, error_msg

def get_numbers(url, retries=2, timeout=3):  # 進一步縮短 timeout 以避免超時
    """獲取網站數字，若失敗則發送錯誤訊息"""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            span = soup.find("span", class_="button is-large is-flexible")
            if not span:
                error_msg = f"無法找到 span 標籤，URL: {url}"
                # 不在此處發送通知，避免延遲
                return 0, 0  # 返回默認值而不是引發錯誤
            text = span.get_text(strip=True)
            match = re.search(r"(\d+)\s*/\s*(\d+)", text)
            if not match:
                error_msg = f"無法從文本中提取數字，URL: {url}"
                # 不在此處發送通知，避免延遲
                return 0, 0  # 返回默認值而不是引發錯誤
            xxxxx = int(match.group(1))
            ooooo = int(match.group(2))
            return xxxxx, ooooo
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(1)  # 縮短重試間隔
                continue
            print(f"請求失敗，URL: {url} - {str(e)}")
            return 0, 0  # 返回默認值而不是引發錯誤

@app.route('/')
def monitor():
    """主監控函數，執行監控邏輯並發送測試訊息"""
    global startup_message_sent
    
    try:
        # 測試Discord是否可用（只在首次執行時發送啟動通知）
        if not startup_message_sent:
            success, msg = send_message("🔍 Web爬蟲監控服務啟動")
            if not success:
                print(f"Discord發送失敗: {msg}")
            startup_message_sent = True
        
        # 使用 try/except 包裝每個可能失敗的操作
        try:
            xxxxx, ooooo = get_numbers(URL)
            xx, oo = get_numbers(URL2)
            
            # 只有在成功獲取數據時才進行比較和發送通知
            if xxxxx > 0 and ooooo > 0 and xx > 0 and oo > 0:
                difference = ooooo - xxxxx
                dif = oo - xx
                
                alert_message = ""
                
                if difference > 2:
                    alert_message += f"警告：ooooo - xxxxx = {difference} > 2\n當前值：{xxxxx} / {ooooo}\n"
                if dif > 2:
                    alert_message += f"警告：oo - xx = {dif} > 2\n當前值：{xx} / {oo}\n"
                
                if alert_message:
                    message = (
                        f"Respority:Davis1233798/monitor.py\n"
                        f"cron-job.org\n"
                        f"網站網址: {URL}\n"
                        f"網站網址: {URL2}\n"
                        f"{URL} 目前可註冊數量: {difference}\n"
                        f"{URL2} 目前可註冊數量: {dif}"
                    )
                    send_message(alert_message + message)
        except Exception as inner_e:
            error_details = traceback.format_exc()
            error_message = f"數據處理錯誤：{str(inner_e)}\n{error_details}"
            print(error_message)
            send_message(error_message)
        
        return jsonify({"status": "success"})
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"監測腳本出現錯誤：{str(e)}\n{error_details}"
        print(error_message)
        try:
            send_message(error_message)
        except Exception as discord_error:
            return jsonify({"status": "error", "message": f"{str(e)} - Discord failed: {str(discord_error)}"}), 500
        return jsonify({"status": "error", "message": str(e)}), 500
