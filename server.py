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

# Initialize OpenAI client with API key

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


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
    print(prompt)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    reply = response.choices[0].message.content
    print(reply)
    return reply

# Send message to Telegram bot
def send_to_telegram(message):
    token = "YOUR_BOT_TOKEN"     # Replace with your actual bot token
    chat_id = "YOUR_CHAT_ID"     # Replace with your actual chat ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

# Handle new screenshot event
def handle_new_screenshot(path):
    try:
        text = extract_text(path)
        if not text.strip():
            return
        reply = ask_chatgpt(text)
        send_to_telegram(reply)
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
