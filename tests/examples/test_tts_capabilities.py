#!/usr/bin/env python3
"""
TTS (文字转语音) 能力测试脚本
测试中英文合成能力和质量
"""

import os
import sys
import json
import time
import httpx
import wave
import struct
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置
BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://localhost:8000")
TTS_MODELS = [
    "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "speaches-ai/Kokoro-82M-v1.0-ONNX-fp16",
    "speaches-ai/Kokoro-82M-v1.0-ONNX-int8"
]

# 测试文本和声音配置
TTS_TEST_CASES = {
    "chinese": {
        "voices": {
            "female": ["zf_xiaoxiao", "zf_xiaobei", "zf_xiaoni", "zf_xiaoyi"],
            "male": ["zm_yunxi", "zm_yunjian", "zm_yunxia", "zm_yunyang"]
        },
        "texts": [
            {
                "content": "你好，欢迎使用语音合成服务。",
                "description": "简单问候语"
            },
            {
                "content": "今天是2024年12月14日，星期六，天气晴朗，温度15摄氏度。",
                "description": "日期天气播报"
            },
            {
                "content": "请注意，列车即将进站，请站在安全线以内。",
                "description": "公共广播"
            },
            {
                "content": "人工智能、机器学习、深度学习是当今科技发展的重要方向。",
                "description": "技术术语"
            },
            {
                "content": "电话号码是13812345678，邮箱是test@example.com。",
                "description": "数字和英文混合"
            }
        ]
    },
    "english": {
        "voices": {
            "female": ["af_heart", "af_bella", "af_nicole", "bf_alice", "bf_emma"],
            "male": ["am_adam", "am_michael", "bm_daniel", "bm_george"]
        },
        "texts": [
            {
                "content": "Hello, welcome to our text-to-speech service.",
                "description": "Simple greeting"
            },
            {
                "content": "The quick brown fox jumps over the lazy dog.",
                "description": "Pangram test"
            },
            {
                "content": "Today is December 14th, 2024. The weather is sunny with a temperature of 59 degrees Fahrenheit.",
                "description": "Date and weather"
            },
            {
                "content": "Artificial Intelligence and Machine Learning are transforming industries worldwide.",
                "description": "Technical terms"
            },
            {
                "content": "Please call us at 1-800-555-1234 or email support@example.com.",
                "description": "Contact information"
            }
        ]
    },
    "mixed": {
        "voices": {
            "all": ["af_nicole", "zf_xiaoxiao", "zm_yunxi"]
        },
        "texts": [
            {
                "content": "Hello大家好，欢迎参加今天的meeting。",
                "description": "中英混合问候"
            },
            {
                "content": "这个APP的DAU已经超过了100万，conversion rate达到了5%。",
                "description": "产品数据混合"
            },
            {
                "content": "请登录www.example.com，输入您的username和password。",
                "description": "网站登录说明"
            },
            {
                "content": "Python 3.9版本支持type hints，让code更加robust。",
                "description": "编程术语混合"
            },
            {
                "content": "CEO说我们的Q4 revenue预计增长20%，超过去年同期。",
                "description": "商务报告混合"
            }
        ]
    }
}

# 语速测试配置
SPEED_TESTS = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]


class TTSTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)
        self.results = []
        self.output_dir = Path("tts_test_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def test_tts(self, text: str, model: str, voice: str, speed: float = 1.0, 
                 output_format: str = "wav") -> Dict:
        """测试 TTS 合成"""
        try:
            start_time = time.time()
            
            response = self.client.post(
                f"{self.base_url}/v1/audio/speech",
                json={
                    "input": text,
                    "model": model,
                    "voice": voice,
                    "speed": speed,
                    "response_format": output_format
                }
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'audio_data': response.content,
                    'duration': duration,
                    'size': len(response.content),
                    'model': model,
                    'voice': voice,
                    'speed': speed
                }
            else:
                return {
                    'success': False,
                    'error': f"Status {response.status_code}",
                    'duration': duration,
                    'model': model,
                    'voice': voice,
                    'speed': speed
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'model': model,
                'voice': voice,
                'speed': speed
            }
    
    def analyze_audio(self, audio_data: bytes) -> Optional[Dict]:
        """分析音频文件的基本信息"""
        try:
            # 保存到临时文件
            temp_path = self.output_dir / "temp_analysis.wav"
            with open(temp_path, 'wb') as f:
                f.write(audio_data)
            
            # 读取 WAV 文件信息
            with wave.open(str(temp_path), 'rb') as wav_file:
                info = {
                    'channels': wav_file.getnchannels(),
                    'sample_width': wav_file.getsampwidth(),
                    'framerate': wav_file.getframerate(),
                    'n_frames': wav_file.getnframes(),
                    'duration': wav_file.getnframes() / wav_file.getframerate()
                }
            
            # 删除临时文件
            temp_path.unlink()
            
            return info
            
        except Exception as e:
            print(f"音频分析错误: {e}")
            return None
    
    def test_voice_quality(self):
        """测试不同声音的质量"""
        print("=" * 80)
        print("TTS 声音质量测试")
        print("=" * 80)
        
        test_text = "您好，这是一段测试语音质量的文本。Hello, this is a test for voice quality."
        
        for lang_type, config in TTS_TEST_CASES.items():
            print(f"\n测试语言: {lang_type.upper()}")
            print("-" * 60)
            
            voices = []
            if 'all' in config['voices']:
                voices = config['voices']['all']
            else:
                for gender_voices in config['voices'].values():
                    voices.extend(gender_voices)
            
            for voice in voices[:3]:  # 每种语言测试前3个声音
                print(f"\n测试声音: {voice}")
                
                for model in TTS_MODELS:
                    if not self.check_model_available(model):
                        print(f"  模型 {model} 未安装")
                        continue
                    
                    result = self.test_tts(test_text, model, voice)
                    
                    if result['success']:
                        # 保存音频文件
                        output_path = self.output_dir / f"{lang_type}_{voice}_{model.split('/')[-1]}.wav"
                        with open(output_path, 'wb') as f:
                            f.write(result['audio_data'])
                        
                        # 分析音频
                        audio_info = self.analyze_audio(result['audio_data'])
                        
                        print(f"  模型: {model.split('/')[-1]}")
                        print(f"    生成耗时: {result['duration']:.2f}秒")
                        print(f"    文件大小: {result['size'] / 1024:.1f} KB")
                        if audio_info:
                            print(f"    音频时长: {audio_info['duration']:.2f}秒")
                            print(f"    采样率: {audio_info['framerate']} Hz")
                    else:
                        print(f"  模型 {model} 合成失败: {result['error']}")
    
    def test_language_capability(self):
        """测试不同语言的合成能力"""
        print("\n" + "=" * 80)
        print("TTS 语言能力测试")
        print("=" * 80)
        
        # 使用主要模型进行测试
        model = TTS_MODELS[0]
        
        for lang_type, config in TTS_TEST_CASES.items():
            print(f"\n语言类型: {lang_type.upper()}")
            print("=" * 60)
            
            # 选择一个代表性声音
            if lang_type == "chinese":
                test_voice = "zf_xiaoxiao"
            elif lang_type == "english":
                test_voice = "af_heart"
            else:
                test_voice = "af_nicole"
            
            for idx, test_case in enumerate(config['texts']):
                text = test_case['content']
                description = test_case['description']
                
                print(f"\n测试 {idx + 1}: {description}")
                print(f"文本: {text}")
                
                result = self.test_tts(text, model, test_voice)
                
                if result['success']:
                    # 保存音频
                    filename = f"{lang_type}_test_{idx + 1}_{test_voice}.wav"
                    output_path = self.output_dir / filename
                    with open(output_path, 'wb') as f:
                        f.write(result['audio_data'])
                    
                    # 分析音频
                    audio_info = self.analyze_audio(result['audio_data'])
                    
                    print(f"✓ 合成成功")
                    print(f"  文件: {filename}")
                    print(f"  耗时: {result['duration']:.2f}秒")
                    if audio_info:
                        print(f"  音频时长: {audio_info['duration']:.2f}秒")
                    
                    # 保存结果
                    self.results.append({
                        'language': lang_type,
                        'description': description,
                        'text': text,
                        'voice': test_voice,
                        'model': model,
                        'success': True,
                        'duration': result['duration'],
                        'audio_duration': audio_info['duration'] if audio_info else 0,
                        'file_size': result['size']
                    })
                else:
                    print(f"✗ 合成失败: {result['error']}")
                    self.results.append({
                        'language': lang_type,
                        'description': description,
                        'text': text,
                        'voice': test_voice,
                        'model': model,
                        'success': False,
                        'error': result['error']
                    })
    
    def test_speed_variation(self):
        """测试不同语速的效果"""
        print("\n" + "=" * 80)
        print("TTS 语速变化测试")
        print("=" * 80)
        
        model = TTS_MODELS[0]
        test_text = "这是一段用于测试不同语速效果的文本。This is a text for testing different speech speeds."
        voice = "af_nicole"
        
        print(f"\n测试文本: {test_text}")
        print(f"使用声音: {voice}")
        print("-" * 60)
        
        for speed in SPEED_TESTS:
            print(f"\n语速: {speed}x")
            
            result = self.test_tts(test_text, model, voice, speed=speed)
            
            if result['success']:
                # 保存音频
                filename = f"speed_test_{speed}x.wav"
                output_path = self.output_dir / filename
                with open(output_path, 'wb') as f:
                    f.write(result['audio_data'])
                
                # 分析音频
                audio_info = self.analyze_audio(result['audio_data'])
                
                print(f"✓ 合成成功")
                print(f"  文件: {filename}")
                if audio_info:
                    print(f"  音频时长: {audio_info['duration']:.2f}秒")
                    # 计算实际语速变化
                    if speed == 1.0:
                        base_duration = audio_info['duration']
                    else:
                        expected_duration = base_duration / speed if 'base_duration' in locals() else 0
                        if expected_duration > 0:
                            actual_speed_ratio = base_duration / audio_info['duration']
                            print(f"  预期语速比: {speed}x, 实际语速比: {actual_speed_ratio:.2f}x")
            else:
                print(f"✗ 合成失败: {result['error']}")
    
    def test_voice_comparison(self):
        """对比不同声音的特点"""
        print("\n" + "=" * 80)
        print("TTS 声音对比测试")
        print("=" * 80)
        
        model = TTS_MODELS[0]
        
        # 中文声音对比
        chinese_text = "大家好，我是您的智能语音助手，很高兴为您服务。"
        print(f"\n中文测试文本: {chinese_text}")
        print("-" * 40)
        
        for voice_type, voices in TTS_TEST_CASES["chinese"]["voices"].items():
            print(f"\n{voice_type.upper()} 声音:")
            for voice in voices:
                result = self.test_tts(chinese_text, model, voice)
                if result['success']:
                    filename = f"chinese_{voice}.wav"
                    output_path = self.output_dir / filename
                    with open(output_path, 'wb') as f:
                        f.write(result['audio_data'])
                    print(f"  {voice}: ✓ 已生成 {filename}")
                else:
                    print(f"  {voice}: ✗ 失败")
        
        # 英文声音对比
        english_text = "Hello everyone, I'm your intelligent voice assistant, happy to serve you."
        print(f"\n英文测试文本: {english_text}")
        print("-" * 40)
        
        for voice_type, voices in TTS_TEST_CASES["english"]["voices"].items():
            print(f"\n{voice_type.upper()} 声音:")
            for voice in voices[:2]:  # 每种类型测试2个
                result = self.test_tts(english_text, model, voice)
                if result['success']:
                    filename = f"english_{voice}.wav"
                    output_path = self.output_dir / filename
                    with open(output_path, 'wb') as f:
                        f.write(result['audio_data'])
                    print(f"  {voice}: ✓ 已生成 {filename}")
                else:
                    print(f"  {voice}: ✗ 失败")
    
    def check_model_available(self, model: str) -> bool:
        """检查模型是否可用"""
        try:
            response = self.client.get(f"{self.base_url}/v1/models")
            if response.status_code == 200:
                models = response.json().get('data', [])
                return any(m.get('id') == model for m in models)
        except:
            pass
        return False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("TTS 测试报告总结")
        print("=" * 80)
        
        if not self.results:
            print("没有测试结果")
            return
        
        # 统计成功率
        total = len(self.results)
        success = sum(1 for r in self.results if r.get('success', False))
        success_rate = (success / total * 100) if total > 0 else 0
        
        print(f"\n总测试数: {total}")
        print(f"成功数: {success}")
        print(f"成功率: {success_rate:.1f}%")
        
        # 按语言统计
        print("\n语言能力统计:")
        print("-" * 40)
        for lang in ['chinese', 'english', 'mixed']:
            lang_results = [r for r in self.results if r.get('language') == lang]
            if lang_results:
                lang_success = sum(1 for r in lang_results if r.get('success', False))
                print(f"{lang:10} - 测试: {len(lang_results)}, 成功: {lang_success}, "
                      f"成功率: {lang_success/len(lang_results)*100:.1f}%")
        
        # 性能统计
        success_results = [r for r in self.results if r.get('success', False)]
        if success_results:
            avg_duration = sum(r['duration'] for r in success_results) / len(success_results)
            avg_audio_duration = sum(r.get('audio_duration', 0) for r in success_results) / len(success_results)
            
            print(f"\n平均生成耗时: {avg_duration:.2f}秒")
            print(f"平均音频时长: {avg_audio_duration:.2f}秒")
        
        # 保存详细报告
        report_path = Path("tts_test_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'base_url': self.base_url,
                'models_tested': TTS_MODELS,
                'output_directory': str(self.output_dir),
                'summary': {
                    'total_tests': total,
                    'successful': success,
                    'success_rate': success_rate,
                    'average_generation_time': avg_duration if success_results else 0
                },
                'results': self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_path}")
        print(f"音频文件保存在: {self.output_dir}/")
    
    def run_all_tests(self):
        """运行所有测试"""
        # 1. 声音质量测试
        self.test_voice_quality()
        
        # 2. 语言能力测试
        self.test_language_capability()
        
        # 3. 语速变化测试
        self.test_speed_variation()
        
        # 4. 声音对比测试
        self.test_voice_comparison()
        
        # 5. 生成报告
        self.generate_report()


def main():
    """主函数"""
    tester = TTSTester()
    
    # 检查服务是否可用
    try:
        response = httpx.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("错误: Speaches 服务不可用")
            return
    except Exception as e:
        print(f"错误: 无法连接到 Speaches 服务 - {e}")
        return
    
    print("TTS 能力测试开始...")
    print(f"服务地址: {BASE_URL}")
    print(f"输出目录: tts_test_output/")
    print()
    
    # 运行所有测试
    tester.run_all_tests()
    
    print("\n测试完成！")


if __name__ == "__main__":
    main()