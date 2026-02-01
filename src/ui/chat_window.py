#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
聊天窗口
"""

import sys
import json
from typing import List, Dict, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QScrollArea, QFrame, QFileDialog,
    QDialog, QLineEdit, QDoubleSpinBox, QMessageBox, QSpacerItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QResizeEvent

from src.screenshot import ScreenshotCapture
from agent import Agent, MessageRole, PRESET_SYSTEM_PROMPTS


class ChatLogger:
    """聊天日志记录器"""

    def __init__(self, log_dir: str = 'logs'):
        """
        初始化日志记录器

        Args:
            log_dir: 日志目录
        """
        import os
        self.log_dir = log_dir
        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def save_messages(self, messages: List[Dict[str, Any]]) -> str:
        """
        保存消息到日志文件

        Args:
            messages: 消息列表

        Returns:
            保存的文件路径
        """
        # 生成文件名：聊天日志_YYYYMMDD_HHMMSS.json
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'聊天日志_{timestamp}.json'
        filepath = f'{self.log_dir}/{filename}'

        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'message_count': len(messages),
                'messages': messages
            }, f, ensure_ascii=False, indent=2)

        return filepath

    def log_to_console(self, messages: List[Dict[str, Any]]) -> None:
        """
        打印消息到控制台

        Args:
            messages: 消息列表
        """
        print("\n" + "="*60)
        print("当前对话上下文:")
        print("="*60)

        for i, msg in enumerate(messages, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            print(f"\n[{i}] {role.upper()}:")

            if isinstance(content, list):
                # 多模态消息
                for item in content:
                    if item.get('type') == 'text':
                        print(f"  {item.get('text', '')}")
                    elif item.get('type') == 'image_url':
                        print(f"  [图片: {item['image_url']['url'][:50]}...]")
            else:
                print(f"  {content}")

        print("\n" + "="*60)
        print(f"共 {len(messages)} 条消息")
        print("="*60 + "\n")


class ChatThread(QThread):
    """聊天请求线程"""
    stream_received = pyqtSignal(str)  # 流式内容信号
    stream_finished = pyqtSignal(str)  # 流式完成信号
    error_occurred = pyqtSignal(str)

    def __init__(self, ai_client, messages):
        super().__init__()
        self.ai_client = ai_client
        self.messages = messages
        self.full_content = ''

    def run(self):
        try:
            for chunk in self.ai_client.chat_stream(self.messages):
                if chunk.get('choices') and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        self.full_content += content
                        self.stream_received.emit(content)
            self.stream_finished.emit(self.full_content)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MessageBubble(QFrame):
    """消息气泡"""

    def __init__(self, role: str, content: Any, parent=None, streamable: bool = False):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.streamable = streamable
        self.text_label = None
        self.content_widget = None
        self.setup_ui()

    def update_content(self, text: str):
        """更新文本内容（用于流式输出）"""
        if self.text_label and self.streamable:
            self.text_label.setText(text)
            self.content = text

    def append_content(self, text: str):
        """追加文本内容（用于流式输出）"""
        if self.text_label and self.streamable:
            current = self.text_label.text()
            self.text_label.setText(current + text)
            self.content = current + text

    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        # 头像
        avatar = QLabel()
        avatar.setFixedSize(36, 36)

        if self.role == 'user':
            avatar.setText('👤')
        elif self.role == 'assistant':
            avatar.setText('🤖')
        else:
            avatar.setText('⚠️')

        avatar.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                background-color: {'#f093fb' if self.role == 'user' else '#667eea'};
                border-radius: 18px;
                qproperty-alignment: AlignCenter;
            }}
        """)

        # 内容
        content_widget = QWidget()
        self.content_widget = content_widget
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 处理多模态内容
        if isinstance(self.content, list):
            for item in self.content:
                if item.get('type') == 'image_url':
                    image_label = QLabel()
                    pixmap = self._base64_to_pixmap(item['image_url']['url'])
                    if pixmap:
                        scaled_pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
                        image_label.setPixmap(scaled_pixmap)
                    content_layout.addWidget(image_label)
                elif item.get('type') == 'text':
                    text_label = self._create_text_label(item['text'])
                    content_layout.addWidget(text_label)
        else:
            text_label = self._create_text_label(self.content if self.content else '')
            content_layout.addWidget(text_label)

        # 样式
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
            }}
        """)

        # 根据角色设置布局方向
        if self.role == 'user':
            layout.addStretch()
            layout.addWidget(content_widget)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addWidget(content_widget)
            layout.addStretch()

        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {'#f5576c' if self.role == 'user' else '#16213e'};
                border-radius: 16px;
                padding: 12px 16px;
                max-width: 300%;
            }}
        """)

    def _create_text_label(self, text: str) -> QLabel:
        """创建文本标签"""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setStyleSheet("""
            QLabel {
                color: #eaeaea;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        # 保存文本标签引用（用于流式更新）
        if not self.text_label:
            self.text_label = label
        return label

    def _base64_to_pixmap(self, data_url: str) -> QPixmap:
        """将base64 data URL转换为QPixmap"""
        try:
            if data_url.startswith('data:'):
                # 移除data URL前缀
                parts = data_url.split(',')
                if len(parts) == 2:
                    import base64
                    image_data = base64.b64decode(parts[1])
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    return pixmap
        except Exception as e:
            print(f'图片加载失败: {e}')
        return None


class ChatWindow(QMainWindow):
    """聊天窗口"""

    def __init__(self, ai_client, config_manager, config, floating_widget=None):
        super().__init__()
        self.ai_client = ai_client
        self.config_manager = config_manager
        self.config = config
        self.floating_widget = floating_widget
        self.current_image = None
        self.is_loading = False
        self.assistant_bubble = None

        # 创建日志记录器
        self.logger = ChatLogger()

        # 创建Agent，支持多轮对话
        # systemPrompt可选，不设置则不加system消息以提高响应速度
        system_prompt = config.get('systemPrompt', None)
        self.agent = Agent(
            system_prompt=system_prompt,
            ai_client=ai_client,
            max_history=50,
            on_stream=self._on_stream_chunk
        )

        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle('Windy AI Assistant')
        self.setGeometry(
            100, 100,
            self.config['ui'].get('width', 900),
            self.config['ui'].get('height', 700)
        )
        self.setMinimumSize(
            self.config['ui'].get('minWidth', 600),
            self.config['ui'].get('minHeight', 400)
        )

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                background-color: #e94560;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:pressed {
                background-color: #d63545;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
            QTextEdit {
                background-color: #0f3460;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 12px;
                color: #eaeaea;
                font-size: 15px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: #e94560;
            }
        """)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建顶部工具栏
        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)

        # 创建聊天区域
        self.chat_area = self._create_chat_area()
        main_layout.addWidget(self.chat_area)

        # 创建输入区域
        self.input_area = self._create_input_area()
        main_layout.addWidget(self.input_area)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        toolbar.setStyleSheet('background-color: #16213e; border-bottom: 1px solid #2a2a4a;')
        toolbar.setMaximumHeight(60)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 10, 20, 10)

        # Logo
        logo = QLabel('🤖 Windy AI')
        logo.setStyleSheet('font-size: 18px; font-weight: 600; color: #eaeaea;')

        # 设置按钮
        settings_btn = QPushButton('⚙️')
        settings_btn.setFixedSize(36, 36)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #2a2a4a;
            }
        """)
        settings_btn.clicked.connect(self.show_settings)

        # 最小化按钮
        minimize_btn = QPushButton('🤖')
        minimize_btn.setFixedSize(36, 36)
        minimize_btn.setToolTip('缩小为悬浮助手')
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #2a2a4a;
            }
        """)
        minimize_btn.clicked.connect(self.minimize_to_floating)

        layout.addWidget(logo)
        layout.addStretch()
        layout.addWidget(minimize_btn)
        layout.addWidget(settings_btn)

        return toolbar

    def _create_chat_area(self) -> QScrollArea:
        """创建聊天区域"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1a1a2e;
            }
            QScrollBar:vertical {
                width: 6px;
                background-color: #1a1a2e;
            }
            QScrollBar::handle:vertical {
                background-color: #2a2a4a;
                border-radius: 3px;
            }
        """)

        # 欢迎消息
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet('background-color: #1a1a2e;')
        container_layout = QVBoxLayout(self.chat_container)

        # 欢迎消息
        welcome = QLabel()
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setText("""
            <div style="text-align: center;">
                <div style="font-size: 64px;">👋</div>
                <h2 style="color: #eaeaea; font-size: 24px;">欢迎使用 Windy AI Assistant</h2>
                <p style="color: #a0a0a0;">点击下方输入框开始对话，或使用截图功能进行多模态交互</p>
            </div>
        """)
        welcome.setTextFormat(Qt.TextFormat.RichText)
        container_layout.addWidget(welcome)

        container_layout.addStretch()

        scroll_area.setWidget(self.chat_container)
        return scroll_area

    def _create_input_area(self) -> QWidget:
        """创建输入区域"""
        input_widget = QWidget()
        input_widget.setStyleSheet('background-color: #16213e; border-top: 1px solid #2a2a4a; padding: 16px;')
        input_widget.setMaximumHeight(200)

        layout = QVBoxLayout(input_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 图片预览区域
        self.image_preview_container = QWidget()
        self.image_preview_container.setVisible(False)
        preview_layout = QVBoxLayout(self.image_preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 8)

        # 输入框和按钮
        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(20, 12, 20, 12)
        input_layout.setSpacing(10)

        # 输入框
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText('输入消息...')
        self.message_input.setMaximumHeight(150)
        self.message_input.textChanged.connect(self._auto_resize)

        # 截图按钮
        screenshot_btn = QPushButton('📷')
        screenshot_btn.setFixedSize(50, 50)
        screenshot_btn.setToolTip('截取屏幕')
        screenshot_btn.clicked.connect(self.capture_screenshot)

        # 上传按钮
        upload_btn = QPushButton('📁')
        upload_btn.setFixedSize(50, 50)
        upload_btn.setToolTip('上传图片')
        upload_btn.clicked.connect(self.upload_image)

        # 发送按钮
        self.send_btn = QPushButton('发送')
        self.send_btn.setFixedSize(100, 50)
        self.send_btn.clicked.connect(self.send_message)

        # 快捷键按钮
        self.message_input.installEventFilter(self)

        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: #1a1a2e;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e94560;
            }
        """
        screenshot_btn.setStyleSheet(button_style)
        upload_btn.setStyleSheet(button_style)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(screenshot_btn)
        input_layout.addWidget(upload_btn)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(self.image_preview_container)
        layout.addWidget(input_row)

        return input_widget

    def setup_shortcuts(self):
        """设置快捷键"""
        # 这里可以添加全局快捷键
        pass

    def closeEvent(self, event):
        """窗口关闭事件 - 保存日志"""
        try:
            messages = self.agent.get_messages()

            if messages:
                # 打印到控制台
                self.logger.log_to_console(messages)

                # 保存到文件
                filepath = self.logger.save_messages(messages)
                print(f"日志已保存到: {filepath}")
            else:
                print("没有对话历史需要保存")

        except Exception as e:
            print(f"保存日志失败: {e}")

        super().closeEvent(event)

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理回车发送"""
        if obj == self.message_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def _auto_resize(self):
        """自动调整输入框高度"""
        height = self.message_input.document().size().height()
        self.message_input.setFixedHeight(int(min(height + 30, 150)))

    def send_message(self):
        """发送消息"""
        text = self.message_input.toPlainText().strip()

        if self.is_loading or (not text and not self.current_image):
            return

        # 移除欢迎消息
        self._remove_welcome_message()

        # 构建用户消息内容
        if self.current_image:
            user_content = [
                {'type': 'text', 'text': text or '请分析这张图片'},
                {'type': 'image_url', 'image_url': {'url': self.current_image}}
            ]
        else:
            user_content = text

        # 先在Agent中添加用户消息
        self.agent.add_message(MessageRole.USER, user_content)

        # 显示用户消息（在发送前显示）
        self._append_message('user', user_content)

        # 清空输入
        self.message_input.clear()
        self.message_input.setFixedHeight(80)
        self._remove_image_preview()

        # 创建assistant消息气泡（空内容，用于流式更新）
        self.assistant_bubble = self._append_message('assistant', '', streamable=True)

        # 发送请求（使用Agent）
        self.is_loading = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText('发送中...')

        # 创建线程 - 使用Agent的messages（现在已经包含用户消息）
        self.chat_thread = ChatThread(self.ai_client, self.agent.get_messages())
        self.chat_thread.stream_received.connect(self._on_stream_chunk)
        self.chat_thread.stream_finished.connect(self._on_stream_finished)
        self.chat_thread.error_occurred.connect(self._on_error)
        self.chat_thread.start()

    def _on_response(self, response):
        """处理响应（已弃用，保留用于兼容性）"""
        self.is_loading = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText('发送')

        assistant_content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        # 使用Agent添加assistant消息
        self.agent.add_message(MessageRole.ASSISTANT, assistant_content)
        self._append_message('assistant', assistant_content)

    def _on_stream_chunk(self, chunk: str):
        """处理流式响应片段"""
        if self.assistant_bubble:
            self.assistant_bubble.append_content(chunk)
            # 自动滚动到底部
            QTimer.singleShot(10, lambda: self.chat_area.verticalScrollBar().setValue(
                self.chat_area.verticalScrollBar().maximum()
            ))

    def _on_stream_finished(self, full_content: str):
        """流式响应完成"""
        self.is_loading = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText('发送')

        # 保存完整消息到Agent历史（仅当内容非空时）
        if full_content and full_content.strip():
            self.agent.add_message(MessageRole.ASSISTANT, full_content)
        self.assistant_bubble = None

    def _on_error(self, error):
        """处理错误"""
        self.is_loading = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText('发送')

        self._append_message('system', f'错误: {error}')

    def _append_message(self, role: str, content, streamable: bool = False):
        """追加消息"""
        message_bubble = MessageBubble(role, content, streamable=streamable)
        container_layout = self.chat_container.layout()

        # 移除最后一个stretch
        while container_layout.count() > 0:
            item = container_layout.takeAt(container_layout.count() - 1)
            if isinstance(item, QSpacerItem):
                # 是spacer，不再放回去
                continue
            else:
                container_layout.addItem(item)
                break

        container_layout.addWidget(message_bubble)
        container_layout.addStretch()

        # 滚动到底部
        QTimer.singleShot(100, lambda: self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        ))

        return message_bubble

    def _remove_welcome_message(self):
        """移除欢迎消息"""
        container_layout = self.chat_container.layout()
        for i in reversed(range(container_layout.count())):
            item = container_layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, QLabel) and '欢迎' in widget.text():
                container_layout.removeWidget(widget)
                widget.deleteLater()
                break

    def capture_screenshot(self):
        """截取屏幕"""
        try:
            # 隐藏窗口以避免截图包含本应用
            self.hide()

            # 延迟一下确保窗口已隐藏
            import time
            time.sleep(0.2)

            capture = ScreenshotCapture()
            base64_img = capture.capture_to_base64()
            if base64_img:
                self.current_image = base64_img
                self._show_image_preview(base64_img)

            # 显示窗口
            self.show()
            self.activateWindow()
            self.raise_()
        except Exception as e:
            self.show()
            QMessageBox.warning(self, '截图失败', str(e))

    def upload_image(self):
        """上传图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择图片', '', '图片文件 (*.png *.jpg *.jpeg *.gif *.webp)'
        )
        if file_path:
            try:
                import base64
                with open(file_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                self.current_image = f'data:image/jpeg;base64,{image_data}'
                self._show_image_preview(self.current_image)
            except Exception as e:
                QMessageBox.warning(self, '上传失败', str(e))

    def _show_image_preview(self, data_url: str):
        """显示图片预览"""
        self.image_preview_container.setVisible(True)

        # 清除旧预览
        preview_layout = self.image_preview_container.layout()
        while preview_layout.count():
            item = preview_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 创建预览
        layout = preview_layout

        pixmap = self._base64_to_pixmap(data_url)
        if pixmap:
            scaled_pixmap = pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            image_label = QLabel()
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            # 移除按钮
            remove_btn = QPushButton('×')
            remove_btn.setFixedSize(24, 24)
            remove_btn.clicked.connect(self._remove_image_preview)

            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(image_label)
            container_layout.addWidget(remove_btn)

            layout.addWidget(container)

    def _remove_image_preview(self):
        """移除图片预览"""
        self.current_image = None
        self.image_preview_container.setVisible(False)
        preview_layout = self.image_preview_container.layout()
        while preview_layout.count():
            item = preview_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _base64_to_pixmap(self, data_url: str) -> QPixmap:
        """将base64 data URL转换为QPixmap"""
        try:
            if data_url.startswith('data:'):
                parts = data_url.split(',')
                if len(parts) == 2:
                    import base64
                    image_data = base64.b64decode(parts[1])
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    return pixmap
        except Exception as e:
            print(f'图片加载失败: {e}')
        return None

    def minimize_to_floating(self):
        """缩小为悬浮助手"""
        if self.floating_widget:
            self.hide()
            self.floating_widget.show()

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config_manager, self)
        dialog.exec()
        if dialog.saved:
            # 重新加载配置
            self.config = self.config_manager.load_config()
            self.ai_client.update_config(self.config['ai'])


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.saved = False
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle('设置')
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: #eaeaea;
            }
            QLabel {
                font-size: 14px;
                color: #a0a0a0;
                margin-bottom: 8px;
            }
            QLineEdit, QDoubleSpinBox {
                background-color: #0f3460;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 10px;
                color: #eaeaea;
                font-size: 14px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border-color: #e94560;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel('设置')
        title.setStyleSheet('font-size: 24px; font-weight: 600; color: #eaeaea; margin-bottom: 20px;')
        layout.addWidget(title)

        # API URL
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText('https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.api_url_input.setText(self.config_manager.get('ai.baseUrl', ''))
        layout.addWidget(QLabel('API URL'))
        layout.addWidget(self.api_url_input)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText('输入你的 API Key')
        self.api_key_input.setText(self.config_manager.get('ai.apiKey', ''))
        layout.addWidget(QLabel('API Key'))
        layout.addWidget(self.api_key_input)

        # 模型
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText('qwen-vl-max')
        self.model_input.setText(self.config_manager.get('ai.model', ''))
        layout.addWidget(QLabel('模型'))
        layout.addWidget(self.model_input)

        # 温度
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0, 2)
        self.temperature_input.setSingleStep(0.1)
        self.temperature_input.setValue(self.config_manager.get('ai.temperature', 0.7))
        layout.addWidget(QLabel('温度 (0-2)'))
        layout.addWidget(self.temperature_input)

        layout.addStretch()

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self.save)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def save(self):
        """保存设置"""
        new_config = {
            'ai': {
                'baseUrl': self.api_url_input.text(),
                'apiKey': self.api_key_input.text(),
                'model': self.model_input.text(),
                'temperature': self.temperature_input.value()
            }
        }

        self.config_manager.save_config({
            **self.config_manager.config,
            **new_config
        })
        self.saved = True
        self.accept()
