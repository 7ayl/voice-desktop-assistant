# 智能电脑助手 - Voice Desktop Assistant

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Flask 2.3](https://img.shields.io/badge/Flask-2.3-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

一个基于**语音识别、自然语言理解和文件系统操作**的智能桌面助手。用户可以通过语音命令完成文件管理操作，无需手动输入。

## 🌟 主要特性

### 核心功能
- ✅ **语音识别（ASR）** - 使用百度智能云 API 将语音转换为文本
- ✅ **自然语言理解（NLU）** - 本地规则引擎解析命令意图与参数
- ✅ **文件操作** - 支持创建、删除、复制、移动、搜索、重命名
- ✅ **语音合成（TTS）** - 使用 Edge TTS（微软免费服务）提供语音反馈
- ✅ **Web界面** - 现代化响应式界面，支持录音与手动输入
- ✅ **操作历史** - 记录所有执行的操作，支持清除

### 支持的操作
1. **新建** - 创建文件夹或页面（.txt 文件）
2. **删除** - 删除文件夹或文件
3. **复制** - 复制文件到指定位置（自动查找源文件）
4. **移动** - 移动文件到指定位置（自动查找源文件）
5. **查询** - 在指定目录搜索包含关键词的文件/文件夹
6. **重命名** - 重命名文件夹或文件（自动处理 .txt 扩展名）

### 技术栈
- **后端框架**: Flask 2.3.2
- **语言**: Python 3.8+
- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **ASR**: 百度智能云语音识别（支持 PCM/WAV，16kHz）
- **TTS**: Edge TTS (Microsoft 免费服务)
- **文件操作**: 本地 Python `os`, `shutil`, `pathlib`
- **音频转换**: pydub + ffmpeg（前端录音自动转换为 16kHz 单声道 WAV）

## 📋 项目结构
