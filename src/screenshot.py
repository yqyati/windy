#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
屏幕截图功能
"""

import base64
import io
from typing import Optional
from PIL import Image
import mss


class ScreenshotCapture:
    """
    屏幕截图功能类
    使用mss库进行跨平台屏幕截图
    """

    def __init__(self):
        self.sct = mss.mss()

    def capture_screen(self, monitor: int = 1) -> Optional[Image.Image]:
        """
        捕获整个屏幕截图

        Args:
            monitor: 显示器编号（多显示器时使用）

        Returns:
            PIL Image对象
        """
        try:
            # 获取显示器信息
            monitors = self.sct.monitors
            if monitor >= len(monitors):
                monitor = 1

            monitor_info = monitors[monitor]

            # 截图
            screenshot = self.sct.grab(monitor_info)

            # 转换为PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            return img
        except Exception as e:
            print(f'截图失败: {str(e)}')
            return None

    def capture_all_monitors(self) -> list[Image.Image]:
        """
        捕获所有显示器截图

        Returns:
            PIL Image对象列表
        """
        images = []
        monitors = self.sct.monitors

        for i, monitor in enumerate(monitors[1:], start=1):
            img = self.capture_screen(i)
            if img:
                images.append(img)

        return images

    def capture_to_base64(self, monitor: int = 1, format: str = 'JPEG') -> Optional[str]:
        """
        捕获屏幕并转换为base64 data URL

        Args:
            monitor: 显示器编号
            format: 图片格式 (JPEG, PNG, WEBP)

        Returns:
            base64 data URL字符串
        """
        try:
            img = self.capture_screen(monitor)
            if not img:
                return None

            # 转换为base64
            buffered = io.BytesIO()
            img.save(buffered, format=format)
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

            mime_type = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'WEBP': 'image/webp'
            }.get(format, 'image/jpeg')

            return f'data:{mime_type};base64,{img_str}'
        except Exception as e:
            print(f'转换base64失败: {str(e)}')
            return None

    def capture_to_file(self, filepath: str, monitor: int = 1, format: str = 'JPEG') -> bool:
        """
        捕获屏幕并保存到文件

        Args:
            filepath: 保存路径
            monitor: 显示器编号
            format: 图片格式

        Returns:
            是否成功
        """
        try:
            img = self.capture_screen(monitor)
            if not img:
                return False

            img.save(filepath, format=format)
            return True
        except Exception as e:
            print(f'保存截图失败: {str(e)}')
            return False

    def get_monitors_info(self) -> list[dict]:
        """
        获取所有显示器信息

        Returns:
            显示器信息列表
        """
        monitors = []
        for i, monitor in enumerate(self.sct.monitors[1:], start=1):
            monitors.append({
                'index': i,
                'left': monitor['left'],
                'top': monitor['top'],
                'width': monitor['width'],
                'height': monitor['height']
            })
        return monitors


# 示例使用
if __name__ == '__main__':
    capture = ScreenshotCapture()

    # 获取显示器信息
    print('显示器信息:')
    for m in capture.get_monitors_info():
        print(f"  显示器 {m['index']}: {m['width']}x{m['height']}")

    # 截图并保存
    # capture.capture_to_file('screenshot.jpg')
    # print('截图已保存')

    # 截图并转换为base64
    base64_img = capture.capture_to_base64()
    if base64_img:
        print(f'截图base64长度: {len(base64_img)}')
