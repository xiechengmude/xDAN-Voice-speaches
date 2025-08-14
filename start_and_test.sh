#!/bin/bash

# 启动 Speaches 服务并运行测试

echo "=== Speaches 服务启动和测试脚本 ==="
echo ""

# 设置变量
PROJECT_DIR="/Users/gump_m2/Documents/Agent-RL/xDAN-Voice-speaches"
export SPEACHES_BASE_URL="http://localhost:8000"

cd "$PROJECT_DIR"

# 检查服务是否已经运行
check_service() {
    curl -s "$SPEACHES_BASE_URL/health" > /dev/null 2>&1
    return $?
}

# 启动服务的函数
start_service() {
    echo "选择启动方式:"
    echo "1. Docker Compose (推荐)"
    echo "2. Python 开发环境"
    echo "3. 跳过启动（服务已运行）"
    read -p "请选择 (1-3): " choice
    
    case $choice in
        1)
            echo "使用 Docker Compose 启动..."
            if [ -f "compose.cpu.yaml" ]; then
                export COMPOSE_FILE=compose.cpu.yaml
                docker compose up -d
                echo "等待服务启动..."
                sleep 10
            else
                echo "错误: 找不到 compose.cpu.yaml"
                return 1
            fi
            ;;
        2)
            echo "使用 Python 开发环境启动..."
            if command -v uv &> /dev/null; then
                # 创建虚拟环境
                if [ ! -d ".venv" ]; then
                    echo "创建虚拟环境..."
                    uv venv
                fi
                
                # 激活虚拟环境并安装依赖
                source .venv/bin/activate
                echo "安装依赖..."
                uv sync --all-extras
                
                # 后台启动服务
                echo "启动服务..."
                nohup uvicorn --factory --host 0.0.0.0 speaches.main:create_app > speaches.log 2>&1 &
                echo $! > speaches.pid
                echo "服务 PID: $(cat speaches.pid)"
                echo "等待服务启动..."
                sleep 10
            else
                echo "错误: 需要安装 uv"
                return 1
            fi
            ;;
        3)
            echo "跳过服务启动"
            ;;
        *)
            echo "无效选择"
            return 1
            ;;
    esac
}

# 下载必要的模型
download_models() {
    echo ""
    echo "下载测试所需的模型..."
    
    # ASR 模型
    echo "下载 ASR 模型..."
    curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-large-v3" || echo "ASR 模型可能已存在"
    
    # TTS 模型
    echo "下载 TTS 模型..."
    curl -X POST "$SPEACHES_BASE_URL/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX" || echo "TTS 模型可能已存在"
    
    echo ""
}

# 运行测试
run_tests() {
    echo ""
    echo "开始运行测试..."
    cd "$PROJECT_DIR/tests/examples"
    
    # 安装测试依赖
    pip3 install httpx > /dev/null 2>&1
    
    # 运行快速测试
    echo ""
    echo "=== 运行快速测试 ==="
    python3 quick_test.py
    
    # 询问是否运行完整测试
    echo ""
    read -p "是否运行完整测试？(y/n): " answer
    if [ "$answer" = "y" ]; then
        echo ""
        echo "=== 运行 ASR 完整测试 ==="
        python3 test_asr_capabilities.py
        
        echo ""
        echo "=== 运行 TTS 完整测试 ==="
        python3 test_tts_capabilities.py
    fi
}

# 主流程
main() {
    # 检查服务状态
    if check_service; then
        echo "✓ Speaches 服务已在运行"
    else
        echo "✗ Speaches 服务未运行"
        start_service
        
        # 再次检查
        if ! check_service; then
            echo "错误: 服务启动失败"
            echo "请检查日志文件 speaches.log"
            exit 1
        fi
        echo "✓ 服务启动成功"
    fi
    
    # 下载模型
    download_models
    
    # 运行测试
    run_tests
    
    echo ""
    echo "=== 测试完成 ==="
    echo ""
    echo "查看结果:"
    echo "- 测试报告: tests/examples/*.json"
    echo "- 生成的音频: tests/examples/tts_test_output/"
    echo "- 服务日志: speaches.log"
    
    # 提示停止服务
    if [ -f "speaches.pid" ]; then
        echo ""
        echo "停止服务请运行: kill $(cat speaches.pid)"
    fi
}

# 运行主流程
main