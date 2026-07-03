"""聊天API路由"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...agents.chat import get_chat_agent

router = APIRouter(prefix="/chat", tags=["聊天助手"])


class ChatRequest(BaseModel):
    """聊天请求"""

    message: str = Field(..., min_length=1, max_length=4000, description="用户提问")


def _to_sse(event: str, payload: dict) -> str:
    """格式化SSE消息"""

    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post(
    "/stream",
    summary="流式聊天",
    description="以SSE方式流式返回聊天回答",
)
async def stream_chat(request: ChatRequest):
    """流式聊天接口"""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            user_message = request.message.strip()
            if not user_message:
                yield _to_sse("error", {"message": "问题不能为空"})
                return

            # 先返回启动事件,让前端立刻进入流式状态
            yield _to_sse("start", {"message": "正在思考..."})

            agent = get_chat_agent()
            for chunk in agent.stream_ask(user_message):
                if chunk:
                    yield _to_sse("chunk", {"content": chunk})

            yield _to_sse("done", {"message": "完成"})
        except Exception as e:
            yield _to_sse("error", {"message": f"聊天失败: {str(e)}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
