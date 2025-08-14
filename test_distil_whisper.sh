#!/bin/bash

echo "=== 测试 Systran/faster-distil-whisper-large-v3 ==="
echo ""
echo "说明：在 Speaches 中，已下载的模型会自动加载，无需额外启动服务"
echo ""

# 1. 确认模型已下载
echo "1. 检查模型状态..."
echo "=================="
curl -s "$SPEACHES_BASE_URL/v1/models" | jq '.data[] | select(.id == "Systran/faster-distil-whisper-large-v3")'

# 2. 生成测试音频
echo ""
echo "2. 生成测试音频..."
echo "=================="

# 中文测试
curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
  --output test_chinese_distil.wav \
  --data '{
    "input": "这是一个测试音频，用来测试语音识别的准确性。今天的日期是2024年12月14日。",
    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "voice": "zf_xiaoxiao",
    "response_format": "wav"
  }'
echo "✓ 生成中文测试音频"

# 英文测试
curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
  --output test_english_distil.wav \
  --data '{
    "input": "This is a test audio for speech recognition. The date today is December 14th, 2024.",
    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "voice": "af_heart",
    "response_format": "wav"
  }'
echo "✓ 生成英文测试音频"

# 3. 对比两个模型的识别效果
echo ""
echo "3. 对比识别效果..."
echo "=================="

# 测试函数
compare_models() {
    local audio_file=$1
    local language=$2
    local description=$3
    
    echo ""
    echo "=== $description ==="
    
    # 测试 distil 模型
    echo "使用 faster-distil-whisper-large-v3:"
    start_time=$(date +%s.%N)
    result_distil=$(curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
        -F "file=@$audio_file" \
        -F "model=Systran/faster-distil-whisper-large-v3" \
        -F "language=$language" \
        -F "response_format=json")
    end_time=$(date +%s.%N)
    duration_distil=$(echo "$end_time - $start_time" | bc)
    echo "结果: $(echo "$result_distil" | jq -r '.text' 2>/dev/null || echo "$result_distil")"
    echo "耗时: ${duration_distil}秒"
    
    echo ""
    
    # 测试 large-v3 模型
    echo "使用 faster-whisper-large-v3:"
    start_time=$(date +%s.%N)
    result_large=$(curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
        -F "file=@$audio_file" \
        -F "model=Systran/faster-whisper-large-v3" \
        -F "language=$language" \
        -F "response_format=json")
    end_time=$(date +%s.%N)
    duration_large=$(echo "$end_time - $start_time" | bc)
    echo "结果: $(echo "$result_large" | jq -r '.text' 2>/dev/null || echo "$result_large")"
    echo "耗时: ${duration_large}秒"
    echo "---"
}

# 执行对比测试
compare_models "test_chinese_distil.wav" "zh" "中文识别对比"
compare_models "test_english_distil.wav" "en" "英文识别对比"

# 4. API 服务使用说明
echo ""
echo "4. API 服务使用说明"
echo "=================="
echo ""
echo "HTTP API 使用方式："
echo "curl -s \"\$SPEACHES_BASE_URL/v1/audio/transcriptions\" \\"
echo "  -F \"file=@your_audio.wav\" \\"
echo "  -F \"model=Systran/faster-distil-whisper-large-v3\""
echo ""
echo "支持的参数："
echo "- model: 模型ID"
echo "- language: 语言代码 (zh, en, auto等)"
echo "- prompt: 提供上下文提示"
echo "- response_format: json, text, srt, verbose_json, vtt"
echo "- temperature: 0-1 之间的值"
echo "- timestamp_granularities[]: word 或 segment"
echo ""

# 5. 流式识别说明
echo "5. 实时/流式识别 (WebSocket)"
echo "============================"
echo ""
echo "WebSocket 端点: ws://localhost:8000/v1/realtime"
echo ""
echo "使用示例（需要支持 WebSocket 的客户端）："
echo "- 连接到 ws://localhost:8000/v1/realtime"
echo "- 发送音频流数据"
echo "- 接收实时识别结果"
echo ""
echo "Python WebSocket 示例："
cat << 'EOF'
import asyncio
import websockets
import json

async def transcribe_stream():
    uri = "ws://localhost:8000/v1/realtime"
    async with websockets.connect(uri) as websocket:
        # 发送配置
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "model": "Systran/faster-distil-whisper-large-v3",
                "language": "zh"
            }
        }))
        
        # 发送音频数据
        with open("audio.wav", "rb") as f:
            audio_data = f.read()
            await websocket.send(audio_data)
        
        # 接收识别结果
        result = await websocket.recv()
        print(f"识别结果: {result}")

# 运行
asyncio.run(transcribe_stream())
EOF

echo ""
echo "6. 性能对比总结"
echo "==============="
echo ""
echo "faster-distil-whisper-large-v3:"
echo "- 优点：速度更快，资源占用少"
echo "- 缺点：准确度略低于 large-v3"
echo "- 适用：实时识别、资源受限场景"
echo ""
echo "faster-whisper-large-v3:"
echo "- 优点：准确度最高，支持99+种语言"
echo "- 缺点：速度较慢，资源占用大"
echo "- 适用：离线识别、准确度要求高的场景"