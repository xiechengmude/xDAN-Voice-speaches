# Speaches ASR/TTS 测试示例

本目录包含用于测试 Speaches 服务中英文语音识别（ASR）和语音合成（TTS）能力的脚本。

## 测试脚本说明

### 1. quick_test.py - 快速测试
- **用途**：快速验证 ASR 和 TTS 基本功能
- **测试内容**：
  - 生成中文、英文、中英混合语音
  - 识别生成的语音文件
  - 显示可用模型列表
- **运行时间**：约 30 秒

### 2. test_asr_capabilities.py - ASR 完整测试
- **用途**：全面测试语音识别能力
- **测试内容**：
  - 多个 ASR 模型对比（large-v3, distil-large-v3, medium, small）
  - 中文识别测试（日常对话、技术术语、数字等）
  - 英文识别测试（问候、技术内容、联系信息等）
  - 中英混合识别测试
  - 准确率计算和性能统计
- **输出**：
  - 控制台实时显示
  - `asr_test_report.json` 详细报告
- **运行时间**：约 5-10 分钟

### 3. test_tts_capabilities.py - TTS 完整测试
- **用途**：全面测试语音合成能力
- **测试内容**：
  - 声音质量测试（不同模型对比）
  - 语言能力测试（中文、英文、混合）
  - 语速变化测试（0.5x - 2.0x）
  - 声音对比（男声、女声、不同口音）
- **输出**：
  - 控制台实时显示
  - `tts_test_report.json` 详细报告
  - `tts_test_output/` 目录下的音频文件
- **运行时间**：约 5-10 分钟

## 使用方法

### 方法一：使用运行脚本（推荐）
```bash
cd tests/examples
chmod +x run_tests.sh
./run_tests.sh
```

然后选择：
- 1: 快速测试
- 2: ASR 完整测试
- 3: TTS 完整测试
- 4: 运行所有测试

### 方法二：直接运行 Python 脚本
```bash
# 快速测试
python3 quick_test.py

# ASR 完整测试
python3 test_asr_capabilities.py

# TTS 完整测试
python3 test_tts_capabilities.py
```

## 环境要求

1. **Python 3.6+**
2. **依赖包**：
   ```bash
   pip install httpx
   ```
3. **Speaches 服务**：
   - 确保 Speaches 服务正在运行
   - 默认地址：`http://localhost:8000`
   - 可通过环境变量修改：`export SPEACHES_BASE_URL="http://your-server:8000"`

## 测试结果解读

### ASR 测试结果
- **准确率**：基于最长公共子序列（LCS）算法计算
- **耗时**：包括网络传输和模型处理时间
- **模型对比**：
  - `large-v3`：最准确，但速度较慢
  - `distil-large-v3`：平衡选择，推荐使用
  - `small`：速度最快，准确度较低

### TTS 测试结果
- **音频质量**：检查采样率、时长、文件大小
- **语速准确性**：对比设置语速和实际音频时长
- **声音特点**：
  - 中文女声：晓晓、晓贝、晓妮、晓伊
  - 中文男声：云熙、云健、云夏、云扬
  - 英文声音：多种美式和英式口音

## 测试用例示例

### ASR 测试用例
```python
# 中文
"今天天气真好，适合出去散步。"
"人工智能技术正在改变我们的生活方式。"
"电话号码是13812345678。"

# 英文
"The weather is beautiful today."
"Artificial intelligence is revolutionizing industries."

# 混合
"Hello大家好，欢迎参加今天的meeting。"
"Python版本是3.9，TensorFlow版本是2.10.0。"
```

### TTS 测试用例
```python
# 不同语速
speeds = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]

# 不同声音
chinese_voices = ["zf_xiaoxiao", "zm_yunxi"]
english_voices = ["af_heart", "am_adam"]
```

## 常见问题

1. **连接失败**
   - 检查 Speaches 服务是否运行
   - 确认服务地址正确
   - 检查防火墙设置

2. **模型未找到**
   - 先下载所需模型
   - 使用 `curl -X POST "$SPEACHES_BASE_URL/v1/models/模型名"`

3. **音频文件无法播放**
   - 确保生成格式为 WAV
   - 检查音频播放器支持

## 扩展使用

可以修改测试脚本来：
- 测试特定领域的语音（医疗、法律、技术等）
- 添加噪音环境下的识别测试
- 测试长音频的处理能力
- 批量处理性能测试