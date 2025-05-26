import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60"
CHANNEL_ID = -1001763041158
WEBHOOK_URL = "https://telegram-bot-nkal.onrender.com"

user_last_sent = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()

    if user_id in user_last_sent and now - user_last_sent[user_id] < 10:
        warn = await update.message.reply_text("请勿频繁发送消息")
        await context.bot.delete_message(chat_id=warn.chat_id, message_id=warn.message_id, delay=10)
        return

    user_last_sent[user_id] = now

    if update.message and update.message.text:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=update.message.text)
        sent = await update.message.reply_text("发送成功")
        await context.bot.delete_message(chat_id=sent.chat_id, message_id=sent.message_id, delay=10)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=qingting-1.onrender.com,
    )