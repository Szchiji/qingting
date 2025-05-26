import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# 日志设置
logging.basicConfig(level=logging.INFO)

# 读取环境变量
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "10000"))

# 限流设置
HOURLY_LIMIT = 60
DAILY_LIMIT = 500

# 限流记录
user_message_times = defaultdict(list)

# /start 消息存储
START_MESSAGE_FILE = "start_message.json"
if not os.path.exists(START_MESSAGE_FILE):
    with open(START_MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump({"text": "欢迎使用匿名投稿机器人"}, f, ensure_ascii=False)

def get_start_message():
    with open(START_MESSAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("text", "欢迎使用匿名投稿机器人")

def set_start_message(text):
    with open(START_MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump({"text": text}, f, ensure_ascii=False)

# 缓存同一用户的媒体组合（照片、视频）内容
user_media_cache = defaultdict(list)
user_media_timer = {}

# 限流检查
def check_rate_limit(user_id):
    now = datetime.utcnow()
    hourly = [t for t in user_message_times[user_id] if now - t < timedelta(hours=1)]
    daily = [t for t in user_message_times[user_id] if now - t < timedelta(days=1)]
    user_message_times[user_id] = daily  # 清理过期记录

    if len(hourly) >= HOURLY_LIMIT:
        return False, "您发送太频繁了，请稍后再试（每小时限 60 条）"
    if len(daily) >= DAILY_LIMIT:
        return False, "您今日已达上限，请明天再试（每天限 500 条）"

    user_message_times[user_id].append(now)
    return True, ""

# 自动删除反馈消息
async def auto_delete(msg, seconds=10):
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass

# 修改 /start 显示内容（管理员）
async def set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("请提供新消息内容")
        return
    set_start_message(text)
    await update.message.reply_text("Start 消息已更新")

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_start_message())

# 核心消息处理
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_allowed, error_msg = check_rate_limit(user_id)
    if not is_allowed:
        sent = await update.message.reply_text(error_msg)
        await auto_delete(sent)
        return

    message = update.message
    media_group_id = message.media_group_id

    # 收集同一组媒体消息
    if media_group_id:
        user_media_cache[media_group_id].append(message)

        if media_group_id not in user_media_timer:
            user_media_timer[media_group_id] = asyncio.create_task(send_combined_media(context, media_group_id))
    else:
        await forward_to_channel(context, [message])

    sent = await update.message.reply_text("发送成功")
    await auto_delete(sent)

# 合并媒体组转发
async def send_combined_media(context, group_id):
    await asyncio.sleep(1.5)
    messages = user_media_cache.pop(group_id, [])
    user_media_timer.pop(group_id, None)

    if not messages:
        return

    media = []
    caption_sent = False

    for msg in messages:
        caption = msg.caption if (not caption_sent and msg.caption) else None
        if msg.photo:
            media.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=caption))
        elif msg.video:
            media.append(InputMediaVideo(media=msg.video.file_id, caption=caption))
        caption_sent = caption_sent or (caption is not None)

    if media:
        await context.bot.send_media_group(chat_id=CHANNEL_ID, media=media)

# 单条消息转发
async def forward_to_channel(context, messages):
    for msg in messages:
        if msg.text:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=msg.text)
        elif msg.photo:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=msg.photo[-1].file_id, caption=msg.caption or "")
        elif msg.video:
            await context.bot.send_video(chat_id=CHANNEL_ID, video=msg.video.file_id, caption=msg.caption or "")
        elif msg.document:
            await context.bot.send_document(chat_id=CHANNEL_ID, document=msg.document.file_id, caption=msg.caption or "")

# 主函数
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setstart", set_start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # 设置 webhook
    logging.info(f"设置Webhook地址: {WEBHOOK_URL}/{BOT_TOKEN}, 监听端口: {PORT}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()