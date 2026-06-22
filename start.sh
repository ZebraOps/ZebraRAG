#!/bin/bash
# ZebraRAG服务启动脚本
# Usage:
#   ./start.sh              # 开发模式（热重载）
#   ./start.sh --prod       # 生产模式（无热重载）
#   ./start.sh --wait       # 启动后等待健康检查通过

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROD_MODE=false
WAIT_HEALTH=false

# 解析参数
for arg in "$@"; do
    case $arg in
        --prod) PROD_MODE=true ;;
        --wait) WAIT_HEALTH=true ;;
    esac
done

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
export SERVICE_IP="${SERVICE_IP:-127.0.0.1}"
export SERVICE_PORT="${SERVICE_PORT:-4124}"

# Nacos配置（可选）
export NACOS_SERVER_ADDR="${NACOS_SERVER_ADDR:-localhost:8848}"

HEALTH_URL="http://${SERVICE_IP}:${SERVICE_PORT}/health"

# 健康检查函数
wait_for_health() {
    local max_retries=60
    local retry=0
    echo "⏳ 等待服务健康检查通过..."

    while [[ $retry -lt $max_retries ]]; do
        if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
            echo "✅ 服务健康检查通过: $HEALTH_URL"
            return 0
        fi
        retry=$((retry + 1))
        echo "  重试 $retry/$max_retries..."
        sleep 1
    done

    echo "❌ 健康检查超时（${max_retries}s）"
    return 1
}

# 检查端口是否被占用
check_port() {
    if lsof -i:"$SERVICE_PORT" > /dev/null 2>&1; then
        echo "⚠️  端口 $SERVICE_PORT 已被占用"
        echo "  使用进程:"
        lsof -i:"$SERVICE_PORT"
        echo ""
        read -p "是否终止占用进程？[y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -t -i:"$SERVICE_PORT" | xargs kill -9 2>/dev/null
            echo "✅ 已终止占用进程"
        else
            echo "❌ 启动取消"
            exit 1
        fi
    fi
}

check_port

echo "🚀 启动ZebraRAG服务..."
echo "📚 端口: $SERVICE_PORT"
echo "🔧 配置文件: $SCRIPT_DIR/.env"
echo "🏗️  模式: $([ "$PROD_MODE" = true ] && echo "生产" || echo "开发")"

cd "$SCRIPT_DIR"

# 构建启动参数
UVICORN_ARGS=(
    app.main:app
    --host "$SERVICE_IP"
    --port "$SERVICE_PORT"
    --log-level info
)

# 生产模式不启用热重载
if [[ "$PROD_MODE" = true ]]; then
    UVICORN_ARGS+=(--workers 1)
else
    UVICORN_ARGS+=(--reload)
fi

# 后台启动服务
venv/bin/python -m uvicorn "${UVICORN_ARGS[@]}" &

# 保存进程PID
APP_PID=$!
echo "📍 进程 PID: $APP_PID"

# 等待健康检查
if [[ "$WAIT_HEALTH" = true ]] || [[ "$PROD_MODE" = true ]]; then
    if ! wait_for_health; then
        echo "❌ 服务启动失败"
        kill $APP_PID 2>/dev/null
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ZebraRAG 服务已启动"
echo "🌐 访问地址: http://${SERVICE_IP}:${SERVICE_PORT}"
echo "📖 API 文档: http://${SERVICE_IP}:${SERVICE_PORT}/docs"
echo "🔍 健康检查: $HEALTH_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 等待进程结束
wait $APP_PID
