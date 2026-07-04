"""文章双子Agent模块: 搜索子Agent + 汇总子Agent"""

import json
from typing import Any, Dict, Iterator, List

from hello_agents import SimpleAgent
from hello_agents.tools import MCPTool

from ..services.llm_service import get_llm


SEARCH_AGENT_PROMPT = """你是论文检索专家。

**重要提示:**
你必须使用paper-search MCP工具检索,不要编造论文信息。

**可用工具调用格式:**
- arXiv: `[TOOL_CALL:paper_search_search_arxiv:query=检索词,max_results=数量]`
- PubMed: `[TOOL_CALL:paper_search_search_pubmed:query=检索词,max_results=数量]`
- bioRxiv: `[TOOL_CALL:paper_search_search_biorxiv:query=检索词,max_results=数量]`
- medRxiv: `[TOOL_CALL:paper_search_search_medrxiv:query=检索词,max_results=数量]`
- Google Scholar: `[TOOL_CALL:paper_search_search_google_scholar:query=检索词,max_results=数量]`

规则:
1. 必须至少调用一次工具。
2. 默认优先使用arXiv,必要时再补充PubMed。
3. 先将用户问题精炼成简短英文或中英混合检索词再调用工具。
4. 工具执行后,只输出如下JSON:
	{"rewritten_query":"...","papers":[...工具返回的论文数组...]}
5. 不要输出除JSON以外的任何文本。
"""


PAPER_SEARCH_SERVER_COMMAND = [
	"npx",
	"-y",
	"@smithery/cli",
	"run",
	"@openags/paper-search-mcp",
]

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
		self.paper_mcp_tool = MCPTool(
			name="paper_search",
			description="论文检索MCP服务,支持arXiv/PubMed/bioRxiv/medRxiv/Google Scholar",
			server_command=PAPER_SEARCH_SERVER_COMMAND,
			auto_expand=True,
		)
		self.search_agent = SimpleAgent(
			name="文章搜索子Agent",
			llm=llm,
			system_prompt=SEARCH_AGENT_PROMPT,
		)
		self.search_agent.add_tool(self.paper_mcp_tool)
		self.summary_agent = SimpleAgent(
			name="文章汇总子Agent",
			llm=llm,
			system_prompt=SUMMARY_AGENT_PROMPT,
		)

	def search_articles(self, user_query: str, limit: int = 5) -> Dict[str, object]:
		"""搜索文章候选"""
		safe_limit = max(1, min(limit, 10))
		agent_output = self.search_agent.run(
			f"用户问题: {user_query}\n请检索相关论文,最多返回{safe_limit}条。"
		)

		rewritten_query = user_query
		articles: List[Dict[str, str]] = []

		parsed = self._parse_json_payload(agent_output)
		if isinstance(parsed, dict):
			candidate_query = str(parsed.get("rewritten_query", "")).strip()
			if candidate_query:
				rewritten_query = candidate_query

			papers = parsed.get("papers")
			if isinstance(papers, list):
				articles = self._normalize_papers_to_articles(papers, safe_limit)

		if not articles:
			articles = self._normalize_papers_to_articles(
				self._extract_paper_items(agent_output),
				safe_limit,
			)

		return {
			"rewritten_query": rewritten_query,
			"articles": articles,
		}

	def _normalize_papers_to_articles(self, papers: List[Dict[str, Any]], limit: int) -> List[Dict[str, str]]:
		"""将论文数据标准化为前端展示结构"""
		items: List[Dict[str, str]] = []
		seen_keys = set()

		for paper in papers:
			if not isinstance(paper, dict):
				continue

			title = str(paper.get("title", "")).strip() or "未命名论文"
			snippet = str(
				paper.get("abstract")
				or paper.get("summary")
				or paper.get("snippet")
				or paper.get("description")
				or "暂无摘要"
			).strip()
			url = str(
				paper.get("url")
				or paper.get("pdf_url")
				or paper.get("link")
				or ""
			).strip()

			key = (title.lower(), url)
			if key in seen_keys:
				continue

			seen_keys.add(key)
			items.append(
				{
					"title": title,
					"snippet": snippet,
					"url": url,
				}
			)

			if len(items) >= limit:
				return items[:limit]

		return items[:limit]

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

	def _extract_paper_items(self, raw_result: Any) -> List[Dict[str, Any]]:
		"""兼容不同MCP返回格式,提取论文数组"""
		parsed = self._parse_json_payload(raw_result)

		if isinstance(parsed, list):
			return [item for item in parsed if isinstance(item, dict)]

		if isinstance(parsed, dict):
			for key in ("papers", "results", "items", "data"):
				value = parsed.get(key)
				if isinstance(value, list):
					return [item for item in value if isinstance(item, dict)]

		return []

	def _parse_json_payload(self, raw_result: Any) -> Any:
		"""解析MCP工具返回,支持字符串与对象格式"""
		if isinstance(raw_result, (list, dict)):
			return raw_result

		if not isinstance(raw_result, str):
			return None

		text = raw_result.strip()
		if not text:
			return None

		try:
			return json.loads(text)
		except Exception:
			start = text.find("[")
			end = text.rfind("]")
			if start != -1 and end != -1 and end > start:
				candidate = text[start : end + 1]
				try:
					return json.loads(candidate)
				except Exception:
					return None

		return None


_article_agent_instance = None


def get_article_agent() -> ArticleAgent:
	"""获取文章Agent单例"""
	global _article_agent_instance
	if _article_agent_instance is None:
		_article_agent_instance = ArticleAgent()
	return _article_agent_instance

if __name__ == "__main__":
	# 测试文章Agent
	#cd app\agents
	#python article_agent.py
	agent = get_article_agent()
	user_query = "人工智能在医疗领域的应用"
	search_result = agent.search_articles(user_query)
	print("搜索结果:")
	print(search_result)

	print("\n汇总结果:")
	for chunk in agent.stream_summarize(user_query, search_result["articles"]):
		print(chunk, end="")