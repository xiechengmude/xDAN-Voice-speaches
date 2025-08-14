# 实时 ASR 实现指南

## 一、Speaches 实时 ASR 支持

Speaches 提供了多种实时 ASR 实现方式：

### 1. WebSocket 实时 API (`/v1/realtime`)
- 支持 OpenAI 兼容的实时 API
- 双向音频流传输
- 低延迟实时转录

### 2. WebRTC 支持
- 点对点音频传输
- 浏览器直接支持
- 适合 Web 应用

### 3. 流式转录 API
- Server-Sent Events (SSE)
- 实时返回识别结果

## 二、实时 ASR 实现方案

### 方案 1：使用 WebSocket API

```python
# realtime_asr_websocket.py
import asyncio
import websockets
import json
import pyaudio
import base64
import numpy as np

class RealtimeASR:
    def __init__(self, model="Systran/faster-distil-whisper-large-v3"):
        self.model = model
        self.ws_url = "ws://localhost:8000/v1/realtime"
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        
    async def start_streaming(self):
        async with websockets.connect(self.ws_url) as websocket:
            # 1. 配置会话
            await websocket.send(json.dumps({
                "type": "session.update",
                "session": {
                    "model": self.model,
                    "transcription_options": {
                        "language": "zh",
                        "temperature": 0.3
                    }
                }
            }))
            
            # 2. 启动音频流
            p = pyaudio.PyAudio()
            stream = p.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("开始实时语音识别... (按 Ctrl+C 停止)")
            
            # 3. 同时处理发送和接收
            async def send_audio():
                try:
                    while True:
                        data = stream.read(self.chunk, exception_on_overflow=False)
                        audio_data = base64.b64encode(data).decode('utf-8')
                        
                        await websocket.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": audio_data
                        }))
                        
                        await asyncio.sleep(0.01)
                except KeyboardInterrupt:
                    pass
            
            async def receive_transcription():
                try:
                    while True:
                        response = await websocket.recv()
                        data = json.loads(response)
                        
                        if data.get("type") == "response.audio_transcript.delta":
                            transcript = data.get("delta", {}).get("text", "")
                            print(f"识别结果: {transcript}", end="", flush=True)
                        elif data.get("type") == "response.audio_transcript.done":
                            print()  # 换行
                            
                except KeyboardInterrupt:
                    pass
            
            # 并行运行发送和接收
            await asyncio.gather(
                send_audio(),
                receive_transcription()
            )
            
            # 清理
            stream.stop_stream()
            stream.close()
            p.terminate()

# 运行
if __name__ == "__main__":
    asr = RealtimeASR()
    asyncio.run(asr.start_streaming())
```

### 方案 2：使用流式 HTTP API

```python
# realtime_asr_streaming.py
import requests
import pyaudio
import threading
import queue
import json

class StreamingASR:
    def __init__(self, model="Systran/faster-distil-whisper-large-v3"):
        self.model = model
        self.api_url = "http://localhost:8000/v1/audio/transcriptions"
        self.audio_queue = queue.Queue()
        self.chunk_duration = 5  # 每5秒发送一次
        
    def record_audio(self):
        """录制音频并放入队列"""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print("开始录音...")
        frames = []
        
        try:
            while True:
                data = stream.read(1024)
                frames.append(data)
                
                # 每5秒处理一次
                if len(frames) >= 16000 * self.chunk_duration / 1024:
                    self.audio_queue.put(b''.join(frames))
                    frames = []
                    
        except KeyboardInterrupt:
            if frames:
                self.audio_queue.put(b''.join(frames))
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def process_audio(self):
        """处理音频队列中的数据"""
        while True:
            try:
                audio_data = self.audio_queue.get(timeout=1)
                
                # 创建临时WAV文件
                import wave
                import tempfile
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    wf = wave.open(tmp_file.name, 'wb')
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(audio_data)
                    wf.close()
                    
                    # 发送识别请求
                    with open(tmp_file.name, 'rb') as f:
                        files = {'file': f}
                        data = {
                            'model': self.model,
                            'language': 'zh',
                            'response_format': 'json'
                        }
                        
                        response = requests.post(self.api_url, files=files, data=data)
                        result = response.json()
                        
                        if 'text' in result:
                            print(f"\n识别结果: {result['text']}")
                            
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                break
    
    def start(self):
        """启动实时识别"""
        # 创建录音线程
        record_thread = threading.Thread(target=self.record_audio)
        process_thread = threading.Thread(target=self.process_audio)
        
        record_thread.start()
        process_thread.start()
        
        try:
            record_thread.join()
            process_thread.join()
        except KeyboardInterrupt:
            print("\n停止识别...")

# 使用示例
if __name__ == "__main__":
    asr = StreamingASR()
    asr.start()
```

### 方案 3：WebRTC 实现（适合 Web 应用）

```html
<!-- realtime_asr_web.html -->
<!DOCTYPE html>
<html>
<head>
    <title>实时语音识别</title>
</head>
<body>
    <h1>实时语音识别 (WebRTC)</h1>
    <button id="startBtn">开始识别</button>
    <button id="stopBtn" disabled>停止识别</button>
    <div id="transcription"></div>

    <script>
        let pc;
        let ws;
        const model = "Systran/faster-distil-whisper-large-v3";
        
        async function startRecognition() {
            // 1. 建立 WebSocket 连接
            ws = new WebSocket('ws://localhost:8000/v1/realtime');
            
            ws.onopen = async () => {
                // 2. 配置会话
                ws.send(JSON.stringify({
                    type: "session.update",
                    session: {
                        model: model,
                        transcription_options: {
                            language: "zh"
                        }
                    }
                }));
                
                // 3. 获取用户音频权限
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                
                // 4. 创建 WebRTC 连接
                pc = new RTCPeerConnection();
                
                // 添加音频流
                stream.getTracks().forEach(track => {
                    pc.addTrack(track, stream);
                });
                
                // 5. 创建和交换 offer/answer
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                // 发送 offer 到服务器
                const response = await fetch('http://localhost:8000/rtc/offer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        offer: offer.sdp,
                        model: model
                    })
                });
                
                const answer = await response.json();
                await pc.setRemoteDescription({
                    type: 'answer',
                    sdp: answer.sdp
                });
            };
            
            // 6. 接收识别结果
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === "response.audio_transcript.delta") {
                    document.getElementById('transcription').innerHTML += data.delta.text;
                }
            };
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        }
        
        function stopRecognition() {
            if (pc) pc.close();
            if (ws) ws.close();
            
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
        
        document.getElementById('startBtn').onclick = startRecognition;
        document.getElementById('stopBtn').onclick = stopRecognition;
    </script>
</body>
</html>
```

## 三、性能优化建议

### 1. 模型选择
- **实时性优先**: 使用 `faster-distil-whisper-large-v3`
- **准确度优先**: 使用 `faster-whisper-large-v3`
- **极低延迟**: 使用 `faster-whisper-small`

### 2. 音频配置
```python
# 优化的音频参数
AUDIO_CONFIG = {
    "sample_rate": 16000,      # 16kHz 足够语音识别
    "channels": 1,             # 单声道
    "chunk_size": 1024,        # 缓冲区大小
    "format": "int16",         # 16位整数
}
```

### 3. 流式处理策略
- **VAD（语音活动检测）**: 只在检测到语音时发送数据
- **缓冲管理**: 合理设置音频缓冲区大小
- **并行处理**: 录音和识别并行进行

### 4. 实现 VAD 优化

```python
# 简单的 VAD 实现
import numpy as np

def is_speech(audio_chunk, threshold=500):
    """简单的能量阈值 VAD"""
    audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
    energy = np.mean(np.abs(audio_array))
    return energy > threshold

# 在发送前检查
if is_speech(audio_data):
    # 发送到 ASR
    pass
```

## 四、并发和多用户支持

### 并发测试结果
根据测试，Speaches 支持：
- ✅ 多用户同时请求
- ✅ 动态模型加载
- ✅ 自动资源管理
- ✅ 请求队列管理

### 扩展建议
1. **负载均衡**: 部署多个实例
2. **模型缓存**: 配置合理的模型缓存时间
3. **资源限制**: 设置最大并发数

```bash
# 环境变量配置
export SPEACHES_MAX_MODELS=3  # 最大同时加载模型数
export SPEACHES_MODEL_IDLE_TIMEOUT=300  # 模型空闲卸载时间(秒)
```

## 五、快速开始

```bash
# 1. 运行并发测试
bash test_concurrent_asr.sh

# 2. 安装 Python 依赖（实时识别）
pip install websockets pyaudio numpy requests

# 3. 运行实时识别
python realtime_asr_websocket.py
```