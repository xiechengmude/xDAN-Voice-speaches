#!/bin/bash

# ASR 模型测试脚本
# 测试支持中英文的语音识别模型

echo "=== Speaches ASR 模型测试 ==="
echo "测试中英文语音识别能力"
echo ""

# 设置基础 URL
if [ -z "$SPEACHES_BASE_URL" ]; then
    export SPEACHES_BASE_URL="http://localhost:8000"
fi

echo "服务地址: $SPEACHES_BASE_URL"
echo ""

# 1. 查看可用的 ASR 模型
echo "1. 查看可用的 ASR 模型..."
echo "=========================="
curl -s "$SPEACHES_BASE_URL/v1/registry?task=automatic-speech-recognition" | jq '.data[] | {id: .id, languages: .languages}' 2>/dev/null || echo "提示：需要安装 jq 来查看格式化输出"

# 推荐的支持中英文的 ASR 模型
MODELS=(
    "Systran/faster-whisper-large-v3"           # 最准确，支持多语言
    "Systran/faster-whisper-medium"             # 平衡选择
    "Systran/faster-whisper-small"              # 速度快
    "openai/whisper-large-v3"                   # OpenAI 原版
)

# 2. 下载模型
echo ""
echo "2. 下载推荐的 ASR 模型..."
echo "=========================="
for model in "${MODELS[@]}"; do
    echo "下载模型: $model"
    response=$(curl -s -X POST "$SPEACHES_BASE_URL/v1/models/$model" 2>&1)
    if [[ $response == *"already exists"* ]]; then
        echo "✓ 模型已存在"
    elif [[ $response == *"error"* ]]; then
        echo "✗ 下载失败: $response"
    else
        echo "✓ 下载成功"
    fi
    echo ""
done

# 3. 检查已安装的模型
echo "3. 已安装的 ASR 模型..."
echo "=========================="
curl -s "$SPEACHES_BASE_URL/v1/models" | jq '.data[] | select(.task == "automatic-speech-recognition") | {id: .id, created: .created}'

# 4. 创建测试音频（如果需要）
echo ""
echo "4. 准备测试音频..."
echo "=========================="

# 检查是否已有测试音频
if [ ! -f "test_chinese.wav" ] || [ ! -f "test_english.wav" ] || [ ! -f "test_mixed.wav" ]; then
    echo "创建测试音频文件..."
    
    # 使用已有的 TTS 模型创建测试音频
    if curl -s "$SPEACHES_BASE_URL/v1/models" | grep -q "Kokoro-82M"; then
        # 中文测试音频
        curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
          --output test_chinese.wav \
          --data '{
            "input": "今天天气真好，适合出去散步。人工智能技术发展迅速。",
            "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
            "voice": "zf_xiaoxiao",
            "response_format": "wav"
          }'
        echo "✓ 创建中文测试音频"
        
        # 英文测试音频
        curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
          --output test_english.wav \
          --data '{
            "input": "The weather is beautiful today. Artificial intelligence is advancing rapidly.",
            "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
            "voice": "af_heart",
            "response_format": "wav"
          }'
        echo "✓ 创建英文测试音频"
        
        # 中英混合测试音频
        curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
          --output test_mixed.wav \
          --data '{
            "input": "Hello大家好，这是一个mixed language测试。AI技术very powerful。",
            "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
            "voice": "af_nicole",
            "response_format": "wav"
          }'
        echo "✓ 创建中英混合测试音频"
    else
        echo "提示：如果没有测试音频，请准备以下文件："
        echo "- test_chinese.wav (中文音频)"
        echo "- test_english.wav (英文音频)"
        echo "- test_mixed.wav (中英混合音频)"
        echo "- audio.wav (您自己的测试音频)"
    fi
fi

# 5. 测试函数
test_asr_model() {
    local model=$1
    local audio_file=$2
    local test_name=$3
    
    echo ""
    echo "测试: $test_name"
    echo "模型: $model"
    echo "音频: $audio_file"
    
    if [ ! -f "$audio_file" ]; then
        echo "✗ 音频文件不存在: $audio_file"
        return
    fi
    
    # 记录开始时间
    start_time=$(date +%s.%N)
    
    # 执行识别
    result=$(curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
        -F "file=@$audio_file" \
        -F "model=$model" \
        -F "language=zh" \
        -F "response_format=json")
    
    # 记录结束时间
    end_time=$(date +%s.%N)
    
    # 计算耗时
    duration=$(echo "$end_time - $start_time" | bc)
    
    # 显示结果
    if [ -n "$result" ]; then
        echo "✓ 识别成功 (耗时: ${duration}秒)"
        echo "结果: $result"
    else
        echo "✗ 识别失败"
    fi
    echo "---"
}

# 6. 执行测试
echo ""
echo "5. 执行 ASR 识别测试..."
echo "=========================="

# 选择一个可用的模型进行测试
AVAILABLE_MODEL=""
for model in "${MODELS[@]}"; do
    if curl -s "$SPEACHES_BASE_URL/v1/models" | grep -q "$model"; then
        AVAILABLE_MODEL="$model"
        break
    fi
done

if [ -z "$AVAILABLE_MODEL" ]; then
    echo "✗ 没有找到已安装的 ASR 模型，请先下载模型"
    exit 1
fi

echo "使用模型: $AVAILABLE_MODEL"

# 测试不同的音频文件
test_asr_model "$AVAILABLE_MODEL" "test_chinese.wav" "中文识别"
test_asr_model "$AVAILABLE_MODEL" "test_english.wav" "英文识别"
test_asr_model "$AVAILABLE_MODEL" "test_mixed.wav" "中英混合识别"

# 如果存在用户的音频文件
if [ -f "audio.wav" ]; then
    test_asr_model "$AVAILABLE_MODEL" "audio.wav" "用户音频识别"
fi

# 7. 批量测试所有模型（可选）
echo ""
echo "6. 是否测试所有已安装的模型？(y/n)"
read -r answer

if [ "$answer" = "y" ]; then
    echo ""
    echo "批量测试所有模型..."
    echo "=========================="
    
    # 获取所有已安装的 ASR 模型
    installed_models=$(curl -s "$SPEACHES_BASE_URL/v1/models" | jq -r '.data[] | select(.task == "automatic-speech-recognition") | .id')
    
    for model in $installed_models; do
        echo ""
        echo "=== 测试模型: $model ==="
        test_asr_model "$model" "test_chinese.wav" "中文识别"
        test_asr_model "$model" "test_english.wav" "英文识别"
        test_asr_model "$model" "test_mixed.wav" "中英混合识别"
    done
fi

echo ""
echo "测试完成！"
echo ""
echo "建议："
echo "1. faster-whisper-large-v3: 最准确，适合对精度要求高的场景"
echo "2. faster-whisper-medium: 平衡选择，速度和精度都不错"
echo "3. faster-whisper-small: 速度最快，适合实时场景"