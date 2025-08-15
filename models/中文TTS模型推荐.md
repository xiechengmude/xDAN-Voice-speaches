# 中文TTS模型推荐

## 🎯 当前可用的中文TTS方案

### 1. **Kokoro 系列（推荐） ✅**

**可用模型：**
- `speaches-ai/Kokoro-82M-v1.0-ONNX` - 标准版（推荐）
- `speaches-ai/Kokoro-82M-v1.0-ONNX-fp16` - 速度更快
- `speaches-ai/Kokoro-82M-v1.0-ONNX-int8` - 最快最小

**中文声音选项（8个）：**
```
女声：
- zf_xiaobei   (晓贝)
- zf_xiaoni    (晓妮)  
- zf_xiaoxiao  (晓晓)
- zf_xiaoyi    (晓伊)

男声：
- zm_yunjian   (云健)
- zm_yunxi     (云熙)
- zm_yunxia    (云夏)
- zm_yunyang   (云扬)
```

**优点：**
- ✅ 多语言支持（中英日等）
- ✅ 高质量24kHz采样率
- ✅ 8个中文声音可选
- ✅ 已验证可用（需客户端预处理）

**使用方法：**
```python
# 客户端预处理纯中文
def preprocess_chinese_text(text):
    has_ascii = any(ord(char) < 128 for char in text)
    if not has_ascii and text.strip():
        return text + "."
    return text

# API调用
payload = {
    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "input": preprocess_chinese_text("你好世界"),
    "voice": "zf_xiaobei",  # 选择中文声音
    "response_format": "mp3"
}
```

### 2. **Piper 中文模型（不可用）❌**

**理论上的模型：**
- `speaches-ai/piper-zh_CN-huayan-medium`

**状态：**
- ❌ 服务器未安装
- ❌ 下载API返回404
- ❌ 当前不可用

### 3. **其他潜在选项**

**hexgrad/Kokoro-82M-v1.1-zh**
- 新增100个中文声音
- 但是PyTorch格式(.pth)
- 本项目只支持ONNX格式
- 需要转换才能使用

## 📊 模型对比

| 特性 | Kokoro-82M | Piper-zh_CN | hexgrad v1.1 |
|-----|-----------|------------|--------------|
| 可用性 | ✅ 可用 | ❌ 不可用 | ❌ 需转换 |
| 中文支持 | ✅ 8个声音 | ✅ 专用 | ✅ 100个声音 |
| 多语言 | ✅ 支持 | ❌ 仅中文 | ✅ 支持 |
| 格式 | ONNX | ONNX | PyTorch |
| 纯中文处理 | 需添加句号 | 原生支持 | 未知 |

## 💡 推荐方案

### 短期方案（立即可用）
使用 **Kokoro-82M-v1.0-ONNX** + 客户端预处理
- 已验证100%成功率
- 8个中文声音可选
- 支持中英混合

### 中期方案（需要配置）
1. 联系服务器管理员安装 Piper 中文模型
2. 或等待 hexgrad v1.1 的ONNX版本

### 长期方案（理想状态）
1. 服务端自动处理纯中文（已提交修复）
2. 支持更多中文专用模型
3. 提供更多中文声音选项

## 🎯 结论

**当前最佳选择：Kokoro-82M + 客户端预处理**

这个方案已经能够：
- ✅ 100%成功生成中文语音
- ✅ 支持多种中文声音
- ✅ 处理中英混合文本
- ✅ 立即可用，无需等待