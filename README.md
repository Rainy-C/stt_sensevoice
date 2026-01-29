# AstrBot SenseVoice 语音转文字插件

基于 SenseVoice 的语音识别插件，支持自动识别语音消息并送大模型处理，完美支持人格和上下文。

## 功能特点

- **自动识别**：收到语音消息自动转文字并送大模型，无需手动触发
- **人格支持**：完美继承 AstrBot 人格设置，语音对话与文字对话体验一致
- **上下文连贯**：自动携带历史对话记录，支持多轮语音对话
- **格式兼容**：支持 AMR、WAV、MP3 等格式，自动转换
- **多平台支持**：支持 QQ (aiocqhttp)、Telegram 等平台

## 安装要求

- AstrBot >= 3.4.0
- ffmpeg（用于 AMR 格式转换，QQ 语音必需）
- SenseVoice API 服务

### 安装 ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
