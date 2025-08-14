#!/bin/bash

# 运行测试脚本
# 用于测试 Speaches 的 ASR 和 TTS 能力

echo "=== Speaches ASR/TTS 能力测试 ==="
echo ""

# 设置环境变量
export SPEACHES_BASE_URL="${SPEACHES_BASE_URL:-http://localhost:8000}"

echo "服务地址: $SPEACHES_BASE_URL"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要安装 Python 3"
    exit 1
fi

# 安装依赖
echo "检查依赖..."
pip3 install httpx > /dev/null 2>&1 || echo "提示: 可能需要安装 httpx (pip install httpx)"

# 选择测试
echo "请选择测试类型:"
echo "1. 快速测试 (推荐)"
echo "2. ASR 完整测试"
echo "3. TTS 完整测试"
echo "4. 运行所有测试"
echo ""
read -p "请输入选择 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "运行快速测试..."
        python3 quick_test.py
        ;;
    2)
        echo ""
        echo "运行 ASR 完整测试..."
        echo "这将测试多个模型的中英文识别能力，可能需要几分钟..."
        python3 test_asr_capabilities.py
        ;;
    3)
        echo ""
        echo "运行 TTS 完整测试..."
        echo "这将测试不同声音和语言的合成能力，生成多个音频文件..."
        python3 test_tts_capabilities.py
        ;;
    4)
        echo ""
        echo "运行所有测试..."
        python3 quick_test.py
        echo ""
        echo "继续 ASR 测试..."
        python3 test_asr_capabilities.py
        echo ""
        echo "继续 TTS 测试..."
        python3 test_tts_capabilities.py
        ;;
    *)
        echo "无效的选择"
        exit 1
        ;;
esac

echo ""
echo "测试完成！"

# 显示生成的文件
echo ""
echo "生成的文件:"
if [ -f "asr_test_report.json" ]; then
    echo "  - asr_test_report.json (ASR测试报告)"
fi
if [ -f "tts_test_report.json" ]; then
    echo "  - tts_test_report.json (TTS测试报告)"
fi
if [ -d "tts_test_output" ]; then
    echo "  - tts_test_output/ (TTS生成的音频文件)"
    echo "    包含 $(ls tts_test_output/*.wav 2>/dev/null | wc -l) 个音频文件"
fi
if [ -f "tts_chinese.wav" ] || [ -f "tts_english.wav" ] || [ -f "tts_mixed.wav" ]; then
    echo "  - tts_*.wav (快速测试音频)"
fi