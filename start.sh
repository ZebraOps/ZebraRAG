#!/bin/bash
# ZebraRAG服务启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查虚拟环境
if [[ ! -d "$SCRIPT_DIR/venv" ]]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# 设置环境变量
export SERVICE_IP="127.0.0.1"
export SERVICE_PORT="4124"

# Nacos配置（可选）
export NACOS_SERVER_ADDR="localhost:8848"

echo "🚀 启动ZebraRAG服务..."
echo "📚 端口: $SERVICE_PORT"
echo "🔧 配置文件: $SCRIPT_DIR/.env"

# 启动服务
cd "$SCRIPT_DIR"
venv/bin/python -m uvicorn app.main:app \
    --reload \
    --host "$SERVICE_IP" \
    --port "$SERVICE_PORT" \
    --log-level info
