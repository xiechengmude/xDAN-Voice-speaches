#!/bin/bash

echo "=== 测试 Whisper Large V3 中文识别 ==="
echo ""

# 1. 先生成测试音频
echo "1. 生成中文测试音频..."
echo ""

# 测试1: 日常对话
curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
  --output test_daily_conversation.wav \
  --data '{
    "input": "你好，我想订一张明天去上海的高铁票。请问最早的一班是几点？票价多少钱？需要提前多久到达车站？",
    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "voice": "zf_xiaoxiao",
    "response_format": "wav"
  }'
echo "✓ 生成日常对话音频"

# 测试2: 新闻播报风格
curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
  --output test_news_style.wav \
  --data '{
    "input": "各位观众大家好，欢迎收看今日新闻。据最新消息，我国成功发射了新一代通信卫星，这将大大提升偏远地区的网络覆盖能力。",
    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "voice": "zm_yunyang",
    "response_format": "wav"
  }'
echo "✓ 生成新闻播报音频"

# 测试3: 技术内容
curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
  --output test_technical.wav \
  --data '{
    "input": "人工智能模型的训练需要大量的数据和计算资源。目前，大语言模型的参数量已经达到了千亿级别，训练成本也越来越高。",
    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "voice": "zm_yunxi",
    "response_format": "wav"
  }'
echo "✓ 生成技术内容音频"

# 2. 测试 ASR 识别
echo ""
echo "2. 使用 Systran/faster-whisper-large-v3 进行识别..."
echo "================================================"

# 测试函数
test_recognition() {
    local audio_file=$1
    local description=$2
    
    echo ""
    echo "测试: $description"
    echo "文件: $audio_file"
    
    # 开始计时
    start_time=$(date +%s)
    
    # 执行识别
    result=$(curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
        -F "file=@$audio_file" \
        -F "model=Systran/faster-whisper-large-v3" \
        -F "language=zh" \
        -F "response_format=json")
    
    # 结束计时
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    # 显示结果
    echo "耗时: ${duration}秒"
    echo "识别结果:"
    echo "$result" | jq -r '.text' 2>/dev/null || echo "$result"
    echo "---"
}

# 执行测试
test_recognition "test_daily_conversation.wav" "日常对话"
test_recognition "test_news_style.wav" "新闻播报"
test_recognition "test_technical.wav" "技术内容"

# 3. 测试带时间戳的识别
echo ""
echo "3. 测试带时间戳的识别..."
echo "========================"

curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
    -F "file=@test_daily_conversation.wav" \
    -F "model=Systran/faster-whisper-large-v3" \
    -F "language=zh" \
    -F "timestamp_granularities[]=word" \
    -F "response_format=verbose_json" | jq '.words[:5]'

echo ""
echo "测试完成！"
echo ""
echo "提示："
echo "1. 如果识别结果不理想，可以尝试不指定 language 参数，让模型自动检测"
echo "2. 可以使用 'prompt' 参数提供上下文，提高识别准确度"
echo "3. 使用 'temperature' 参数（0-1）控制识别的创造性"