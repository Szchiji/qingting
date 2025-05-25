import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask
import threading
import requests

# 初始化 Flask 用于健康检查
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# 从环境变量获取配置
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1001763041158')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '6383212444'))

# 频率限制配置
RATE_LIMIT = {
    'minute': 5,
    'hour': 30,
    'day': 100
}

# 用户活动记录
user_activity = {}

class RateLimiter:
    @staticmethod
    def check_limit(user_id):
        now = datetime.now()
        if user_id not in user_activity:
            user_activity[user_id] = {
                'minute': {'count': 0, 'time': now},
                'hour': {'count': 0, 'time': now},
                'day': {'count': 0, 'time': now}
            }
            return True

        user_data = user_activity[user_id]
        windows = {
            'minute': timedelta(minutes=1),
            'hour': timedelta(hours=1),
            'day': timedelta(days=1)
        }

        for window, delta in windows.items():
            if user_data[window]['time'] + delta <= now:
                user_data[window] = {'count': 0, 'time': now}
            elif user_data[window]['count'] >= RATE_LIMIT[window]:
                return False

        for window in windows:
            user_data[window]['count'] += 1

        return True

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🤖 匿名投稿机器人\n\n"
        "直接发送内容即可自动转发到频道\n"
        f"频率限制：{RATE_LIMIT['minute']}条/分钟 | {RATE_LIMIT['hour']}条/小时"
    )

def forward_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if not RateLimiter.check_limit(user_id):
        update.message.reply_text("⏳ 发送过于频繁，请稍后再试")
        return

    try:
        # 文本消息
        if update.message.text:
            context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=update.message.text
            )
        # 图片
        elif update.message.photo:
            context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption
            )
        # 视频
        elif update.message.video:
            context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=update.message.video.file_id,
                caption=update.message.caption
            )
        # 文档
        elif update.message.document:
            context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=update.message.document.file_id,
                caption=update.message.caption
            )
        
        update.message.reply_text("✅ 内容已发布")
    except Exception as e:
        error_msg = f"转发失败: {str(e)}"
        logging.error(error_msg)
        update.message.reply_text("❌ 发布失败")
        
        # 通知管理员
        if ADMIN_ID:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ 转发错误\n用户: {user_id}\n错误: {error_msg}"
            )

def keep_alive():
    """防止Heroku休眠"""
    while True:
        try:
            requests.get(f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com")
        except:
            pass
        time.sleep(1200)  # 每20分钟唤醒一次

def main():
    # 启动Flask服务
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 启动防休眠
    threading.Thread(target=keep_alive, daemon=True).start()

    # 初始化机器人
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(
        Filters.text | Filters.photo | Filters.video | Filters.document,
        forward_message
    ))

    logging.info("机器人启动中...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()