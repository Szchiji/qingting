import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Bot Token 和频道 ID
BOT_TOKEN = "8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60"
CHANNEL_ID = "-1001763041158"

# Webhook 设置
WEBHOOK_URL = "https://telegram-bot-nkal.onrender.com"  # 替换为你的实际 Render 地址
WEBHOOK_PATH = f"/{BOT_TOKEN}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.effective_user:
        # 构造匿名消息内容
        message = update.message
        text = message.text or ""
        caption = message.caption or ""

        # 文本消息
        if text:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=f"匿名投稿：\n{text}")

        # 图片、视频、语音等媒体消息
        elif message.photo:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id, caption=f"匿名投稿：\n{caption}")
        elif message.video:
            await context.bot.send_video(chat_id=CHANNEL_ID, video=message.video.file_id, caption=f"匿名投稿：\n{caption}")
        elif message.voice:
            await context.bot.send_voice(chat_id=CHANNEL_ID, voice=message.voice.file_id, caption=f"匿名投稿：\n{caption}")
        elif message.document:
            await context.bot.send_document(chat_id=CHANNEL_ID, document=message.document.file_id, caption=f"匿名投稿：\n{caption}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 处理所有消息
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # 设置 webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL + WEBHOOK_PATH
    )

if __name__ == "__main__":
    main()