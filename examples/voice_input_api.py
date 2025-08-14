#!/usr/bin/env python3
"""
语音输入 API 封装
提供简单易用的接口，类似微信语音输入
"""

import os
import httpx
import asyncio
from pathlib import Path
from typing import Optional, Union, BinaryIO
from dataclasses import dataclass
from datetime import datetime

# 配置
SPEACHES_BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://localhost:8000")

@dataclass
class TranscriptionResult:
    """转录结果"""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    confidence: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class VoiceInputAPI:
    """
    语音输入 API
    
    使用示例:
        api = VoiceInputAPI()
        
        # 方式1: 从文件转文字
        result = api.voice_to_text("voice.wav")
        print(result.text)
        
        # 方式2: 从音频数据转文字
        with open("voice.wav", "rb") as f:
            audio_data = f.read()
        result = api.voice_to_text(audio_data)
        
        # 方式3: 异步调用
        result = await api.voice_to_text_async("voice.wav")
    """
    
    def __init__(self, 
                 base_url: str = SPEACHES_BASE_URL,
                 model: str = "Systran/faster-distil-whisper-large-v3",
                 language: str = "zh"):
        """
        初始化
        
        Args:
            base_url: Speaches 服务地址
            model: ASR 模型，推荐 faster-distil-whisper-large-v3
            language: 默认语言，zh=中文, en=英文, 空字符串=自动检测
        """
        self.base_url = base_url
        self.model = model
        self.language = language
        self.client = httpx.Client(timeout=30.0)
        self.async_client = None
        
    def voice_to_text(self, 
                      audio: Union[str, Path, bytes, BinaryIO],
                      language: Optional[str] = None,
                      model: Optional[str] = None) -> TranscriptionResult:
        """
        语音转文字（同步）
        
        Args:
            audio: 音频文件路径、Path对象、二进制数据或文件对象
            language: 语言设置，覆盖默认值
            model: 模型设置，覆盖默认值
            
        Returns:
            TranscriptionResult: 转录结果
            
        Example:
            result = api.voice_to_text("recording.wav")
            print(f"识别结果: {result.text}")
        """
        # 准备音频数据
        audio_data, filename = self._prepare_audio(audio)
        
        # 准备请求
        files = {'file': (filename, audio_data, 'audio/wav')}
        data = {
            'model': model or self.model,
            'response_format': 'json'
        }
        
        # 设置语言
        lang = language if language is not None else self.language
        if lang:
            data['language'] = lang
            
        try:
            # 发送请求
            response = self.client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result_data = response.json()
                return TranscriptionResult(
                    text=result_data.get('text', ''),
                    language=result_data.get('language'),
                    duration=result_data.get('duration')
                )
            else:
                raise Exception(f"ASR 请求失败: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"语音识别错误: {str(e)}")
            
    async def voice_to_text_async(self,
                                  audio: Union[str, Path, bytes, BinaryIO],
                                  language: Optional[str] = None,
                                  model: Optional[str] = None) -> TranscriptionResult:
        """
        语音转文字（异步）
        
        Example:
            result = await api.voice_to_text_async("recording.wav")
        """
        if self.async_client is None:
            self.async_client = httpx.AsyncClient(timeout=30.0)
            
        # 准备音频数据
        audio_data, filename = self._prepare_audio(audio)
        
        # 准备请求
        files = {'file': (filename, audio_data, 'audio/wav')}
        data = {
            'model': model or self.model,
            'response_format': 'json'
        }
        
        lang = language if language is not None else self.language
        if lang:
            data['language'] = lang
            
        try:
            response = await self.async_client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result_data = response.json()
                return TranscriptionResult(
                    text=result_data.get('text', ''),
                    language=result_data.get('language'),
                    duration=result_data.get('duration')
                )
            else:
                raise Exception(f"ASR 请求失败: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"语音识别错误: {str(e)}")
            
    def _prepare_audio(self, audio: Union[str, Path, bytes, BinaryIO]) -> tuple:
        """准备音频数据"""
        if isinstance(audio, (str, Path)):
            # 文件路径
            path = Path(audio)
            with open(path, 'rb') as f:
                return f.read(), path.name
        elif isinstance(audio, bytes):
            # 二进制数据
            return audio, "audio.wav"
        elif hasattr(audio, 'read'):
            # 文件对象
            data = audio.read()
            filename = getattr(audio, 'name', 'audio.wav')
            return data, Path(filename).name
        else:
            raise ValueError("不支持的音频数据类型")
            
    def close(self):
        """关闭客户端"""
        self.client.close()
        if self.async_client:
            asyncio.create_task(self.async_client.aclose())
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷函数
def voice_to_text(audio_file: str, language: str = "zh") -> str:
    """
    快速语音转文字
    
    Args:
        audio_file: 音频文件路径
        language: 语言（zh/en/auto）
        
    Returns:
        识别的文字
        
    Example:
        text = voice_to_text("recording.wav")
        print(text)
    """
    api = VoiceInputAPI(language=language)
    try:
        result = api.voice_to_text(audio_file)
        return result.text
    finally:
        api.close()


# 高级功能
class VoiceInputBatch:
    """批量语音转文字"""
    
    def __init__(self, api: Optional[VoiceInputAPI] = None):
        self.api = api or VoiceInputAPI()
        
    def process_files(self, file_paths: list) -> dict:
        """
        批量处理音频文件
        
        Args:
            file_paths: 音频文件路径列表
            
        Returns:
            dict: {文件路径: TranscriptionResult}
        """
        results = {}
        
        for file_path in file_paths:
            try:
                result = self.api.voice_to_text(file_path)
                results[file_path] = result
                print(f"✓ {file_path}: {result.text[:50]}...")
            except Exception as e:
                results[file_path] = None
                print(f"✗ {file_path}: {str(e)}")
                
        return results
        
    async def process_files_async(self, file_paths: list) -> dict:
        """异步批量处理"""
        tasks = []
        for file_path in file_paths:
            task = self.api.voice_to_text_async(file_path)
            tasks.append((file_path, task))
            
        results = {}
        for file_path, task in tasks:
            try:
                result = await task
                results[file_path] = result
            except Exception as e:
                results[file_path] = None
                
        return results


# 使用示例
def example_usage():
    """使用示例"""
    print("=== 语音输入 API 使用示例 ===\n")
    
    # 1. 基本使用
    print("1. 基本使用:")
    api = VoiceInputAPI()
    
    # 模拟音频文件
    test_audio = b"fake audio data"  # 实际使用时是真实的音频数据
    
    try:
        # 如果有真实的音频文件
        # result = api.voice_to_text("test.wav")
        # print(f"识别结果: {result.text}")
        print("需要真实的音频文件进行测试")
    except Exception as e:
        print(f"错误: {e}")
        
    # 2. 快捷函数
    print("\n2. 快捷函数:")
    print("text = voice_to_text('recording.wav')")
    print("print(text)")
    
    # 3. 批量处理
    print("\n3. 批量处理:")
    batch = VoiceInputBatch(api)
    # files = ['file1.wav', 'file2.wav', 'file3.wav']
    # results = batch.process_files(files)
    print("可以批量处理多个音频文件")
    
    # 4. 不同语言
    print("\n4. 多语言支持:")
    print("# 中文")
    print("api_zh = VoiceInputAPI(language='zh')")
    print("# 英文") 
    print("api_en = VoiceInputAPI(language='en')")
    print("# 自动检测")
    print("api_auto = VoiceInputAPI(language='')")
    
    api.close()


if __name__ == "__main__":
    example_usage()