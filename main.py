#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windy AI Assistant - PC AI助手
主程序入口
"""

import sys
import json
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt

from src.ui.chat_window import ChatWindow
from src.ui.floating_widget import FloatingWidget
from src.ai_client import AIClient
from src.config_manager import ConfigManager


class WindyApp(QApplication):
    """Windy AI 主应用类"""

    def __init__(self):
        super().__init__(sys.argv)

        # 加载配置
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # 初始化AI客户端
        self.ai_client = AIClient(self.config['ai'])

        # 创建窗口
        self.chat_window = None
        self.floating_widget = None

        # 应用样式
        self.apply_theme()

        # 创建启动窗口
        self.create_splash()

        # 创建主窗口
        self.create_windows()

    def apply_theme(self):
        """应用主题样式"""
        style = """
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            font-size: 14px;
        }
        QMainWindow {
            background-color: #1a1a2e;
        }
        """
        self.setStyleSheet(style)

    def create_splash(self):
        """创建启动画面"""
        splash = QSplashScreen()
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor('#1a1a2e'))
        splash.setPixmap(pixmap)
        splash.show()
        self.processEvents()
        splash.showMessage('正在启动 Windy AI Assistant...',
                          Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                          Qt.GlobalColor.white)
        self.processEvents()
        splash.close()

    def create_windows(self):
        """创建窗口"""
        # 创建聊天窗口（初始隐藏）
        self.chat_window = ChatWindow(self.ai_client, self.config_manager, self.config)
        self.chat_window.hide()

        # 创建悬浮助手
        self.floating_widget = FloatingWidget(self.chat_window)
        self.floating_widget.show()

    def run(self):
        """运行应用"""
        self.chat_window.show()
        return self.exec()


def main():
    """主函数"""
    app = WindyApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
