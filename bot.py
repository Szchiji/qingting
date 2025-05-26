import os
import logging
import asyncio
from datetime import datetime, timedelta

from telegram import InputMediaPhoto, InputMediaVideo, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "10000"))

LIMIT_SECONDS = 10
MEDIA_GROUP_WAIT = 1  # 秒，缓存同组消息的等待时间

last_msg_time = {}
media_group_cache = {}


async def send_media_group(context: ContextTypes.DEFAULT_TYPE, media_group_id: str):
    group = media_group_cache.pop(media_group_id, None)
    if not group:
        return

    messages = group["messages"]
    media = []
    for update in messages:
        msg = update.message
        caption = msg.caption or ""
        if msg.photo:
            media.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=caption))
        elif msg.video:
            media.append(InputMediaVideo(media=msg.video.file_id, caption=caption))
        else:
            # 跳过非图片/视频消息
            pass

    if not media:
        # 没有合适媒体，单条转发文本
        for update in messages:
            text = update.message.text or ""
            if text:
                try:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
                except Exception as e:
                    logger.error(f"转发文本失败: {e}")
        return

    try:
        await context.bot.send_media_group(chat_id=CHANNEL_ID, media=media)
    except Exception as e:
        logger.error(f"转发media group失败: {e}")


async def wait_and_send_media_group(context: ContextTypes.DEFAULT_TYPE, media_group_id: str):
    await asyncio.sleep(MEDIA_GROUP_WAIT)
    await send_media_group(context, media_group_id)


async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.utcnow()

    last_time = last_msg_time.get(user_id)
    if last_time and (now - last_time) < timedelta(seconds=LIMIT_SECONDS):
        try:
            await update.message.reply_text(f"发送太快啦，请{LIMIT_SECONDS}秒后再试。")
        except Exception as e:
            logger.error(f"限流反馈失败: {e}")
        return

    last_msg_time[user_id] = now

    msg = update.message

    if msg.media_group_id:
        mgid = msg.media_group_id
        if mgid not in media_group_cache:
            media_group_cache[mgid] = {
                "messages": [],
                "timer_task": context.application.create_task(
                    wait_and_send_media_group(context, mgid)
                ),
            }
        media_group_cache[mgid]["messages"].append(update)
        return

    # 非群组消息单条转发
    try:
        if msg.text:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=msg.text)
        elif msg.photo:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID, photo=msg.photo[-1].file_id, caption=msg.caption or ""
            )
        elif msg.video:
            await context.bot.send_video(
                chat_id=CHANNEL_ID, video=msg.video.file_id, caption=msg.caption or ""
            )
        else:
            await update.message.reply_text("暂时只支持文本、图片和视频转发。")
            return

        feedback = await update.message.reply_text("发送成功，10秒后此消息自动删除。")
        await asyncio.sleep(10)
        await feedback.delete()
    except Exception as e:
        logger.error(f"转发消息失败: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), forward_message))

    logger.info(f"设置Webhook地址: {WEBHOOK_URL}/{BOT_TOKEN}, 监听端口: {PORT}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )


if __name__ == "__main__":
    main()