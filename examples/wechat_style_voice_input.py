#!/usr/bin/env python3
"""
微信风格的语音输入转文字功能实现
非实时语音识别，录制完成后转文字
"""

import os
import httpx
import pyaudio
import wave
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

# 配置
SPEACHES_BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://localhost:8000")
ASR_MODEL = "Systran/faster-distil-whisper-large-v3"  # 推荐的模型

class WeChatStyleVoiceInput:
    """
    微信风格的语音输入实现
    - 按住录音
    - 松开停止
    - 自动转文字
    """
    
    def __init__(self, 
                 base_url: str = SPEACHES_BASE_URL,
                 model: str = ASR_MODEL,
                 max_duration: int = 60):  # 最长录音时间（秒）
        self.base_url = base_url
        self.model = model
        self.max_duration = max_duration
        self.is_recording = False
        self.audio_data = []
        self.client = httpx.Client(timeout=30.0)
        
        # 音频参数（微信标准）
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # 16kHz 采样率
        self.chunk = 1024
        
        # 初始化 PyAudio
        self.audio = pyaudio.PyAudio()
        
    def start_recording(self, on_start: Optional[Callable] = None):
        """开始录音"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.audio_data = []
        
        if on_start:
            on_start()
            
        # 在新线程中录音
        self.record_thread = threading.Thread(target=self._record_audio)
        self.record_thread.start()
        
    def stop_recording(self) -> Optional[str]:
        """
        停止录音并返回识别结果
        
        Returns:
            识别的文字，如果失败返回 None
        """
        if not self.is_recording:
            return None
            
        self.is_recording = False
        self.record_thread.join()
        
        # 检查是否有录音数据
        if not self.audio_data:
            print("没有录音数据")
            return None
            
        # 保存为临时 WAV 文件
        temp_file = self._save_audio()
        
        try:
            # 调用 ASR 识别
            result = self._transcribe_audio(temp_file)
            return result
        finally:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
                
    def _record_audio(self):
        """录音线程"""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print("开始录音...")
        start_time = time.time()
        
        try:
            while self.is_recording:
                # 检查是否超过最大时长
                if time.time() - start_time > self.max_duration:
                    print(f"达到最大录音时长 {self.max_duration} 秒")
                    self.is_recording = False
                    break
                    
                # 读取音频数据
                data = stream.read(self.chunk, exception_on_overflow=False)
                self.audio_data.append(data)
                
        finally:
            stream.stop_stream()
            stream.close()
            
        duration = time.time() - start_time
        print(f"录音结束，时长: {duration:.1f} 秒")
        
    def _save_audio(self) -> Path:
        """保存音频为 WAV 文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = Path(f"voice_input_{timestamp}.wav")
        
        with wave.open(str(temp_file), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.audio_data))
            
        return temp_file
        
    def _transcribe_audio(self, audio_file: Path) -> Optional[str]:
        """调用 Speaches ASR 识别音频"""
        try:
            with open(audio_file, 'rb') as f:
                files = {'file': (audio_file.name, f, 'audio/wav')}
                data = {
                    'model': self.model,
                    'language': 'zh',  # 可以设置为 auto 自动检测
                    'response_format': 'json'
                }
                
                response = self.client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files=files,
                    data=data
                )
                
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
            else:
                print(f"识别失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"识别错误: {e}")
            return None
            
    def close(self):
        """清理资源"""
        self.audio.terminate()
        self.client.close()


class VoiceInputUI:
    """简单的语音输入 UI 模拟"""
    
    def __init__(self):
        self.voice_input = WeChatStyleVoiceInput()
        
    def simulate_wechat_input(self):
        """模拟微信语音输入流程"""
        print("\n=== 微信风格语音输入 ===")
        print("使用说明:")
        print("- 按 Enter 开始录音")
        print("- 再按 Enter 停止录音")
        print("- 输入 'quit' 退出")
        print("-" * 40)
        
        while True:
            command = input("\n按 Enter 开始录音 (或输入 'quit' 退出): ")
            
            if command.lower() == 'quit':
                break
                
            # 开始录音
            self.voice_input.start_recording(
                on_start=lambda: print("🎤 正在录音... (按 Enter 停止)")
            )
            
            # 等待用户停止
            input()
            
            # 停止录音并识别
            print("⏹️  停止录音，正在识别...")
            text = self.voice_input.stop_recording()
            
            if text:
                print(f"\n📝 识别结果: {text}")
            else:
                print("\n❌ 识别失败，请重试")
                
        self.voice_input.close()
        print("\n退出语音输入")


# 高级功能：带回调的语音输入
class AdvancedVoiceInput(WeChatStyleVoiceInput):
    """
    高级语音输入，支持各种回调和事件
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.callbacks = {
            'on_recording_start': None,
            'on_recording_stop': None,
            'on_transcription_start': None,
            'on_transcription_complete': None,
            'on_error': None
        }
        
    def set_callback(self, event: str, callback: Callable):
        """设置回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback
            
    def start_recording(self, on_start: Optional[Callable] = None):
        """开始录音（带回调）"""
        super().start_recording(on_start)
        if self.callbacks['on_recording_start']:
            self.callbacks['on_recording_start']()
            
    def stop_recording(self) -> Optional[str]:
        """停止录音并识别（带回调）"""
        if self.callbacks['on_recording_stop']:
            self.callbacks['on_recording_stop']()
            
        # 停止录音
        self.is_recording = False
        self.record_thread.join()
        
        if not self.audio_data:
            if self.callbacks['on_error']:
                self.callbacks['on_error']("没有录音数据")
            return None
            
        # 保存音频
        temp_file = self._save_audio()
        
        try:
            if self.callbacks['on_transcription_start']:
                self.callbacks['on_transcription_start']()
                
            # 识别
            result = self._transcribe_audio(temp_file)
            
            if result and self.callbacks['on_transcription_complete']:
                self.callbacks['on_transcription_complete'](result)
                
            return result
            
        except Exception as e:
            if self.callbacks['on_error']:
                self.callbacks['on_error'](str(e))
            return None
            
        finally:
            if temp_file.exists():
                temp_file.unlink()


# 实际应用示例
def demo_voice_message():
    """演示：语音消息功能"""
    print("\n=== 语音消息演示 ===")
    
    voice_input = AdvancedVoiceInput()
    
    # 设置回调
    voice_input.set_callback('on_recording_start', 
                           lambda: print("🔴 录音中..."))
    voice_input.set_callback('on_recording_stop', 
                           lambda: print("⏹️  录音结束"))
    voice_input.set_callback('on_transcription_start', 
                           lambda: print("🔄 正在转文字..."))
    voice_input.set_callback('on_transcription_complete', 
                           lambda text: print(f"✅ 转换完成: {text}"))
    voice_input.set_callback('on_error', 
                           lambda err: print(f"❌ 错误: {err}"))
    
    # 录制语音消息
    print("\n请说一段话作为语音消息...")
    input("按 Enter 开始: ")
    
    voice_input.start_recording()
    
    input("按 Enter 结束: ")
    
    text = voice_input.stop_recording()
    
    if text:
        print(f"\n语音消息文字版: {text}")
        # 这里可以将文字发送出去
        
    voice_input.close()


def demo_voice_search():
    """演示：语音搜索功能"""
    print("\n=== 语音搜索演示 ===")
    
    voice_input = WeChatStyleVoiceInput()
    
    print("请说出您要搜索的内容...")
    input("按 Enter 开始: ")
    
    voice_input.start_recording()
    time.sleep(3)  # 自动 3 秒后停止
    
    search_query = voice_input.stop_recording()
    
    if search_query:
        print(f"\n🔍 搜索: {search_query}")
        # 这里可以执行搜索操作
        
    voice_input.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # 运行演示
        demo_voice_message()
        demo_voice_search()
    else:
        # 运行交互式界面
        ui = VoiceInputUI()
        ui.simulate_wechat_input()