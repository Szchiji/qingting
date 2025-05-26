# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制全部代码
COPY . .

# 设置环境变量（如果需要也可以在 Render 里设置）
# ENV BOT_TOKEN=your_bot_token
# ENV CHANNEL_ID=your_channel_id
# ENV ADMIN_ID=your_admin_id
# ENV WEBHOOK_URL=your_webhook_url

# 启动命令
CMD ["python", "bot.py"]
