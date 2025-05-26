import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# 机器人配置
BOT_TOKEN = "8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60"
CHANNEL_ID = -1001763041158  # 频道 ID，数字形式
ADMIN_ID = 7848870377        # 管理员用户 ID，数字形式

# 频率限制（秒）
LIMIT_SECONDS = 10

# 记录用户最后一次发送时间
user_last_time = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("机器人已启动，发送消息即可匿名转发到频道。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = asyncio.get_event_loop().time()
    last_time = user_last_time.get(user_id, 0)
    if now - last_time < LIMIT_SECONDS:
        # 限制内重复发送，反馈给用户
        warn_msg = await update.message.reply_text(
            f"发送频率过快，请等待 {int(LIMIT_SECONDS - (now - last_time))} 秒后再发送。"
        )
        await asyncio.sleep(10)
        await warn_msg.delete()
        await update.message.delete()
        return
    user_last_time[user_id] = now

    # 转发匿名消息到频道
    content = update.message.text or ""
    if not content.strip():
        # 非文本消息不处理
        return

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=content,
            disable_notification=True,
        )
        # 反馈发送成功
        feedback_msg = await update.message.reply_text("消息已匿名转发到频道！")
        await asyncio.sleep(10)
        await feedback_msg.delete()
        await update.message.delete()
    except Exception as e:
        logger.error(f"转发消息失败: {e}")
        await update.message.reply_text("转发消息失败，请稍后再试。")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Webhook 运行配置
    application.run_webhook(
        listen="0.0.0.0",
        port=8000,
        webhook_url="https://telegram-bot-nkal.onrender.com",
    )

if __name__ == "__main__":
    main()