"""文章双子Agent模块: 搜索子Agent + 汇总子Agent"""

from typing import Dict, Iterator, List
from urllib.parse import quote

import httpx
from hello_agents import SimpleAgent

from ..services.llm_service import get_llm


SEARCH_AGENT_PROMPT = """你是文章检索助手。
你的任务是将用户需求改写为更适合搜索引擎的关键词。

规则:
1. 输出2-5个关键词。
2. 关键词之间用空格分隔。
3. 不要输出解释、标点和编号。
"""


SUMMARY_AGENT_PROMPT = """你是文章汇总助手。
你会基于给定的文章候选信息生成中文总结。

规则:
1. 先给出简短结论。
2. 再给出要点列表。
3. 明确标注信息可能不完整或有时效性。
4. 若信息不足,给出下一步检索建议。
"""


class ArticleAgent:
	"""文章双子Agent"""

	def __init__(self):
		llm = get_llm()
		self.search_agent = SimpleAgent(
			name="文章搜索子Agent",
			llm=llm,
			system_prompt=SEARCH_AGENT_PROMPT,
		)
		self.summary_agent = SimpleAgent(
			name="文章汇总子Agent",
			llm=llm,
			system_prompt=SUMMARY_AGENT_PROMPT,
		)

	def search_articles(self, user_query: str, limit: int = 5) -> Dict[str, object]:
		"""搜索文章候选"""
		rewritten_query = self.search_agent.run(
			f"用户需求: {user_query}\n请输出可用于搜索的关键词"
		).strip()
		if not rewritten_query:
			rewritten_query = user_query

		articles = self._search_wikipedia(rewritten_query, limit=limit)

		if not articles and rewritten_query != user_query:
			articles = self._search_wikipedia(user_query, limit=limit)

		return {
			"rewritten_query": rewritten_query,
			"articles": articles,
		}

	def stream_summarize(self, user_query: str, articles: List[Dict[str, str]]) -> Iterator[str]:
		"""流式汇总"""
		if not articles:
			yield "未检索到相关文章。建议你换一个更具体的关键词，例如加入领域、年份或作者。"
			return

		context = []
		for idx, article in enumerate(articles, start=1):
			context.append(
				f"[{idx}] 标题: {article['title']}\n"
				f"摘要: {article['snippet']}\n"
				f"链接: {article['url']}"
			)

		prompt = (
			f"用户需求: {user_query}\n\n"
			"候选文章:\n"
			+ "\n\n".join(context)
			+ "\n\n请基于候选文章给出汇总。"
		)

		for chunk in self.summary_agent.stream_run(prompt):
			yield chunk

	def _search_wikipedia(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
		"""通过Wikipedia搜索公开文章信息"""
		safe_limit = max(1, min(limit, 10))
		params = {
			"action": "query",
			"list": "search",
			"utf8": 1,
			"format": "json",
			"srsearch": query,
			"srlimit": safe_limit,
		}

		endpoints = [
			"https://zh.wikipedia.org/w/api.php",
			"https://en.wikipedia.org/w/api.php",
		]

		for endpoint in endpoints:
			try:
				response = httpx.get(endpoint, params=params, timeout=12.0)
				response.raise_for_status()
				data = response.json()
				raw_items = data.get("query", {}).get("search", [])

				if not raw_items:
					continue

				base_wiki = endpoint.replace("/w/api.php", "/wiki/")
				items: List[Dict[str, str]] = []
				for item in raw_items:
					title = item.get("title", "未命名")
					snippet = item.get("snippet", "")
					clean_snippet = snippet.replace("<span class=\"searchmatch\">", "").replace("</span>", "")
					url = base_wiki + quote(title.replace(" ", "_"))
					items.append(
						{
							"title": title,
							"snippet": clean_snippet,
							"url": url,
						}
					)

				return items
			except Exception:
				continue

		return []


_article_agent_instance = None


def get_article_agent() -> ArticleAgent:
	"""获取文章Agent单例"""
	global _article_agent_instance
	if _article_agent_instance is None:
		_article_agent_instance = ArticleAgent()
	return _article_agent_instance

if __name__ == "__main__":
	# 测试文章Agent
	agent = get_article_agent()
	user_query = "人工智能在医疗领域的应用"
	search_result = agent.search_articles(user_query)
	print("搜索结果:")
	print(search_result)

	print("\n汇总结果:")
	for chunk in agent.stream_summarize(user_query, search_result["articles"]):
		print(chunk, end="")