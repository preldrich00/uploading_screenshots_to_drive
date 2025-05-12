# screenshot_watcher.py

import os
import time
import threading
import requests
import pytesseract
from dotenv import load_dotenv


from datetime import datetime
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
token_viv = os.getenv("token_viv")
chat_id_viv = os.getenv("chat_id_viv")
token_shu = os.getenv("token_shu")
chat_id_shu = os.getenv("chat_id_shu")

client = OpenAI(api_key=api_key)


# Paths and timestamps
SCREENSHOT_DIR = os.path.expanduser("~/Pictures/Screenshots")
LOG_FILE = os.path.expanduser("~/screenshot_log.txt")
start_time = time.time()

# OCR: Extract text from image
def extract_text(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

# Query ChatGPT with the extracted text
def ask_chatgpt(prompt):
    prompt = prompt + " please answer this question? give me the specific option like 1st 2nd 3rd or 4th"
    print(prompt)
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    reply = response.choices[0].message.content
    print("start reply",reply)
    return reply

# Send message to Telegram bot
def send_response_to_telegram(message):
    token = "7408438455:AAFiJ9BWHYUCh_QHl6pZfQBt-dPp_cDpmd4"     
    chat_id = "6237825469"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

def send_image_to_telegram(path):

    bots = [
        {"token": token_viv, "chat_id": chat_id_viv},
        {"token": token_shu, "chat_id": chat_id_shu},
    ]

    for bot in bots:
        url = f"https://api.telegram.org/bot{bot['token']}/sendPhoto"
        with open(path, "rb") as image_file:
            files = {"photo": image_file}
            data = {"chat_id": bot["chat_id"]}
            response = requests.post(url, files=files, data=data)
            print(f"Sent to {bot['chat_id']}: {response.status_code} {response.json()}")



# Handle new screenshot event
def handle_new_screenshot(path):
    send_image_to_telegram(path)
    try:
        text = extract_text(path)
        if not text.strip():
            return
        reply = ask_chatgpt(text)
        send_response_to_telegram(reply)
    except Exception as e:
        error_log = f"[{datetime.now().isoformat()}] Error: {e}\n"
        with open(LOG_FILE, "a") as f:
            f.write(error_log)

# Event handler
class ScreenshotHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.png', '.jpg')):
            ctime = os.path.getctime(event.src_path)
            if ctime >= start_time:
                log_entry = f"[{datetime.now().isoformat()}] Detected screenshot: {event.src_path}\n"
                handle_new_screenshot(event.src_path)
                with open(LOG_FILE, "a") as f:
                    f.write(log_entry)

# Main loop
if __name__ == "__main__":
    observer = Observer()
    event_handler = ScreenshotHandler()
    observer.schedule(event_handler, path=SCREENSHOT_DIR, recursive=False)
    observer.start()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] Screenshot watcher started\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
