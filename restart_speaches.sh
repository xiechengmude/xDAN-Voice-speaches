#!/bin/bash
# Speaches 服务重启脚本 - 自动 kill 旧进程并启动新服务

set -e  # 遇到错误立即退出

echo "=== Speaches 服务重启脚本 ==="
echo ""

# 项目配置
PROJECT_DIR="/Users/gump_m2/Documents/Agent-RL/xDAN-Voice-speaches"
PORT=8000
PID_FILE="$PROJECT_DIR/speaches.pid"
LOG_FILE="$PROJECT_DIR/speaches_6h.log"

# 环境配置
export SPEACHES_MODEL_IDLE_TIMEOUT=21600  # 6小时缓存
export SPEACHES_MAX_MODELS=5
export SPEACHES_BASE_URL="http://localhost:$PORT"
export HF_HUB_ENABLE_HF_TRANSFER=1

cd "$PROJECT_DIR"

# 函数：检查进程是否运行
check_process() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi
    
    if kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 函数：停止旧进程
stop_old_service() {
    echo "1. 检查并停止旧服务..."
    
    # 从 PID 文件停止
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if check_process "$OLD_PID"; then
            echo "  发现旧进程 (PID: $OLD_PID)，正在停止..."
            kill "$OLD_PID"
            
            # 等待进程结束
            for i in {1..10}; do
                if ! check_process "$OLD_PID"; then
                    echo "  ✓ 旧进程已停止"
                    break
                fi
                sleep 1
            done
            
            # 如果还没停止，强制 kill
            if check_process "$OLD_PID"; then
                echo "  正在强制停止进程..."
                kill -9 "$OLD_PID" 2>/dev/null || true
                sleep 2
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # 检查端口占用
    if lsof -ti:$PORT > /dev/null 2>&1; then
        echo "  端口 $PORT 仍被占用，查找并停止进程..."
        PORT_PID=$(lsof -ti:$PORT)
        if [ -n "$PORT_PID" ]; then
            echo "  停止端口 $PORT 上的进程 (PID: $PORT_PID)..."
            kill "$PORT_PID" 2>/dev/null || true
            sleep 2
            
            # 强制 kill 如果还在运行
            if kill -0 "$PORT_PID" 2>/dev/null; then
                kill -9 "$PORT_PID" 2>/dev/null || true
                sleep 1
            fi
        fi
    fi
    
    # 额外检查：通过进程名查找
    UVICORN_PIDS=$(pgrep -f "uvicorn.*speaches" || true)
    if [ -n "$UVICORN_PIDS" ]; then
        echo "  发现 uvicorn speaches 进程，正在停止..."
        echo "$UVICORN_PIDS" | xargs kill 2>/dev/null || true
        sleep 2
    fi
    
    echo "  ✓ 旧服务停止完成"
}

# 函数：准备环境
prepare_environment() {
    echo ""
    echo "2. 准备环境..."
    
    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        echo "  创建虚拟环境..."
        uv venv
    fi
    
    # 激活虚拟环境
    echo "  激活虚拟环境..."
    source .venv/bin/activate
    
    # 检查依赖
    if ! python -c "import speaches" 2>/dev/null; then
        echo "  安装/更新依赖..."
        uv sync --all-extras
    fi
    
    echo "  ✓ 环境准备完成"
}

# 函数：启动新服务
start_new_service() {
    echo ""
    echo "3. 启动新服务..."
    
    # 清理旧日志（可选）
    if [ -f "$LOG_FILE" ]; then
        # 保留最近 1000 行日志
        tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE" || rm -f "$LOG_FILE"
    fi
    
    # 启动服务
    nohup uvicorn --factory --host 0.0.0.0 --port $PORT speaches.main:create_app >> "$LOG_FILE" 2>&1 &
    NEW_PID=$!
    
    # 保存新 PID
    echo $NEW_PID > "$PID_FILE"
    
    echo "  服务已启动 (PID: $NEW_PID)"
    echo "  日志文件: $LOG_FILE"
    echo "  PID 文件: $PID_FILE"
}

# 函数：等待服务就绪
wait_for_service() {
    echo ""
    echo "4. 等待服务就绪..."
    
    local max_wait=30
    local wait_count=0
    
    while [ $wait_count -lt $max_wait ]; do
        if curl -s "$SPEACHES_BASE_URL/health" > /dev/null 2>&1; then
            echo "  ✓ 服务已就绪!"
            return 0
        fi
        
        sleep 1
        wait_count=$((wait_count + 1))
        echo "  等待中... ($wait_count/$max_wait)"
    done
    
    echo "  ✗ 服务启动超时"
    echo "  请检查日志: tail -f $LOG_FILE"
    return 1
}

# 函数：预加载模型
preload_models() {
    echo ""
    echo "5. 预加载模型..."
    
    # ASR 模型
    echo "  下载 ASR 模型..."
    if curl -s -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-large-v3" | grep -q "exists\|success"; then
        echo "    ✓ faster-distil-whisper-large-v3"
    else
        echo "    ⚠ faster-distil-whisper-large-v3 下载可能失败"
    fi
    
    # TTS 模型
    echo "  下载 TTS 模型..."
    if curl -s -X POST "$SPEACHES_BASE_URL/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX" | grep -q "exists\|success"; then
        echo "    ✓ Kokoro-82M-v1.0-ONNX"
    else
        echo "    ⚠ Kokoro-82M-v1.0-ONNX 下载可能失败"
    fi
    
    echo "  ✓ 模型加载完成"
}

# 函数：显示状态
show_status() {
    echo ""
    echo "=== 服务状态 ==="
    echo "服务地址: $SPEACHES_BASE_URL"
    echo "健康检查: $SPEACHES_BASE_URL/health"
    echo "API 文档: $SPEACHES_BASE_URL/docs"
    echo ""
    echo "进程信息:"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "  PID: $PID"
        
        if check_process "$PID"; then
            echo "  状态: 运行中 ✓"
        else
            echo "  状态: 已停止 ✗"
        fi
    fi
    echo ""
    echo "配置信息:"
    echo "  模型缓存: 6 小时"
    echo "  最大模型数: 5"
    echo "  日志文件: $LOG_FILE"
    echo ""
    echo "常用命令:"
    echo "  查看日志: tail -f $LOG_FILE"
    echo "  停止服务: $0 stop"
    echo "  重启服务: $0 restart"
    echo "  查看状态: $0 status"
    echo "  运行测试: python3 test_model_cache.py"
}

# 函数：仅停止服务
stop_service() {
    echo "停止 Speaches 服务..."
    stop_old_service
    echo "✓ 服务已停止"
}

# 函数：仅显示状态
status_service() {
    show_status
    
    # 检查服务是否响应
    echo "连接测试:"
    if curl -s "$SPEACHES_BASE_URL/health" > /dev/null 2>&1; then
        echo "  HTTP 连接: ✓"
        
        # 获取模型信息
        MODEL_COUNT=$(curl -s "$SPEACHES_BASE_URL/v1/models" | jq '.data | length' 2>/dev/null || echo "未知")
        echo "  可用模型: $MODEL_COUNT 个"
    else
        echo "  HTTP 连接: ✗ (服务未响应)"
    fi
}

# 主函数
main() {
    case "${1:-start}" in
        "start"|"restart")
            stop_old_service
            prepare_environment
            start_new_service
            
            if wait_for_service; then
                preload_models
                show_status
                echo ""
                echo "🎉 Speaches 服务重启成功！"
            else
                echo ""
                echo "❌ 服务启动失败"
                exit 1
            fi
            ;;
        "stop")
            stop_service
            ;;
        "status")
            status_service
            ;;
        *)
            echo "用法: $0 [start|restart|stop|status]"
            echo ""
            echo "命令说明:"
            echo "  start/restart - 重启服务 (默认)"
            echo "  stop         - 停止服务"
            echo "  status       - 查看状态"
            echo ""
            echo "示例:"
            echo "  $0           # 重启服务"
            echo "  $0 restart   # 重启服务"
            echo "  $0 stop      # 停止服务"
            echo "  $0 status    # 查看状态"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"