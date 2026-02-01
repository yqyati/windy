#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI客户端封装
支持OpenAI SDK兼容的API
"""

import base64
import os
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI
import httpx


class AIClient:
    """
    AI客户端封装
    支持OpenAI SDK兼容的API和多模态消息
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 创建不使用代理的 httpx 客户端
        self.client = OpenAI(
            api_key=config.get('apiKey'),
            base_url=config.get('baseUrl'),
        )

    def chat(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: OpenAI SDK格式的消息列表

        Returns:
            响应结果

        消息格式支持:
        - { role: 'user' | 'assistant' | 'system', content: string }
        - { role: 'user', content: [{ type: 'text', text: string }, { type: 'image_url', image_url: { url: string } }] }
        """
        try:
            # 格式化消息
            formatted_messages = self._format_messages(messages)

            completion = self.client.chat.completions.create(
                model=self.config.get('model'),
                messages=formatted_messages,
                temperature=self.config.get('temperature', 0.7)
            )

            return {
                'id': completion.id,
                'choices': [
                    {
                        'index': choice.index,
                        'message': {
                            'role': choice.message.role,
                            'content': choice.message.content
                        },
                        'finish_reason': choice.finish_reason
                    }
                    for choice in completion.choices
                ],
                'model': completion.model,
                'usage': {
                    'prompt_tokens': completion.usage.prompt_tokens,
                    'completion_tokens': completion.usage.completion_tokens,
                    'total_tokens': completion.usage.total_tokens
                }
            }
        except Exception as e:
            raise Exception(f'AI请求失败: {str(e)}')

    def chat_stream(self, messages: List[Dict[str, Any]]):
        """
        流式聊天

        Args:
            messages: OpenAI SDK格式的消息列表

        Yields:
            流式响应块
        """
        try:
            formatted_messages = self._format_messages(messages)

            stream = self.client.chat.completions.create(
                model=self.config.get('model'),
                messages=formatted_messages,
                temperature=self.config.get('temperature', 0.7),
                stream=True
            )

            for chunk in stream:
                yield {
                    'id': chunk.id,
                    'choices': [
                        {
                            'index': choice.index,
                            'delta': {
                                'role': choice.delta.role,
                                'content': choice.delta.content
                            } if choice.delta else {}
                        }
                        for choice in chunk.choices
                    ],
                    'model': chunk.model
                }
        except Exception as e:
            raise Exception(f'AI流式请求失败: {str(e)}')

    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化消息为OpenAI SDK兼容格式

        Args:
            messages: 原始消息列表

        Returns:
            格式化后的消息列表
        """
        formatted = []

        for msg in messages:
            if isinstance(msg.get('content'), list):
                # 多模态消息
                content_list = []
                for item in msg['content']:
                    if item.get('type') == 'image_url':
                        # 处理base64图片
                        url = item['image_url']['url']
                        if url.startswith('data:image'):
                            # 已经是data URL格式，直接使用
                            content_list.append({
                                'type': 'image_url',
                                'image_url': {'url': url}
                            })
                        else:
                            # 假设是文件路径，转换为base64
                            content_list.append({
                                'type': 'image_url',
                                'image_url': {'url': self._image_to_base64(url)}
                            })
                    elif item.get('type') == 'text':
                        content_list.append({
                            'type': 'text',
                            'text': item['text']
                        })

                formatted.append({
                    'role': msg['role'],
                    'content': content_list
                })
            else:
                # 普通文本消息
                formatted.append({
                    'role': msg['role'],
                    'content': msg.get('content', '')
                })

        return formatted

    def _image_to_base64(self, image_path: str) -> str:
        """
        将图片文件转换为base64 data URL

        Args:
            image_path: 图片文件路径

        Returns:
            base64 data URL
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')

            # 检测图片类型
            if image_path.endswith('.png'):
                mime_type = 'image/png'
            elif image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif image_path.endswith('.gif'):
                mime_type = 'image/gif'
            elif image_path.endswith('.webp'):
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'

            return f'data:{mime_type};base64,{base64_data}'
        except Exception as e:
            raise Exception(f'图片转换失败: {str(e)}')

    def update_config(self, config: Dict[str, Any]):
        """
        更新配置

        Args:
            config: 新的配置
        """
        self.config.update(config)
        # 创建不使用代理的 httpx 客户端
        #http_client = httpx.Client()
        self.client = OpenAI(
            api_key=self.config.get('apiKey'),
            base_url=self.config.get('baseUrl'),
            #http_client=http_client
        )


# 示例使用
if __name__ == '__main__':
    # 示例配置
    config = {
        'baseUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'apiKey': 'YOUR_API_KEY_HERE',
        'model': 'qwen-vl-max',
        'temperature': 0.7
    }

    client = AIClient(config)

    # 文本消息示例
    messages = [
        {'role': 'user', 'content': '你好，请介绍一下自己'}
    ]

    # 多模态消息示例
    # messages = [
    #     {
    #         'role': 'user',
    #         'content': [
    #             {'type': 'text', 'text': '请分析这张图片'},
    #             {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,...'}}
    #         ]
    #     }
    # ]

    # try:
    #     response = client.chat(messages)
    #     print(response)
    # except Exception as e:
    #     print(f'Error: {e}')
