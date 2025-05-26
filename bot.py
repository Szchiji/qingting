import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError
import asyncio
from datetime import datetime, timedelta

# 启用日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 从环境变量读取配置
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))  # 频道ID，示例：-1001234567890
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # 你的域名，例如 https://qingting-1.onrender.com
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # 管理员的 Telegram 用户ID

if not all([BOT_TOKEN, CHANNEL_ID, WEBHOOK_URL, ADMIN_ID]):
    logger.error("请确保 BOT_TOKEN, CHANNEL_ID, WEBHOOK_URL, ADMIN_ID 四个环境变量均已设置")
    exit(1)

# 频率限制：记录用户最后发送时间
last_send_time = {}

# 限制时间间隔，单位秒
LIMIT_SECONDS = 10

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用匿名转发机器人，请发送消息，我将匿名转发到频道。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = datetime.now()

    # 频率限制判断
    last_time = last_send_time.get(user_id)
    if last_time and (now - last_time).total_seconds() < LIMIT_SECONDS:
        await update.message.reply_text(
            f"请不要频繁发送消息，{LIMIT_SECONDS}秒内只能发送一次。"
        )
        return
    last_send_time[user_id] = now

    text = update.message.text
    if not text:
        await update.message.reply_text("抱歉，我只支持文本消息转发。")
        return

    try:
        # 转发匿名消息到频道
        await context.bot.send_message(chat_id=CHANNEL_ID, text=text)

        # 发送成功反馈，10秒后删除
        sent_msg = await update.message.reply_text("消息已匿名转发到频道。该提示10秒后消失。")

        # 等待10秒后删除反馈消息
        await asyncio.sleep(10)
        await sent_msg.delete()
    except TelegramError as e:
        logger.error(f"转发消息失败: {e}")
        await update.message.reply_text("转发消息失败，请稍后重试。")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # 端口和路径
    PORT = int(os.environ.get("PORT", "10000"))
    WEBHOOK_PATH = f"/{BOT_TOKEN}"

    logger.info(f"设置Webhook地址: {WEBHOOK_URL}{WEBHOOK_PATH}，监听端口: {PORT}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
    )

if __name__ == "__main__":
    main()