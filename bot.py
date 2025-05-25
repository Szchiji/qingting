import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 配置信息（实际部署时会用环境变量覆盖）
BOT_TOKEN = os.getenv('BOT_TOKEN', '8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60')
CHANNEL_ID = os.getenv('CHANNEL_ID', '-1001763041158')
ADMIN_ID = int(os.getenv('ADMIN_ID', '6383212444'))

# 频率限制配置
RATE_LIMITS = {
    'minute': 5,
    'hour': 30,
    'day': 100
}

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.user_activity = {}

    def check_limit(self, user_id):
        now = datetime.now()
        if user_id not in self.user_activity:
            self.user_activity[user_id] = {
                'minute': {'count': 0, 'time': now},
                'hour': {'count': 0, 'time': now},
                'day': {'count': 0, 'time': now}
            }
            return True

        user_data = self.user_activity[user_id]
        time_windows = {
            'minute': timedelta(minutes=1),
            'hour': timedelta(hours=1),
            'day': timedelta(days=1)
        }

        for window, delta in time_windows.items():
            if user_data[window]['time'] + delta <= now:
                user_data[window] = {'count': 0, 'time': now}
            elif user_data[window]['count'] >= RATE_LIMITS[window]:
                return False

        for window in time_windows:
            user_data[window]['count'] += 1

        return True

limiter = RateLimiter()

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🤖 匿名投稿机器人已就绪\n\n"
        "直接发送内容即可匿名转发到频道\n"
        "频率限制：5条/分钟，30条/小时"
    )

def forward_to_channel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if not limiter.check_limit(user_id):
        update.message.reply_text("⏳ 发送频率过高，请稍后再试")
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
        # 其他媒体类型...
        
        update.message.reply_text("✅ 内容已发布")
    except Exception as e:
        logger.error(f"转发失败: {e}")
        update.message.reply_text("❌ 发布失败，请稍后再试")
        if ADMIN_ID:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ 转发错误\n用户: {user_id}\n错误: {str(e)}"
            )

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(
        Filters.text | Filters.photo | Filters.video,
        forward_to_channel
    ))

    # 添加健康检查端点（Railway需要）
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def health_check():
        return "Bot is running", 200
        
    import threading
    threading.Thread(
        target=app.run,
        kwargs={'host': '0.0.0.0', 'port': 5000},
        daemon=True
    ).start()

    updater.start_polling()
    logger.info("机器人启动成功")
    updater.idle()

if __name__ == '__main__':
    main()