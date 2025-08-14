#!/bin/bash

echo "=== 测试 ASR 并发支持 ==="
echo "使用模型: Systran/faster-distil-whisper-large-v3"
echo ""

# 1. 准备测试音频
echo "1. 准备测试音频..."
for i in {1..5}; do
    curl -s "$SPEACHES_BASE_URL/v1/audio/speech" -H "Content-Type: application/json" \
      --output "test_concurrent_${i}.wav" \
      --data "{
        \"input\": \"这是第${i}个测试音频。用于测试并发识别功能。当前时间是$(date +%H:%M:%S)。\",
        \"model\": \"speaches-ai/Kokoro-82M-v1.0-ONNX\",
        \"voice\": \"zf_xiaoxiao\",
        \"response_format\": \"wav\"
      }"
done
echo "✓ 生成了 5 个测试音频"

# 2. 单个请求测试（基准）
echo ""
echo "2. 单个请求基准测试..."
start_time=$(date +%s.%N)
curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
    -F "file=@test_concurrent_1.wav" \
    -F "model=Systran/faster-distil-whisper-large-v3" \
    -F "language=zh" | jq -r '.text'
end_time=$(date +%s.%N)
single_duration=$(echo "$end_time - $start_time" | bc)
echo "单个请求耗时: ${single_duration}秒"

# 3. 并发测试函数
test_concurrent_request() {
    local file_num=$1
    local start=$(date +%s.%N)
    
    result=$(curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
        -F "file=@test_concurrent_${file_num}.wav" \
        -F "model=Systran/faster-distil-whisper-large-v3" \
        -F "language=zh")
    
    local end=$(date +%s.%N)
    local duration=$(echo "$end - $start" | bc)
    
    echo "请求 #$file_num 完成 - 耗时: ${duration}秒"
    echo "$result" | jq -r '.text' 2>/dev/null
}

# 4. 并发测试
echo ""
echo "3. 并发测试（5个同时请求）..."
echo "================================"
start_concurrent=$(date +%s.%N)

# 使用后台进程实现并发
for i in {1..5}; do
    test_concurrent_request $i &
done

# 等待所有后台进程完成
wait

end_concurrent=$(date +%s.%N)
total_duration=$(echo "$end_concurrent - $start_concurrent" | bc)
echo ""
echo "并发请求总耗时: ${total_duration}秒"
echo "平均每个请求: $(echo "scale=2; $total_duration / 5" | bc)秒"

# 5. 服务配置检查
echo ""
echo "4. 检查服务配置..."
echo "=================="
echo "提示：Speaches 支持动态模型加载和多实例管理"
echo "- 模型会根据需求自动加载"
echo "- 空闲时自动卸载以节省资源"
echo "- 支持多用户并发请求"

# 清理测试文件
rm -f test_concurrent_*.wav