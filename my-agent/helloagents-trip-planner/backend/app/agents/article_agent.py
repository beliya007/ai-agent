"""文章双子Agent模块: 搜索子Agent + 汇总子Agent"""

import json
from typing import Any, Dict, Iterator, List

from hello_agents import SimpleAgent
from .SimpleArticle import SimpleArticleAgent

from hello_agents.tools import MCPTool

from ..services.llm_service import get_llm


SEARCH_AGENT_PROMPT = """你是论文检索专家。

**重要提示:**
你必须使用paper-search MCP工具检索,不要编造论文信息。

**可用工具调用格式示例:**
- arXiv: `[TOOL_CALL:paper_search_search_arxiv:query=检索词,max_results=数量]`
- PubMed: `[TOOL_CALL:paper_search_search_pubmed:query=检索词,max_results=数量]`

**规则:**
1. 必须至少调用一次工具。
2. 默认优先使用arXiv,必要时再补充PubMed。
3. 先将用户问题精炼成简短英文或中英混合检索词再调用工具。
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

**规则:**
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
		self.search_agent = SimpleArticleAgent(
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
		print(f"🔍 搜索子Agent输出--: {agent_output}")
		# 解析工具执行结果,提取论文列表,提取
		tool_results = agent_output.get("last_tool_results", [])
		llm_output = agent_output.get("final_response", "")
		display_results = []
		if isinstance(tool_results, list):
			display_results = tool_results
		elif isinstance(tool_results, str):
			start = tool_results.find("[")
			end = tool_results.rfind("]")
			if start != -1 and end != -1 and start < end:
				try:
					display_results = json.loads(tool_results[start : end + 1])
				except json.JSONDecodeError:
					display_results = []
		print(f"🔍 前端展示结果: {display_results}")
		return {
			"rewritten_query": llm_output,
			"articles": display_results,
		}

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
	# print("搜索结果----:", search_result)

	# print("\n汇总结果:")
	# for chunk in agent.stream_summarize(user_query, search_result["articles"]):
	# 	print(chunk, end="")