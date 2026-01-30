# AstrBot SenseVoice 语音转文字插件

<p align="center">
  <img src="https://img.shields.io/badge/AstrBot-≥3.4.0-blue?style=flat-square" alt="AstrBot版本">
  <img src="https://img.shields.io/badge/Python-3.10+-green?style=flat-square" alt="Python版本">
  <img src="https://img.shields.io/badge/Docker-支持-orange?style=flat-square" alt="Docker支持">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="许可证">
</p>

基于 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 的语音识别插件，支持自动识别语音消息并送大模型处理，完美支持人格和上下文。

## 功能特点

- **🎙️ 自动识别**：收到语音消息自动转文字并送大模型，无需手动触发
- **🎭 人格支持**：完美继承 AstrBot 人格设置，语音对话与文字对话体验一致
- **💬 上下文连贯**：自动携带历史对话记录，支持多轮语音对话
- **🔄 格式兼容**：支持 AMR、WAV、MP3、OGG 等格式，自动转换
- **🌐 多平台支持**：支持 QQ (aiocqhttp/gocqhttp)、Telegram 等平台
- **⚡ 高性能**：支持 GPU/CPU 推理，可选集群部署应对高并发

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [SenseVoice 服务部署](#sensevoice-服务部署)
  - [Docker 部署（推荐）](#docker-部署推荐)
  - [本地部署](#本地部署)
  - [集群部署](#集群部署)
- [插件安装与配置](#插件安装与配置)
- [平台配置指南](#平台配置指南)
- [故障排查](#故障排查)
- [API 文档](#api-文档)
- [更新日志](#更新日志)

## 环境要求

### 基础环境

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| **操作系统** | Linux/macOS/Windows | Ubuntu 20.04+ |
| **CPU** | 4核 | 8核及以上 |
| **内存** | 8GB | 16GB及以上 |
| **Python** | 3.8+ | 3.10 |
| **CUDA** | 11.6+ | 12.1（GPU版本）|
| **Docker** | 20.10+ | 24.0+（容器部署）|
| **AstrBot** | 3.4.0+ | 最新版 |

### 依赖安装

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg -y
