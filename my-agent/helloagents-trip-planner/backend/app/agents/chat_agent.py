"""聊天Agent模块"""

from typing import Iterator

from hello_agents import SimpleAgent
from ..services.llm_service import get_llm


CHAT_SYSTEM_PROMPT = """你是一个中文智能助手,名称是“我的聊天Agent”。

要求:
1. 默认使用简体中文回答。
2. 回答简洁、准确、可执行。
3. 如果用户问题不明确,先提出1个澄清问题。
4. 不要编造事实,不确定时请明确说明。
"""


class ChatAgent:
    """简单聊天Agent"""

    def __init__(self):
        self.agent = SimpleAgent(
            name="聊天助手",
            llm=get_llm(),
            system_prompt=CHAT_SYSTEM_PROMPT,
        )

    def ask(self, message: str) -> str:
        """执行一次问答"""
        return self.agent.run(message)

    def stream_ask(self, message: str) -> Iterator[str]:
        """基于SimpleAgent.stream_run的流式问答"""
        return self.agent.stream_run(message)


_chat_agent_instance = None


def get_chat_agent() -> ChatAgent:
    """获取聊天Agent单例"""
    global _chat_agent_instance
    if _chat_agent_instance is None:
        _chat_agent_instance = ChatAgent()
    return _chat_agent_instance
