import logging
import pytesseract
import cv2
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from PIL import Image
import numpy as np
from io import BytesIO
import requests

# === OCR path ===
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# === Telegram Bot Token ===
TELEGRAM_BOT_TOKEN = '7587424532:AAH-cJARPkwvW2K3zl4k_he5LZo_M4ih62w'

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === OCR Function ===
def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
    text = pytesseract.image_to_string(enhanced, lang='eng')
    return text

# === Forex Logic ===
def analyze_news(text):
    lines = text.split('\n')
    news_events = []
    suggested_pairs = set()

    for line in lines:
        line = line.strip()
        if not line or len(line) < 6:
            continue
        if 'AUD' in line:
            news_events.append(f"🇦🇺 AUD - {line}")
            suggested_pairs.update(["AUDUSD", "AUDJPY", "EURAUD"])
        elif 'USD' in line:
            news_events.append(f"🇺🇸 USD - {line}")
            suggested_pairs.update(["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "XAUUSD"])
        elif 'EUR' in line:
            news_events.append(f"🇪🇺 EUR - {line}")
            suggested_pairs.update(["EURUSD", "EURJPY", "EURGBP"])
        elif 'GBP' in line:
            news_events.append(f"🇬🇧 GBP - {line}")
            suggested_pairs.update(["GBPUSD", "GBPJPY", "EURGBP"])
        elif 'JPY' in line:
            news_events.append(f"🇯🇵 JPY - {line}")
            suggested_pairs.update(["USDJPY", "EURJPY", "GBPJPY"])
        elif 'CAD' in line:
            news_events.append(f"🇨🇦 CAD - {line}")
            suggested_pairs.update(["USDCAD", "CADJPY"])

    if not news_events:
        return "❌ No recognizable events found in the screenshot."

    summary = "📊 **News Events Detected**\n\n"
    for event in news_events:
        summary += f"🔹 {event}\n"

    summary += "\n📈 **Suggested Pairs to Watch:**\n"
    for pair in sorted(suggested_pairs):
        summary += f"⭐ {pair}\n"

    return summary

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send me a Forex Factory screenshot and I’ll extract the news and suggest pairs.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Received image from user {user.id}")

    photo_file = await update.message.photo[-1].get_file()
    image_bytes = await photo_file.download_as_bytearray()

    image_path = "received_screenshot.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    logger.info("Saved the received image as 'received_screenshot.png'")
    try:
        text = extract_text_from_image(image_path)
        logger.info("OCR Extracted Text:\n" + text)
        summary = analyze_news(text)
        await update.message.reply_text(summary)
    except Exception as e:
        logger.exception("OCR failed")
        await update.message.reply_text("❌ Sorry, I couldn’t read the image properly. Please try a clearer screenshot.")

# === Main Bot ===
def main():
    logger.info("🤖 Bot is running...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    scheduler = AsyncIOScheduler()
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()
