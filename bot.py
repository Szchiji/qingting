from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import json

# 配置
BOT_TOKEN = "8092070129:AAGxrcDxMFniPLjNnZ4eNYd-Mtq9JBra-60"
CHANNEL_ID = -1001763041158
ADMIN_IDS = [7848870377]
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"https://telegram-bot-nkal.onrender.com{WEBHOOK_PATH}"
VIP_FILE = "vip_users.json"

# 初始化 VIP 数据文件
def load_vip_users():
    if not os.path.exists(VIP_FILE):
        with open(VIP_FILE, 'w') as f:
            json.dump({"enabled": True, "users": []}, f)
    with open(VIP_FILE, 'r') as f:
        return json.load(f)

def save_vip_users(data):
    with open(VIP_FILE, 'w') as f:
        json.dump(data, f)

# 命令处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用匿名投稿机器人，请发送消息进行投稿。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    vip_data = load_vip_users()

    if vip_data.get("enabled") and user_id in vip_data["users"]:
        # VIP 直接转发到频道
        await context.bot.send_message(chat_id=CHANNEL_ID, text=update.message.text)
        await update.message.reply_text("您的消息已匿名发送到频道。")
    else:
        # 非 VIP 提交给管理员审核
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"收到新投稿（用户 {user_id}）：\n\n{update.message.text}",
                reply_markup=telegram.InlineKeyboardMarkup([
                    [telegram.InlineKeyboardButton("通过", callback_data=f"approve|{user_id}|{update.message.text}"),
                     telegram.InlineKeyboardButton("拒绝", callback_data=f"reject|{user_id}")]
                ])
            )
        await update.message.reply_text("您的消息已提交审核，请等待管理员处理。")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    action = data[0]
    user_id = int(data[1])

    if action == "approve":
        text = data[2]
        await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
        await context.bot.send_message(chat_id=user_id, text="您的投稿已通过并匿名发布。")
        await query.edit_message_text("已通过并发送到频道。")
    elif action == "reject":
        await context.bot.send_message(chat_id=user_id, text="您的投稿未通过审核。")
        await query.edit_message_text("已拒绝该投稿。")

# 管理员命令
async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not context.args:
        return await update.message.reply_text("用法：/addvip 用户ID 或 @用户名")
    user = context.args[0]
    if user.startswith("@"):
        user_obj = await context.bot.get_chat(user)
        user_id = user_obj.id
    else:
        user_id = int(user)

    vip_data = load_vip_users()
    if user_id not in vip_data["users"]:
        vip_data["users"].append(user_id)
        save_vip_users(vip_data)
        await update.message.reply_text(f"已添加 {user_id} 为 VIP 用户。")
    else:
        await update.message.reply_text("该用户已经是 VIP。")

async def del_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not context.args:
        return await update.message.reply_text("用法：/delvip 用户ID 或 @用户名")
    user = context.args[0]
    if user.startswith("@"):
        user_obj = await context.bot.get_chat(user)
        user_id = user_obj.id
    else:
        user_id = int(user)

    vip_data = load_vip_users()
    if user_id in vip_data["users"]:
        vip_data["users"].remove(user_id)
        save_vip_users(vip_data)
        await update.message.reply_text(f"已移除 {user_id} 的 VIP 权限。")
    else:
        await update.message.reply_text("该用户不是 VIP。")

async def enable_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    vip_data = load_vip_users()
    vip_data["enabled"] = True
    save_vip_users(vip_data)
    await update.message.reply_text("已启用 VIP 免审核机制。")

async def disable_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    vip_data = load_vip_users()
    vip_data["enabled"] = False
    save_vip_users(vip_data)
    await update.message.reply_text("已禁用 VIP 免审核机制。")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    text = " ".join(context.args)
    if not text:
        return await update.message.reply_text("用法：/broadcast 内容")
    vip_data = load_vip_users()
    for uid in vip_data["users"]:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except:
            continue
    await update.message.reply_text("广播已发送。")

# 主函数
def main():
    import telegram

    application = Application.builder().token(BOT_TOKEN).build()

    # 命令
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addvip", add_vip))
    application.add_handler(CommandHandler("delvip", del_vip))
    application.add_handler(CommandHandler("enablevip", enable_vip))
    application.add_handler(CommandHandler("disablevip", disable_vip))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # 消息 & 回调
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(telegram.ext.CallbackQueryHandler(handle_callback))

    port = int(os.environ.get("PORT", 8443))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()