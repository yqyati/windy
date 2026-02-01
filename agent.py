#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent模块 - 管理多轮对话和上下文
支持OpenAI SDK格式的消息：system -> user -> assistant -> user -> assistant
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


class Agent:
    """
    Agent类 - 管理多轮对话

    支持功能：
    - 维护对话历史（messages列表）
    - 设置system prompt
    - 发送消息并自动更新历史
    - 清除历史
    - 获取上下文
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        ai_client=None,
        max_history: int = 50,
        on_stream: Optional[Callable[[str], None]] = None
    ):
        """
        初始化Agent

        Args:
            system_prompt: 系统提示词，设置agent的角色和行为
            ai_client: AI客户端实例
            max_history: 最大保留历史消息数
            on_stream: 流式回调函数，接收生成的文本片段
        """
        self.ai_client = ai_client
        self.max_history = max_history
        self.on_stream = on_stream

        # 消息历史 - OpenAI SDK格式
        self.messages: List[Dict[str, Any]] = []

        # 如果有system prompt，添加到开头
        if system_prompt:
            self.set_system_prompt(system_prompt)

    def set_system_prompt(self, prompt: str) -> None:
        """
        设置系统提示词

        如果已存在system消息，会更新它；否则添加到开头

        Args:
            prompt: 系统提示词
        """
        # 检查是否已有system消息
        if self.messages and self.messages[0].get('role') == MessageRole.SYSTEM.value:
            self.messages[0]['content'] = prompt
        else:
            self.messages.insert(0, {
                'role': MessageRole.SYSTEM.value,
                'content': prompt
            })

    def get_system_prompt(self) -> Optional[str]:
        """
        获取当前系统提示词

        Returns:
            系统提示词，如果不存在返回None
        """
        if self.messages and self.messages[0].get('role') == MessageRole.SYSTEM.value:
            return self.messages[0].get('content')
        return None

    def add_message(
        self,
        role: MessageRole,
        content: Any,
        silent: bool = False
    ) -> None:
        """
        添加消息到历史

        Args:
            role: 消息角色（system/user/assistant）
            content: 消息内容（字符串或多模态内容列表）
            silent: 是否静默添加（不触发历史清理）
        """
        self.messages.append({
            'role': role.value,
            'content': content
        })

        # 限制历史长度（保留system消息）
        if not silent and len(self.messages) > self.max_history + 1:
            # 保留第一条system消息，删除最早的对话
            if self.messages[0].get('role') == MessageRole.SYSTEM.value:
                # 删除最早的一对user-assistant消息
                if len(self.messages) > 2:
                    self.messages.pop(1)  # 删除第一个user
                    self.messages.pop(1)  # 删除对应的assistant
            else:
                self.messages.pop(0)

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        获取完整的消息历史

        Returns:
            消息列表（OpenAI SDK格式）
        """
        return self.messages.copy()

    def get_context(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话上下文（用于发送给AI）

        Args:
            limit: 限制返回的消息数量，None表示返回全部

        Returns:
            消息列表
        """
        if limit is None:
            return self.messages.copy()
        elif self.messages and self.messages[0].get('role') == MessageRole.SYSTEM.value:
            # 始终包含system消息
            if limit <= 1:
                return [self.messages[0]]
            return [self.messages[0]] + self.messages[-(limit - 1):]
        else:
            return self.messages[-limit:]

    def clear_history(self, keep_system: bool = True) -> None:
        """
        清除对话历史

        Args:
            keep_system: 是否保留system prompt
        """
        if keep_system and self.messages and self.messages[0].get('role') == MessageRole.SYSTEM.value:
            self.messages = [self.messages[0]]
        else:
            self.messages = []

    def chat(
        self,
        user_message: Any,
        stream: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        发送用户消息并获取回复

        Args:
            user_message: 用户消息（字符串或多模态内容列表）
            stream: 是否使用流式输出

        Returns:
            AI响应（非流式模式）或None（流式模式）
        """
        if not self.ai_client:
            raise RuntimeError("AI客户端未初始化")

        # 添加用户消息
        if isinstance(user_message, list):
            self.add_message(MessageRole.USER, user_message)
        else:
            self.add_message(MessageRole.USER, str(user_message))

        try:
            if stream:
                # 流式输出
                full_content = ''
                for chunk in self.ai_client.chat_stream(self.messages):
                    if chunk.get('choices') and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            full_content += content
                            if self.on_stream:
                                self.on_stream(content)

                # 保存assistant回复
                self.add_message(MessageRole.ASSISTANT, full_content, silent=True)
                return None
            else:
                # 非流式输出
                response = self.ai_client.chat(self.messages)
                assistant_content = response.get('choices', [{}])[0].get('message', {}).get('content', '')

                # 保存assistant回复
                self.add_message(MessageRole.ASSISTANT, assistant_content)
                return response
        except Exception as e:
            # 发生错误，移除刚才添加的用户消息
            self.messages.pop()
            raise

    def set_on_stream(self, callback: Callable[[str], None]) -> None:
        """
        设置流式回调函数

        Args:
            callback: 接收文本片段的回调函数
        """
        self.on_stream = callback

    def set_ai_client(self, ai_client) -> None:
        """
        设置AI客户端

        Args:
            ai_client: AI客户端实例
        """
        self.ai_client = ai_client

    def set_max_history(self, max_history: int) -> None:
        """
        设置最大历史消息数

        Args:
            max_history: 最大保留历史消息数
        """
        self.max_history = max_history

    def get_history_count(self) -> int:
        """
        获取当前历史消息数量（不含system消息）

        Returns:
            历史消息数量
        """
        count = len(self.messages)
        if self.messages and self.messages[0].get('role') == MessageRole.SYSTEM.value:
            count -= 1
        return max(0, count)

    def get_user_messages(self) -> List[Dict[str, Any]]:
        """
        获取所有用户消息

        Returns:
            用户消息列表
        """
        return [msg for msg in self.messages if msg.get('role') == MessageRole.USER.value]

    def get_assistant_messages(self) -> List[Dict[str, Any]]:
        """
        获取所有助手消息

        Returns:
            助手消息列表
        """
        return [msg for msg in self.messages if msg.get('role') == MessageRole.ASSISTANT.value]

    def export_messages(self) -> str:
        """
        导出消息历史为可读格式

        Returns:
            格式化的消息历史字符串
        """
        lines = []
        for msg in self.messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            # 处理多模态内容
            if isinstance(content, list):
                content_text = '[多模态消息]'
                for item in content:
                    if item.get('type') == 'text':
                        content_text = item.get('text', '')
                        break
                    elif item.get('type') == 'image_url':
                        content_text = '[图片]'
                        break
            else:
                content_text = content

            if role == MessageRole.SYSTEM.value:
                lines.append(f"[SYSTEM] {content_text}")
            elif role == MessageRole.USER.value:
                lines.append(f"[USER] {content_text}")
            elif role == MessageRole.ASSISTANT.value:
                lines.append(f"[ASSISTANT] {content_text}")

        return '\n\n'.join(lines)

    def __repr__(self) -> str:
        """字符串表示"""
        system_prompt = self.get_system_prompt() or 'None'
        return f"Agent(system_prompt='{system_prompt[:30]}...', history={self.get_history_count()} messages)"


# 预设的System Prompt模板
PRESET_SYSTEM_PROMPTS = {
    'default': """你是一个有用的AI助手。你会以友好、专业的方式回答用户的问题，提供准确、有用的信息。""",

    'coding': """你是一个专业的编程助手。你精通多种编程语言，能够帮助用户编写、调试、优化代码。你会提供清晰的代码解释和最佳实践建议。""",

    'writing': """你是一个专业的写作助手。你能够帮助用户进行各种类型的写作，包括文章创作、编辑、润色、翻译等。你会提供具体的改进建议和修改方案。""",

    'analysis': """你是一个专业的数据分析师。你能够分析数据、识别模式、发现洞察，并提供清晰的数据可视化建议和解释。""",

    'translator': """你是一个专业的翻译助手。你精通多种语言，能够准确、流畅地进行翻译，同时保持原文的风格和语调。你会根据上下文调整翻译策略。"""
}

def create_agent(
    preset: str = 'default',
    custom_prompt: Optional[str] = None,
    ai_client=None,
    **kwargs
) -> Agent:
    """
    创建一个Agent实例

    Args:
        preset: 预设的system prompt类型（default/coding/writing/analysis/translator）
        custom_prompt: 自定义system prompt（优先级高于preset）
        ai_client: AI客户端实例
        **kwargs: 传递给Agent的其他参数

    Returns:
        Agent实例
    """
    system_prompt = custom_prompt or PRESET_SYSTEM_PROMPTS.get(preset, PRESET_SYSTEM_PROMPTS['default'])
    return Agent(system_prompt=system_prompt, ai_client=ai_client, **kwargs)


# 示例使用
if __name__ == '__main__':
    from src.ai_client import AIClient

    # 示例配置
    config = {
        'baseUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'apiKey': 'YOUR_API_KEY_HERE',
        'model': 'qwen-vl-max',
        'temperature': 0.7
    }

    # 创建AI客户端
    ai_client = AIClient(config)

    # 创建Agent
    agent = Agent(
        system_prompt="你是一个友好的AI助手。",
        ai_client=ai_client,
        max_history=20
    )

    # 设置流式回调
    def on_stream(text):
        print(text, end='', flush=True)

    agent.set_on_stream(on_stream)

    # 发送消息
    try:
        print("用户: 你好")
        agent.chat("你好，请介绍一下自己", stream=False)

        print("\n\n用户: 你能做什么？")
        agent.chat("你能做什么？", stream=False)

        # 查看历史
        print(f"\n\n历史消息数: {agent.get_history_count()}")
        print("\n消息历史:")
        print(agent.export_messages())

    except Exception as e:
        print(f"Error: {e}")
