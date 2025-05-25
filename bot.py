import json
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

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
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('欢迎使用匿名转发机器人！')

# 处理用户消息并转发到频道
def forward_message(update: Update, context: CallbackContext) -> None:
    # 获取消息内容
    text = update.message.text

    # 向指定频道转发消息
    context.bot.send_message(chat_id=CHANNEL_ID, text=text, disable_notification=True)

    # 获取用户信息
    user_id = update.message.from_user.id
    username = update.message.from_user.username  # 获取用户名（如果存在）

    # 将用户信息添加到用户列表
    users = load_users()

    # 检查用户是否已存在，不存在则添加
    if not any(user['user_id'] == user_id for user in users):
        users.append({'user_id': user_id, 'username': username})
        save_users(users)

# 广播命令
def broadcast(update: Update, context: CallbackContext) -> None:
    # 检查是否为管理员
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("只有管理员才能使用此命令！")
        return
    
    # 获取广播内容
    if context.args:
        message = ' '.join(context.args)  # 获取用户输入的广播内容
        # 向所有用户广播消息
        users = load_users()
        for user in users:
            user_id = user['user_id']
            context.bot.send_message(chat_id=user_id, text=message, disable_notification=True)
        update.message.reply_text("消息已广播给所有用户！")
    else:
        update.message.reply_text("请提供要广播的消息内容！")

def main():
    # 创建 Updater 对象并设置 Webhook URL
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # 处理启动命令
    dispatcher.add_handler(CommandHandler("start", start))
    
    # 处理所有文本消息
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, forward_message))

    # 添加广播命令（管理员使用）
    dispatcher.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))

    # 启动 Webhook
    updater.start_webhook(
        listen='0.0.0.0',  # 监听所有 IP
        port=5000,         # Webhook 服务端口
        url_path=TOKEN,    # 你的机器人 Token
        webhook_url="https://qingting.onrender.com"  # 更新后的 Webhook 地址
    )
    
    updater.idle()

if __name__ == '__main__':
    main()
