# bot.py
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60"
CHANNEL_ID = "-1001763041158"
WEBHOOK_URL = "https://telegram-bot-nkal.onrender.com"
WEBHOOK_PATH = f"/{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.message:
        message = update.message.text or ""
        if message.strip():
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"匿名投稿：\n{message}"
            )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=8000,
        webhook_url=WEBHOOK_URL + WEBHOOK_PATH,
    )

if __name__ == "__main__":
    main()