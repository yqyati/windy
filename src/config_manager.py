#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理器
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            # 创建默认配置
            default_config = {
                'ai': {
                    'baseUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                    'apiKey': 'YOUR_API_KEY_HERE',
                    'model': 'qwen-vl-max',
                    'temperature': 0.7
                },
                'ui': {
                    'width': 900,
                    'height': 700,
                    'minWidth': 600,
                    'minHeight': 400
                }
            }
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError as e:
            print(f'配置文件格式错误: {e}')
            return {}

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.config = config
            return True
        except Exception as e:
            print(f'保存配置失败: {e}')
            return False

    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config(self.config)
