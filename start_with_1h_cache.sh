#!/bin/bash
# 启动 Speaches 服务，配置 1 小时模型缓存

echo "=== 启动 Speaches 服务 (1小时缓存) ==="
echo ""

# 设置项目目录 - 使用脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
cd "$PROJECT_DIR"

# 检查是否已有服务运行
if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  端口 8000 已被占用"
    echo "请先停止现有服务或使用其他端口"
    exit 1
fi

# 设置环境变量
echo "配置环境变量..."
export SPEACHES_MODEL_IDLE_TIMEOUT=3600   # 1小时 = 3600秒
export SPEACHES_MAX_MODELS=5              # 最多保持5个模型
export SPEACHES_BASE_URL="http://localhost:8000"
export HF_HUB_ENABLE_HF_TRANSFER=1        # 加速模型下载

echo "  模型空闲超时: 1 小时"
echo "  最大模型数: 5"
echo "  服务地址: $SPEACHES_BASE_URL"
echo ""

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    uv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 检查并安装依赖
if ! python -c "import speaches" 2>/dev/null; then
    echo "安装依赖..."
    uv sync --all-extras
fi

# 启动服务
echo "启动服务..."
LOG_FILE="speaches_1h.log"
nohup uvicorn --factory --host 0.0.0.0 --port 8000 speaches.main:create_app > "$LOG_FILE" 2>&1 &
PID=$!

# 保存 PID
echo $PID > speaches.pid

echo ""
echo "✅ 服务已启动！"
echo "   PID: $PID"
echo "   日志: $LOG_FILE"
echo ""

# 等待服务启动
echo "等待服务就绪..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 服务已就绪！"
        break
    fi
    sleep 1
done

echo ""
echo "预加载模型..."

# 下载 ASR 模型
echo "  下载 ASR 模型..."
curl -X POST http://localhost:8000/v1/models/Systran/faster-distil-whisper-large-v3 || echo "模型可能已存在"

# 下载 TTS 模型
echo "  下载 TTS 模型..."
curl -X POST http://localhost:8000/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX || echo "模型可能已存在"

echo ""
echo "=== 服务信息 ==="
echo "服务地址: http://localhost:8000"
echo "健康检查: http://localhost:8000/health"
echo "API 文档: http://localhost:8000/docs"
echo "模型缓存: 1 小时"
echo ""
echo "查看日志: tail -f $LOG_FILE"
echo "停止服务: kill $(cat speaches.pid)"
echo ""