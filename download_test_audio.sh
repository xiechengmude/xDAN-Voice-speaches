#!/bin/bash

echo "=== 下载公开的中文测试音频 ==="
echo ""

# 创建测试音频目录
mkdir -p test_audio
cd test_audio

# 1. 使用 TTS 生成测试音频（最可靠的方法）
echo "1. 使用 TTS 生成测试音频..."
if curl -s "$SPEACHES_BASE_URL/v1/models" | grep -q "Kokoro-82M"; then
    # 生成纯中文测试
    curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
      --output chinese_news.wav \
      --data '{
        "input": "据新华社报道，中国科学院今天宣布，在人工智能领域取得重大突破。这项新技术将应用于医疗诊断和自动驾驶等多个领域。专家表示，这标志着我国在人工智能研究方面已经达到国际先进水平。",
        "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "voice": "zf_xiaoxiao",
        "response_format": "wav"
      }'
    echo "✓ 生成中文新闻音频: chinese_news.wav"
    
    # 生成中文对话
    curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
      --output chinese_dialogue.wav \
      --data '{
        "input": "你好，欢迎来到北京。今天天气怎么样？我觉得今天天气不错，温度大概二十五度左右，很适合出去游玩。你打算去哪里参观？我推荐你去故宫和长城看看。",
        "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "voice": "zm_yunxi",
        "response_format": "wav"
      }'
    echo "✓ 生成中文对话音频: chinese_dialogue.wav"
    
    # 生成中英混合
    curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
      --output chinese_english_mixed.wav \
      --data '{
        "input": "大家好，我是AI助手。Today我们来学习machine learning的基础知识。首先，我们需要了解什么是neural network，也就是神经网络。这个concept在深度学习中非常important。",
        "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "voice": "af_nicole",
        "response_format": "wav"
      }'
    echo "✓ 生成中英混合音频: chinese_english_mixed.wav"
    
    # 生成数字和日期测试
    curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
      --output chinese_numbers.wav \
      --data '{
        "input": "今天是2024年12月14日，星期六。现在的时间是下午3点45分。电话号码是13812345678。价格是299.99元。圆周率约等于3.14159。",
        "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "voice": "zf_xiaobei",
        "response_format": "wav"
      }'
    echo "✓ 生成数字日期音频: chinese_numbers.wav"
else
    echo "✗ 未找到 TTS 模型，无法生成测试音频"
fi

# 2. 下载公开的音频样本（如果有的话）
echo ""
echo "2. 尝试下载公开音频样本..."

# Common Voice 项目的样本（Mozilla 的开源语音数据）
# 注意：这些是示例URL，实际使用时需要从 Common Voice 官网获取
echo "提示：您可以从以下来源获取公开的中文音频："
echo "- Mozilla Common Voice: https://commonvoice.mozilla.org/zh-CN"
echo "- OpenSLR: http://www.openslr.org/resources.php"
echo "- AI Shell: http://www.aishelltech.com/kysjcp"

# 3. 创建一个简单的录音脚本（如果系统支持）
echo ""
echo "3. 创建录音脚本..."
cat > record_audio.sh << 'EOF'
#!/bin/bash
echo "准备录制音频（5秒）..."
echo "3秒后开始录音..."
sleep 3
echo "开始录音！"

# macOS 录音命令
if [[ "$OSTYPE" == "darwin"* ]]; then
    sox -d -r 16000 -c 1 -b 16 recorded_audio.wav trim 0 5
elif command -v arecord &> /dev/null; then
    # Linux with ALSA
    arecord -d 5 -f S16_LE -r 16000 -c 1 recorded_audio.wav
else
    echo "未找到录音工具，请安装 sox 或 arecord"
fi

echo "录音完成！保存为 recorded_audio.wav"
EOF
chmod +x record_audio.sh

echo "✓ 创建录音脚本: record_audio.sh"
echo ""
echo "=== 测试音频准备完成 ==="
echo ""
echo "生成的测试音频文件："
ls -la *.wav 2>/dev/null || echo "（暂无音频文件）"
echo ""
echo "现在可以测试这些音频文件了！"