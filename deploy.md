# Speaches 部署和使用指南

## 环境准备

设置环境变量（建议添加到 ~/.bashrc 或 ~/.zshrc）：
```bash
# 设置 Speaches 服务地址（默认本地服务）
export SPEACHES_BASE_URL="http://localhost:8000"

# 如果使用远程服务器，修改为实际地址
# export SPEACHES_BASE_URL="http://your-server-ip:8000"
```

验证环境变量：
```bash
echo $SPEACHES_BASE_URL
```

## 一、安装和启动

### 方法1：使用 Docker Compose（推荐）

```bash
# CPU 版本
curl --silent --remote-name https://raw.githubusercontent.com/speaches-ai/speaches/master/compose.yaml
curl --silent --remote-name https://raw.githubusercontent.com/speaches-ai/speaches/master/compose.cpu.yaml
export COMPOSE_FILE=compose.cpu.yaml
docker compose up --detach

# GPU 版本（需要 NVIDIA GPU）
curl --silent --remote-name https://raw.githubusercontent.com/speaches-ai/speaches/master/compose.yaml
curl --silent --remote-name https://raw.githubusercontent.com/speaches-ai/speaches/master/compose.cuda.yaml
export COMPOSE_FILE=compose.cuda.yaml
docker compose up --detach
```

### 方法2：使用 Python 开发环境

```bash
# 克隆项目
git clone https://github.com/speaches-ai/speaches.git
cd speaches

# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv sync --all-extras

# 启动服务器
uvicorn --factory --host 0.0.0.0 speaches.main:create_app
```

### 方法3：使用 Task 命令

```bash
# 启动服务器
task server

# 运行测试
task test
```

## 二、模型管理

### 查看可用模型

```bash
# 查看所有可用模型
curl "$SPEACHES_BASE_URL/v1/registry"

# 按任务类型筛选模型
curl "$SPEACHES_BASE_URL/v1/registry?task=automatic-speech-recognition"  # STT 模型
curl "$SPEACHES_BASE_URL/v1/registry?task=text-to-speech"                # TTS 模型
```

### 下载模型

```bash
# 下载 STT 模型
curl "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-small.en" -X POST

# 下载 TTS 模型
curl "$SPEACHES_BASE_URL/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX" -X POST

# 查看已下载的模型
curl "$SPEACHES_BASE_URL/v1/models"
```

### 模型别名配置

在 `model_aliases.json` 文件中配置模型别名：

```json
{
  "tts-1": "speaches-ai/Kokoro-82M-v1.0-ONNX",
  "tts-1-hd": "speaches-ai/Kokoro-82M-v1.0-ONNX",
  "whisper-1": "Systran/faster-whisper-large-v3"
}
```

使用别名：
```bash
# 使用别名下载模型
curl "$SPEACHES_BASE_URL/v1/models/whisper-1" -X POST

# 等同于
curl "$SPEACHES_BASE_URL/v1/models/Systran/faster-whisper-large-v3" -X POST
```

⚠️ 注意：修改 model_aliases.json 后需要重启服务器。


## 三、语音转文字 (STT)

### 下载 STT 模型

使用 Speaches CLI：
```bash
# 列出所有可用的 STT 模型
uvx speaches-cli registry ls --task automatic-speech-recognition | jq '.data | [].id'

# 下载模型
uvx speaches-cli model download Systran/faster-distil-whisper-small.en

# 确认模型已安装
uvx speaches-cli model ls --task automatic-speech-recognition | jq '.data | map(select(.id == "Systran/faster-distil-whisper-small.en"))'
```

或使用 cURL：
```bash
# 下载模型
curl "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-small.en" -X POST
```
### STT 调用示例

#### 使用 cURL

```bash
export TRANSCRIPTION_MODEL_ID="Systran/faster-distil-whisper-small.en"

# 基本转录
curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
  -F "file=@audio.wav" \
  -F "model=$TRANSCRIPTION_MODEL_ID"

# 带时间戳的转录
curl -s "$SPEACHES_BASE_URL/v1/audio/transcriptions" \
  -F "file=@audio.wav" \
  -F "model=$TRANSCRIPTION_MODEL_ID" \
  -F "timestamp_granularities[]=word" \
  -F "response_format=verbose_json"
```
#### 使用 Python (httpx)

```python
import httpx

TRANSCRIPTION_MODEL_ID = "Systran/faster-distil-whisper-small.en"

with open('audio.wav', 'rb') as f:
    files = {'file': ('audio.wav', f)}
    data = {'model': TRANSCRIPTION_MODEL_ID}
    response = httpx.post(
        'http://localhost:8000/v1/audio/transcriptions',
        files=files,
        data=data
    )

print(response.json())
```

#### 使用 OpenAI SDK

```python
from pathlib import Path
from openai import OpenAI

# 设置客户端（需要假的 API key）
client = OpenAI(
    api_key="sk-fake-key",  # 任意非空值
    base_url="http://localhost:8000/v1"
)

with Path("audio.wav").open("rb") as audio_file:
    transcription = client.audio.transcriptions.create(
        model="Systran/faster-distil-whisper-small.en",
        file=audio_file
    )

print(transcription.text)
```



## 四、文字转语音 (TTS)

### 下载 TTS 模型

使用 Speaches CLI：
```bash
# 列出所有可用的 TTS 模型
uvx speaches-cli registry ls --task text-to-speech | jq '.data | [].id'

# 下载模型
uvx speaches-cli model download speaches-ai/Kokoro-82M-v1.0-ONNX

# 确认模型已安装
uvx speaches-cli model ls --task text-to-speech | jq '.data | map(select(.id == "speaches-ai/Kokoro-82M-v1.0-ONNX"))'
```

或使用 cURL：
```bash
# 下载模型
curl "$SPEACHES_BASE_URL/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX" -X POST
```
### TTS 调用示例

#### 使用 cURL

```bash
export SPEECH_MODEL_ID="speaches-ai/Kokoro-82M-v1.0-ONNX"
export VOICE_ID="af_heart"  # 可用语音：af_heart, af_bella, af_nicole 等

# 生成 MP3 格式语音
curl "$SPEACHES_BASE_URL/v1/audio/speech" -s -H "Content-Type: application/json" \
  --output output.mp3 \
  --data @- << EOF
{
  "input": "你好，世界！",
  "model": "$SPEECH_MODEL_ID",
  "voice": "$VOICE_ID"
}
EOF

# 生成 WAV 格式语音
curl "$SPEACHES_BASE_URL/v1/audio/speech" -s -H "Content-Type: application/json" \
  --output output.wav \
  --data @- << EOF
{
  "input": "你好，世界！",
  "model": "$SPEECH_MODEL_ID",
  "voice": "$VOICE_ID",
  "response_format": "wav"
}
EOF

# 调整语速（2.0 = 2倍速）
curl "$SPEACHES_BASE_URL/v1/audio/speech" -s -H "Content-Type: application/json" \
  --output output_fast.mp3 \
  --data @- << EOF
{
  "input": "你好，世界！",
  "model": "$SPEECH_MODEL_ID",
  "voice": "$VOICE_ID",
  "speed": 2.0
}
EOF
```
#### 使用 Python (httpx)

```python
from pathlib import Path
import httpx

client = httpx.Client(base_url="http://localhost:8000/")
model_id = "speaches-ai/Kokoro-82M-v1.0-ONNX"
voice_id = "af_heart"

res = client.post(
    "v1/audio/speech",
    json={
        "model": model_id,
        "voice": voice_id,
        "input": "你好，世界！",
        "response_format": "mp3",
        "speed": 1.0,
    },
).raise_for_status()

with Path("output.mp3").open("wb") as f:
    f.write(res.read())
```

#### 使用 OpenAI SDK

```python
from pathlib import Path
from openai import OpenAI

# 设置客户端（需要假的 API key）
client = OpenAI(
    api_key="sk-fake-key",  # 任意非空值
    base_url="http://localhost:8000/v1"
)

response = client.audio.speech.create(
    model="speaches-ai/Kokoro-82M-v1.0-ONNX",
    voice="af_heart",
    input="你好，世界！"
)

response.write_to_file("output.mp3")
```

## 五、实时语音交互

```bash
# WebSocket 连接
ws://localhost:8000/v1/realtime

# WebRTC 连接
http://localhost:8000/rtc/offer
```

## 六、健康检查

```bash
# 检查服务状态
curl "$SPEACHES_BASE_URL/health"
```

## 注意事项

1. **API 兼容性**：Speaches 兼容 OpenAI API，使用 OpenAI SDK 时需要设置假的 API key
2. **模型加载**：模型按需加载，首次使用时会有延迟
3. **系统要求**：TTS 功能仅支持 Linux 系统
4. **格式限制**：TTS 不支持 opus 和 aac 格式输出