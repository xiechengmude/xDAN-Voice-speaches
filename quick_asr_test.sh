#!/bin/bash

# 快速 ASR 测试脚本

echo "=== 快速 ASR 测试 ==="

# 1. 首先下载推荐的 ASR 模型
echo "1. 下载 ASR 模型..."
echo ""

# 下载最准确的模型
echo "下载 Systran/faster-whisper-large-v3 (最准确，支持中英文)..."
curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-large-v3"
echo ""

# 下载平衡型模型
echo "下载 Systran/faster-whisper-medium (平衡速度和准确度)..."
curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-medium"
echo ""

# 下载快速模型
echo "下载 Systran/faster-whisper-small (速度最快)..."
curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-small"
echo ""

# 2. 查看已安装的模型
echo "2. 已安装的模型："
curl -s "$SPEACHES_BASE_URL/v1/models" | jq '.data[] | {id: .id, task: .task}' | grep -B1 -A1 "automatic-speech-recognition"

# 3. 测试现有的 audio.wav 文件
if [ -f "audio.wav" ]; then
    echo ""
    echo "3. 测试 audio.wav 文件..."
    echo "=========================="
    
    # 使用 large 模型测试
    echo "使用 large 模型识别..."
    curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
        -F "file=@audio.wav" \
        -F "model=Systran/faster-whisper-large-v3" \
        -F "response_format=json" | jq '.'
else
    echo ""
    echo "未找到 audio.wav 文件"
    echo "您可以："
    echo "1. 录制或准备一个音频文件命名为 audio.wav"
    echo "2. 或者运行完整测试脚本: bash test_asr.sh"
fi

# 4. 简单的中英文测试命令示例
echo ""
echo "4. ASR 使用示例："
echo "=========================="
echo ""
echo "# 基本识别（自动检测语言）:"
echo 'curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \'
echo '  -F "file=@your_audio.wav" \'
echo '  -F "model=Systran/faster-whisper-large-v3"'
echo ""
echo "# 指定中文识别:"
echo 'curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \'
echo '  -F "file=@chinese_audio.wav" \'
echo '  -F "model=Systran/faster-whisper-large-v3" \'
echo '  -F "language=zh"'
echo ""
echo "# 获取详细信息（包含时间戳）:"
echo 'curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \'
echo '  -F "file=@audio.wav" \'
echo '  -F "model=Systran/faster-whisper-large-v3" \'
echo '  -F "timestamp_granularities[]=word" \'
echo '  -F "response_format=verbose_json" | jq'
echo ""