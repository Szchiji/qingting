import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # 如：-1001763041158
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # 管理员用户ID，如：7848870377
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # 如：https://your-domain.com
PORT = int(os.getenv("PORT", 10000))

# 存储 /start 消息内容
START_TEXT_FILE = "start_text.json"
if os.path.exists(START_TEXT_FILE):
    with open(START_TEXT_FILE, "r") as f:
        START_TEXT = json.load(f).get("text", "欢迎使用本机器人，发送消息即可匿名投稿。")
else:
    START_TEXT = "欢迎使用本机器人，发送消息即可匿名投稿。"

# 消息限流数据
user_message_times = defaultdict(list)
HOURLY_LIMIT = 60
DAILY_LIMIT = 500

# 多媒体组缓存
media_group_cache = {}

def save_start_text(text):
    with open(START_TEXT_FILE, "w") as f:
        json.dump({"text": text}, f)

def is_allowed(user_id):
    now = datetime.now()
    timestamps = user_message_times[user_id]
    timestamps = [t for t in timestamps if now - t < timedelta(days=1)]
    user_message_times[user_id] = timestamps

    hourly_count = len([t for t in timestamps if now - t < timedelta(hours=1)])
    daily_count = len(timestamps)

    if hourly_count >= HOURLY_LIMIT or daily_count >= DAILY_LIMIT:
        return False
    timestamps.append(now)
    return True

async def delete_after_delay(msg, delay=10):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)

async def set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    new_text = " ".join(context.args)
    if new_text:
        global START_TEXT
        START_TEXT = new_text
        save_start_text(new_text)
        msg = await update.message.reply_text("Start 信息已更新")
        await delete_after_delay(msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        msg = await update.message.reply_text("您发送太频繁，请稍后再试。")
        await delete_after_delay(msg)
        return
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=update.message.text)
        msg = await update.message.reply_text("发送成功！")
    except Exception:
        msg = await update.message.reply_text("发送失败，请稍后再试。")
    await delete_after_delay(msg)

async def handle_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    if not is_allowed(user_id):
        msg = await message.reply_text("您发送太频繁，请稍后再试。")
        await delete_after_delay(msg)
        return

    group_id = message.media_group_id
    if group_id not in media_group_cache:
        media_group_cache[group_id] = []

    media_group_cache[group_id].append(message)

    # 等待 1 秒确认一组已完成
    await asyncio.sleep(1)

    if group_id in media_group_cache:
        messages = media_group_cache.pop(group_id)
        media = []
        for msg in messages:
            if msg.photo:
                file = msg.photo[-1].file_id
                media.append(InputMediaPhoto(media=file, caption=msg.caption if len(media) == 0 else None))
            elif msg.video:
                file = msg.video.file_id
                media.append(InputMediaVideo(media=file, caption=msg.caption if len(media) == 0 else None))

        try:
            await context.bot.send_media_group(chat_id=CHANNEL_ID, media=media)
            res = await message.reply_text("发送成功！")
        except Exception:
            res = await message.reply_text("发送失败，请稍后再试。")
        await delete_after_delay(res)

async def handle_photo_or_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.media_group_id:
        await handle_media_group(update, context)
        return

    user_id = update.effective_user.id
    if not is_allowed(user_id):
        msg = await update.message.reply_text("您发送太频繁，请稍后再试。")
        await delete_after_delay(msg)
        return

    caption = update.message.caption
    file = update.message.photo[-1].file_id if update.message.photo else update.message.video.file_id
    media = InputMediaPhoto(media=file, caption=caption) if update.message.photo else InputMediaVideo(media=file, caption=caption)

    try:
        await context.bot.send_media_group(chat_id=CHANNEL_ID, media=[media])
        msg = await update.message.reply_text("发送成功！")
    except Exception:
        msg = await update.message.reply_text("发送失败，请稍后再试。")
    await delete_after_delay(msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setstart", set_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_photo_or_video))

    print(f"设置Webhook地址: {WEBHOOK_URL}/{BOT_TOKEN}, 监听端口: {PORT}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()