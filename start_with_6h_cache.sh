#!/bin/bash
# 启动 Speaches 服务，配置 6 小时模型缓存

echo "=== 启动 Speaches 服务 (6小时缓存) ==="
echo ""

# 设置项目目录
PROJECT_DIR="/Users/gump_m2/Documents/Agent-RL/xDAN-Voice-speaches"
cd "$PROJECT_DIR"

# 检查是否已有服务运行
if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  端口 8000 已被占用"
    echo "请先停止现有服务或使用其他端口"
    exit 1
fi

# 设置环境变量
echo "配置环境变量..."
export SPEACHES_MODEL_IDLE_TIMEOUT=21600  # 6小时 = 21600秒
export SPEACHES_MAX_MODELS=5              # 最多保持5个模型
export SPEACHES_BASE_URL="http://localhost:8000"
export HF_HUB_ENABLE_HF_TRANSFER=1        # 加速模型下载

echo "  模型空闲超时: 6 小时"
echo "  最大模型数: 5"
echo "  服务地址: $SPEACHES_BASE_URL"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    uv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "检查依赖..."
if ! python -c "import speaches" 2>/dev/null; then
    echo "安装依赖..."
    uv sync --all-extras
fi

# 启动服务
echo ""
echo "启动服务..."
echo "----------------------------------------"

# 使用 nohup 后台运行，日志输出到文件
nohup uvicorn --factory --host 0.0.0.0 --port 8000 speaches.main:create_app > speaches_6h.log 2>&1 &

# 保存 PID
echo $! > speaches.pid
PID=$(cat speaches.pid)

echo "服务已启动 (PID: $PID)"
echo "日志文件: speaches_6h.log"
echo ""

# 等待服务启动
echo "等待服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ 服务启动成功!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "✗ 服务启动超时"
        echo "请查看日志: tail -f speaches_6h.log"
        exit 1
    fi
done

echo ""
echo "=== 下载常用模型 ==="

# 下载 ASR 模型
echo "下载 ASR 模型: faster-distil-whisper-large-v3..."
curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-large-v3" || echo "  (可能已存在)"

# 下载 TTS 模型  
echo "下载 TTS 模型: Kokoro-82M..."
curl -X POST "$SPEACHES_BASE_URL/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX" || echo "  (可能已存在)"

echo ""
echo "=== 服务已就绪 ==="
echo ""
echo "服务地址: http://localhost:8000"
echo "健康检查: http://localhost:8000/health"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "查看日志: tail -f speaches_6h.log"
echo "停止服务: kill $PID"
echo ""
echo "现在可以运行测试:"
echo "python3 test_model_cache.py"
echo ""