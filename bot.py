import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # 频道ID，格式类似 -1001763041158
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # 管理员ID，可根据需求使用

# 记录用户最后发送消息的时间戳，做频率限制
user_last_msg_time = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = asyncio.get_event_loop().time()

    last_time = user_last_msg_time.get(user_id, 0)
    if now - last_time < 10:
        # 10秒内重复发送，提醒限制
        await update.message.reply_text("发送频率太快，请10秒后再试。")
        return
    user_last_msg_time[user_id] = now

    # 匿名转发消息到频道
    text = update.message.text or "（收到消息）"
    await context.bot.send_message(chat_id=CHANNEL_ID, text=text)

    # 给用户反馈，10秒后删除反馈和用户消息
    sent = await update.message.reply_text("消息已匿名转发到频道！")
    await asyncio.sleep(10)
    await sent.delete()
    await update.message.delete()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    port = int(os.getenv("PORT", "10000"))
    webhook_path = f"/{BOT_TOKEN}"
    webhook_url = f"{os.getenv('WEBHOOK_URL')}{webhook_path}"  # WEBHOOK_URL环境变量存域名，带https

    print(f"设置Webhook地址: {webhook_url}, 监听端口: {port}")

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url,
        webhook_path=webhook_path,
    )

if __name__ == "__main__":
    main()