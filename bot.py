import json
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# 设置机器人 Token 和频道 ID
TOKEN = '8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60'
CHANNEL_ID = '-1001763041158'  # 频道 ID
ADMIN_ID = 7848870377  # 管理员用户 ID
USER_FILE = 'users.json'  # 存储用户信息的 JSON 文件

# 加载用户列表
def load_users():
    try:
        with open(USER_FILE, 'r') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []
    return users

# 保存用户列表
def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# 启动命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('欢迎使用匿名转发机器人！')

# 处理用户消息并转发到频道
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    await context.bot.send_message(chat_id=CHANNEL_ID, text=text, disable_notification=True)

    user_id = update.message.from_user.id
    username = update.message.from_user.username
    users = load_users()
    if not any(user['user_id'] == user_id for user in users):
        users.append({'user_id': user_id, 'username': username})
        save_users(users)

# 广播命令
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("只有管理员才能使用此命令！")
        return

    if context.args:
        message = ' '.join(context.args)
        users = load_users()
        for user in users:
            user_id = user['user_id']
            try:
                await context.bot.send_message(chat_id=user_id, text=message, disable_notification=True)
            except Exception as e:
                print(f"无法发送给 {user_id}：{e}")
        await update.message.reply_text("消息已广播给所有用户！")
    else:
        await update.message.reply_text("请提供要广播的消息内容！")

# 主函数（异步）
async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
    application.add_handler(CommandHandler("broadcast", broadcast))  # 删除 pass_args

    # 设置 Webhook
    webhook_url = "https://qingting-1.onrender.com/" + TOKEN
    await application.bot.set_webhook(url=webhook_url)

    # 启动 Webhook 模式
    await application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=webhook_url
    )

# 启动入口
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())