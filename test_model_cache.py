#!/usr/bin/env python3
"""
测试模型缓存是否生效
验证设置的空闲超时时间
"""

import os
import time
import httpx
from datetime import datetime
from pathlib import Path

# 配置
BASE_URL = os.getenv("SPEACHES_BASE_URL", "http://localhost:8000")
ASR_MODEL = "Systran/faster-distil-whisper-large-v3"  # 使用 distil 模型
TTS_MODEL = "speaches-ai/Kokoro-82M-v1.0-ONNX"

def log(message):
    """带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_service():
    """检查服务是否运行"""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def generate_test_audio():
    """生成测试音频"""
    log("生成测试音频...")
    
    text = "这是一个测试音频，用于验证模型缓存功能是否正常工作。"
    
    try:
        response = httpx.post(
            f"{BASE_URL}/v1/audio/speech",
            json={
                "input": text,
                "model": TTS_MODEL,
                "voice": "zf_xiaoxiao",
                "response_format": "wav"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            with open("test_cache_audio.wav", "wb") as f:
                f.write(response.content)
            log("✓ 音频生成成功")
            return True
        else:
            log(f"✗ 音频生成失败: {response.status_code}")
            return False
    except Exception as e:
        log(f"✗ 生成音频错误: {e}")
        return False

def test_asr_with_timing(audio_file, test_name):
    """测试 ASR 并计时"""
    log(f"测试 {test_name}...")
    
    if not Path(audio_file).exists():
        log(f"✗ 音频文件不存在: {audio_file}")
        return None
    
    start_time = time.time()
    
    try:
        with open(audio_file, 'rb') as f:
            response = httpx.post(
                f"{BASE_URL}/v1/audio/transcriptions",
                files={"file": (audio_file, f, "audio/wav")},
                data={
                    "model": ASR_MODEL,
                    "language": "zh",
                    "response_format": "json"
                },
                timeout=60
            )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "")
            log(f"✓ 识别成功")
            log(f"  模型: {ASR_MODEL}")
            log(f"  耗时: {elapsed_time:.2f} 秒")
            log(f"  结果: {text}")
            return elapsed_time
        else:
            log(f"✗ 识别失败: {response.status_code}")
            return None
            
    except Exception as e:
        log(f"✗ 识别错误: {e}")
        return None

def check_loaded_models():
    """检查当前已加载的模型"""
    try:
        response = httpx.get(f"{BASE_URL}/v1/models")
        if response.status_code == 200:
            models = response.json().get('data', [])
            
            # 查找我们的模型
            asr_loaded = any(m['id'] == ASR_MODEL for m in models)
            tts_loaded = any(m['id'] == TTS_MODEL for m in models)
            
            log("当前模型状态:")
            log(f"  ASR ({ASR_MODEL}): {'已加载' if asr_loaded else '未加载'}")
            log(f"  TTS ({TTS_MODEL}): {'已加载' if tts_loaded else '未加载'}")
            
            return asr_loaded, tts_loaded
    except Exception as e:
        log(f"检查模型状态失败: {e}")
        return False, False

def run_cache_test():
    """运行缓存测试"""
    log("=" * 60)
    log("开始模型缓存测试")
    log(f"ASR 模型: {ASR_MODEL}")
    log(f"TTS 模型: {TTS_MODEL}")
    log("=" * 60)
    
    # 1. 检查服务
    if not check_service():
        log("❌ Speaches 服务未运行!")
        log("请先启动服务:")
        log("export SPEACHES_MODEL_IDLE_TIMEOUT=21600")
        log("uvicorn --factory --host 0.0.0.0 speaches.main:create_app")
        return
    
    log("✓ Speaches 服务正在运行")
    
    # 2. 生成测试音频
    if not generate_test_audio():
        log("❌ 无法生成测试音频")
        return
    
    # 3. 第一次 ASR 测试（冷启动）
    log("\n" + "-" * 40)
    time1 = test_asr_with_timing("test_cache_audio.wav", "第一次调用（冷启动）")
    if time1 is None:
        log("❌ 第一次测试失败")
        return
    
    # 检查模型状态
    check_loaded_models()
    
    # 4. 等待一小段时间
    wait_time = 5
    log(f"\n等待 {wait_time} 秒...")
    time.sleep(wait_time)
    
    # 5. 第二次 ASR 测试（使用缓存）
    log("\n" + "-" * 40)
    time2 = test_asr_with_timing("test_cache_audio.wav", "第二次调用（缓存）")
    if time2 is None:
        log("❌ 第二次测试失败")
        return
    
    # 6. 第三次测试
    log("\n" + "-" * 40)
    time3 = test_asr_with_timing("test_cache_audio.wav", "第三次调用（缓存）")
    
    # 7. 分析结果
    log("\n" + "=" * 60)
    log("测试结果分析")
    log("=" * 60)
    log(f"第一次调用（冷启动）: {time1:.2f} 秒")
    log(f"第二次调用（缓存）: {time2:.2f} 秒")
    if time3:
        log(f"第三次调用（缓存）: {time3:.2f} 秒")
    
    # 计算加速比
    if time2 > 0:
        speedup = time1 / time2
        log(f"\n缓存加速比: {speedup:.1f}x")
        
        if speedup > 2:
            log("✅ 模型缓存工作正常！")
            log("✅ 模型已常驻内存，响应速度显著提升")
        else:
            log("⚠️  缓存效果不明显，可能需要检查配置")
    
    # 检查最终模型状态
    log("\n最终模型状态:")
    check_loaded_models()
    
    # 清理
    if Path("test_cache_audio.wav").exists():
        Path("test_cache_audio.wav").unlink()
        log("\n✓ 清理测试文件")

def test_model_persistence():
    """测试模型持久性（长时间）"""
    log("\n" + "=" * 60)
    log("模型持久性测试")
    log("=" * 60)
    
    # 获取当前配置的超时时间
    timeout = os.getenv("SPEACHES_MODEL_IDLE_TIMEOUT", "300")
    log(f"当前配置的空闲超时: {timeout} 秒 ({float(timeout)/3600:.1f} 小时)")
    
    if int(timeout) >= 21600:
        log("✅ 已设置为 6 小时缓存")
        log("模型将在内存中保持 6 小时")
    else:
        log("⚠️  当前超时时间较短")
        log("建议设置: export SPEACHES_MODEL_IDLE_TIMEOUT=21600")
    
    # 测试计划
    log("\n测试计划:")
    log("1. 立即测试 - 验证模型加载")
    log("2. 5分钟后 - 验证短期缓存")
    log("3. 1小时后 - 验证中期缓存")
    log("4. 6小时后 - 验证长期缓存")
    
    response = input("\n是否运行长时间测试? (y/n): ")
    if response.lower() == 'y':
        intervals = [0, 300, 3600, 21600]  # 0, 5分钟, 1小时, 6小时
        
        for i, interval in enumerate(intervals):
            if interval > 0:
                log(f"\n等待 {interval/60:.0f} 分钟...")
                time.sleep(interval)
            
            log(f"\n测试 {i+1}: {interval/60:.0f} 分钟后")
            test_asr_with_timing("test_cache_audio.wav", f"间隔 {interval/60:.0f} 分钟")
            check_loaded_models()

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "long":
        # 长时间测试
        test_model_persistence()
    else:
        # 快速测试
        run_cache_test()
    
    log("\n测试完成！")
    
    # 提示
    print("\n" + "="*60)
    print("提示:")
    print("1. 如果要设置 6 小时缓存:")
    print("   export SPEACHES_MODEL_IDLE_TIMEOUT=21600")
    print("2. 运行长时间测试:")
    print("   python test_model_cache.py long")
    print("="*60)

if __name__ == "__main__":
    main()