import asyncio
from hello_agents.protocols import MCPClient

#cd app\agents
#cd my-agent\helloagents-trip-planner\backend\app\agents
#python mcp-test.py
#npx -y @smithery/cli run @openags/paper-search-mcp
async def main() -> None:
    # 步骤1：连接到社区提供的MCP服务器（无需自己实现）@smithery/cli run @openags/paper-search-mcp
    #[TOOL_CALL:paper_search_search_arxiv:query=artificial intelligence in healthcare,max_results=5]
    github_client = MCPClient([
        "npx", "-y", "@smithery/cli", "run", "@openags/paper-search-mcp"
    ])
    # q={'name': 'search_arxiv', 
    #    'description': 'Search academic papers from arXiv', 
    #    'input_schema': {
    #        'type': 'object', 
    #        'properties': {
    #            'query': {'type': 'string', 'description': 'Search query string'}, 
    #            'max_results': {'type': 'number', 'default': 10, 'description': 'Maximum number of papers to return'}
    #         }, 
    #         'required': ['query'], 
    #         'additionalProperties': False, 
    #         '$schema': 'http://json-schema.org/draft-07/schema#'
    #     }
    # },
    # 步骤2：统一的调用方式（与模型无关）
    async with github_client:
        tools = await github_client.list_tools()
        print("可用工具:")
        print(tools)

        # 调用工具（标准化接口）
        # result = await github_client.call_tool(
        #     "search_repositories",
        #     {"query": "AI agents"}
        # )
        # print("\n搜索结果:")
        # print(result)


if __name__ == "__main__":
    asyncio.run(main())