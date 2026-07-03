"""文章相关API路由"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...agents.article_agent import get_article_agent

router = APIRouter(prefix="/article", tags=["文章Agent"])


class ArticleSearchRequest(BaseModel):
    """文章搜索请求"""

    query: str = Field(..., min_length=1, max_length=2000, description="搜索问题")
    limit: int = Field(default=5, ge=1, le=10, description="候选文章数量")


def _to_sse(event: str, payload: dict) -> str:
    """格式化SSE消息"""

    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post(
    "/search",
    summary="文章搜索",
    description="搜索相关文章并生成汇总文本",
)
async def search_article(request: ArticleSearchRequest):
    """非流式文章搜索接口"""
    user_query = request.query.strip()
    agent = get_article_agent()

    search_result = agent.search_articles(user_query, limit=request.limit)
    articles = search_result["articles"]

    summary = ""
    for chunk in agent.stream_summarize(user_query, articles):
        summary += chunk

    return {
        "success": True,
        "message": "文章搜索成功",
        "data": {
            "rewritten_query": search_result["rewritten_query"],
            "articles": articles,
            "summary": summary,
        },
    }


@router.post(
    "/stream",
    summary="流式文章搜索与汇总",
    description="先返回搜索结果，再流式返回汇总内容",
)
async def stream_article(request: ArticleSearchRequest):
    """流式文章搜索接口"""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            user_query = request.query.strip()
            if not user_query:
                yield _to_sse("error", {"message": "搜索内容不能为空"})
                return

            yield _to_sse("start", {"message": "搜索子Agent开始检索"})

            agent = get_article_agent()
            search_result = agent.search_articles(user_query, limit=request.limit)
            articles = search_result["articles"]

            yield _to_sse(
                "search_results",
                {
                    "rewritten_query": search_result["rewritten_query"],
                    "articles": articles,
                },
            )

            yield _to_sse("summary_start", {"message": "汇总子Agent开始生成总结"})
            for chunk in agent.stream_summarize(user_query, articles):
                if chunk:
                    yield _to_sse("chunk", {"content": chunk})

            yield _to_sse("done", {"message": "完成"})
        except Exception as e:
            yield _to_sse("error", {"message": f"文章搜索失败: {str(e)}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
