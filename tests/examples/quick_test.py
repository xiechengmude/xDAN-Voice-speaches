#!/usr/bin/env python3
"""
快速测试脚本 - 测试 ASR 和 TTS 基本功能
"""

import os
import httpx
import time
from pathlib import Path

BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://localhost:8000")

def quick_tts_test():
    """快速 TTS 测试"""
    print("=== TTS 快速测试 ===")
    
    test_cases = [
        {
            "text": "你好，欢迎使用语音合成服务。",
            "voice": "zf_xiaoxiao",
            "filename": "tts_chinese.wav"
        },
        {
            "text": "Hello, welcome to text-to-speech service.",
            "voice": "af_heart",
            "filename": "tts_english.wav"
        },
        {
            "text": "这是一个mixed language测试，very good!",
            "voice": "af_nicole",
            "filename": "tts_mixed.wav"
        }
    ]
    
    for case in test_cases:
        print(f"\n生成: {case['text']}")
        print(f"声音: {case['voice']}")
        
        response = httpx.post(
            f"{BASE_URL}/v1/audio/speech",
            json={
                "input": case['text'],
                "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
                "voice": case['voice'],
                "response_format": "wav"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            with open(case['filename'], 'wb') as f:
                f.write(response.content)
            print(f"✓ 已保存到 {case['filename']}")
        else:
            print(f"✗ 失败: {response.status_code}")

def quick_asr_test():
    """快速 ASR 测试"""
    print("\n\n=== ASR 快速测试 ===")
    
    # 测试生成的音频文件
    test_files = ["tts_chinese.wav", "tts_english.wav", "tts_mixed.wav"]
    
    for audio_file in test_files:
        if not Path(audio_file).exists():
            print(f"\n跳过 {audio_file} (文件不存在)")
            continue
            
        print(f"\n识别: {audio_file}")
        
        with open(audio_file, 'rb') as f:
            start = time.time()
            response = httpx.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                files={"file": f},
                data={
                    "model": "Systran/faster-distil-whisper-large-v3",
                    "response_format": "json"
                },
                timeout=30
            )
            duration = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 识别结果: {result.get('text', '')}")
            print(f"  耗时: {duration:.2f}秒")
        else:
            print(f"✗ 失败: {response.status_code}")

def test_models():
    """测试可用模型"""
    print("\n\n=== 可用模型 ===")
    
    response = httpx.get(f"{BASE_URL}/v1/models")
    if response.status_code == 200:
        models = response.json().get('data', [])
        
        asr_models = [m for m in models if m.get('task') == 'automatic-speech-recognition']
        tts_models = [m for m in models if m.get('task') == 'text-to-speech']
        
        print(f"\nASR 模型 ({len(asr_models)}):")
        for model in asr_models[:5]:
            print(f"  - {model['id']}")
        
        print(f"\nTTS 模型 ({len(tts_models)}):")
        for model in tts_models[:5]:
            print(f"  - {model['id']}")

def main():
    """主函数"""
    print(f"Speaches 服务地址: {BASE_URL}")
    
    # 检查服务
    try:
        response = httpx.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ 服务正常\n")
        else:
            print("✗ 服务异常")
            return
    except Exception as e:
        print(f"✗ 无法连接服务: {e}")
        return
    
    # 运行测试
    test_models()
    quick_tts_test()
    quick_asr_test()
    
    print("\n\n测试完成！")
    print("生成的音频文件:")
    for f in ["tts_chinese.wav", "tts_english.wav", "tts_mixed.wav"]:
        if Path(f).exists():
            print(f"  - {f}")

if __name__ == "__main__":
    main()