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
voice-desktop-assistant/
├── app.py # Flask 应用主文件
├── requirements.txt # Python 依赖
├── .env # 环境变量（需自行配置百度 API 密钥）
├── README.md # 项目说明（本文件）
├── config/ # 配置管理
│ ├── init.py
│ └── config.py
├── modules/ # 核心模块
│ ├── init.py
│ ├── logger.py # 日志系统
│ ├── asr_engine.py # 百度 ASR 引擎
│ ├── tts_engine.py # Edge TTS 引擎
│ ├── nlu_engine.py # 自然语言理解（规则+正则）
│ └── file_operator.py # 文件操作处理器
├── templates/ # HTML 模板
│ └── index.html
├── static/ # 静态资源
│ ├── css/
│ │ └── style.css
│ └── js/
│ └── main.js
├── logs/ # 日志目录（运行时创建）
└── uploads/ # 音频上传临时目录（运行时创建）

text

## 🚀 快速开始

### 系统要求
- Python 3.8 或更高版本
- macOS / Windows / Linux
- 麦克风设备（用于语音输入）
- 网络连接（用于百度 ASR 和 Edge TTS）

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/7ayl/voice-desktop-assistant.git
cd voice-desktop-assistant
2. 创建虚拟环境（推荐）
bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# 或 venv\Scripts\activate  # Windows
3. 安装依赖
bash
pip install -r requirements.txt
4. 配置百度 API 密钥
在项目根目录创建 .env 文件（可复制 .env.example），内容如下：

ini
ASR_SERVICE=baidu
ASR_API_KEY=你的百度API Key
BAIDU_SECRET_KEY=你的百度Secret Key
TTS_SERVICE=edge-tts
FLASK_ENV=development
百度语音识别 API 密钥可在 百度智能云控制台 申请。

5. 安装 ffmpeg（音频转换必需）
macOS: brew install ffmpeg

Windows: 下载并添加到 PATH

Linux: sudo apt install ffmpeg

6. 运行应用
bash
python app.py
7. 打开浏览器
访问 http://localhost:5005（端口可能因占用变为 5005）

📖 使用说明
语音命令格式
系统支持自然语言，以下为推荐格式（可微调）：

操作	语音命令示例	说明
创建文件夹	帮我在桌面创建文件夹，a。	在桌面创建名为 a 的文件夹
创建页面	帮我在a里面创建一个页面x	在文件夹 a 内创建 x.txt
删除	删除 a 或 删除桌面上的b文件夹	删除文件夹或文件（默认桌面）
重命名	重命名 a 为 b 或 把a重命名为b	将 a 重命名为 b
搜索	查找 x 在 a	在文件夹 a 内搜索包含 x 的项目
复制	复制 a里的x 到桌面	将 a 文件夹内的 x 复制到桌面
移动	移动 a里的x 到桌面	将 a 文件夹内的 x 移动到桌面
使用流程
点击 “开始录音” 按钮并清晰说出命令。

点击 “停止录音”，系统自动识别并执行。

执行结果会通过语音播报，并显示在界面上。

也可直接在文本框手动输入命令，点击 “执行命令”。

注意事项
文件操作默认基于桌面（~/Desktop），子文件夹需先创建。

页面（.txt 文件）自动添加扩展名，无需手动输入。

复制/移动时会自动在桌面及其子目录中查找源文件。

删除操作不可逆，请谨慎使用。

🔧 配置说明
环境变量 (.env)
env
# ASR 配置
ASR_SERVICE=baidu                # 百度云 ASR
ASR_API_KEY=你的API Key
BAIDU_SECRET_KEY=你的Secret Key
ASR_LANGUAGE=zh_CN
ASR_TIMEOUT=30

# TTS 配置
TTS_SERVICE=edge-tts             # Edge TTS（免费，无需密钥）
TTS_LANGUAGE=zh-CN
TTS_VOICE=zh-CN-XiaoxiaoNeural

# Flask 配置
FLASK_ENV=development
FLASK_DEBUG=True

# 日志配置
LOG_LEVEL=INFO

# NLU 配置
NLU_CONFIDENCE_THRESHOLD=0.3     # 降低阈值提高容错
切换 ASR 服务
如需使用本地离线 ASR（PaddleSpeech），修改 .env：

ini
ASR_SERVICE=paddlespeech
然后安装 paddlespeech 库（模型较大，首次运行自动下载）。

🏗️ 技术架构
系统流程图
前端录音 → 音频 Blob → Flask 后端

后端使用 pydub + ffmpeg 转换为 16kHz 单声道 WAV

调用百度 ASR API 获取文本

NLU 引擎解析文本得到操作类型、参数

文件操作模块执行（自动查找源文件、处理路径）

结果返回前端，同时 Edge TTS 合成语音反馈

关键模块说明
asr_engine.py: 封装百度 ASR JSON 方式请求（base64 编码），自动刷新 token。

nlu_engine.py: 基于正则和关键词匹配，支持“X里的Y”等自然语言模式。

file_operator.py: 支持 macOS 路径，自动创建父目录，智能查找文件（遍历桌面及子目录）。

main.js: 使用 MediaRecorder 录音，每 1 秒触发 dataavailable，避免无数据。

📊 API 文档
POST /api/recognize
请求：multipart/form-data，字段 audio（音频文件）

响应：{"success": true, "text": "识别文本", "confidence": 0.9}

POST /api/parse
请求：{"command": "用户命令"}

响应：{"operation": "create", "source_name": "a", "source_path": "桌面", ...}

POST /api/execute
请求：{"command": "用户命令"}

响应：执行结果，包含 success, message, affected_items 等

POST /api/synthesize
请求：{"text": "要朗读的文本"}

响应：音频文件（MP3）

🐛 故障排除
录音无反应
检查浏览器麦克风权限

查看控制台是否有错误（F12）

确认 main.js 中 MediaRecorder.start(1000) 已调用

语音识别返回 token 错误
检查 .env 中的 ASR_API_KEY 和 BAIDU_SECRET_KEY 是否正确

确保网络可访问 aip.baidubce.com

手动测试 token 获取：curl 示例见百度文档

文件操作提示“目标已存在”
说明文件/文件夹已存在，请先删除或使用其他名称

TTS 错误“'Communicate' object has no attribute 'stream_by_chunk'”
Edge TTS 库版本问题，已改用 stream() 方法，请更新 edge-tts 至最新版：pip install -U edge-tts

📝 日志
日志文件位于 logs/app.log，包含详细错误信息，便于调试。

👨‍💼 项目信息
课程: 智能机语音技术与应用 (本科)

学年: 2025-2026

项目类型: 课程设计

选题: 项目2 - 电脑助手

开发者: 黄梓效（独立完成）

最后更新: 2026年6月15日

📚 相关资源
百度智能云语音识别

Edge TTS GitHub

Flask 文档

pydub 文档

