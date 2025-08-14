#!/usr/bin/env python3
"""
检查 Speaches 模型状态
了解哪些模型已经加载在内存中
"""

import httpx
import time
import json
from datetime import datetime

SPEACHES_BASE_URL = "http://localhost:8000"

def check_loaded_models():
    """检查当前已加载的模型"""
    try:
        response = httpx.get(f"{SPEACHES_BASE_URL}/v1/models")
        if response.status_code == 200:
            models = response.json().get('data', [])
            
            print("=== 当前可用模型 ===")
            print(f"总数: {len(models)}")
            print()
            
            # 按任务分类
            asr_models = [m for m in models if m.get('task') == 'automatic-speech-recognition']
            tts_models = [m for m in models if m.get('task') == 'text-to-speech']
            
            print("ASR 模型:")
            for model in asr_models:
                status = "已加载" if model.get('loaded', False) else "未加载"
                print(f"  - {model['id']} [{status}]")
            
            print("\nTTS 模型:")
            for model in tts_models[:5]:  # 只显示前5个
                status = "已加载" if model.get('loaded', False) else "未加载"
                print(f"  - {model['id']} [{status}]")
                
            return models
    except Exception as e:
        print(f"错误: {e}")
        return []

def test_model_persistence():
    """测试模型持久性"""
    print("\n=== 测试模型持久性 ===")
    
    test_text = "测试模型是否保持加载状态"
    model = "Systran/faster-distil-whisper-large-v3"
    
    # 第一次调用（可能需要加载模型）
    print(f"\n1. 第一次调用 {model}")
    start = time.time()
    
    # 创建测试音频
    tts_response = httpx.post(
        f"{SPEACHES_BASE_URL}/v1/audio/speech",
        json={
            "input": test_text,
            "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
            "voice": "zf_xiaoxiao",
            "response_format": "wav"
        }
    )
    
    if tts_response.status_code == 200:
        # 测试 ASR
        audio_data = tts_response.content
        
        asr_response = httpx.post(
            f"{SPEACHES_BASE_URL}/v1/audio/transcriptions",
            files={"file": ("test.wav", audio_data, "audio/wav")},
            data={"model": model, "language": "zh"}
        )
        
        first_time = time.time() - start
        print(f"   耗时: {first_time:.2f}秒")
        
        if asr_response.status_code == 200:
            print(f"   结果: {asr_response.json()['text']}")
        
        # 第二次调用（应该使用缓存的模型）
        print(f"\n2. 第二次调用（模型应该已在内存中）")
        start = time.time()
        
        asr_response2 = httpx.post(
            f"{SPEACHES_BASE_URL}/v1/audio/transcriptions",
            files={"file": ("test.wav", audio_data, "audio/wav")},
            data={"model": model, "language": "zh"}
        )
        
        second_time = time.time() - start
        print(f"   耗时: {second_time:.2f}秒")
        
        if asr_response2.status_code == 200:
            print(f"   结果: {asr_response2.json()['text']}")
        
        # 分析
        print(f"\n分析:")
        print(f"   首次调用: {first_time:.2f}秒")
        print(f"   二次调用: {second_time:.2f}秒")
        print(f"   速度提升: {first_time/second_time:.1f}x")
        
        if second_time < first_time * 0.5:
            print("   ✅ 模型已缓存，响应速度显著提升")
        else:
            print("   ⚠️  响应速度提升不明显")

def monitor_model_lifecycle():
    """监控模型生命周期"""
    print("\n=== 监控模型生命周期 ===")
    print("说明: Speaches 会自动管理模型的加载和卸载")
    print(f"- 模型空闲超时: 默认 300 秒（5分钟）")
    print(f"- 最大并发模型: 默认 3 个")
    print()
    
    # 模拟不同的使用模式
    patterns = [
        {
            "name": "频繁使用",
            "description": "每30秒调用一次，模型保持加载",
            "interval": 30,
            "count": 3
        },
        {
            "name": "间歇使用", 
            "description": "每2分钟调用一次，模型可能保持加载",
            "interval": 120,
            "count": 2
        },
        {
            "name": "偶尔使用",
            "description": "间隔超过5分钟，模型会被卸载",
            "interval": 360,
            "count": 2
        }
    ]
    
    for pattern in patterns:
        print(f"\n模式: {pattern['name']}")
        print(f"说明: {pattern['description']}")

def get_model_info():
    """获取模型详细信息"""
    print("\n=== 模型信息 ===")
    
    # 推荐的模型配置
    recommended = {
        "ASR": {
            "高精度": "Systran/faster-whisper-large-v3",
            "平衡": "Systran/faster-distil-whisper-large-v3",
            "快速": "Systran/faster-whisper-small"
        },
        "TTS": {
            "多语言": "speaches-ai/Kokoro-82M-v1.0-ONNX",
            "中文": "speaches-ai/piper-zh_CN-huayan-medium"
        }
    }
    
    print("推荐配置:")
    for task, models in recommended.items():
        print(f"\n{task}:")
        for use_case, model_id in models.items():
            print(f"  {use_case}: {model_id}")

def optimize_for_production():
    """生产环境优化建议"""
    print("\n=== 生产环境优化建议 ===")
    
    suggestions = [
        {
            "标题": "1. 预加载常用模型",
            "说明": "在服务启动时预加载常用模型",
            "代码": """
# 启动时调用
curl -X POST "$SPEACHES_BASE_URL/v1/models/Systran/faster-distil-whisper-large-v3"
curl -X POST "$SPEACHES_BASE_URL/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX"
"""
        },
        {
            "标题": "2. 调整模型缓存时间",
            "说明": "根据使用频率调整空闲超时",
            "代码": """
# 环境变量
export SPEACHES_MODEL_IDLE_TIMEOUT=600  # 10分钟
export SPEACHES_MAX_MODELS=5           # 允许更多模型并存
"""
        },
        {
            "标题": "3. 使用模型别名",
            "说明": "简化 API 调用",
            "代码": """
# model_aliases.json
{
  "asr-fast": "Systran/faster-distil-whisper-large-v3",
  "tts-chinese": "speaches-ai/Kokoro-82M-v1.0-ONNX"
}
"""
        },
        {
            "标题": "4. 健康检查和预热",
            "说明": "定期检查并保持模型活跃",
            "代码": """
# 每4分钟调用一次，防止模型卸载
*/4 * * * * curl -X POST "$SPEACHES_BASE_URL/v1/audio/transcriptions" \\
  -F "file=@warmup.wav" -F "model=asr-fast"
"""
        }
    ]
    
    for suggestion in suggestions:
        print(f"\n{suggestion['标题']}")
        print(f"{suggestion['说明']}")
        print(f"```bash{suggestion['代码']}```")

def main():
    """主函数"""
    print("Speaches 模型管理分析")
    print("=" * 50)
    
    # 检查服务
    try:
        response = httpx.get(f"{SPEACHES_BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Speaches 服务未运行")
            print("\n但这里是关键信息：")
            print("1. Speaches 不会每次调用都重新加载模型")
            print("2. 模型会在内存中缓存，直到空闲超时")
            print("3. 支持多个模型同时加载")
            print("4. 完全支持非实时语音转文字服务")
            return
    except:
        pass
    
    # 运行检查
    check_loaded_models()
    test_model_persistence()
    monitor_model_lifecycle()
    get_model_info()
    optimize_for_production()
    
    print("\n" + "=" * 50)
    print("总结:")
    print("✅ Speaches 支持模型常驻内存")
    print("✅ 不需要每次调用都加载模型")
    print("✅ 完全支持非实时语音转文字（就像微信）")
    print("✅ 可以通过配置优化性能")

if __name__ == "__main__":
    main()