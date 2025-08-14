# Speaches 客户端快速入门

## 概述

Speaches 提供了完整的 ASR（语音识别）和 TTS（文字转语音）服务，支持中英文，并提供多种集成方式。

## 快速开始

### 1. 服务地址配置

```bash
# 环境变量
export SPEACHES_BASE_URL="http://localhost:8000"

# 或在代码中配置
# Python: base_url="http://localhost:8000"
# TypeScript: baseURL: 'http://localhost:8000'
```

### 2. Python 快速示例

```python
# 安装依赖
pip install httpx openai

# ASR - 语音识别
import httpx

# 识别音频文件
with open("audio.wav", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/v1/audio/transcriptions",
        files={"file": f},
        data={
            "model": "Systran/faster-distil-whisper-large-v3",
            "language": "zh"
        }
    )
    print(response.json()["text"])

# TTS - 语音合成
response = httpx.post(
    "http://localhost:8000/v1/audio/speech",
    json={
        "input": "你好，欢迎使用语音服务",
        "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "voice": "zf_xiaoxiao"
    }
)
with open("output.mp3", "wb") as f:
    f.write(response.content)
```

### 3. TypeScript/JavaScript 快速示例

```typescript
// 安装依赖
// npm install axios

// ASR - 语音识别
const formData = new FormData();
formData.append('file', audioFile);
formData.append('model', 'Systran/faster-distil-whisper-large-v3');
formData.append('language', 'zh');

const response = await axios.post(
  'http://localhost:8000/v1/audio/transcriptions',
  formData
);
console.log(response.data.text);

// TTS - 语音合成
const ttsResponse = await axios.post(
  'http://localhost:8000/v1/audio/speech',
  {
    input: '你好，欢迎使用语音服务',
    model: 'speaches-ai/Kokoro-82M-v1.0-ONNX',
    voice: 'zf_xiaoxiao'
  },
  { responseType: 'blob' }
);

// 播放音频
const audio = new Audio(URL.createObjectURL(ttsResponse.data));
audio.play();
```

## 主要功能

### ASR（语音识别）

| 功能 | Python | TypeScript | 说明 |
|-----|--------|------------|------|
| 基础转录 | ✅ `asr.transcribe()` | ✅ `asr.transcribe()` | 音频文件转文字 |
| 带时间戳 | ✅ `transcribe_with_timestamps()` | ✅ `transcribeWithTimestamps()` | 获取每个词的时间信息 |
| 实时识别 | ✅ WebSocket | ✅ WebSocket/WebRTC | 实时语音流识别 |
| 批量处理 | ✅ `BatchASR` | ✅ Promise.all() | 并发处理多个文件 |

### TTS（文字转语音）

| 功能 | Python | TypeScript | 说明 |
|-----|--------|------------|------|
| 基础合成 | ✅ `tts.synthesize()` | ✅ `tts.synthesize()` | 文字转音频文件 |
| 直接播放 | ✅ `synthesize_and_play()` | ✅ `synthesizeAndPlay()` | 合成并播放 |
| 声音选择 | ✅ 中英文多种声音 | ✅ 中英文多种声音 | 支持男女声 |
| 语速调节 | ✅ speed: 0.5-2.0 | ✅ speed: 0.5-2.0 | 调节播放速度 |

## 推荐模型

### ASR 模型（中英文）
1. **最准确**: `Systran/faster-whisper-large-v3`
2. **平衡选择**: `Systran/faster-distil-whisper-large-v3` ⭐推荐
3. **速度优先**: `Systran/faster-whisper-small`

### TTS 模型
- **多语言**: `speaches-ai/Kokoro-82M-v1.0-ONNX` ⭐推荐
- **中文专用**: `speaches-ai/piper-zh_CN-huayan-medium`

### 可用声音

**中文声音**:
- 女声: `zf_xiaoxiao`, `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoyi`
- 男声: `zm_yunxi`, `zm_yunjian`, `zm_yunxia`, `zm_yunyang`

**英文声音**:
- 女声: `af_heart`, `af_bella`, `af_nicole`
- 男声: `am_adam`, `am_michael`

## 实时语音识别

### Python WebSocket
```python
import asyncio
import websockets

async def realtime_asr():
    async with websockets.connect("ws://localhost:8000/v1/realtime") as ws:
        # 配置会话
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "model": "Systran/faster-distil-whisper-large-v3",
                "transcription_options": {"language": "zh"}
            }
        }))
        
        # 发送音频流...
```

### TypeScript WebSocket
```typescript
const ws = new WebSocket('ws://localhost:8000/v1/realtime');

ws.onopen = () => {
  // 配置会话
  ws.send(JSON.stringify({
    type: 'session.update',
    session: {
      model: 'Systran/faster-distil-whisper-large-v3',
      transcription_options: { language: 'zh' }
    }
  }));
  
  // 发送音频流...
};
```

## 完整示例项目

### Python 语音助手
```python
class VoiceAssistant:
    def __init__(self):
        self.asr = SpeachesASR()
        self.tts = SpeachesTTS()
    
    async def process_voice(self, audio_file):
        # 1. 识别语音
        text = await self.asr.transcribe(audio_file)
        
        # 2. 处理内容（调用 AI 等）
        response = await self.get_ai_response(text)
        
        # 3. 合成回复
        await self.tts.synthesize_and_play(response)
```

### React 语音聊天
```tsx
function VoiceChat() {
  const { transcript, startListening } = useRealtimeASR();
  const tts = new SpeachesTTS();
  
  const handleResponse = async (text: string) => {
    // 获取 AI 回复
    const response = await getAIResponse(text);
    
    // 播放语音回复
    await tts.synthesizeAndPlay(response);
  };
  
  return (
    <div>
      <button onClick={startListening}>开始对话</button>
      <p>{transcript}</p>
    </div>
  );
}
```

## 注意事项

1. **并发支持**: Speaches 支持多用户并发请求
2. **模型加载**: 首次使用模型时会有加载延迟
3. **音频格式**: 推荐使用 WAV 格式，16kHz 采样率
4. **浏览器限制**: 实时录音需要 HTTPS 或 localhost
5. **错误处理**: 建议实现重试机制

## 更多资源

- 完整 Python 客户端指南: [python_client_guide.md](./python_client_guide.md)
- 完整 TypeScript 客户端指南: [typescript_client_guide.md](./typescript_client_guide.md)
- ASR 模型列表: [推荐ASR模型列表.md](./推荐ASR模型列表.md)
- TTS 模型列表: [中英文模型列表.md](./中英文模型列表.md)