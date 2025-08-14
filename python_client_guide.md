# Speaches Python 客户端使用指南

## 安装依赖

```bash
pip install openai httpx websockets pyaudio numpy
```

## 一、ASR（语音识别）服务

### 1. 基础语音识别

```python
import httpx
from pathlib import Path

class SpeachesASR:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def transcribe(self, audio_file_path, model="Systran/faster-distil-whisper-large-v3", language="zh"):
        """
        转录音频文件
        
        Args:
            audio_file_path: 音频文件路径
            model: 使用的模型ID
            language: 语言代码 (zh, en, auto等)
        
        Returns:
            dict: 包含转录结果的字典
        """
        with open(audio_file_path, 'rb') as f:
            files = {'file': (Path(audio_file_path).name, f, 'audio/wav')}
            data = {
                'model': model,
                'language': language,
                'response_format': 'json'
            }
            
            response = self.client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files=files,
                data=data
            )
            
            return response.json()
    
    def transcribe_with_timestamps(self, audio_file_path, model="Systran/faster-distil-whisper-large-v3"):
        """
        转录音频文件并返回时间戳
        """
        with open(audio_file_path, 'rb') as f:
            files = {'file': (Path(audio_file_path).name, f, 'audio/wav')}
            data = {
                'model': model,
                'response_format': 'verbose_json',
                'timestamp_granularities[]': 'word'
            }
            
            response = self.client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files=files,
                data=data
            )
            
            return response.json()

# 使用示例
asr = SpeachesASR()

# 基础转录
result = asr.transcribe("audio.wav")
print(f"转录结果: {result['text']}")

# 带时间戳的转录
detailed_result = asr.transcribe_with_timestamps("audio.wav")
for word in detailed_result.get('words', [])[:10]:
    print(f"{word['word']} ({word['start']:.2f}s - {word['end']:.2f}s)")
```

### 2. 使用 OpenAI SDK

```python
from openai import OpenAI

# 配置客户端
client = OpenAI(
    api_key="sk-fake-key",  # Speaches 不需要真实的 API key
    base_url="http://localhost:8000/v1"
)

# 转录音频
def transcribe_with_openai_sdk(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="Systran/faster-distil-whisper-large-v3",
            file=audio_file,
            language="zh",
            response_format="text"
        )
    return transcription

# 使用示例
text = transcribe_with_openai_sdk("chinese_audio.wav")
print(f"识别结果: {text}")
```

### 3. 实时语音识别（WebSocket）

```python
import asyncio
import websockets
import json
import pyaudio
import base64
from datetime import datetime

class RealtimeASR:
    def __init__(self, base_url="ws://localhost:8000", model="Systran/faster-distil-whisper-large-v3"):
        self.ws_url = f"{base_url}/v1/realtime"
        self.model = model
        self.is_running = False
    
    async def start(self):
        """启动实时语音识别"""
        async with websockets.connect(self.ws_url) as websocket:
            # 配置会话
            await self._configure_session(websocket)
            
            # 启动音频录制
            audio_task = asyncio.create_task(self._record_and_send_audio(websocket))
            receive_task = asyncio.create_task(self._receive_transcriptions(websocket))
            
            try:
                await asyncio.gather(audio_task, receive_task)
            except KeyboardInterrupt:
                print("\n停止实时识别...")
                self.is_running = False
    
    async def _configure_session(self, websocket):
        """配置识别会话"""
        config = {
            "type": "session.update",
            "session": {
                "model": self.model,
                "transcription_options": {
                    "language": "zh",
                    "temperature": 0.3,
                    "beam_size": 5
                }
            }
        }
        await websocket.send(json.dumps(config))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 会话配置完成，使用模型: {self.model}")
    
    async def _record_and_send_audio(self, websocket):
        """录制并发送音频流"""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print("开始录音... (按 Ctrl+C 停止)")
        self.is_running = True
        
        try:
            while self.is_running:
                # 读取音频数据
                audio_data = stream.read(1024, exception_on_overflow=False)
                
                # 编码并发送
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                message = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64
                }
                await websocket.send(json.dumps(message))
                
                # 短暂延迟避免过载
                await asyncio.sleep(0.01)
                
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    async def _receive_transcriptions(self, websocket):
        """接收识别结果"""
        try:
            while self.is_running:
                message = await websocket.recv()
                data = json.loads(message)
                
                # 处理不同类型的消息
                if data.get("type") == "response.audio_transcript.delta":
                    # 增量转录结果
                    text = data.get("delta", {}).get("text", "")
                    print(text, end="", flush=True)
                    
                elif data.get("type") == "response.audio_transcript.done":
                    # 转录完成
                    print()  # 换行
                    
                elif data.get("type") == "error":
                    # 错误处理
                    print(f"\n错误: {data.get('error', {}).get('message', '未知错误')}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n连接已关闭")
            self.is_running = False

# 使用示例
async def main():
    asr = RealtimeASR()
    await asr.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. 批量处理

```python
import concurrent.futures
from pathlib import Path

class BatchASR:
    def __init__(self, base_url="http://localhost:8000", max_workers=5):
        self.base_url = base_url
        self.max_workers = max_workers
    
    def process_batch(self, audio_files, model="Systran/faster-distil-whisper-large-v3"):
        """批量处理多个音频文件"""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self._transcribe_file, file, model): file 
                for file in audio_files
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results[file] = result
                    print(f"✓ 完成: {file}")
                except Exception as e:
                    results[file] = {"error": str(e)}
                    print(f"✗ 失败: {file} - {e}")
        
        return results
    
    def _transcribe_file(self, audio_file, model):
        """转录单个文件"""
        with httpx.Client() as client:
            with open(audio_file, 'rb') as f:
                files = {'file': (Path(audio_file).name, f)}
                data = {'model': model, 'language': 'zh'}
                
                response = client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files=files,
                    data=data,
                    timeout=30.0
                )
                
                return response.json()

# 使用示例
batch_asr = BatchASR()
audio_files = ["audio1.wav", "audio2.wav", "audio3.wav"]
results = batch_asr.process_batch(audio_files)

for file, result in results.items():
    if "text" in result:
        print(f"{file}: {result['text']}")
```

## 二、TTS（文字转语音）服务

### 1. 基础语音合成

```python
import httpx
from pathlib import Path

class SpeachesTTS:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def synthesize(self, text, output_file="output.mp3", 
                   model="speaches-ai/Kokoro-82M-v1.0-ONNX",
                   voice="zf_xiaoxiao", speed=1.0):
        """
        合成语音
        
        Args:
            text: 要合成的文本
            output_file: 输出文件路径
            model: TTS模型ID
            voice: 声音ID
            speed: 语速 (0.25-4.0)
        
        Returns:
            bool: 是否成功
        """
        response = self.client.post(
            f"{self.base_url}/v1/audio/speech",
            json={
                "input": text,
                "model": model,
                "voice": voice,
                "speed": speed,
                "response_format": Path(output_file).suffix[1:]  # mp3, wav等
            }
        )
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True
        return False
    
    def list_voices(self, model="speaches-ai/Kokoro-82M-v1.0-ONNX"):
        """获取可用的声音列表"""
        # 预定义的声音列表
        voices = {
            "中文女声": ["zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi"],
            "中文男声": ["zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"],
            "英文女声": ["af_heart", "af_bella", "af_nicole", "bf_alice", "bf_emma"],
            "英文男声": ["am_adam", "am_michael", "bm_daniel", "bm_george"]
        }
        return voices

# 使用示例
tts = SpeachesTTS()

# 合成中文
tts.synthesize(
    text="你好，欢迎使用语音合成服务。今天天气真不错！",
    output_file="chinese_output.mp3",
    voice="zf_xiaoxiao"
)

# 合成英文
tts.synthesize(
    text="Hello, welcome to our text-to-speech service!",
    output_file="english_output.mp3",
    voice="af_heart"
)

# 调整语速
tts.synthesize(
    text="这是慢速播放的示例。",
    output_file="slow_output.mp3",
    voice="zm_yunxi",
    speed=0.8
)
```

### 2. 使用 OpenAI SDK

```python
from openai import OpenAI
from pathlib import Path

# 配置客户端
client = OpenAI(
    api_key="sk-fake-key",
    base_url="http://localhost:8000/v1"
)

def text_to_speech(text, voice="zf_xiaoxiao", output_file="speech.mp3"):
    """使用 OpenAI SDK 进行语音合成"""
    response = client.audio.speech.create(
        model="speaches-ai/Kokoro-82M-v1.0-ONNX",
        voice=voice,
        input=text,
        speed=1.0
    )
    
    # 保存音频文件
    response.write_to_file(output_file)
    return output_file

# 使用示例
text_to_speech("你好，这是使用 OpenAI SDK 的示例。", "zf_xiaoxiao", "openai_tts.mp3")
```

### 3. 流式语音合成

```python
import httpx
import pyaudio
import io
from pydub import AudioSegment
from pydub.playback import play

class StreamingTTS:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def speak(self, text, voice="zf_xiaoxiao", play_audio=True):
        """流式合成并播放语音"""
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/v1/audio/speech",
                json={
                    "input": text,
                    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
                    "voice": voice,
                    "response_format": "mp3"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                # 如果需要播放
                if play_audio:
                    audio = AudioSegment.from_mp3(io.BytesIO(response.content))
                    play(audio)
                
                return response.content
            else:
                print(f"错误: {response.status_code}")
                return None
    
    def batch_synthesize(self, texts, voice="zf_xiaoxiao"):
        """批量合成多段文本"""
        results = []
        
        for i, text in enumerate(texts):
            print(f"合成第 {i+1}/{len(texts)} 段...")
            audio_data = self.speak(text, voice, play_audio=False)
            if audio_data:
                results.append({
                    'text': text,
                    'audio': audio_data,
                    'filename': f"batch_{i+1}.mp3"
                })
        
        return results

# 使用示例
tts = StreamingTTS()

# 直接播放
tts.speak("你好，这是实时语音合成的示例。")

# 批量合成
texts = [
    "第一段：今天天气真好。",
    "第二段：适合出去散步。",
    "第三段：记得带上雨伞。"
]

results = tts.batch_synthesize(texts)
for result in results:
    with open(result['filename'], 'wb') as f:
        f.write(result['audio'])
    print(f"已保存: {result['filename']}")
```

### 4. 高级功能示例

```python
class AdvancedSpeaches:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.asr = SpeachesASR(base_url)
        self.tts = SpeachesTTS(base_url)
    
    def voice_clone(self, reference_audio, text_to_speak):
        """语音克隆示例（如果支持）"""
        # 1. 分析参考音频
        transcription = self.asr.transcribe(reference_audio)
        print(f"参考音频内容: {transcription['text']}")
        
        # 2. 使用相似的声音合成
        # 注意：这是模拟，实际的语音克隆需要特殊模型
        self.tts.synthesize(
            text=text_to_speak,
            output_file="cloned_voice.mp3",
            voice="zf_xiaoxiao"  # 选择最接近的预设声音
        )
    
    def translate_and_speak(self, audio_file, target_lang="en"):
        """识别音频并翻译后合成（需要额外的翻译服务）"""
        # 1. 识别原始音频
        result = self.asr.transcribe(audio_file)
        original_text = result['text']
        print(f"识别结果: {original_text}")
        
        # 2. 这里应该调用翻译API
        # translated_text = translate(original_text, target_lang)
        translated_text = "This is a translation example."  # 模拟翻译结果
        
        # 3. 合成翻译后的语音
        voice = "af_heart" if target_lang == "en" else "zf_xiaoxiao"
        self.tts.synthesize(
            text=translated_text,
            output_file="translated_speech.mp3",
            voice=voice
        )
        
        return original_text, translated_text

# 使用示例
advanced = AdvancedSpeaches()

# 语音翻译
original, translated = advanced.translate_and_speak("chinese_audio.wav", "en")
print(f"原文: {original}")
print(f"译文: {translated}")
```

## 三、完整应用示例

```python
# voice_assistant.py
import asyncio
import threading
import queue
from datetime import datetime

class VoiceAssistant:
    """简单的语音助手示例"""
    
    def __init__(self):
        self.asr = SpeachesASR()
        self.tts = SpeachesTTS()
        self.is_listening = False
        self.command_queue = queue.Queue()
    
    def start(self):
        """启动语音助手"""
        print("语音助手已启动，说'你好'开始对话...")
        
        # 启动监听线程
        listen_thread = threading.Thread(target=self._listen_loop)
        process_thread = threading.Thread(target=self._process_loop)
        
        listen_thread.start()
        process_thread.start()
        
        try:
            listen_thread.join()
            process_thread.join()
        except KeyboardInterrupt:
            print("\n语音助手已停止")
    
    def _listen_loop(self):
        """监听循环"""
        # 这里应该实现实时音频监听
        # 为了演示，我们模拟用户输入
        while True:
            try:
                # 实际应该从麦克风获取
                user_input = input("\n请说话（输入文本模拟）: ")
                if user_input.lower() == 'exit':
                    break
                
                self.command_queue.put(user_input)
            except KeyboardInterrupt:
                break
    
    def _process_loop(self):
        """处理命令循环"""
        while True:
            try:
                command = self.command_queue.get(timeout=1)
                response = self._process_command(command)
                
                # 合成并播放回复
                self.tts.synthesize(
                    text=response,
                    output_file=f"response_{datetime.now().strftime('%H%M%S')}.mp3",
                    voice="zf_xiaoxiao"
                )
                print(f"助手: {response}")
                
            except queue.Empty:
                continue
            except KeyboardInterrupt:
                break
    
    def _process_command(self, command):
        """处理用户命令"""
        command = command.lower()
        
        if "时间" in command:
            return f"现在是{datetime.now().strftime('%H点%M分')}"
        elif "天气" in command:
            return "今天天气晴朗，温度适宜"
        elif "你好" in command:
            return "你好！我是你的语音助手，有什么可以帮助你的吗？"
        else:
            return "对不起，我还不太理解这个指令，请再说一遍"

# 运行语音助手
if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.start()
```

## 四、错误处理和最佳实践

```python
import logging
import time
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustSpeachesClient:
    """带有错误处理和重试机制的客户端"""
    
    def __init__(self, base_url="http://localhost:8000", max_retries=3):
        self.base_url = base_url
        self.max_retries = max_retries
    
    def transcribe_with_retry(self, audio_file: str, **kwargs) -> Optional[Dict[str, Any]]:
        """带重试机制的转录"""
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    with open(audio_file, 'rb') as f:
                        files = {'file': f}
                        data = {
                            'model': kwargs.get('model', 'Systran/faster-distil-whisper-large-v3'),
                            'language': kwargs.get('language', 'zh')
                        }
                        
                        response = client.post(
                            f"{self.base_url}/v1/audio/transcriptions",
                            files=files,
                            data=data
                        )
                        
                        response.raise_for_status()
                        return response.json()
                        
            except httpx.TimeoutException:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                time.sleep(2 ** attempt)  # 指数退避
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP错误 {e.response.status_code}: {e.response.text}")
                if e.response.status_code >= 500:
                    time.sleep(2 ** attempt)
                else:
                    raise
                    
            except Exception as e:
                logger.error(f"未预期的错误: {e}")
                raise
        
        return None
    
    def health_check(self) -> bool:
        """检查服务健康状态"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False

# 使用示例
client = RobustSpeachesClient()

# 检查服务状态
if not client.health_check():
    logger.error("Speaches 服务不可用")
else:
    # 进行转录
    result = client.transcribe_with_retry("audio.wav")
    if result:
        print(f"转录成功: {result['text']}")
```

## 安装和配置

### 1. 安装依赖

```bash
# 基础依赖
pip install httpx openai

# 实时识别依赖
pip install websockets pyaudio

# 音频处理依赖
pip install numpy pydub

# 完整安装
pip install httpx openai websockets pyaudio numpy pydub
```

### 2. 环境配置

```python
# config.py
import os

# Speaches 服务配置
SPEACHES_BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://localhost:8000")
SPEACHES_WS_URL = os.getenv("SPEACHES_WS_URL", "ws://localhost:8000")

# 默认模型配置
DEFAULT_ASR_MODEL = "Systran/faster-distil-whisper-large-v3"
DEFAULT_TTS_MODEL = "speaches-ai/Kokoro-82M-v1.0-ONNX"
DEFAULT_TTS_VOICE = "zf_xiaoxiao"

# 音频配置
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024
```

### 3. 测试连接

```python
# test_connection.py
def test_speaches_connection():
    """测试 Speaches 服务连接"""
    import httpx
    
    tests = {
        "健康检查": lambda: httpx.get(f"{SPEACHES_BASE_URL}/health"),
        "模型列表": lambda: httpx.get(f"{SPEACHES_BASE_URL}/v1/models"),
        "ASR模型": lambda: httpx.get(f"{SPEACHES_BASE_URL}/v1/registry?task=automatic-speech-recognition")
    }
    
    for name, test_func in tests.items():
        try:
            response = test_func()
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name}: {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: {e}")

if __name__ == "__main__":
    test_speaches_connection()
```