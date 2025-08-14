# Speaches TypeScript/前端客户端使用指南

## 安装依赖

```bash
# 基础依赖
npm install axios openai

# WebSocket 和音频处理
npm install socket.io-client recordrtc

# TypeScript 类型定义
npm install --save-dev @types/recordrtc
```

## 一、ASR（语音识别）服务

### 1. 基础 ASR 客户端

```typescript
// speachesASR.ts
import axios, { AxiosInstance } from 'axios';

interface TranscriptionResult {
  text: string;
  language?: string;
  duration?: number;
  words?: Array<{
    word: string;
    start: number;
    end: number;
    probability: number;
  }>;
}

class SpeachesASR {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
    });
  }

  /**
   * 转录音频文件
   */
  async transcribe(
    audioFile: File | Blob,
    options: {
      model?: string;
      language?: string;
      responseFormat?: 'json' | 'text' | 'srt' | 'vtt' | 'verbose_json';
      temperature?: number;
      prompt?: string;
    } = {}
  ): Promise<TranscriptionResult> {
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('model', options.model || 'Systran/faster-distil-whisper-large-v3');
    
    if (options.language) formData.append('language', options.language);
    if (options.responseFormat) formData.append('response_format', options.responseFormat);
    if (options.temperature) formData.append('temperature', options.temperature.toString());
    if (options.prompt) formData.append('prompt', options.prompt);

    const response = await this.client.post('/v1/audio/transcriptions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * 转录音频并获取时间戳
   */
  async transcribeWithTimestamps(audioFile: File | Blob, model?: string): Promise<TranscriptionResult> {
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('model', model || 'Systran/faster-distil-whisper-large-v3');
    formData.append('response_format', 'verbose_json');
    formData.append('timestamp_granularities[]', 'word');

    const response = await this.client.post('/v1/audio/transcriptions', formData);
    return response.data;
  }
}

// 使用示例
const asr = new SpeachesASR();

// 文件上传处理
const fileInput = document.getElementById('audioFile') as HTMLInputElement;
fileInput.addEventListener('change', async (event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) {
    try {
      const result = await asr.transcribe(file, { language: 'zh' });
      console.log('转录结果:', result.text);
    } catch (error) {
      console.error('转录失败:', error);
    }
  }
});
```

### 2. 使用 OpenAI SDK

```typescript
// openaiClient.ts
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'sk-fake-key', // Speaches 不需要真实的 API key
  baseURL: 'http://localhost:8000/v1',
  dangerouslyAllowBrowser: true, // 浏览器环境需要
});

/**
 * 使用 OpenAI SDK 转录音频
 */
async function transcribeWithOpenAI(audioFile: File): Promise<string> {
  const transcription = await openai.audio.transcriptions.create({
    file: audioFile,
    model: 'Systran/faster-distil-whisper-large-v3',
    language: 'zh',
  });

  return transcription.text;
}

// React 组件示例
import React, { useState } from 'react';

const TranscriptionComponent: React.FC = () => {
  const [transcription, setTranscription] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    try {
      const text = await transcribeWithOpenAI(file);
      setTranscription(text);
    } catch (error) {
      console.error('转录失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <input type="file" accept="audio/*" onChange={handleFileUpload} />
      {isLoading && <p>正在转录...</p>}
      {transcription && (
        <div>
          <h3>转录结果：</h3>
          <p>{transcription}</p>
        </div>
      )}
    </div>
  );
};
```

### 3. 实时语音识别（WebSocket）

```typescript
// realtimeASR.ts
interface RealtimeASRConfig {
  wsURL?: string;
  model?: string;
  language?: string;
  onTranscript?: (text: string) => void;
  onError?: (error: Error) => void;
}

class RealtimeASR {
  private ws: WebSocket | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private config: RealtimeASRConfig;

  constructor(config: RealtimeASRConfig = {}) {
    this.config = {
      wsURL: 'ws://localhost:8000/v1/realtime',
      model: 'Systran/faster-distil-whisper-large-v3',
      language: 'zh',
      ...config,
    };
  }

  /**
   * 开始实时识别
   */
  async start(): Promise<void> {
    try {
      // 1. 获取麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // 2. 建立 WebSocket 连接
      this.ws = new WebSocket(this.config.wsURL!);

      this.ws.onopen = () => {
        console.log('WebSocket 连接已建立');
        
        // 配置会话
        this.ws!.send(JSON.stringify({
          type: 'session.update',
          session: {
            model: this.config.model,
            transcription_options: {
              language: this.config.language,
              temperature: 0.3,
            },
          },
        }));

        // 开始录音
        this.startRecording(stream);
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'response.audio_transcript.delta') {
          const text = data.delta?.text || '';
          this.config.onTranscript?.(text);
        } else if (data.type === 'error') {
          this.config.onError?.(new Error(data.error?.message || '未知错误'));
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
        this.config.onError?.(new Error('WebSocket 连接错误'));
      };

      this.ws.onclose = () => {
        console.log('WebSocket 连接已关闭');
        this.stop();
      };

    } catch (error) {
      console.error('启动失败:', error);
      this.config.onError?.(error as Error);
    }
  }

  /**
   * 开始录音
   */
  private startRecording(stream: MediaStream): void {
    this.mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
    });

    this.mediaRecorder.ondataavailable = async (event) => {
      if (event.data.size > 0 && this.ws?.readyState === WebSocket.OPEN) {
        // 转换为 base64 并发送
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result?.toString().split(',')[1];
          if (base64) {
            this.ws!.send(JSON.stringify({
              type: 'input_audio_buffer.append',
              audio: base64,
            }));
          }
        };
        reader.readAsDataURL(event.data);
      }
    };

    // 每 100ms 发送一次数据
    this.mediaRecorder.start(100);
  }

  /**
   * 停止识别
   */
  stop(): void {
    if (this.mediaRecorder?.state === 'recording') {
      this.mediaRecorder.stop();
    }
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.close();
    }

    this.mediaRecorder = null;
    this.ws = null;
  }
}

// React Hook 示例
import { useState, useCallback, useRef } from 'react';

function useRealtimeASR() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const asrRef = useRef<RealtimeASR | null>(null);

  const startListening = useCallback(async () => {
    try {
      setError(null);
      setTranscript('');
      
      asrRef.current = new RealtimeASR({
        onTranscript: (text) => {
          setTranscript(prev => prev + text);
        },
        onError: (err) => {
          setError(err.message);
          setIsListening(false);
        },
      });

      await asrRef.current.start();
      setIsListening(true);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  const stopListening = useCallback(() => {
    asrRef.current?.stop();
    setIsListening(false);
  }, []);

  return {
    isListening,
    transcript,
    error,
    startListening,
    stopListening,
  };
}

// 使用 Hook 的组件
const RealtimeTranscription: React.FC = () => {
  const { isListening, transcript, error, startListening, stopListening } = useRealtimeASR();

  return (
    <div>
      <button onClick={isListening ? stopListening : startListening}>
        {isListening ? '停止' : '开始'}识别
      </button>
      
      {error && <div style={{ color: 'red' }}>错误: {error}</div>}
      
      <div>
        <h3>识别结果：</h3>
        <p>{transcript || '等待语音输入...'}</p>
      </div>
    </div>
  );
};
```

### 4. 录音并识别

```typescript
// audioRecorder.ts
import RecordRTC from 'recordrtc';

class AudioRecorder {
  private recorder: RecordRTC | null = null;
  private stream: MediaStream | null = null;

  /**
   * 开始录音
   */
  async startRecording(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    this.recorder = new RecordRTC(this.stream, {
      type: 'audio',
      mimeType: 'audio/wav',
      recorderType: RecordRTC.StereoAudioRecorder,
      numberOfAudioChannels: 1,
      desiredSampRate: 16000,
    });

    this.recorder.startRecording();
  }

  /**
   * 停止录音并返回音频 Blob
   */
  stopRecording(): Promise<Blob> {
    return new Promise((resolve) => {
      if (!this.recorder) {
        throw new Error('录音器未初始化');
      }

      this.recorder.stopRecording(() => {
        const blob = this.recorder!.getBlob();
        
        // 清理
        if (this.stream) {
          this.stream.getTracks().forEach(track => track.stop());
        }
        
        resolve(blob);
      });
    });
  }
}

// Vue 3 组合式 API 示例
import { ref } from 'vue';

export function useAudioRecorder() {
  const isRecording = ref(false);
  const transcription = ref('');
  const recorder = new AudioRecorder();
  const asr = new SpeachesASR();

  const toggleRecording = async () => {
    if (isRecording.value) {
      // 停止录音
      try {
        const audioBlob = await recorder.stopRecording();
        isRecording.value = false;

        // 转录音频
        const result = await asr.transcribe(audioBlob, { language: 'zh' });
        transcription.value = result.text;
      } catch (error) {
        console.error('处理失败:', error);
      }
    } else {
      // 开始录音
      await recorder.startRecording();
      isRecording.value = true;
      transcription.value = '';
    }
  };

  return {
    isRecording,
    transcription,
    toggleRecording,
  };
}
```

## 二、TTS（文字转语音）服务

### 1. 基础 TTS 客户端

```typescript
// speachesTTS.ts
interface TTSOptions {
  model?: string;
  voice?: string;
  speed?: number;
  responseFormat?: 'mp3' | 'opus' | 'aac' | 'flac' | 'wav' | 'pcm';
}

interface Voice {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female';
}

class SpeachesTTS {
  private client: AxiosInstance;
  private baseURL: string;

  // 预定义的声音列表
  static readonly VOICES = {
    chinese: {
      female: ['zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi'],
      male: ['zm_yunjian', 'zm_yunxi', 'zm_yunxia', 'zm_yunyang'],
    },
    english: {
      female: ['af_heart', 'af_bella', 'af_nicole', 'bf_alice', 'bf_emma'],
      male: ['am_adam', 'am_michael', 'bm_daniel', 'bm_george'],
    },
  };

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
    });
  }

  /**
   * 合成语音
   */
  async synthesize(text: string, options: TTSOptions = {}): Promise<Blob> {
    const response = await this.client.post(
      '/v1/audio/speech',
      {
        input: text,
        model: options.model || 'speaches-ai/Kokoro-82M-v1.0-ONNX',
        voice: options.voice || 'zf_xiaoxiao',
        speed: options.speed || 1.0,
        response_format: options.responseFormat || 'mp3',
      },
      {
        responseType: 'blob',
      }
    );

    return response.data;
  }

  /**
   * 合成并播放语音
   */
  async synthesizeAndPlay(text: string, options: TTSOptions = {}): Promise<void> {
    const audioBlob = await this.synthesize(text, options);
    const audioUrl = URL.createObjectURL(audioBlob);
    
    const audio = new Audio(audioUrl);
    audio.play();

    // 清理 URL
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(audioUrl);
    });

    return new Promise((resolve) => {
      audio.addEventListener('ended', resolve);
    });
  }

  /**
   * 获取可用的声音列表
   */
  getAvailableVoices(language: 'chinese' | 'english' = 'chinese'): Voice[] {
    const voices: Voice[] = [];
    const voiceData = SpeachesTTS.VOICES[language];

    Object.entries(voiceData).forEach(([gender, voiceIds]) => {
      voiceIds.forEach(id => {
        voices.push({
          id,
          name: id.split('_')[1],
          language,
          gender: gender as 'male' | 'female',
        });
      });
    });

    return voices;
  }
}

// 使用示例
const tts = new SpeachesTTS();

// 简单合成
async function speakText() {
  await tts.synthesizeAndPlay('你好，欢迎使用语音合成服务！', {
    voice: 'zf_xiaoxiao',
    speed: 1.0,
  });
}

// 下载音频
async function downloadAudio(text: string) {
  const blob = await tts.synthesize(text);
  
  // 创建下载链接
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'speech.mp3';
  a.click();
  
  URL.revokeObjectURL(url);
}
```

### 2. React TTS 组件

```typescript
// TTSComponent.tsx
import React, { useState, useEffect } from 'react';
import { SpeachesTTS } from './speachesTTS';

interface TTSComponentProps {
  defaultVoice?: string;
  defaultSpeed?: number;
}

const TTSComponent: React.FC<TTSComponentProps> = ({
  defaultVoice = 'zf_xiaoxiao',
  defaultSpeed = 1.0,
}) => {
  const [text, setText] = useState('');
  const [voice, setVoice] = useState(defaultVoice);
  const [speed, setSpeed] = useState(defaultSpeed);
  const [isLoading, setIsLoading] = useState(false);
  const [voices, setVoices] = useState<Voice[]>([]);

  const tts = new SpeachesTTS();

  useEffect(() => {
    // 加载可用声音
    const chineseVoices = tts.getAvailableVoices('chinese');
    const englishVoices = tts.getAvailableVoices('english');
    setVoices([...chineseVoices, ...englishVoices]);
  }, []);

  const handleSpeak = async () => {
    if (!text.trim()) return;

    setIsLoading(true);
    try {
      await tts.synthesizeAndPlay(text, { voice, speed });
    } catch (error) {
      console.error('合成失败:', error);
      alert('语音合成失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!text.trim()) return;

    setIsLoading(true);
    try {
      const blob = await tts.synthesize(text, { voice, speed });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `speech_${Date.now()}.mp3`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="tts-component">
      <h2>文字转语音</h2>
      
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="请输入要合成的文本..."
        rows={4}
        style={{ width: '100%', marginBottom: '10px' }}
      />

      <div style={{ marginBottom: '10px' }}>
        <label>
          声音：
          <select value={voice} onChange={(e) => setVoice(e.target.value)}>
            <optgroup label="中文女声">
              {voices
                .filter(v => v.language === 'chinese' && v.gender === 'female')
                .map(v => (
                  <option key={v.id} value={v.id}>{v.name}</option>
                ))}
            </optgroup>
            <optgroup label="中文男声">
              {voices
                .filter(v => v.language === 'chinese' && v.gender === 'male')
                .map(v => (
                  <option key={v.id} value={v.id}>{v.name}</option>
                ))}
            </optgroup>
            <optgroup label="英文声音">
              {voices
                .filter(v => v.language === 'english')
                .map(v => (
                  <option key={v.id} value={v.id}>{v.name} ({v.gender})</option>
                ))}
            </optgroup>
          </select>
        </label>

        <label style={{ marginLeft: '20px' }}>
          语速：
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={speed}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
          />
          <span>{speed.toFixed(1)}x</span>
        </label>
      </div>

      <div>
        <button 
          onClick={handleSpeak} 
          disabled={isLoading || !text.trim()}
        >
          {isLoading ? '处理中...' : '播放'}
        </button>
        
        <button 
          onClick={handleDownload} 
          disabled={isLoading || !text.trim()}
          style={{ marginLeft: '10px' }}
        >
          下载音频
        </button>
      </div>
    </div>
  );
};

export default TTSComponent;
```

### 3. Vue 3 TTS 组件

```vue
<!-- TTSComponent.vue -->
<template>
  <div class="tts-component">
    <h2>文字转语音</h2>
    
    <textarea
      v-model="text"
      placeholder="请输入要合成的文本..."
      rows="4"
      class="w-full mb-4"
    />

    <div class="mb-4">
      <label class="mr-4">
        声音：
        <select v-model="selectedVoice">
          <optgroup label="中文女声">
            <option 
              v-for="voice in chineseFemaleVoices" 
              :key="voice.id" 
              :value="voice.id"
            >
              {{ voice.name }}
            </option>
          </optgroup>
          <optgroup label="中文男声">
            <option 
              v-for="voice in chineseMaleVoices" 
              :key="voice.id" 
              :value="voice.id"
            >
              {{ voice.name }}
            </option>
          </optgroup>
        </select>
      </label>

      <label>
        语速：
        <input
          type="range"
          min="0.5"
          max="2.0"
          step="0.1"
          v-model.number="speed"
        />
        <span>{{ speed.toFixed(1) }}x</span>
      </label>
    </div>

    <div>
      <button 
        @click="speak" 
        :disabled="isLoading || !text.trim()"
        class="btn btn-primary"
      >
        {{ isLoading ? '处理中...' : '播放' }}
      </button>
      
      <button 
        @click="download" 
        :disabled="isLoading || !text.trim()"
        class="btn btn-secondary ml-2"
      >
        下载音频
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { SpeachesTTS } from './speachesTTS';

const text = ref('');
const selectedVoice = ref('zf_xiaoxiao');
const speed = ref(1.0);
const isLoading = ref(false);
const voices = ref<Voice[]>([]);

const tts = new SpeachesTTS();

const chineseFemaleVoices = computed(() => 
  voices.value.filter(v => v.language === 'chinese' && v.gender === 'female')
);

const chineseMaleVoices = computed(() => 
  voices.value.filter(v => v.language === 'chinese' && v.gender === 'male')
);

onMounted(() => {
  // 加载可用声音
  const chineseVoices = tts.getAvailableVoices('chinese');
  voices.value = chineseVoices;
});

const speak = async () => {
  if (!text.value.trim()) return;

  isLoading.value = true;
  try {
    await tts.synthesizeAndPlay(text.value, {
      voice: selectedVoice.value,
      speed: speed.value,
    });
  } catch (error) {
    console.error('合成失败:', error);
    alert('语音合成失败，请稍后重试');
  } finally {
    isLoading.value = false;
  }
};

const download = async () => {
  if (!text.value.trim()) return;

  isLoading.value = true;
  try {
    const blob = await tts.synthesize(text.value, {
      voice: selectedVoice.value,
      speed: speed.value,
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `speech_${Date.now()}.mp3`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('下载失败:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>
```

## 三、完整应用示例

### 语音聊天应用

```typescript
// voiceChat.ts
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  audioUrl?: string;
}

class VoiceChatApp {
  private asr: SpeachesASR;
  private tts: SpeachesTTS;
  private messages: Message[] = [];
  private isRecording = false;

  constructor() {
    this.asr = new SpeachesASR();
    this.tts = new SpeachesTTS();
  }

  /**
   * 开始语音对话
   */
  async startVoiceChat(): Promise<void> {
    const recorder = new AudioRecorder();
    
    // 开始录音
    await recorder.startRecording();
    this.isRecording = true;

    // 3秒后自动停止（实际应用中可以使用 VAD）
    setTimeout(async () => {
      if (this.isRecording) {
        await this.stopAndProcess(recorder);
      }
    }, 3000);
  }

  /**
   * 停止录音并处理
   */
  private async stopAndProcess(recorder: AudioRecorder): Promise<void> {
    // 停止录音
    const audioBlob = await recorder.stopRecording();
    this.isRecording = false;

    // 转录音频
    const transcription = await this.asr.transcribe(audioBlob, { language: 'zh' });
    
    // 添加用户消息
    this.addMessage(transcription.text, 'user');

    // 生成回复（这里应该调用 AI 服务）
    const reply = await this.generateReply(transcription.text);
    
    // 添加助手消息
    this.addMessage(reply, 'assistant');

    // 合成并播放回复
    await this.tts.synthesizeAndPlay(reply, {
      voice: 'zf_xiaoxiao',
      speed: 1.0,
    });
  }

  /**
   * 生成回复（模拟）
   */
  private async generateReply(userInput: string): Promise<string> {
    // 实际应用中这里应该调用 AI 服务
    const replies = {
      '你好': '你好！很高兴为您服务，有什么可以帮助您的吗？',
      '天气': '今天天气晴朗，温度适宜，是个出门的好日子。',
      '时间': `现在是${new Date().toLocaleTimeString('zh-CN')}`,
    };

    for (const [keyword, reply] of Object.entries(replies)) {
      if (userInput.includes(keyword)) {
        return reply;
      }
    }

    return '抱歉，我没有理解您的意思，请再说一遍。';
  }

  /**
   * 添加消息
   */
  private addMessage(text: string, sender: 'user' | 'assistant'): void {
    this.messages.push({
      id: Date.now().toString(),
      text,
      sender,
      timestamp: new Date(),
    });
  }

  /**
   * 获取所有消息
   */
  getMessages(): Message[] {
    return this.messages;
  }
}

// React 语音聊天组件
const VoiceChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const chatApp = useRef(new VoiceChatApp());

  const handleStartChat = async () => {
    setIsRecording(true);
    await chatApp.current.startVoiceChat();
    setIsRecording(false);
    setMessages([...chatApp.current.getMessages()]);
  };

  return (
    <div className="voice-chat">
      <div className="messages">
        {messages.map(msg => (
          <div 
            key={msg.id} 
            className={`message ${msg.sender}`}
          >
            <span className="sender">{msg.sender === 'user' ? '你' : '助手'}:</span>
            <span className="text">{msg.text}</span>
            <span className="time">{msg.timestamp.toLocaleTimeString()}</span>
          </div>
        ))}
      </div>

      <button 
        onClick={handleStartChat} 
        disabled={isRecording}
        className="record-button"
      >
        {isRecording ? '录音中...' : '按住说话'}
      </button>
    </div>
  );
};
```

## 四、错误处理和最佳实践

### 1. 统一错误处理

```typescript
// errorHandler.ts
class SpeachesError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'SpeachesError';
  }
}

// 请求拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      throw new SpeachesError(
        error.response.data.message || '请求失败',
        error.response.data.code,
        error.response.status
      );
    } else if (error.request) {
      throw new SpeachesError('网络连接失败');
    } else {
      throw new SpeachesError('请求配置错误');
    }
  }
);
```

### 2. 重试机制

```typescript
// retry.ts
async function withRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    delay?: number;
    backoff?: boolean;
  } = {}
): Promise<T> {
  const { maxAttempts = 3, delay = 1000, backoff = true } = options;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) throw error;

      const waitTime = backoff ? delay * Math.pow(2, attempt - 1) : delay;
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }

  throw new Error('Retry failed');
}

// 使用示例
const result = await withRetry(
  () => asr.transcribe(audioFile),
  { maxAttempts: 3, delay: 1000 }
);
```

### 3. 音频工具函数

```typescript
// audioUtils.ts

/**
 * 检查浏览器音频支持
 */
export function checkAudioSupport(): {
  supported: boolean;
  mediaRecorder: boolean;
  getUserMedia: boolean;
} {
  return {
    supported: 'AudioContext' in window || 'webkitAudioContext' in window,
    mediaRecorder: 'MediaRecorder' in window,
    getUserMedia: !!(navigator.mediaDevices?.getUserMedia),
  };
}

/**
 * 转换音频格式
 */
export async function convertAudioFormat(
  blob: Blob,
  targetFormat: 'wav' | 'mp3' | 'webm'
): Promise<Blob> {
  // 使用 Web Audio API 转换
  const audioContext = new AudioContext();
  const arrayBuffer = await blob.arrayBuffer();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

  // 这里应该实现实际的格式转换逻辑
  // 简化示例，返回原始 blob
  return blob;
}

/**
 * 计算音频时长
 */
export async function getAudioDuration(blob: Blob): Promise<number> {
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);

  return new Promise((resolve) => {
    audio.addEventListener('loadedmetadata', () => {
      URL.revokeObjectURL(url);
      resolve(audio.duration);
    });
  });
}

/**
 * 音频可视化
 */
export class AudioVisualizer {
  private analyser: AnalyserNode;
  private dataArray: Uint8Array;

  constructor(stream: MediaStream) {
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    
    this.analyser = audioContext.createAnalyser();
    this.analyser.fftSize = 256;
    
    source.connect(this.analyser);
    
    const bufferLength = this.analyser.frequencyBinCount;
    this.dataArray = new Uint8Array(bufferLength);
  }

  getFrequencyData(): Uint8Array {
    this.analyser.getByteFrequencyData(this.dataArray);
    return this.dataArray;
  }

  getWaveformData(): Uint8Array {
    this.analyser.getByteTimeDomainData(this.dataArray);
    return this.dataArray;
  }
}
```

### 4. 配置管理

```typescript
// config.ts
interface SpeachesConfig {
  baseURL: string;
  wsURL: string;
  defaultASRModel: string;
  defaultTTSModel: string;
  defaultTTSVoice: string;
  timeout: number;
  maxRetries: number;
}

const defaultConfig: SpeachesConfig = {
  baseURL: process.env.REACT_APP_SPEACHES_URL || 'http://localhost:8000',
  wsURL: process.env.REACT_APP_SPEACHES_WS_URL || 'ws://localhost:8000',
  defaultASRModel: 'Systran/faster-distil-whisper-large-v3',
  defaultTTSModel: 'speaches-ai/Kokoro-82M-v1.0-ONNX',
  defaultTTSVoice: 'zf_xiaoxiao',
  timeout: 30000,
  maxRetries: 3,
};

// 配置管理器
class ConfigManager {
  private config: SpeachesConfig;

  constructor(customConfig?: Partial<SpeachesConfig>) {
    this.config = { ...defaultConfig, ...customConfig };
  }

  get(key: keyof SpeachesConfig): any {
    return this.config[key];
  }

  set(key: keyof SpeachesConfig, value: any): void {
    this.config[key] = value;
  }

  getConfig(): SpeachesConfig {
    return { ...this.config };
  }
}

export const config = new ConfigManager();
```

## 五、部署注意事项

### 1. 环境变量配置

```bash
# .env.production
REACT_APP_SPEACHES_URL=https://your-speaches-server.com
REACT_APP_SPEACHES_WS_URL=wss://your-speaches-server.com
```

### 2. CORS 配置

如果前端和 Speaches 服务不在同一域名下，需要配置 CORS：

```typescript
// 在 Speaches 服务端配置 CORS
// 或使用代理配置

// vite.config.ts (Vite 项目)
export default {
  server: {
    proxy: {
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
};

// webpack.config.js (Webpack 项目)
module.exports = {
  devServer: {
    proxy: {
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
};
```

### 3. HTTPS 注意事项

在生产环境中使用 HTTPS 时：
- 麦克风权限需要 HTTPS
- WebSocket 需要使用 wss://
- 混合内容策略需要正确配置

```typescript
// 自动适配协议
const protocol = window.location.protocol;
const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
const baseURL = `${protocol}//your-server.com`;
const wsURL = `${wsProtocol}//your-server.com`;
```