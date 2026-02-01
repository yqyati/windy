# Windy AI Assistant

一个功能强大的PC桌面AI助手，使用Python + PyQt6实现，支持多模态聊天和快速屏幕截图。

## 功能特性

- 🤖 **智能对话**: 类似LM Studio/Ollama的聊天界面，与大模型进行流畅对话
- 📸 **一键截图**: 快速捕获屏幕截图并发送给AI进行分析（支持多模态模型如qwen3-vl）
- 🖼️ **图片上传**: 支持上传本地图片进行交互
- 🎯 **悬浮助手**: 桌面悬浮图标，双击即可打开/关闭聊天界面
- ⚙️ **灵活配置**: 支持自定义API地址、模型、温度等参数
- 🎨 **现代UI**: 使用PyQt6实现的精美深色主题界面

## 技术栈

- **GUI框架**: PyQt6
- **AI客户端**: OpenAI Python SDK (兼容格式)
- **截图**: mss (跨平台)
- **语言**: Python 3.8+

## 安装

### 环境要求

- Python 3.8 或更高版本

### 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖说明

- `PyQt6`: GUI框架
- `openai`: OpenAI SDK兼容的AI客户端
- `Pillow`: 图像处理
- `mss`: 屏幕截图
- `pyautogui`: 辅助功能

## 配置

编辑 `config.json` 文件，设置你的API配置：

```json
{
  "ai": {
    "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "apiKey": "YOUR_API_KEY_HERE",
    "model": "qwen-vl-max",
    "temperature": 0.7
  },
  "ui": {
    "width": 900,
    "height": 700,
    "minWidth": 600,
    "minHeight": 400
  }
}
```

或者在应用中点击设置按钮进行配置。

## 运行

### 运行应用

```bash
python main.py
```

### 打包为可执行文件（可选）

使用PyInstaller打包：

```bash
pip install pyinstaller
pyinstaller --name "Windy AI" --windowed --onefile main.py
```

打包后的文件位于 `dist/Windy AI.exe`

## 使用说明

1. **启动应用**: 运行 `python main.py`，会在桌面右下角显示一个悬浮助手图标
2. **打开聊天**: 双击悬浮助手图标即可打开/关闭聊天界面
3. **发送消息**: 在输入框输入文字，点击发送或按Enter键
4. **截图功能**: 点击输入框中的📷按钮进行截图
5. **上传图片**: 点击📁按钮选择本地图片
6. **多模态对话**: 截图或上传图片后，AI可以分析图片内容

## 项目结构

```
windy/
├── main.py                  # 应用入口
├── requirements.txt         # Python依赖
├── config.json             # AI配置文件
├── README.md               # 使用说明
└── src/
    ├── __init__.py
    ├── config_manager.py   # 配置管理器
    ├── ai_client.py        # AI客户端（OpenAI SDK格式）
    ├── screenshot.py       # 屏幕截图
    └── ui/
        ├── __init__.py
        ├── chat_window.py  # 聊天窗口
        └── floating_widget.py # 悬浮助手
```

## API格式

### 消息格式

#### 文本消息
```python
{
    "role": "user",
    "content": "你好，请介绍一下自己"
}
```

#### 多模态消息
```python
{
    "role": "user",
    "content": [
        {"type": "text", "text": "请分析这张图片"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
    ]
}
```

### 响应格式

```python
{
    "id": "chatcmpl-xxx",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "AI的回复内容"
            },
            "finish_reason": "stop"
        }
    ],
    "model": "qwen-vl-max",
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "total_tokens": 300
    }
}
```

## 支持的模型

支持所有OpenAI SDK兼容的API，包括：

- 通义千问 qwen-vl-max
- OpenAI GPT-4 Vision
- Claude (通过代理)
- 其他多模态大模型

## AI客户端使用示例

```python
from src.ai_client import AIClient

# 初始化客户端
config = {
    'baseUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'apiKey': 'YOUR_API_KEY',
    'model': 'qwen-vl-max',
    'temperature': 0.7
}
client = AIClient(config)

# 发送文本消息
messages = [{'role': 'user', 'content': '你好'}]
response = client.chat(messages)

# 发送多模态消息
messages = [{
    'role': 'user',
    'content': [
        {'type': 'text', 'text': '分析这张图片'},
        {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,...'}}
    ]
}]
response = client.chat(messages)
```

## 截图功能使用示例

```python
from src.screenshot import ScreenshotCapture

capture = ScreenshotCapture()

# 捕获屏幕为图片
img = capture.capture_screen()

# 捕获屏幕并转换为base64
base64_img = capture.capture_to_base64()

# 保存截图到文件
capture.capture_to_file('screenshot.jpg')

# 获取所有显示器信息
monitors = capture.get_monitors_info()
```

## 注意事项

- 首次运行需要配置API Key
- 确保网络可以访问API服务
- 截图功能在Windows上需要应用有屏幕录制权限（自动请求）
- 双击悬浮助手图标切换聊天窗口显示/隐藏

## License

MIT
