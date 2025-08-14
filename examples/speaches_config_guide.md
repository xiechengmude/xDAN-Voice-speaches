# Speaches 配置指南 - 模型缓存设置

## 设置模型空闲超时时间为 6 小时

### 方法 1: 环境变量（推荐）

#### Linux/Mac 临时设置
```bash
# 设置为 6 小时（21600 秒）
export SPEACHES_MODEL_IDLE_TIMEOUT=21600

# 然后启动服务
uvicorn --factory --host 0.0.0.0 speaches.main:create_app
```

#### 永久设置（添加到启动脚本）

1. **创建启动脚本** `start_speaches.sh`:
```bash
#!/bin/bash
# Speaches 启动脚本 - 6小时模型缓存

# 模型缓存配置
export SPEACHES_MODEL_IDLE_TIMEOUT=21600  # 6小时 = 21600秒
export SPEACHES_MAX_MODELS=5              # 最多保持5个模型

# 其他优化配置
export HF_HUB_ENABLE_HF_TRANSFER=1        # 加速模型下载
export SPEACHES_LOG_LEVEL=INFO            # 日志级别

echo "启动 Speaches 服务..."
echo "模型空闲超时: 6 小时"
echo "最大模型数: 5"

# 启动服务
uvicorn --factory --host 0.0.0.0 --port 8000 speaches.main:create_app
```

2. **使用 systemd 服务**（生产环境）:

创建 `/etc/systemd/system/speaches.service`:
```ini
[Unit]
Description=Speaches Voice Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/speaches
Environment="SPEACHES_MODEL_IDLE_TIMEOUT=21600"
Environment="SPEACHES_MAX_MODELS=5"
Environment="SPEACHES_BASE_URL=http://localhost:8000"
ExecStart=/usr/bin/uvicorn --factory --host 0.0.0.0 speaches.main:create_app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 方法 2: Docker Compose 配置

编辑 `compose.yaml` 或 `compose.override.yaml`:

```yaml
version: '3.8'

services:
  speaches:
    image: ghcr.io/speaches-ai/speaches:latest
    ports:
      - "8000:8000"
    environment:
      # 模型缓存配置
      - SPEACHES_MODEL_IDLE_TIMEOUT=21600  # 6小时
      - SPEACHES_MAX_MODELS=5
      # 其他配置
      - SPEACHES_LOG_LEVEL=INFO
      - HF_HUB_ENABLE_HF_TRANSFER=1
    volumes:
      - speaches-models:/home/ubuntu/.cache/huggingface
      - ./model_aliases.json:/app/model_aliases.json:ro

volumes:
  speaches-models:
```

使用自定义配置启动：
```bash
docker compose up -d
```

### 方法 3: Python 开发环境

1. **创建 `.env` 文件**:
```bash
# .env 文件
SPEACHES_MODEL_IDLE_TIMEOUT=21600
SPEACHES_MAX_MODELS=5
SPEACHES_LOG_LEVEL=INFO
```

2. **使用 python-dotenv 加载**:
```python
# 在启动脚本中
from dotenv import load_dotenv
load_dotenv()

# 或者直接在命令行
python -m dotenv run uvicorn --factory speaches.main:create_app
```

### 方法 4: 配置文件（如果支持）

查看是否有 `config.yaml` 或 `settings.json`:
```yaml
# config.yaml
model_management:
  idle_timeout: 21600  # 6 hours in seconds
  max_models: 5
  preload_models:
    - "Systran/faster-distil-whisper-large-v3"
    - "speaches-ai/Kokoro-82M-v1.0-ONNX"
```

## 验证配置

### 1. 检查当前配置
```python
# check_config.py
import os
import httpx

# 检查环境变量
timeout = os.getenv('SPEACHES_MODEL_IDLE_TIMEOUT', '300')
print(f"模型空闲超时: {timeout} 秒 = {int(timeout)/3600:.1f} 小时")

# 如果服务在运行，可以通过 API 检查
try:
    response = httpx.get("http://localhost:8000/v1/models")
    # 某些实现可能在响应中包含配置信息
except:
    pass
```

### 2. 测试模型持久性
```bash
# 测试脚本
#!/bin/bash

echo "测试模型是否保持 6 小时..."

# 第一次调用
echo "1. 首次调用 ($(date))"
time curl -X POST "http://localhost:8000/v1/audio/transcriptions" \
  -F "file=@test.wav" \
  -F "model=Systran/faster-distil-whisper-large-v3"

# 等待 5 小时 59 分钟
echo "等待 5 小时 59 分钟..."
sleep 21540  # 359 分钟

# 第二次调用（应该还在内存中）
echo "2. 5小时59分后调用 ($(date))"
time curl -X POST "http://localhost:8000/v1/audio/transcriptions" \
  -F "file=@test.wav" \
  -F "model=Systran/faster-distil-whisper-large-v3"
```

## 最佳实践

### 1. 生产环境推荐配置
```bash
# 长时间缓存，适合生产环境
export SPEACHES_MODEL_IDLE_TIMEOUT=21600  # 6小时
export SPEACHES_MAX_MODELS=10             # 允许更多模型
export SPEACHES_MODEL_LOAD_TIMEOUT=300    # 加载超时5分钟
```

### 2. 预加载常用模型
```bash
# startup.sh - 服务启动后执行
#!/bin/bash

echo "预加载常用模型..."

# ASR 模型
curl -X POST "http://localhost:8000/v1/models/Systran/faster-distil-whisper-large-v3"
curl -X POST "http://localhost:8000/v1/models/Systran/faster-whisper-large-v3"

# TTS 模型
curl -X POST "http://localhost:8000/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX"

echo "模型预加载完成"
```

### 3. 监控脚本
```python
# monitor_models.py
import time
import httpx
from datetime import datetime

def check_model_status():
    """检查模型状态"""
    response = httpx.get("http://localhost:8000/v1/models")
    models = response.json()['data']
    
    loaded = [m for m in models if m.get('loaded', False)]
    print(f"[{datetime.now()}] 已加载模型: {len(loaded)}")
    
    for model in loaded:
        print(f"  - {model['id']}")

# 每小时检查一次
while True:
    check_model_status()
    time.sleep(3600)
```

## 注意事项

1. **内存使用**: 6小时缓存意味着模型会占用内存更长时间
   - Whisper Large: ~1.5GB
   - Kokoro TTS: ~200MB
   - 建议: 确保有足够的内存

2. **负载均衡**: 如果使用多实例，每个实例都需要设置
   ```bash
   # 实例 1
   SPEACHES_MODEL_IDLE_TIMEOUT=21600 uvicorn --port 8001 ...
   
   # 实例 2  
   SPEACHES_MODEL_IDLE_TIMEOUT=21600 uvicorn --port 8002 ...
   ```

3. **配置优先级**（从高到低）:
   - 命令行参数
   - 环境变量
   - 配置文件
   - 默认值

这样设置后，模型会在内存中保持 6 小时，大大提高了响应速度！