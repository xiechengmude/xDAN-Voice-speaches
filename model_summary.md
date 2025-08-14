# xDAN Voice Speaches 模型分析总结

基于 available_models.md 文件的分析，以下是支持中英文的 TTS 和 ASR 模型整理：

## 一、支持中文的 TTS（文字转语音）模型

### 1. Kokoro 系列（多语言模型，包含中文）
- **模型ID**: speaches-ai/Kokoro-82M-v1.0-ONNX-fp16
- **支持语言**: multilingual（多语言，包括中文）
- **模型大小**: 82M
- **采样率**: 24000 Hz
- **中文声音**:
  - 女声: zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi
  - 男声: zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang
- **特点**: 高质量多语言 TTS，支持多种中文声音，fp16 精度

- **模型ID**: speaches-ai/Kokoro-82M-v1.0-ONNX-int8
- **支持语言**: multilingual（多语言，包括中文）
- **模型大小**: 82M
- **特点**: int8 量化版本，更小更快，精度略有降低

- **模型ID**: speaches-ai/Kokoro-82M-v1.0-ONNX
- **支持语言**: multilingual（多语言，包括中文）
- **模型大小**: 82M
- **特点**: 标准 ONNX 版本

### 2. Piper 中文模型
- **模型ID**: speaches-ai/piper-zh_CN-huayan-medium
- **支持语言**: zh（中文）
- **质量等级**: medium
- **采样率**: 22050 Hz
- **声音**: huayan（女声）

## 二、支持英文的 TTS 模型

### 1. Kokoro 系列（同时支持英文）
- 上述 Kokoro 模型都支持英文，包含多种英式和美式英语声音：
  - 美式英语女声: af_heart, af_alloy, af_nova, af_river 等
  - 美式英语男声: am_adam, am_echo, am_michael, am_onyx 等
  - 英式英语女声: bf_alice, bf_emma, bf_isabella, bf_lily
  - 英式英语男声: bm_daniel, bm_george, bm_lewis

### 2. Piper 英文模型（精选）
- **高质量模型**:
  - speaches-ai/piper-en_US-lessac-high（美式，高质量）
  - speaches-ai/piper-en_US-ryan-high（美式，高质量）
  - speaches-ai/piper-en_GB-cori-high（英式，高质量）

- **中等质量模型**:
  - speaches-ai/piper-en_US-amy-medium（美式女声）
  - speaches-ai/piper-en_US-john-medium（美式男声）
  - speaches-ai/piper-en_GB-alan-medium（英式男声）

## 三、ASR（语音识别）模型

根据文件内容，未发现明确的 ASR（speech-to-text 或 automatic-speech-recognition）模型。该服务似乎主要专注于 TTS（文字转语音）功能。

如果需要 ASR 功能，可能需要：
1. 查看是否有其他 API 端点提供 ASR 服务
2. 考虑使用其他专门的 ASR 服务（如 Whisper API）

## 推荐使用

### 中英文混合场景推荐：
1. **首选**: Kokoro-82M 系列（支持多语言，质量高）
   - 优点：同一模型支持中英文，声音自然，多种音色选择
   - 适用：需要中英文混合输出的场景

### 纯中文场景：
1. speaches-ai/piper-zh_CN-huayan-medium

### 纯英文场景：
1. 高质量需求：使用 -high 结尾的 Piper 模型
2. 平衡需求：使用 -medium 结尾的 Piper 模型

## 注意事项
1. 采样率：Kokoro 使用 24000Hz，Piper 大多使用 22050Hz
2. 模型大小：Kokoro 为 82M，相对较大但质量更好
3. 精度选择：fp16 质量最好，int8 速度更快但质量略降