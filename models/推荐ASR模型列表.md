# 支持中英文的 ASR 模型推荐

## 一、Whisper 系列模型（推荐）

### 1. **Systran/faster-whisper-large-v3** ⭐⭐⭐⭐⭐
- **准确度**: 最高
- **速度**: 较慢
- **模型大小**: 约 1.5GB
- **支持语言**: 99+ 种语言（包括中英文）
- **特点**: 
  - 最新的 Whisper V3 架构
  - 中英文识别准确度最高
  - 支持自动语言检测
  - 适合离线批处理
- **下载命令**:
  ```bash
  curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-large-v3"
  ```

### 2. **Systran/faster-distil-whisper-large-v3** ⭐⭐⭐⭐
- **准确度**: 高（略低于 large-v3）
- **速度**: 快（比 large-v3 快约 2 倍）
- **模型大小**: 约 750MB
- **支持语言**: 多语言（包括中英文）
- **特点**:
  - 蒸馏版本，性能优化
  - 资源占用减半
  - 保持较高准确度
  - 适合实时应用
- **下载命令**:
  ```bash
  curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-large-v3"
  ```

### 3. **Systran/faster-whisper-medium** ⭐⭐⭐
- **准确度**: 良好
- **速度**: 快
- **模型大小**: 约 750MB
- **支持语言**: 多语言（包括中英文）
- **特点**:
  - 平衡选择
  - 适合一般应用场景
  - 资源占用适中
- **下载命令**:
  ```bash
  curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-medium"
  ```

### 4. **Systran/faster-whisper-small** ⭐⭐
- **准确度**: 一般
- **速度**: 非常快
- **模型大小**: 约 250MB
- **支持语言**: 多语言（包括中英文）
- **特点**:
  - 速度优先
  - 适合边缘设备
  - 实时性要求高的场景
- **下载命令**:
  ```bash
  curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-small"
  ```

### 5. **openai/whisper-large-v3** ⭐⭐⭐⭐
- **准确度**: 最高（原版）
- **速度**: 慢
- **模型大小**: 约 1.5GB
- **支持语言**: 99+ 种语言
- **特点**:
  - OpenAI 原版模型
  - 准确度基准
  - 资源要求高
- **下载命令**:
  ```bash
  curl -X POST "$SPEACHES_BASE_URL/v1/models/openai/whisper-large-v3"
  ```

## 二、使用建议

### 场景选择指南

1. **高准确度需求（字幕制作、会议记录）**
   - 首选: `Systran/faster-whisper-large-v3`
   - 备选: `openai/whisper-large-v3`

2. **实时识别需求（语音助手、实时翻译）**
   - 首选: `Systran/faster-distil-whisper-large-v3`
   - 备选: `Systran/faster-whisper-medium`

3. **资源受限环境（边缘设备、移动端）**
   - 首选: `Systran/faster-whisper-small`
   - 备选: `Systran/faster-whisper-medium`

4. **批量处理（视频字幕、音频转文字）**
   - 首选: `Systran/faster-whisper-large-v3`
   - 备选: `Systran/faster-distil-whisper-large-v3`

### 中文识别优化建议

```bash
# 1. 指定中文语言（提高准确度）
curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
  -F "file=@chinese_audio.wav" \
  -F "model=Systran/faster-whisper-large-v3" \
  -F "language=zh"

# 2. 提供上下文提示
curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
  -F "file=@audio.wav" \
  -F "model=Systran/faster-whisper-large-v3" \
  -F "language=zh" \
  -F "prompt=这是一段关于人工智能的技术讨论"

# 3. 自动检测语言（中英混合）
curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
  -F "file=@mixed_audio.wav" \
  -F "model=Systran/faster-whisper-large-v3"
```

## 三、性能对比

| 模型 | 中文准确度 | 英文准确度 | 速度 | 内存占用 | 推荐场景 |
|------|-----------|-----------|------|----------|----------|
| large-v3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 高 | 离线高精度 |
| distil-large-v3 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | 实时识别 |
| medium | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | 通用场景 |
| small | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 低 | 边缘设备 |

## 四、快速测试命令

```bash
# 下载推荐的模型
curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-large-v3"
curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-large-v3"

# 测试中文识别
curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
  -F "file=@test.wav" \
  -F "model=Systran/faster-whisper-large-v3" \
  -F "language=zh" | jq

# 对比不同模型
bash test_distil_whisper.sh
```