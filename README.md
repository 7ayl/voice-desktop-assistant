# 智能电脑助手 - Voice Desktop Assistant

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Flask 2.3](https://img.shields.io/badge/Flask-2.3-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

一个基于**语音识别、自然语言理解和文件系统操作**的智能桌面助手。用户可以通过语音命令完成文件管理操作，无需手动输入。

## 🌟 主要特性

### 核心功能
- ✅ **语音识别（ASR）** - 将用户语音转换为文本命令
- ✅ **自然语言理解（NLU）** - 智能解析用户意图和参数
- ✅ **文件操作** - 支持创建、删除、复制、移动、搜索、重命名
- ✅ **语音合成（TTS）** - 将操作结果转换为语音反馈
- ✅ **Web界面** - 现代化响应式用户界面
- ✅ **操作历史** - 记录所有执行的操作

### 支持的AI服务
- **ASR**: PaddleSpeech (本地免费) / 百度云 / 讯飞
- **TTS**: Edge TTS (微软免费) / ��度云 / 讯飞
- **NLU**: 本地规则引擎 + 正则表达式

### 支持的文件操作
1. **新建** - 创建文件和文件夹
2. **删除** - 删除文件和文件夹
3. **复制** - 复制文件和文件夹
4. **剪切** - 移动文件和文件夹
5. **查询** - 搜索包含关键词的文件
6. **重命名** - 重命名文件和文件夹

## 📋 项目结构

```
voice-desktop-assistant/
├── app.py                      # Flask应用主文件
├── requirements.txt            # 项目依赖
├── .env.example               # 环境变量示例
├── README.md                  # 项目说明（本文件）
├── USAGE.md                   # 使用说明
│
├── config/                     # 配置管理
│   ├── __init__.py
│   └── config.py
│
├── modules/                    # 核心模块
│   ├── __init__.py
│   ├── logger.py              # 日志系统
│   ├── asr_engine.py          # 语音识别引擎
│   ├── tts_engine.py          # 文本转语音引擎
│   ├── nlu_engine.py          # 自然语言理解引擎
│   └── file_operator.py       # 文件操作处理器
│
├── templates/                  # HTML模板
│   └── index.html             # 主页界面
│
├── static/                     # 静态资源
│   ├── css/
│   │   └── style.css          # 样式表
│   └── js/
│       └── main.js            # 前端交互脚本
│
├── tests/                      # 单元测试
│   ├── test_nlu_engine.py
│   └── test_file_operator.py
│
├── logs/                       # 日志目录（运行时创建）
└── uploads/                    # 音频上传目录（运行时创建）
```

## 🚀 快速开始

### 系统要求
- Python 3.8 或更高版本
- Windows / Linux / macOS
- 麦克风设备（用于语音输入）

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/7ayl/voice-desktop-assistant.git
cd voice-desktop-assistant
```

#### 2. 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置您的API密钥
```

#### 5. 运行应用
```bash
python app.py
```

#### 6. 打开浏览器
访问 `http://localhost:5000`

## 📖 使用说明

### 基础流程
1. **点击"开始录音"按钮** 开始录制语音
2. **说出您的命令**，例如：
   - "帮我在D盘创建一个名称为'我的作业'的文件夹"
   - "帮我把D盘里的'我的文档'复制到E盘"
   - "帮我在E盘查找是否有名称包含'测试'的文件"
3. **点击"停止录音"按钮** 完成录制
4. 系统自动识别、解析并执行命令
5. **接收语音反馈** 和操作结果

### 命令示例

#### 创建操作
```
创建: "帮我在D盘创建一个名称为'test'的文件夹"
结果: D:\test 文件夹创建成功
```

#### 删除操作
```
删除: "帮我删除D盘里名称为'oldfile'的文件"
结果: D:\oldfile 文件删除成功
```

#### 复制操作
```
复制: "帮我把D盘的'report.docx'复制到E盘"
结果: D:\report.docx 复制到 E:\report.docx 成功
```

#### 移动操作
```
移动: "帮我把D盘里的'project'移动到E盘"
结果: D:\project 移动到 E:\project 成功
```

#### 搜索操作
```
搜索: "帮我在E盘查找是否有名称包含'2024'的文件"
结果: 找到 5 个包含'2024'的项目
```

#### 重命名操作
```
重命名: "帮我把D盘的'oldname'改成'newname'"
结果: D:\oldname 重命名为 D:\newname 成功
```

### 详细使用指南

请查看 [USAGE.md](USAGE.md) 了解更多命令示例和高级配置。

## 🔧 配置说明

### 环境变量 (.env)

```env
# ASR 配置
ASR_SERVICE=paddlespeech          # 语音识别服务
ASR_API_KEY=your_api_key          # API密钥（如需要）
ASR_LANGUAGE=zh_CN                # 语言（中文）

# TTS 配置
TTS_SERVICE=edge-tts              # 文本转语音服务
TTS_API_KEY=your_api_key          # API密钥（如需要）
TTS_LANGUAGE=zh-CN                # 语言
TTS_VOICE=zh-CN-XiaoxiaoNeural   # 声音

# Flask 配置
FLASK_ENV=development             # 开发环境
FLASK_DEBUG=True                  # 调试模式

# 日志配置
LOG_LEVEL=INFO                    # 日志级别

# 文件操作
DEFAULT_DRIVES=C:,D:,E:,F:       # 可用驱动器
```

### 替换ASR/TTS服务

#### 使用百度云服务
```env
# 编辑 .env
ASR_SERVICE=baidu
ASR_API_KEY=<your_baidu_api_key>
BAIDU_SECRET_KEY=<your_baidu_secret_key>
```

## 🏗️ 技术架构

### 系统架构图
```
┌─────────────────────────────────────────────────────────┐
│                   Web Frontend (HTML/CSS/JS)            │
├─────────────────────────────────────────────────────────┤
│                   Flask Application                     │
│  ┌──────────┬──────────┬──────────┬──────────────────┐ │
│  │ /recognize│ /parse   │/execute  │ /synthesize      │ │
│  └─────┬────┴────┬─────┴────┬─────┴────────┬────────┘ │
└────────┼─────────┼──────────┼──────────────┼──────────┘
         │         │          │              │
    ┌────▼─┐  ┌───▼──┐  ┌───▼───┐      ┌──▼───┐
    │ ASR  │  │ NLU  │  │ File  │      │ TTS  │
    │Engine│  │Engine│  │Operator      │Engine│
    └──────┘  └──────┘  └───────┘      └──────┘
```

### 技术栈
- **后端框架**: Flask 2.3.2
- **语言**: Python 3.8+
- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **ASR**: PaddleSpeech / Baidu / iFlytek
- **TTS**: Edge-TTS / Baidu / iFlytek
- **数据库**: 内存操作历史（可扩展）

## 📊 API 文档

### 语音识别 - POST /api/recognize
```
请求:
  - audio: 二进制音频文件 (WAV)
  - language: 语言代码 (可选，默认zh_CN)

响应:
  {
    "success": true,
    "text": "识别的文本",
    "confidence": 0.95,
    "timestamp": "2024-06-11T12:00:00"
  }
```

### 命令解析 - POST /api/parse
```
请求:
  {
    "command": "用户命令文本"
  }

响应:
  {
    "success": true,
    "operation": "create|delete|copy|move|search|rename",
    "file_type": "file|folder|unknown",
    "source_name": "文件名",
    "source_path": "D:",
    "target_path": "E:",
    "confidence": 0.85,
    "is_valid": true
  }
```

### 命令执行 - POST /api/execute
```
请求:
  {
    "command": "用户命令文本"
  }

响应:
  {
    "success": true,
    "message": "操作成功",
    "operation": "create",
    "affected_items": ["D:\\test"],
    "details": {...}
  }
```

### 文本转语音 - POST /api/synthesize
```
请求:
  {
    "text": "要合成的文本",
    "language": "zh-CN" (可选),
    "voice": "zh-CN-XiaoxiaoNeural" (可选)
  }

响应:
  音频二进制数据 (MP3)
```

## 🧪 测试

### 运行单元测试
```bash
python -m pytest tests/ -v
```

### 测试覆盖范围
- ✅ NLU 命令解析
- ✅ 文件操作执行
- ✅ 路径验证
- ✅ 错误处理

## 🐛 故障排除

### 问题1：无法访问麦克风
**解决方案**:
- 检查浏览器是否有麦克风权限
- 在浏览器设置中允许此应用访问麦克风
- 确保操作系统已授予权限

### 问题2：语音识别不准确
**解决方案**:
- 确保网络连接正常（使用云服务时）
- 清晰说话，避免背景噪音
- 尝试更换ASR服务

### 问题3：文件操作失败
**解决方案**:
- 检查目标路径是否存在
- 确保有文件访问权限
- 查看日志文件 `logs/app.log` 了解详细错误

## 📝 日志

日志文件位置: `logs/app.log`

查看日志:
```bash
# 实时查看日志
tail -f logs/app.log

# 显示最后100行
tail -100 logs/app.log
```

## 🤝 贡献

欢迎提交 Pull Request 或提出 Issue！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 👨‍💼 项目信息

**课程**: 智能机语音技术与应用 (本科)
**学年**: 2025-2026
**项目类型**: 课程设计
**选题**: 项目2 - 电脑助手
**难度**: ★★★☆☆ (中等)

## 📚 相关资源

- [PaddleSpeech 文档](https://github.com/PaddlePaddle/PaddleSpeech)
- [Flask 文档](https://flask.palletsprojects.com/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Edge TTS](https://github.com/rany2/edge-tts)

## 🎯 更新计划

- [ ] 支持多轮对话
- [ ] 添加更多文件操作类型
- [ ] 集成高级NLU模型 (BERT)
- [ ] 支持离线运行
- [ ] 移动应用版本

---

**最后更新**: 2024年6月11日

如有问题，请提交 Issue 或联系开发者。
