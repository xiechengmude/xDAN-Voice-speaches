#!/usr/bin/env python3
"""
ASR (语音识别) 能力测试脚本
测试中英文识别能力和准确度
"""

import os
import sys
import json
import time
import httpx
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置
BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://localhost:8000")
TTS_MODEL = "speaches-ai/Kokoro-82M-v1.0-ONNX"
ASR_MODELS = [
    "Systran/faster-whisper-large-v3",
    "Systran/faster-distil-whisper-large-v3",
    "Systran/faster-whisper-medium",
    "Systran/faster-whisper-small"
]

# 测试文本
TEST_TEXTS = {
    "chinese": [
        {
            "text": "今天天气真好，适合出去散步。",
            "voice": "zf_xiaoxiao",
            "description": "简单中文句子"
        },
        {
            "text": "人工智能技术正在改变我们的生活方式，从语音识别到自动驾驶，应用范围越来越广。",
            "voice": "zm_yunxi",
            "description": "技术类中文"
        },
        {
            "text": "明天下午三点半，我们在会议室开会讨论第四季度的销售计划。",
            "voice": "zf_xiaobei",
            "description": "商务中文"
        },
        {
            "text": "圆周率约等于3.14159，光速是每秒299792458米。",
            "voice": "zm_yunyang",
            "description": "数字和单位"
        }
    ],
    "english": [
        {
            "text": "The weather is beautiful today, perfect for a walk.",
            "voice": "af_heart",
            "description": "简单英文句子"
        },
        {
            "text": "Artificial intelligence is revolutionizing various industries including healthcare and finance.",
            "voice": "am_adam",
            "description": "技术类英文"
        },
        {
            "text": "Please schedule a meeting for tomorrow at 3:30 PM in conference room B.",
            "voice": "bf_alice",
            "description": "商务英文"
        },
        {
            "text": "The speed of light is approximately 186,282 miles per second.",
            "voice": "bm_daniel",
            "description": "科学数据"
        }
    ],
    "mixed": [
        {
            "text": "Hello大家好，欢迎来到AI技术分享会。",
            "voice": "af_nicole",
            "description": "中英混合打招呼"
        },
        {
            "text": "这个feature很powerful，可以handle各种edge case。",
            "voice": "zf_xiaoyi",
            "description": "技术中英混合"
        },
        {
            "text": "请发送email到support@example.com，我们的客服team会尽快reply。",
            "voice": "zm_yunjian",
            "description": "商务中英混合"
        },
        {
            "text": "Python版本是3.9，TensorFlow版本是2.10.0。",
            "voice": "af_bella",
            "description": "版本号混合"
        }
    ]
}


class ASRTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)
        self.results = []
        
    def generate_test_audio(self, text: str, voice: str, output_path: str) -> bool:
        """使用 TTS 生成测试音频"""
        try:
            response = self.client.post(
                f"{self.base_url}/v1/audio/speech",
                json={
                    "input": text,
                    "model": TTS_MODEL,
                    "voice": voice,
                    "response_format": "wav"
                }
            )
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"TTS 生成失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"生成音频错误: {e}")
            return False
    
    def test_asr(self, audio_path: str, model: str, language: str = None) -> Dict:
        """测试 ASR 识别"""
        try:
            start_time = time.time()
            
            with open(audio_path, 'rb') as f:
                files = {'file': ('test.wav', f, 'audio/wav')}
                data = {'model': model}
                if language:
                    data['language'] = language
                
                response = self.client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files=files,
                    data=data
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'text': result.get('text', ''),
                    'duration': duration,
                    'model': model
                }
            else:
                return {
                    'success': False,
                    'error': f"Status {response.status_code}",
                    'duration': duration,
                    'model': model
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'model': model
            }
    
    def calculate_accuracy(self, original: str, recognized: str) -> float:
        """计算识别准确率（简单的字符级别比较）"""
        if not original or not recognized:
            return 0.0
            
        # 移除空格和标点符号进行比较
        import re
        original_clean = re.sub(r'[^\w\s]', '', original.lower())
        recognized_clean = re.sub(r'[^\w\s]', '', recognized.lower())
        
        # 计算最长公共子序列
        def lcs_length(s1: str, s2: str) -> int:
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        lcs_len = lcs_length(original_clean, recognized_clean)
        max_len = max(len(original_clean), len(recognized_clean))
        
        return (lcs_len / max_len * 100) if max_len > 0 else 0
    
    def run_comprehensive_test(self):
        """运行完整测试"""
        print("=" * 80)
        print("ASR 中英文能力测试")
        print("=" * 80)
        print(f"服务地址: {self.base_url}")
        print(f"测试模型: {', '.join(ASR_MODELS)}")
        print()
        
        # 创建临时目录
        temp_dir = Path("temp_test_audio")
        temp_dir.mkdir(exist_ok=True)
        
        # 测试每种语言
        for lang_type, test_cases in TEST_TEXTS.items():
            print(f"\n{'='*60}")
            print(f"测试类型: {lang_type.upper()}")
            print(f"{'='*60}")
            
            for idx, test_case in enumerate(test_cases):
                text = test_case['text']
                voice = test_case['voice']
                description = test_case['description']
                
                print(f"\n测试 {idx + 1}: {description}")
                print(f"原文: {text}")
                print(f"声音: {voice}")
                
                # 生成测试音频
                audio_path = temp_dir / f"{lang_type}_{idx}.wav"
                if not self.generate_test_audio(text, voice, str(audio_path)):
                    print("跳过此测试（音频生成失败）")
                    continue
                
                print("-" * 40)
                
                # 测试每个 ASR 模型
                for model in ASR_MODELS:
                    if not self.check_model_available(model):
                        print(f"模型 {model} 未安装，跳过")
                        continue
                        
                    # 根据语言类型设置参数
                    if lang_type == "chinese":
                        language = "zh"
                    elif lang_type == "english":
                        language = "en"
                    else:
                        language = None  # 混合语言让模型自动检测
                    
                    result = self.test_asr(str(audio_path), model, language)
                    
                    if result['success']:
                        recognized_text = result['text']
                        accuracy = self.calculate_accuracy(text, recognized_text)
                        
                        print(f"\n模型: {model.split('/')[-1]}")
                        print(f"识别: {recognized_text}")
                        print(f"准确率: {accuracy:.1f}%")
                        print(f"耗时: {result['duration']:.2f}秒")
                        
                        # 保存结果
                        self.results.append({
                            'language': lang_type,
                            'description': description,
                            'original': text,
                            'recognized': recognized_text,
                            'model': model,
                            'accuracy': accuracy,
                            'duration': result['duration'],
                            'voice': voice
                        })
                    else:
                        print(f"\n模型 {model} 识别失败: {result['error']}")
        
        # 生成测试报告
        self.generate_report()
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
    
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
        print("测试报告总结")
        print("=" * 80)
        
        if not self.results:
            print("没有测试结果")
            return
        
        # 按模型分组统计
        model_stats = {}
        for result in self.results:
            model = result['model'].split('/')[-1]
            if model not in model_stats:
                model_stats[model] = {
                    'total': 0,
                    'chinese': {'count': 0, 'accuracy': 0, 'duration': 0},
                    'english': {'count': 0, 'accuracy': 0, 'duration': 0},
                    'mixed': {'count': 0, 'accuracy': 0, 'duration': 0}
                }
            
            lang = result['language']
            model_stats[model]['total'] += 1
            model_stats[model][lang]['count'] += 1
            model_stats[model][lang]['accuracy'] += result['accuracy']
            model_stats[model][lang]['duration'] += result['duration']
        
        # 计算平均值并显示
        print("\n模型性能对比:")
        print("-" * 80)
        print(f"{'模型':<30} {'语言':<10} {'平均准确率':<12} {'平均耗时':<10}")
        print("-" * 80)
        
        for model, stats in model_stats.items():
            for lang in ['chinese', 'english', 'mixed']:
                if stats[lang]['count'] > 0:
                    avg_accuracy = stats[lang]['accuracy'] / stats[lang]['count']
                    avg_duration = stats[lang]['duration'] / stats[lang]['count']
                    print(f"{model:<30} {lang:<10} {avg_accuracy:>10.1f}% {avg_duration:>8.2f}s")
        
        # 保存详细结果到文件
        report_path = Path("asr_test_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'base_url': self.base_url,
                'models_tested': list(set(r['model'] for r in self.results)),
                'results': self.results,
                'summary': model_stats
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_path}")


def main():
    """主函数"""
    tester = ASRTester()
    
    # 检查服务是否可用
    try:
        response = httpx.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("错误: Speaches 服务不可用")
            return
    except Exception as e:
        print(f"错误: 无法连接到 Speaches 服务 - {e}")
        return
    
    # 运行测试
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()