#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
桌面悬浮助手
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QPointF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen


class FloatingWidget(QWidget):
    """
    桌面悬浮助手
    可拖动，点击切换聊天窗口显示/隐藏
    """

    def __init__(self, chat_window):
        super().__init__()
        self.chat_window = chat_window
        self.drag_position = None
        self.click_start_pos = None
        self.max_click_distance = 5  # 最大点击移动距离，超过则视为拖动

        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        # 设置窗口属性
        self.setFixedSize(80, 80)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        # 设置位置到屏幕右下角
        screen = self.screen().availableGeometry()
        self.move(
            screen.width() - 120,
            screen.height() - 120
        )

        # 创建内容
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 助手图标
        self.icon_label = QLabel('🤖')
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                background: transparent;
            }
        """)
        layout.addWidget(self.icon_label)

        # 设置背景为圆角
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
                border-radius: 40px;
            }
        """)

    def paintEvent(self, event):
        """绘制事件 - 绘制圆角和阴影效果"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制圆角背景
        rect = self.rect()
        gradient = QRadialGradient(QPointF(rect.center()), rect.width() / 2)
        gradient.setColorAt(0, QColor('#667eea'))
        gradient.setColorAt(1, QColor('#764ba2'))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 40, 40)

        # 绘制阴影边框
        pen = QPen(QColor('#8888cc'), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 38, 38)

    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.click_start_pos = event.globalPosition().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_position = None

        # 单击效果 - 切换聊天窗口显示/隐藏
        if event.button() == Qt.MouseButton.LeftButton:
            # 判断是点击还是拖动
            if self.click_start_pos:
                current_pos = event.globalPosition().toPoint()
                distance = ((current_pos.x() - self.click_start_pos.x()) ** 2 +
                           (current_pos.y() - self.click_start_pos.y()) ** 2) ** 0.5

                # 如果移动距离很小，视为点击
                if distance < self.max_click_distance:
                    self.toggle_chat_window()

            self.click_start_pos = None

    def toggle_chat_window(self):
        """切换聊天窗口显示/隐藏"""
        if self.chat_window:
            if self.chat_window.isVisible():
                self.chat_window.hide()
            else:
                self.chat_window.show()
                self.chat_window.raise_()
                self.chat_window.activateWindow()

    def mouseDoubleClickEvent(self, event):
        """双击事件 - 切换聊天窗口"""
        if self.chat_window:
            if self.chat_window.isVisible():
                self.chat_window.hide()
            else:
                self.chat_window.show()
                self.chat_window.raise_()
                self.chat_window.activateWindow()
        event.accept()

    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # 悬浮时放大效果
        self.setFixedSize(85, 85)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        # 恢复大小
        self.setFixedSize(80, 80)
        super().leaveEvent(event)
