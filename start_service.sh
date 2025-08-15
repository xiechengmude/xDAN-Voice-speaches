#!/bin/bash
# Speaches 服务启动脚本 - 支持后台运行和进程管理

set -e  # 遇到错误立即退出

echo "=== Speaches 服务启动脚本 ==="
echo ""

# 项目配置 - 使用脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PORT=8000
PID_FILE="$PROJECT_DIR/speaches.pid"
LOG_FILE="$PROJECT_DIR/speaches.log"
LOG_MAX_SIZE=10485760  # 10MB

# 环境配置
export SPEACHES_MODEL_IDLE_TIMEOUT=${SPEACHES_MODEL_IDLE_TIMEOUT:-3600}  # 默认1小时，可通过环境变量覆盖
export SPEACHES_MAX_MODELS=${SPEACHES_MAX_MODELS:-5}
export SPEACHES_BASE_URL="http://localhost:$PORT"
export HF_HUB_ENABLE_HF_TRANSFER=1

cd "$PROJECT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

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

# 函数：轮转日志
rotate_log() {
    if [ -f "$LOG_FILE" ]; then
        local size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$size" -gt "$LOG_MAX_SIZE" ]; then
            echo "轮转日志文件 (当前大小: $((size/1024/1024))MB)..."
            mv "$LOG_FILE" "${LOG_FILE}.$(date +%Y%m%d_%H%M%S)"
            # 保留最近5个日志文件
            ls -t "${LOG_FILE}".* 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
        fi
    fi
}

# 函数：停止旧进程
stop_old_service() {
    echo "检查并停止旧服务..."
    
    local stopped=false
    
    # 从 PID 文件停止
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if check_process "$OLD_PID"; then
            echo "  发现旧进程 (PID: $OLD_PID)，正在停止..."
            kill "$OLD_PID" 2>/dev/null || true
            
            # 等待进程结束
            local wait_count=0
            while [ $wait_count -lt 10 ] && check_process "$OLD_PID"; do
                sleep 1
                ((wait_count++))
            done
            
            # 如果还没停止，强制 kill
            if check_process "$OLD_PID"; then
                print_warning "正在强制停止进程..."
                kill -9 "$OLD_PID" 2>/dev/null || true
                sleep 2
            fi
            stopped=true
        fi
        rm -f "$PID_FILE"
    fi
    
    # 检查端口占用
    if lsof -ti:$PORT > /dev/null 2>&1; then
        PORT_PID=$(lsof -ti:$PORT)
        if [ -n "$PORT_PID" ]; then
            print_warning "端口 $PORT 被占用 (PID: $PORT_PID)，正在停止..."
            kill "$PORT_PID" 2>/dev/null || true
            sleep 2
            
            if lsof -ti:$PORT > /dev/null 2>&1; then
                kill -9 $(lsof -ti:$PORT) 2>/dev/null || true
                sleep 1
            fi
            stopped=true
        fi
    fi
    
    # 通过进程名查找
    UVICORN_PIDS=$(pgrep -f "uvicorn.*speaches.*$PORT" || true)
    if [ -n "$UVICORN_PIDS" ]; then
        print_warning "发现相关进程，正在停止..."
        echo "$UVICORN_PIDS" | xargs kill 2>/dev/null || true
        sleep 2
        stopped=true
    fi
    
    if [ "$stopped" = true ]; then
        print_success "旧服务已停止"
    else
        echo "  没有发现运行中的服务"
    fi
}

# 函数：准备环境
prepare_environment() {
    echo ""
    echo "准备环境..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 Python3"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        if command -v uv &> /dev/null; then
            echo "  创建虚拟环境 (使用 uv)..."
            uv venv
        else
            echo "  创建虚拟环境 (使用 venv)..."
            python3 -m venv .venv
        fi
    fi
    
    # 激活虚拟环境
    echo "  激活虚拟环境..."
    source .venv/bin/activate
    
    # 检查依赖
    if ! python -c "import speaches" 2>/dev/null; then
        echo "  安装/更新依赖..."
        if command -v uv &> /dev/null; then
            uv sync --all-extras
        else
            pip install -e ".[all]"
        fi
    fi
    
    print_success "环境准备完成"
}

# 函数：启动服务（前台模式）
start_service_foreground() {
    echo ""
    echo "启动服务 (前台模式)..."
    
    rotate_log
    
    # 直接运行，不使用 nohup
    exec uvicorn --factory --host 0.0.0.0 --port $PORT speaches.main:create_app
}

# 函数：启动服务（后台模式）
start_service_background() {
    echo ""
    echo "启动服务 (后台模式)..."
    
    rotate_log
    
    # 使用 nohup 启动后台服务
    nohup uvicorn --factory --host 0.0.0.0 --port $PORT speaches.main:create_app >> "$LOG_FILE" 2>&1 &
    local NEW_PID=$!
    
    # 保存 PID
    echo $NEW_PID > "$PID_FILE"
    
    # 检查进程是否成功启动
    sleep 2
    if check_process "$NEW_PID"; then
        print_success "服务已启动 (PID: $NEW_PID)"
        echo "  日志文件: $LOG_FILE"
        echo "  PID 文件: $PID_FILE"
    else
        print_error "服务启动失败"
        echo "  请查看日志: tail -f $LOG_FILE"
        return 1
    fi
}

# 函数：等待服务就绪
wait_for_service() {
    echo ""
    echo "等待服务就绪..."
    
    local max_wait=30
    local wait_count=0
    
    while [ $wait_count -lt $max_wait ]; do
        if curl -s "$SPEACHES_BASE_URL/health" > /dev/null 2>&1; then
            print_success "服务已就绪!"
            return 0
        fi
        
        sleep 1
        wait_count=$((wait_count + 1))
        printf "\r  等待中... (%d/%d)" $wait_count $max_wait
    done
    
    echo ""
    print_error "服务启动超时"
    echo "  请检查日志: tail -f $LOG_FILE"
    return 1
}

# 函数：预加载模型
preload_models() {
    echo ""
    echo "预加载常用模型..."
    
    # ASR 模型
    echo "  加载 ASR 模型..."
    if curl -s -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-large-v3" > /dev/null 2>&1; then
        print_success "ASR 模型加载成功"
    else
        print_warning "ASR 模型加载失败（可能已存在）"
    fi
    
    # TTS 模型
    echo "  加载 TTS 模型..."
    if curl -s -X POST "$SPEACHES_BASE_URL/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX" > /dev/null 2>&1; then
        print_success "TTS 模型加载成功"
    else
        print_warning "TTS 模型加载失败（可能已存在）"
    fi
}

# 函数：显示状态
show_status() {
    echo ""
    echo "=== 服务状态 ==="
    echo "服务地址: $SPEACHES_BASE_URL"
    echo "健康检查: $SPEACHES_BASE_URL/health"
    echo "API 文档: $SPEACHES_BASE_URL/docs"
    echo ""
    echo "配置信息:"
    echo "  模型缓存时间: $((SPEACHES_MODEL_IDLE_TIMEOUT/3600)) 小时"
    echo "  最大模型数: $SPEACHES_MAX_MODELS"
    echo "  日志文件: $LOG_FILE"
    echo ""
    
    if [ -f "$PID_FILE" ]; then
        local PID=$(cat "$PID_FILE")
        echo "进程信息:"
        echo "  PID: $PID"
        
        if check_process "$PID"; then
            print_success "服务运行中"
            
            # 显示内存使用
            if command -v ps &> /dev/null; then
                local MEM=$(ps -p $PID -o %mem= 2>/dev/null || echo "N/A")
                local CPU=$(ps -p $PID -o %cpu= 2>/dev/null || echo "N/A")
                echo "  CPU 使用: ${CPU}%"
                echo "  内存使用: ${MEM}%"
            fi
        else
            print_error "服务未运行"
        fi
    else
        print_warning "未找到 PID 文件"
    fi
    
    # 测试连接
    echo ""
    echo "连接测试:"
    if curl -s "$SPEACHES_BASE_URL/health" > /dev/null 2>&1; then
        print_success "服务响应正常"
        
        # 获取模型信息
        local MODEL_COUNT=$(curl -s "$SPEACHES_BASE_URL/v1/models" 2>/dev/null | jq '.data | length' 2>/dev/null || echo "0")
        echo "  已加载模型: $MODEL_COUNT 个"
    else
        print_error "服务未响应"
    fi
}

# 函数：显示日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== 最近日志 (最后 50 行) ==="
        tail -n 50 "$LOG_FILE"
        echo ""
        echo "持续查看日志: tail -f $LOG_FILE"
    else
        print_warning "日志文件不存在"
    fi
}

# 函数：显示帮助
show_help() {
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  start       启动服务（后台模式，默认）"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看服务状态"
    echo "  logs        查看日志"
    echo "  run         前台运行（用于调试）"
    echo "  help        显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  --no-preload    不预加载模型"
    echo "  --timeout=N     设置模型缓存时间（秒）"
    echo ""
    echo "环境变量:"
    echo "  SPEACHES_MODEL_IDLE_TIMEOUT  模型空闲超时（默认：3600秒）"
    echo "  SPEACHES_MAX_MODELS          最大模型数（默认：5）"
    echo ""
    echo "示例:"
    echo "  $0                    # 启动服务（后台）"
    echo "  $0 start              # 启动服务（后台）"
    echo "  $0 run                # 前台运行"
    echo "  $0 restart            # 重启服务"
    echo "  $0 status             # 查看状态"
    echo "  $0 logs               # 查看日志"
    echo "  $0 start --timeout=7200    # 设置2小时缓存"
    echo "  $0 start --no-preload      # 不预加载模型"
}

# 主函数
main() {
    local COMMAND="${1:-start}"
    local NO_PRELOAD=false
    
    # 解析参数
    shift || true
    while [ $# -gt 0 ]; do
        case "$1" in
            --no-preload)
                NO_PRELOAD=true
                ;;
            --timeout=*)
                export SPEACHES_MODEL_IDLE_TIMEOUT="${1#*=}"
                echo "设置模型缓存时间: $SPEACHES_MODEL_IDLE_TIMEOUT 秒"
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
    
    case "$COMMAND" in
        "start")
            stop_old_service
            prepare_environment
            start_service_background
            
            if wait_for_service; then
                if [ "$NO_PRELOAD" = false ]; then
                    preload_models
                fi
                show_status
                echo ""
                print_success "Speaches 服务启动成功！"
            else
                print_error "服务启动失败"
                exit 1
            fi
            ;;
            
        "run")
            stop_old_service
            prepare_environment
            echo ""
            echo "配置信息:"
            echo "  模型缓存时间: $((SPEACHES_MODEL_IDLE_TIMEOUT/3600)) 小时"
            echo "  最大模型数: $SPEACHES_MAX_MODELS"
            echo ""
            print_warning "前台运行模式 - 按 Ctrl+C 停止"
            start_service_foreground
            ;;
            
        "stop")
            stop_old_service
            print_success "服务已停止"
            ;;
            
        "restart")
            # 递归调用
            $0 stop
            sleep 2
            $0 start "$@"
            ;;
            
        "status")
            show_status
            ;;
            
        "logs")
            show_logs
            ;;
            
        "help"|"--help"|"-h")
            show_help
            ;;
            
        *)
            print_error "未知命令: $COMMAND"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"