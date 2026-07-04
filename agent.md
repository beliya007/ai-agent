# 1. Agent

**Workflow 是让 AI 按部就班地执行指令，而 Agent 则是赋予 AI 自由度去自主达成目标。**

**这种基于实时信息进行动态推理和决策的能力，正是 Agent 的核心价值所在。**

监督学习学习**输入到标准答案的映射**；强化学习学习**状态到最优动作的决策策略**，依靠环境奖励替代人工标签。

------

![image-20260621142522256](C:\Users\31461\AppData\Roaming\Typora\typora-user-images\image-20260621142522256.png)

- **Thought (思考)：** 这是智能体的“内心独白”。它会分析当前情况、分解任务、制定下一步计划，或者反思上一步的结果。
- **Action (行动)：** 这是智能体决定采取的具体动作，通常是调用一个外部工具，例如 `Search['华为最新款手机']`。
- **Observation (观察)：** 这是执行`Action`后从外部工具返回的结果，例如搜索结果的摘要或API的返回值。

智能体将不断重复这个 **Thought -> Action -> Observation** 的循环，将新的观察结果追加到历史记录中，形成一个不断增长的上下文，直到它在`Thought`中认为已经找到了最终答案，然后输出结果。这个过程形成了一个强大的协同效应：**推理使得行动更具目的性，而行动则为推理提供了事实依据。**

## 1.1 ReAct

1. **动态规划与纠错能力**：与一次性生成完整计划的范式不同，ReAct 是“走一步，看一步”。它根据每一步从外部世界获得的 `Observation` 来动态调整后续的 `Thought` 和 `Action`。如果上一步的搜索结果不理想，它可以在下一步中修正搜索词，重新尝试。

## 1.2 Plan-and-Solve

1. **规划阶段**： 智能体首先调用 `Planner`，成功地将复杂的应用题分解成了一个包含四个逻辑步骤的 Python 列表。这个结构化的计划为后续的执行奠定了基础。

2. **执行阶段**： `Executor` 严格按照生成的计划，一步一步地向下执行。在每一步中，它都将历史结果作为上下文，确保了信息的正确传递（例如，步骤2正确地使用了步骤1的结果“15个”，步骤3也正确使用了步骤2的结果“30个”）。

   ```python
   class Executor:
       def __init__(self, llm_client: HelloAgentsLLM):
           self.llm_client = llm_client
       def execute(self, question: str, plan: list[str]) -> str:
           history = ""
           final_answer = ""
           print("\n--- 正在执行计划 ---")
           for i, step in enumerate(plan, 1):
               print(f"\n-> 正在执行步骤 {i}/{len(plan)}: {step}")
               prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                   question=question, plan=plan, history=history if history else "无", current_step=step
               )
               messages = [{"role": "user", "content": prompt}]
               response_text = self.llm_client.think(messages=messages) or ""
               history += f"步骤 {i}: {step}\n结果: {response_text}\n\n"
               final_answer = response_text
               print(f"✅ 步骤 {i} 已完成，结果: {final_answer}")
               
           return final_answer
   ```

   

3. **结果**：整个过程逻辑清晰，步骤明确，最终智能体准确地得出了正确答案“70个”。

## 1.3 Reflection

Reflection 机制的核心思想，正是为智能体引入一种**事后（post-hoc）的自我校正循环**，使其能够像人类一样，审视自己的工作，发现不足，并进行迭代优化。

![image-20260621210659680](C:\Users\31461\AppData\Roaming\Typora\typora-user-images\image-20260621210659680.png)

## 1.4 SimpleAge----------------

### 1.4.1子agent

```python
            # 创建景点搜索Agent
            print("  - 创建景点搜索Agent...")
            self.attraction_agent = SimpleAgent(
                name="景点搜索专家",
                llm=self.llm,
                system_prompt=ATTRACTION_AGENT_PROMPT
            )
            self.attraction_agent.add_tool(self.amap_tool)
            #查看工具列表
            print(f"   景点搜索Agent: {len(self.attraction_agent.list_tools())} 个工具")
            #根据请求参数构建字符串请求agent
            attraction_query = self._build_attraction_query(request)
            #执行agent的run
            attraction_response = self.attraction_agent.run(attraction_query)
```

```python
    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """
        运行SimpleAgent，支持可选的工具调用
        """
        messages = []
        # 添加系统消息（可能包含工具信息）
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})
        # 添加历史消息
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        # 添加当前用户消息
        messages.append({"role": "user", "content": input_text})
        
        # 如果没有启用工具调用，使用原有逻辑
        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            return response
        # 迭代处理，支持多轮工具调用
        current_iteration = 0
        final_response = ""

        while current_iteration < max_tool_iterations:
            # 调用LLM
            response = self.llm.invoke(messages, **kwargs)
            # 检查是否有工具调用，并解析出调用格式
            tool_calls = self._parse_tool_calls(response)
            if tool_calls:
                # 执行所有工具调用并收集结果
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    # 从响应中移除工具调用标记
                    clean_response = clean_response.replace(call['original'], "")
                # 构建包含工具结果的消息
                messages.append({"role": "assistant", "content": clean_response})
                # 添加工具结果
                tool_results_text = "\n\n".join(tool_results)
                messages.append({"role": "user", "content": f"工具执行结果：\n{tool_results_text}\n\n请基于这些结果给出完整的回答。"})

                current_iteration += 1
                continue
            # 没有工具调用，这是最终回答
            final_response = response
            break
        # 如果超过最大迭代次数，获取最后一次回答
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs)
        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        return final_response
```

### 1.4.2 tool

**工具格式**

```python
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}
        self._functions[name] = {
            "description": description,
            "func": func
        }
```

**增加工具**

```python
    def add_tool(self, tool, auto_expand: bool = True) -> None:
        """
        如果工具是可展开的（expandable=True），会自动展开为多个独立工具
        """
        if not self.tool_registry:
            from ..tools.registry import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True
        self.tool_registry.register_tool(tool, auto_expand=auto_expand)
```

**注册工具**

```python
    def register_tool(self, tool: Tool, auto_expand: bool = True):
        if auto_expand and hasattr(tool, 'expandable') and tool.expandable:
            expanded_tools = tool.get_expanded_tools()
            if expanded_tools:
                for sub_tool in expanded_tools:
                    if sub_tool.name in self._tools:
                    self._tools[sub_tool.name] = sub_tool
                return
        self._tools[tool.name] = tool
```

**查看工具**

```python
    def list_tools(self) -> list[str]:
        """列出所有工具名称"""
        return list(self._tools.keys()) + list(self._functions.keys())
```

**查看工具描述**

```python
    def get_tools_description(self) -> str:
        descriptions = []
        # Tool对象描述
        for tool in self._tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")
        # 函数工具描述
        for name, info in self._functions.items():
            descriptions.append(f"- {name}: {info['description']}")
        return "\n".join(descriptions) if descriptions else "暂无可用工具"
```

#### 1.4.2.1 MCPTool

**使用**

```python
            # 创建共享的MCP工具(只创建一次)
            print("  - 创建共享MCP工具...")
            self.amap_tool = MCPTool(
                name="amap",
                description="高德地图服务",
                server_command=["uvx", "amap-mcp-server"],
                env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
                auto_expand=True
            )
```

**内部TOOL的run方法**

```python
    def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行 MCP 操作
        Args:
            parameters: 包含以下参数的字典
                - action: 操作类型 (list_tools, call_tool, list_resources, read_resource, list_prompts, get_prompt)
                  如果不指定action但指定了tool_name，会自动推断为call_tool
                - tool_name: 工具名称（call_tool 需要）
                - arguments: 工具参数（call_tool 需要）
                - uri: 资源 URI（read_resource 需要）
                - prompt_name: 提示词名称（get_prompt 需要）
                - prompt_arguments: 提示词参数（get_prompt 可选）
        Returns:
            操作结果
        """
        from hello_agents.protocols.mcp.client import MCPClient
        # 智能推断action：如果没有action但有tool_name，自动设置为call_tool
        try:
            # 使用增强的异步客户端
                async with MCPClient(client_source, self.server_args, env=self.env) as client:
                    if action == "list_tools":
                        tools = await client.list_tools()
                        if not tools:
                            return "没有找到可用的工具"
                        result = f"找到 {len(tools)} 个工具:\n"
                        for tool in tools:
                            result += f"- {tool['name']}: {tool['description']}\n"
                        return result
                    elif action == "call_tool":
                        tool_name = parameters.get("tool_name")
                        arguments = parameters.get("arguments", {})
                        if not tool_name:
                            return "错误：必须指定 tool_name 参数"
                        result = await client.call_tool(tool_name, arguments)
                        return f"工具 '{tool_name}' 执行结果:\n{result}"
```

**实际mcpclient**

```python
from hello_agents.protocols import MCPClient

# 步骤1：连接到社区提供的MCP服务器（无需自己实现）
github_client = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-github"
])
# 步骤2：统一的调用方式（与模型无关）
async with github_client:
    tools = await github_client.list_tools()
    # 调用工具（标准化接口）
    result = await github_client.call_tool(
        "search_repositories",
        {"query": "AI agents"}
    )
# 步骤3：任何支持MCP的模型都能使用
# OpenAI、Claude、Llama等都使用相同的MCP客户端


#真实连接，例如command：npx，args：-y @model...
                # 其他命令，使用通用 Stdio 传输
                from fastmcp.client.transports import StdioTransport
                return StdioTransport(
                    command=server_source[0],
                    args=server_source[1:] + self.server_args,
                    env=self.env if self.env else None,
                    **self.transport_kwargs
                )
```

·

### 1.4.3 系统提示词

```python
    def _get_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个有用的AI助手。"
        #是否有工具
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt
        #是否获取工具描述
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt
        #获取工具
        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题：\n"
        tools_section += tools_description + "\n"
        tools_section += "\n## 工具调用格式\n"
        tools_section += "当需要使用工具时，请使用以下格式：\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n\n"
        return base_prompt + tools_section
   
```



# 2 低代码

## 2.1 n8n 的节点与工作流

n8n 的世界由两个最基本的概念构成：**节点 (Node)** 和 **工作流 (Workflow)**。

- **节点 (Node)**：节点是工作流中执行具体操作的最小单元。你可以把它想象成一个具有特定功能的“积木块”。n8n 提供了数百种预置节点，涵盖了从发送邮件、读写数据库、调用 API 到处理文件等各种常见操作。每个节点都有输入和输出，并提供图形化的配置界面。节点大致可以分为两类：
  - **触发节点 (Trigger Node)**：它是整个工作流的起点，负责启动流程。例如，“当收到一封新的 Gmail 邮件时”、“每小时定时触发一次”或“当接收到一个 Webhook 请求时”。一个工作流必须有且仅有一个触发节点。
  - **常规节点 (Regular Node)**：负责处理具体的数据和逻辑。例如，“读取 Google Sheets 表格”、“调用 OpenAI 模型”或“在数据库中插入一条记录”。
- **工作流 (Workflow)**：工作流是由多个节点连接而成的自动化流程图。它定义了数据从触发节点开始，如何一步步地在不同节点之间传递、被处理，并最终完成预设任务的完整路径。数据在节点之间以结构化的 JSON 格式进行传递，这使得我们可以精确地控制每一个环节的输入和输出。

n8n 的真正威力在于其强大的“连接”能力。它可以将原本孤立的应用程序和服务（如企业内部的 CRM、外部的社交媒体平台、你的数据库以及大语言模型）串联起来，实现过去需要复杂编码才能完成的端到端业务流程自动化。在接下来的实战中，我们将亲手体验如何利用这套节点和工作流系统，构建一个集成了 AI 能力的自动化应用。

整个过程模拟了一个更高级的决策逻辑：`接收 -> AI Agent (思考 -> 决策 -> 工具调用) -> 回复`

# 3. 框架

1. **提升代码复用与开发效率**：这是最直接的价值。一个好的框架会提供一个通用的 `Agent` 基类或执行器，它封装了智能体运行的核心循环（Agent Loop）。无论是 ReAct 还是 Plan-and-Solve，都可以基于框架提供的标准组件快速搭建，从而避免重复劳动。
2. 实现核心组件的解耦与可扩展性：一个健壮的智能体系统应该由多个松散耦合的模块组成。框架的设计会强制我们分离不同的关注点：
   - **模型层 (Model Layer)**：负责与大语言模型交互，可以轻松替换不同的模型（OpenAI, Anthropic, 本地模型）。
   - **工具层 (Tool Layer)**：提供标准化的工具定义、注册和执行接口，添加新工具不会影响其他代码。
   - **记忆层 (Memory Layer)**：处理短期和长期记忆，可以根据需求切换不同的记忆策略（如滑动窗口、摘要记忆）。 这种模块化的设计使得整个系统极具可扩展性，更换或升级任何一个组件都变得简单。
3. **标准化复杂的状态管理**：我们在 `ReflectionAgent` 中实现的 `Memory` 类只是一个简单的开始。在真实的、长时运行的智能体应用中，状态管理是一个巨大的挑战，它需要处理上下文窗口限制、历史信息持久化、多轮对话状态跟踪等问题。一个框架可以提供一套强大而通用的状态管理机制，开发者无需每次都重新处理这些复杂问题。
4. **简化可观测性与调试过程**：当智能体的行为变得复杂时，理解其决策过程变得至关重要。一个精心设计的框架可以内置强大的可观测性能力。例如，通过引入事件回调机制（Callbacks），我们可以在智能体生命周期的关键节点（如 `on_llm_start`, `on_tool_end`, `on_agent_finish`）自动触发日志记录或数据上报，从而轻松地追踪和调试智能体的完整运行轨迹。这远比在代码中手动添加 `print` 语句要高效和系统化。

## 3.1 AutoGen

```python
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

# 定义团队聊天和协作规则
team_chat = RoundRobinGroupChat(
    participants=[
        product_manager,//几个系统提示词不一样的原始大模型对话
        engineer,
        code_reviewer,
        user_proxy
    ],
    termination_condition=TextMentionTermination("TERMINATE"),//终止条件
    max_turns=20,
)
```

- 虽然 `RoundRobinGroupChat` 提供了顺序化的流程，但基于 LLM 的对话本质上具有不确定性。智能体可能会产生偏离预期的回复，导致对话走向意外的分支，甚至陷入循环。

## 3.2 AgentScope

**基础组件层 (Foundational Components)**，它为整个框架提供了核心的构建块。`Message` 组件定义了统一的消息格式，支持从简单的文本交互到复杂的多模态内容；`Memory` 组件提供了短期和长期记忆管理；`Model API` 层抽象了对不同大语言模型的调用；而 `Tool` 组件则封装了智能体与外部世界交互的能力。

**智能体基础设施层 (Agent-level Infrastructure)** 提供了更高级的抽象。这一层不仅包含了各种预构建的智能体（如浏览器使用智能体、深度研究智能体），还实现了经典的 ReAct 范式，支持智能体钩子、并行工具调用、状态管理等高级特性。特别值得注意的是，这一层原生支持异步执行与实时控制，这是 AgentScope 相比其他框架的一个重要优势。

**多智能体协作层 (Multi-Agent Cooperation)** 是 AgentScope 的核心创新所在。`MsgHub` 作为消息中心，负责智能体间的消息路由和状态管理；而 `Pipeline` 系统则提供了灵活的工作流编排能力，支持顺序、并发等多种执行模式。这种设计使得开发者可以轻松构建复杂的多智能体协作场景。

**主体：**

```python
from agentscope.agents import AgentBase
class CustomAgent(AgentBase):
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        # 智能体初始化逻辑
    def reply(self, x: Msg) -> Msg:
        # 智能体的核心响应逻辑
        response = self.model(x.content)
        return Msg(name=self.name, content=response, role="assistant")
    def observe(self, x: Msg) -> None:
        # 智能体的观察逻辑（可选）
        self.memory.add(x)
```

```python
from agentscope.message import Msg

# 消息的标准结构
message = Msg(
    name="Alice",           # 发送者名称
    content="Hello, Bob!",  # 消息内容
    role="user",           # 角色类型
    metadata={             # 元数据信息
        "timestamp": "2024-01-15T10:30:00Z",
        "message_type": "text",
        "priority": "normal"
    }
)
```

**实例过程：**

```python
async def werewolf_phase(self, round_num: int):
    """狼人阶段 - 展示消息驱动的协作模式"""
    if not self.werewolves:
        return None
    # 通过消息中心建立狼人专属通信频道
    async with MsgHub(
        self.werewolves,
        enable_auto_broadcast=True,
        announcement=await self.moderator.announce(
            f"狼人们，请讨论今晚的击杀目标。存活玩家：{format_player_list(self.alive_players)}"
        ),
    ) as werewolves_hub:
        # 讨论阶段：狼人通过消息交换策略
        for _ in range(MAX_DISCUSSION_ROUND):
            for wolf in self.werewolves:
                await wolf(structured_model=DiscussionModelCN)
        # 投票阶段：收集并统计狼人的击杀决策
        werewolves_hub.set_auto_broadcast(False)
        kill_votes = await fanout_pipeline(
            self.werewolves,
            msg=await self.moderator.announce("请选择击杀目标"),
            structured_model=WerewolfKillModelCN,
            enable_gather=False,
        )
```

多智能体专用**临时消息聊天室**，限定只有传入的 `self.werewolves` 能看到频道内消息。

- `self.werewolves`：频道成员 = 所有狼人 AI
- `enable_auto_broadcast=True`：开启自动广播，任意狼人发言自动同步给所有其他狼人
- `announcement`：频道创建时自动推送的开场白
  - 法官发公告：告知狼人可以商量刀谁，附带当前全场存活玩家名单

`async with` 上下文管理器：代码块结束自动销毁狼人私聊频道，狼人白天无法互通信息。

> await wolf()` 触发 `__call__
>
> MsgHub 推送频道所有历史对话 → 批量 `observe`，更新该狼记忆
>
> 进入 `reply()`，加载完整记忆上下文，调用 LLM 生成狼人发言
>
> 返回发言 Msg，`enable_auto_broadcast=True` 自动扔进频道公共历史
>
> 下一轮其他狼人执行 `wolf()` 时，这条新发言会被一起 observe 读取

## 3.3 CAMEL

CAMEL最初的核心目标是探索如何在最少的人类干预下，让两个智能体通过“角色扮演”自主协作解决复杂任务。

```python
# 初始化角色扮演会话
# AI 作家作为 "user"，负责提出写作结构和要求
# AI 心理学家作为 "assistant"，负责提供专业知识和内容
role_play_session = RolePlaying(
    assistant_role_name="心理学家",
    user_role_name="作家",
    task_prompt=task_prompt,
    model=model,
    with_task_specify=False, # 在本例中，我们直接使用给定的task_prompt
)

print(Fore.CYAN + f"具体任务描述:\n{role_play_session.task_prompt}\n")

# 开始协作对话
chat_turn_limit, n = 30, 0
# 调用 init_chat() 来获得由 AI 生成的初始对话消息
input_msg = role_play_session.init_chat()

while n < chat_turn_limit:
    n += 1
    # step() 方法驱动一轮完整的对话，AI 用户和 AI 助理各发言一次
    assistant_response, user_response = role_play_session.step(input_msg)
    
    # 检查是否有消息返回，防止对话提前终止
    if assistant_response.msg is None or user_response.msg is None:
        break
    
    print_text_animated(Fore.BLUE + f"作家 (AI User):\n\n{user_response.msg.content}\n")
    print_text_animated(Fore.GREEN + f"心理学家 (AI Assistant):\n\n{assistant_response.msg.content}\n")
    
    # 检查任务完成标志
    if "<CAMEL_TASK_DONE>" in user_response.msg.content or "<CAMEL_TASK_DONE>" in assistant_response.msg.content:
        print(Fore.MAGENTA + "✅ 电子书创作完成！")
        break
    
    # 将助理的回复作为下一轮对话的输入
    input_msg = assistant_response.msg

print(Fore.YELLOW + f"总共进行了 {n} 轮协作对话")
```

## 3.4 LangGraph

LangGraph 将智能体的执行流程建模为一种**状态机（State Machine）**，并将其表示为**有向图（Directed Graph）**。在这种范式中，图的**节点（Nodes）**代表一个具体的计算步骤（如调用 LLM、执行工具），而**边（Edges）**则定义了从一个节点到另一个节点的跳转逻辑。

**全局状态（State）**。整个图的执行过程都围绕一个共享的状态对象进行。这个状态通常被定义为一个 Python 的 `TypedDict`，它可以包含任何你需要追踪的信息，如对话历史、中间结果、迭代次数等。所有的节点都能读取和更新这个中心状态。

```python
from typing import TypedDict, List
# 定义全局状态的数据结构
class AgentState(TypedDict):
    messages: List[str]      # 对话历史
    current_task: str        # 当前任务
    final_answer: str        # 最终答案
    # ... 任何其他需要追踪的状态
```

**节点（Nodes）**。每个节点都是一个接收当前状态作为输入、并返回一个更新后的状态作为输出的 Python 函数。节点是执行具体工作的单元。（LLM+TOOL）

```python
# 定义一个“规划者”节点函数
def planner_node(state: AgentState) -> AgentState:
    """根据当前任务制定计划，并更新状态。"""
    current_task = state["current_task"]
    # ... 调用LLM生成计划 ...
    plan = f"为任务 '{current_task}' 生成的计划..."
    
    # 将新消息追加到状态中
    state["messages"].append(plan)
    return state
# 定义一个“执行者”节点函数
def executor_node(state: AgentState) -> AgentState:
    """执行最新计划，并更新状态。"""
    latest_plan = state["messages"][-1]
    # ... 执行计划并获得结果 ...
    result = f"执行计划 '{latest_plan}' 的结果..."
    state["messages"].append(result)
    return state
```

**边（Edges）**。边负责连接节点，定义工作流的方向。最简单的边是常规边，它指定了一个节点的输出总是流向另一个固定的节点。而 LangGraph 最强大的功能在于**条件边（Conditional Edges）**。它通过一个函数来判断当前的状态，然后动态地决定下一步应该跳转到哪个节点。这正是实现循环和复杂逻辑分支的关键。

```python
def should_continue(state: AgentState) -> str:
    """条件函数：根据状态决定下一步路由。"""
    # 假设如果消息少于3条，则需要继续规划
    if len(state["messages"]) < 3:
        # 返回的字符串需要与添加条件边时定义的键匹配
        return "continue_to_planner"
    else:
        state["final_answer"] = state["messages"][-1]
        return "end_workflow"
```

**工作流**

```python
from langgraph.graph import StateGraph, END
# 初始化一个状态图，并绑定我们定义的状态结构
workflow = StateGraph(AgentState)
# 将节点函数添加到图中
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
# 设置图的入口点
workflow.set_entry_point("planner")
# 添加常规边，连接 planner 和 executor
workflow.add_edge("planner", "executor")
# 添加条件边，实现动态路由
workflow.add_conditional_edges(
    # 起始节点
    "executor",
    # 判断函数
    should_continue,
    # 路由映射：将判断函数的返回值映射到目标节点
    {
        "continue_to_planner": "planner", # 如果返回"continue_to_planner"，则跳回planner节点
        "end_workflow": END               # 如果返回"end_workflow"，则结束流程
    }
)
# 编译图，生成可执行的应用
app = workflow.compile()
# 运行图
inputs = {"current_task": "分析最近的AI行业新闻", "messages": []}
for event in app.stream(inputs):
    print(event)
```

# 4. MY Agent

```
hello-agents/
├── hello_agents/
│   │
│   ├── core/                     # 核心框架层
│   │   ├── agent.py              # Agent基类
│   │   ├── llm.py                # HelloAgentsLLM统一接口
│   │   ├── message.py            # 消息系统
│   │   ├── config.py             # 配置管理
│   │   └── exceptions.py         # 异常体系
│   │
│   ├── agents/                   # Agent实现层
│   │   ├── simple_agent.py       # SimpleAgent实现
│   │   ├── react_agent.py        # ReActAgent实现
│   │   ├── reflection_agent.py   # ReflectionAgent实现
│   │   └── plan_solve_agent.py   # PlanAndSolveAgent实现
│   │
│   ├── tools/                    # 工具系统层
│   │   ├── base.py               # 工具基类
│   │   ├── registry.py           # 工具注册机制
│   │   ├── chain.py              # 工具链管理系统
│   │   ├── async_executor.py     # 异步工具执行器
│   │   └── builtin/              # 内置工具集
│   │       ├── calculator.py     # 计算工具
│   │       └── search.py         # 搜索工具
└──
```

## 4.1工具系统

**工具的抽象类**

```python
class Tool(ABC):
    """工具基类"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    @abstractmethod
    def run(self, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        pass
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        pass
```

**工具的注册**

```python
class ToolRegistry:
    """HelloAgents工具注册表"""
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}
    def register_tool(self, tool: Tool):
        """注册Tool对象"""
        if tool.name in self._tools:
            print(f"⚠️ 警告:工具 '{tool.name}' 已存在，将被覆盖。")
        self._tools[tool.name] = tool
        print(f"✅ 工具 '{tool.name}' 已注册。")  
    def register_function(self, name: str, description: str, func: Callable[[str], str]):
        """
        直接注册函数作为工具（简便方式）
        Args:
            name: 工具名称
            description: 工具描述
            func: 工具函数，接受字符串参数，返回字符串结果
        """
        if name in self._functions:
            print(f"⚠️ 警告:工具 '{name}' 已存在，将被覆盖。")

        self._functions[name] = {
            "description": description,
            "func": func
        }
        print(f"✅ 工具 '{name}' 已注册。")
```

**使用：**functionCall

```python
# 步骤1：为每个LLM提供商定义函数
# OpenAI格式
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_github",
            "description": "搜索GitHub仓库",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    }
]
# Claude格式
claude_tools = [
    {
        "name": "search_github",
        "description": "搜索GitHub仓库",
        "input_schema": {  # 注意：不是parameters
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }
    }
]
# 步骤2：自己实现工具函数
def search_github(query):
    import requests
    response = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": query}
    )
    return response.json()
# 步骤3：处理不同模型的响应格式
# OpenAI的响应
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    result = search_github(**json.loads(tool_call.function.arguments))
# Claude的响应
if response.content[0].type == "tool_use":
    tool_use = response.content[0]
    result = search_github(**tool_use.input)
    
#OpenAI 标准完整分发逻辑
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    tool_name = tool_call.function.name  # 从响应获取LLM指定的工具名
    args = json.loads(tool_call.function.arguments)
    # 根据LLM返回的工具名，动态匹配对应函数执行
    target_func = tool_mapping[tool_name]
    result = target_func(**args)
```



# 5. 记忆

**why**

**（1）局限一：无状态导致的对话遗忘**

当前的大语言模型虽然强大，但设计上是**无状态的**。这意味着，每一次用户请求（或API调用）都是一次独立的、无关联的计算。模型本身不会自动“记住”上一次对话的内容。这带来了几个问题：

1. **上下文丢失**：在长对话中，早期的重要信息可能会因为上下文窗口限制而丢失
2. **个性化缺失**：Agent无法记住用户的偏好、习惯或特定需求
3. **学习能力受限**：无法从过往的成功或失败经验中学习改进
4. **一致性问题**：在多轮对话中可能出现前后矛盾的回答

让我们通过一个具体例子来理解这个问题：

要解决这个问题，我们的框架需要引入记忆系统。

**（2）局限二：模型内置知识的局限性**

除了遗忘对话历史，LLM 的另一个核心局限在于其知识是**静态的、有限的**。这些知识完全来自于它的训练数据，并因此带来一系列问题：

1. **知识时效性**：大模型的训练数据有时间截止点，无法获取最新信息
2. **专业领域知识**：通用模型在特定领域的深度知识可能不足
3. **事实准确性**：通过检索验证，减少模型的幻觉问题
4. **可解释性**：提供信息来源，增强回答的可信度

在实现上，我们将记忆和RAG设计为两个独立的工具：`memory_tool`负责存储和维护对话过程中的交互信息，`rag_tool`则负责从用户提供的知识库中检索相关信息作为上下文，并可将重要的检索结果自动存储到记忆系统中。

```
HelloAgents记忆系统
├── 基础设施层 (Infrastructure Layer)
│   ├── MemoryManager - 记忆管理器（统一调度和协调）
│   ├── MemoryItem - 记忆数据结构（标准化记忆项）
│   ├── MemoryConfig - 配置管理（系统参数设置）
│   └── BaseMemory - 记忆基类（通用接口定义）
├── 记忆类型层 (Memory Types Layer)
│   ├── WorkingMemory - 工作记忆（临时信息，TTL管理）
│   ├── EpisodicMemory - 情景记忆（具体事件，时间序列）
│   ├── SemanticMemory - 语义记忆（抽象知识，图谱关系）
│   └── PerceptualMemory - 感知记忆（多模态数据）
├── 存储后端层 (Storage Backend Layer)
│   ├── QdrantVectorStore - 向量存储（高性能语义检索）
│   ├── Neo4jGraphStore - 图存储（知识图谱管理）
│   └── SQLiteDocumentStore - 文档存储（结构化持久化）
└── 嵌入服务层 (Embedding Service Layer)
    ├── DashScopeEmbedding - 通义千问嵌入（云端API）
    ├── LocalTransformerEmbedding - 本地嵌入（离线部署）
    └── TFIDFEmbedding - TFIDF嵌入（轻量级兜底）
```

```
HelloAgents RAG系统
├── 文档处理层 (Document Processing Layer)
│   ├── DocumentProcessor - 文档处理器（多格式解析）
│   ├── Document - 文档对象（元数据管理）
│   └── Pipeline - RAG管道（端到端处理）
├── 嵌入表示层 (Embedding Layer)
│   └── 统一嵌入接口 - 复用记忆系统的嵌入服务
├── 向量存储层 (Vector Storage Layer)
│   └── QdrantVectorStore - 向量数据库（命名空间隔离）
└── 智能问答层 (Intelligent Q&A Layer)
    ├── 多策略检索 - 向量检索 + MQE + HyDE
    ├── 上下文构建 - 智能片段合并与截断
    └── LLM增强生成 - 基于上下文的准确问答
```

```
hello-agents/
├── hello_agents/
│   ├── memory/                   # 记忆系统模块
│   │   ├── base.py               # 基础数据结构（MemoryItem, MemoryConfig, BaseMemory）
│   │   ├── manager.py            # 记忆管理器（统一协调调度）
│   │   ├── embedding.py          # 统一嵌入服务（DashScope/Local/TFIDF）
│   │   ├── types/                # 记忆类型实现
│   │   │   ├── working.py        # 工作记忆（TTL管理，纯内存）
│   │   │   ├── episodic.py       # 情景记忆（事件序列，SQLite+Qdrant）
│   │   │   ├── semantic.py       # 语义记忆（知识图谱，Qdrant+Neo4j）
│   │   │   └── perceptual.py     # 感知记忆（多模态，SQLite+Qdrant）
│   │   ├── storage/              # 存储后端实现
│   │   │   ├── qdrant_store.py   # Qdrant向量存储（高性能向量检索）
│   │   │   ├── neo4j_store.py    # Neo4j图存储（知识图谱管理）
│   │   │   └── document_store.py # SQLite文档存储（结构化持久化）
│   │   └── rag/                  # RAG系统
│   │       ├── pipeline.py       # RAG管道（端到端处理）
│   │       └── document.py       # 文档处理器（多格式解析）
│   └── tools/builtin/            # 扩展内置工具
│       ├── memory_tool.py        # 记忆工具（Agent记忆能力）
│       └── rag_tool.py           # RAG工具（智能问答能力）
└──
```

```

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6NGRmZmY4M2ItZGUwNS00NzhiLTllZGItYzM1ODNkMzc5MjY3In0.FJGAA-SzXV9dFx3y-Aoe6SSpbz5TX7xM3efPO8A1_sY

https://82f785df-2c3b-4329-9f04-d4b59bd0c989.eu-central-1-0.aws.cloud.qdrant.io
```

```
Username:4638d7ef
Password:BQGbY40IVQI-W1ZFZO_pPpBNy7iXIOWnQ1QpU7N3fUg
```

**工作记忆 (Working Memory)**，它扮演着智能体“短期记忆”的角色，主要用于存储当前对话的上下文信息。为确保高速访问和响应，其容量被有意限制（例如，默认50条），并且生命周期与单个会话绑定，会话结束后便会自动清理。

**情景记忆 (Episodic Memory)**，它负责长期存储具体的交互事件和智能体的学习经历。与工作记忆不同，情景记忆包含了丰富的上下文信息，并支持按时间序列或主题进行回顾式检索，是智能体“复盘”和学习过往经验的基础。

与具体事件相对应的是**语义记忆 (Semantic Memory)**，它存储的是更为抽象的知识、概念和规则。例如，通过对话了解到的用户偏好、需要长期遵守的指令或领域知识点，都适合存放在这里。这部分记忆具有高度的持久性和重要性，是智能体形成“知识体系”和进行关联推理的核心。

最后，为了与日益丰富的多媒体交互，我们引入了**感知记忆 (Perceptual Memory)**。该模块专门处理图像、音频等多模态信息，并支持跨模态检索。其生命周期会根据信息的重要性和可用存储空间进行动态管理。

| 记忆类型         | 存储内容                     | 生命周期                     | 核心用途                               |
| ---------------- | ---------------------------- | ---------------------------- | -------------------------------------- |
| 工作记忆         | 当前会话对话文本             | 单次会话，会话结束清空       | 实时连贯对话、上下文理解               |
| 情景记忆episodic | 完整历史交互事件（带时间戳） | 长期持久，手动删除才销毁     | （计算机考研话题相关）                 |
| 语义记忆semantic | 抽象知识、用户偏好、固定规则 | 永久固化存储                 | 遵循用户固定要求（用户偏好，彩色风格） |
| 感知记忆         | 图片、音频、视频多模态素材   | 动态管理，低价值素材自动清理 | 跨模态交互、图文 / 音图检索            |

**增加记忆：**

```
会话ID的自动管理（确保每个记忆都有明确的会话归属）

多模态数据的智能处理（自动推断文件类型并保存相关元数据）：工作，情景，语义，感知

上下文信息的自动补充（为每个记忆添加时间戳和会话信息）：属于哪一个会话
```

（1）工作记忆（WorkingMemory）

工作记忆是记忆系统中最活跃的部分，它负责存储当前对话会话中的临时信息。工作记忆的设计重点在于快速访问和自动清理，这种设计确保了系统的响应速度和资源效率。工作记忆采用了纯内存存储方案，配合TTL（Time To Live）机制进行自动清理。

**工作记忆的检索**采用了混合检索策略，首先尝试使用**TF-IDF向量化进行语义检索**，如果失败则回退到**关键词**匹配。这种设计确保了在各种环境下都能提供可靠的检索服务。评分算法结合了语义相似度、时间衰减和重要性权重，最终得分公式为：`(相似度（向量化和关键词） × 时间衰减) × (0.8 + 重要性 × 0.4)`。

```
关键词实现简单、速度极快、不依赖模型，能精准命中字面完全一致的内容；但是无法理解语义，同义词、近义
TF-IDF 向量化检索（浅层语义匹配）TF (词频) - IDF (逆文档频率)
TF：某个词在单条记忆里出现次数；
IDF：词在全部记忆里稀有程度，生僻专业词权重更高，“你、我、好” 这类通用词权重压低；
优点：相比纯关键词，能区分词语重要程度，浅层捕捉文本主题；无需外部大模型，纯内存计算；
缺点：只基于词汇统计，不具备深层语义理解，无法跨语义匹配。

词：离散文字符号（语音、音频、图像）；
TF-IDF：计算规则，用来给词分配权重；
TF-IDF 值：单个词的权重数值；
TF-IDF 向量：一段文本所有词权重组成的多维数组，用来做余弦相似度计算。
```

（2）情景记忆（EpisodicMemory）

情景记忆负责存储具体的事件和经历，它的设计重点在于保持事件的完整性和时间序列关系。情景记忆采用了SQLite+Qdrant的混合存储方案，SQLite负责结构化数据的存储和复杂查询，Qdrant负责高效的向量检索。

**情景记忆的检索**实现展现了复杂的多因素评分机制。它不仅考虑了语义相似度，还加入了时间近因性的考量，最终通过重要性权重进行调节。评分公式为：`(向量相似度 × 0.8 + 时间近因性 × 0.2) × (0.8 + 重要性 × 0.4)`，确保检索结果既语义相关又时间相关。

```
只用 SQLite：只能关键词模糊匹配，无法语义检索，召回效果差；
只用 Qdrant：向量库不擅长复杂条件筛选（时间、会话、用户多条件联合过滤），过滤成本极高；
混合方案互补：
SQLite 负责结构化精确筛选，先筛出符合条件的候选记忆，缩小范围；
Qdrant 负责全局语义相似召回，在候选池内做精准语义匹配；
两者通过 episode_id 关联，各司其职。
```

```
为什么用情景记忆？ 因为这是一个具体的、有时间戳的事件，适合用情景记忆记录。session_id参数将这个事件关联到当前学习会话，便于后续回顾学习历程。
```

（3）语义记忆（SemanticMemory）

语义记忆是记忆系统中最复杂的部分，它负责存储抽象的概念、规则和知识。语义记忆的设计重点在于知识的结构化表示和智能推理能力。语义记忆采用了Neo4j图数据库和Qdrant向量数据库的混合架构，这种设计让系统既能进行快速的语义检索，又能利用知识图谱进行复杂的关系推理。

**语义记忆的检索**实现了混合搜索策略，结合了向量检索的语义理解能力和图检索的关系推理能力/语义记忆的评分公式为：`(向量相似度 × 0.7 + 图相似度 × 0.3) × (0.8 + 重要性 × 0.4)`。这种设计的核心思想是：

- **向量检索权重（0.7）**：语义相似度是主要因素，确保检索结果与查询语义相关
- **图检索权重（0.3）**：关系推理作为补充，发现概念间的隐含关联
- **重要性权重范围[0.8, 1.2]**：避免重要性过度影响相似度排序，保持检索的准确性
- NPLP能力：中英文文本自动抽取实体、识别主谓宾关系，用于**自动构建知识图谱**

（4）感知记忆（PerceptualMemory）

感知记忆支持文本、图像、音频等多种模态的数据存储和检索。它采用了模态分离的存储策略，为不同模态的数据创建独立的向量集合，这种设计避免了维度不匹配的问题，同时保证了检索的准确性。

**感知记忆的检索**支持同模态和跨模态两种模式。同模态检索利用专业的编码器进行精确匹配，而跨模态检索则需要更复杂的语义对齐机制。感知记忆的评分公式为：`(向量相似度 × 0.8 + 时间近因性 × 0.2) × (0.8 + 重要性 × 0.4)`。感知记忆的评分机制还支持跨模态检索，通过统一的向量空间实现文本、图像、音频等不同模态数据的语义对齐。当进行跨模态检索时，系统会自动调整评分权重，确保检索结果的多样性和准确性。此外，感知记忆中的时间近因性计算采用了指数衰减模型：

```
必须引入跨模态对齐模型做统一映射，代表就是 CLIP（图文）、CLAP（文音）。
2. 语义对齐机制是什么？
对齐模型（CLIP/CLAP）在海量图文 / 文音对联合训练，实现一个核心目标：
语义相近的不同模态数据，映射到同一个共享向量空间，向量距离可以代表跨模态语义相似度。
流程拆解（文搜图举例）：
输入文字送入 CLIP 文本分支 → 生成文本共享向量
库里图片全部由 CLIP 图像分支编码 → 图像共享向量
两类向量处在同一共享空间，距离越小代表画面和文字描述越匹配
```

Memory 是**智能体短期 / 长期记忆**（对话、视听感知记录，随会话 / 用户动态产生）

RAGTool 是**静态外部知识库**（PDF、文档、素材等业务固定资料，供问答查阅）

# 6. RAGTool

检索增强生成（Retrieval-Augmented Generation，RAG）是一种结合了信息检索和文本生成的技术。它的核心思想是：在生成回答之前，先从外部知识库中检索相关信息，然后将检索到的信息作为上下文提供给大语言模型，从而生成更准确、更可靠的回答。

一个完整的RAG应用流程主要分为两大核心环节。在**数据准备阶段**，系统通过**数据提取**、**文本分割**和**向量化**，将外部知识构建成一个可检索的数据库。随后在**应用阶段**，系统会响应用户的**提问**，从数据库中**检索**相关信息，将其**注入Prompt**，并最终驱动大语言模型**生成答案**。

（1）多模态文档载入：无论输入是PDF、Word、Excel、图片还是音频，最终都会转换为标准的Markdown格式，然后进入统一的分块、向量化和存储流程。

（2）智能分块策略：经过MarkItDown转换后，所有文档都统一为标准的Markdown格式。这为后续的智能分块提供了结构化的基础。HelloAgents实现了专门针对Markdown格式的智能分块策略，充分利用Markdown的结构化特性进行精确分割。**Markdown段落分割**的基础上，系统进一步根据**Token数量**进行智能分块。

（3）统一嵌入与向量存储：嵌入模型是RAG系统的核心，它负责将文本转换为高维向量，使得计算机能够理解和比较文本的语义相似性。RAG系统的检索能力很大程度上取决于嵌入模型的质量和向量存储的效率。HelloAgents实现了统一的嵌入接口。在这里为了演示，使用百炼API，如果尚未配置可以切换为本地的`all-MiniLM-L6-v2`模型，如果两种方案都不支持，也配置了TF-IDF算法来兜底。实际使用可以替换为自己想要的模型或者API，也可以尝试去扩展框架内容~

**高级检索策略：**

1）多查询扩展（MQE）

多查询扩展（Multi-Query Expansion）：同一个问题可以有多种不同的表述方式，而不同的表述可能匹配到不同的相关文档。例如，"如何学习Python"可以扩展为"Python入门教程"、"Python学习方法"、"Python编程指南"等多个查询。通过并行执行这些扩展查询并合并结果，系统能够覆盖更广泛的相关文档，避免因用词差异而遗漏重要信息。

（2）假设文档嵌入（HyDE）

假设文档嵌入（Hypothetical Document Embeddings，HyDE）：是"用答案找答案"。传统的检索方法是用问题去匹配文档，但问题和答案在语义空间中的分布往往存在差异——问题通常是疑问句，而文档内容是陈述句。HyDE通过让LLM先生成一个假设性的答案段落，然后用这个答案段落去检索真实文档，从而缩小了查询和文档之间的语义鸿沟。

3）扩展检索框架

HelloAgents将MQE和HyDE两种策略整合到统一的扩展检索框架中。系统通过`enable_mqe`和`enable_hyde`参数让用户可以根据具体场景选择启用哪些策略：对于需要高召回率的场景可以同时启用两种策略，对于性能敏感的场景可以只使用基础检索。

扩展检索的核心机制是"扩展-检索-合并"三步流程。首先，系统根据原始查询生成多个扩展查询（包括MQE生成的多样化查询和HyDE生成的假设文档）；然后，对每个扩展查询并行执行向量检索，获取候选文档池；最后，通过去重和分数排序合并所有结果，返回最相关的top-k文档。这种设计的巧妙之处在于，它通过`candidate_pool_multiplier`参数（默认为4）扩大候选池，确保有足够的候选文档进行筛选，同时通过智能去重避免返回重复内容。

# 7. 上下文工程

提示词：大多数用例（除日常聊天外）都需要针对单轮分类或文本生成做精调式的**提示优化**

上下文：需要管理**整个上下文状态**的策略——其中包括系统指令、工具、MCP（Model Context Protocol）、外部数据、消息历史等。一个循环运行的智能体，会不断产生下一轮推理可能相关的数据，这些信息必须被**周期性地提炼**。**不再预先加载所有相关数据，而是维护轻量化引用（文件路径、存储查询、URL 等），在运行时通过工具动态加载所需数据。**

- **上下文腐蚀（context rot）**——随着上下文窗口中的 tokens 增加，模型从上下文中准确回忆信息的能力反而下降。
- **上下文必须被视作一种有限资源，且具有边际收益递减**。每新增一个 token，都会消耗这笔预算的一部分，因此我们更需要谨慎地筛选哪些 tokens 应该被提供给 LLM。
  - 源自 LLM 的架构约束。Transformer 让每个 token 能够与上下文中的**所有** token 建立关联，理论上形成 (n^2) 级别的两两注意力关系。随着上下文长度增长，模型对这些两两关系的建模能力会被“拉薄”，从而自然地产生“上下文规模”与“注意力集中度”的张力。

**用尽可能少、但高信号密度的 tokens，最大化获得期望结果的概率**。

- **系统提示（System Prompt）**：。常见两极误区：
  - 过度硬编码：在提示中写入复杂、脆弱的 if-else 逻辑，长期维护成本高、易碎。
  - 过于空泛：只给出宏观目标，缺少对期望输出的**具体信号**或假定了错误的“共享上下文”。 建议将提示分区组织（背景、工具指引、输出描述等）。
- **工具（Tools）**：
  - 职责单一、相互低重叠，接口语义清晰；
  - 入参描述明确、无歧义，充分发挥模型擅长的表达与推理能力。 

**混合策略**更有效：前置加载少量“高价值”上下文以保证速度，然后允许智能体按需继续自主探索。边界的选择取决于任务动态性与时效要求。在工程上，可以预先放入类似“项目约定说明（如 README/指南）”的文件，同时提供 `glob`、`grep` 等原语，让智能体即时检索具体文件，从而绕开过时索引与复杂语法树的沉没成本。

```python
import glob
# 获取当前全部json文件
files = glob.glob("*.json")
# 递归查找所有子目录下md文件
all_md = glob.glob("**/*.md", recursive=True)

# 在 agent.py 里查找包含 add_note 的所有行
grep "add_note" agent.py
```

## 7.1面向长时程任务的上下文工程

长时程任务要求智能体在超出上下文窗口的长序列行动中，仍能保持连贯性、上下文一致与目标导向。例如大型代码库迁移、跨数小时的系统性研究。指望无限增大上下文窗口并不能根治“上下文污染”与相关性退化的问题，因此需要直接面向这些约束的工程手段：**压缩整合（Compaction）**、**结构化笔记（Structured note-taking）**与**子代理架构（Sub-agent architectures）**。

- **压缩整合（Compaction）**
  - 定义：当对话接近上下文上限时，对其进行高保真总结，并用该摘要重启一个新的上下文窗口，以维持长程连贯性。
  - 实践：让模型压缩并保留架构性决策、未解决缺陷、实现细节，丢弃重复的工具输出与噪声；新窗口携带压缩摘要 + 最近少量高相关工件（如“最近访问的若干文件”）。
  - 调参建议：先优化**召回**（确保不遗漏关键信息），再优化**精确度**（剔除冗余内容）；一种安全的“轻触式”压缩是对“深历史中的工具调用与结果”进行清理。
- **结构化笔记（Structured note-taking）**
  - 定义：也称“智能体记忆”。智能体以固定频率将关键信息写入**上下文外的持久化存储**，在后续阶段按需拉回。
  - 价值：以极低的上下文开销维持持久状态与依赖关系。例如维护 TODO 列表、项目 NOTES.md、关键结论/依赖/阻塞项的索引，跨数十次工具调用与多轮上下文重置仍能保持进度与一致性。
  - 说明：在非编码场景中同样有效（如长期策略性任务、游戏/仿真中的目标管理与统计计数）。结合第八章的 `MemoryTool`，可轻松实现文件式/向量式的外部记忆并在运行时检索。
- **子代理架构（Sub-agent architectures）**
  - 思想：由主代理负责高层规划与综合，多个专长子代理在“干净的上下文窗口”中各自深挖、调用工具并探索，最后仅回传**凝练摘要**（常见 1,000–2,000 tokens）。
  - 好处：实现关注点分离。庞杂的搜索上下文留在子代理内部，主代理专注于整合与推理；适合需要并行探索的复杂研究/分析任务。
  - 经验：公开的多智能体研究系统显示，该模式在复杂研究任务上相较单代理基线具有显著优势。

方法取舍可以遵循以下经验法则：

- **压缩整合**：适合需要长对话连续性的任务，强调上下文的“接力”。
- **结构化笔记**：适合有里程碑/阶段性成果的迭代式开发与研究。
- **子代理架构**：适合复杂研究与分析，能从并行探索中获益。

即便模型能力持续提升，“在长交互中维持连贯性与聚焦”仍是构建强健智能体的核心挑战。谨慎而系统的上下文工程将长期保持其关键价值。

## 7.2 ContextBuilder 

一个优秀的上下文管理系统应该解决以下几个关键问题：

1. **统一入口**：将"获取(Gather)- 选择(Select)- 结构化(Structure)- 压缩(Compress)"抽象为可复用流水线，减少在 Agent 实现中的重复模板代码。这种统一的接口设计让开发者无需在每个 Agent 中重复编写上下文管理逻辑。
2. **稳定形态**：输出固定骨架的上下文模板，便于调试、A/B 测试与评估。我们采用了分区组织的模板结构：
   - `[Role & Policies]`：明确 Agent 的角色定位和行为准则
   - `[Task]`：当前需要完成的具体任务
   - `[State]`：Agent 的当前状态和上下文信息
   - `[Evidence]`：从外部知识库检索的证据信息
   - `[Context]`：历史对话和相关记忆
   - `[Output]`：期望的输出格式和要求
3. **预算守护**：在 token 预算内尽量保留高价值信息，对超限上下文提供兜底压缩策略。这确保了即使在信息量巨大的场景下，系统也能稳定运行。
4. **最小规则**：不引入来源/优先级等分类维度，避免复杂度增长。实践表明，基于相关性和新近性的简单评分机制，在大多数场景下已经足够有效。

 GSSC(Gather-Select-Structure-Compress)流水线，它将上下文构建过程分解为四个清晰的阶段。让我们深入了解每个阶段的实现细节。

（1）Gather：多源信息汇集

```python
def _gather() -> List[ContextPacket]:
    """汇集所有候选信息
    Args:
        user_query: 用户查询
        conversation_history: 对话历史
        system_instructions: 系统指令
        custom_packets: 自定义信息包
    Returns:
        List[ContextPacket]: 候选信息列表
    """
    packets = []
    # 1. 添加系统指令(最高优先级,不参与评分)
    # 2. 从记忆系统检索相关记忆
    # 3. 从 RAG 系统检索相关知识
    # 4. 添加对话历史(仅保留最近的 N 条)
    # 5. 添加自定义信息包
    if custom_packets:
        packets.extend(custom_packets)

    print(f"[ContextBuilder] 汇集了 {len(packets)} 个候选信息包")
    return packets
```

（2）Select：智能信息选择

```python
def _select() -> List[ContextPacket]:
    """选择最相关的信息包
    Args:
        packets: 候选信息包列表
        user_query: 用户查询(用于计算相关性)
        available_tokens: 可用的 token 数量

    Returns:
        List[ContextPacket]: 选中的信息包列表
    """
    # 1. 分离系统指令和其他信息
    system_packets = [p for p in packets if p.metadata.get("type") == "system_instruction"]
    other_packets = [p for p in packets if p.metadata.get("type") != "system_instruction"]
    # 2. 计算系统指令占用的 token
    # 3. 为其他信息计算综合分数
    for packet in other_packets:
        # 计算相关性分数(如果尚未计算)
        # 计算新近性分数
        # 综合分数 = 相关性权重 × 相关性 + 新近性权重 × 新近性
        # 过滤低于最小相关性阈值的信息
    # 4. 按分数降序排序
    # 5. 贪心选择:按分数从高到低填充,直到达到 token 上限
```

（3）Structure：结构化输出

```python
def _structure(self, selected_packets: List[ContextPacket], user_query: str) -> str:
    """将选中的信息包组织成结构化的上下文模板
    Args:
        selected_packets: 选中的信息包列表
        user_query: 用户查询
    Returns:
        str: 结构化的上下文字符串
    """
    # 按类型分组
    system_instructions = []
    evidence = []
    context = []
    # 构建结构化模板
    sections = []
    # [Role & Policies]
    if system_instructions:
        sections.append("[Role & Policies]\n" + "\n".join(system_instructions))
    # [Task]
    sections.append(f"[Task]\n{user_query}")
    # [Evidence]，rag知识和memory
    if evidence:
        sections.append("[Evidence]\n" + "\n---\n".join(evidence))
    # [Context]，上下文对话历史
    if context:
        sections.append("[Context]\n" + "\n".join(context))
    # [Output]
    sections.append("[Output]\n请基于以上信息,提供准确、有据的回答。")
    return "\n\n".join(sections)
```

（4）Compress：兜底压缩

```python
def _compress(self, context: str, max_tokens: int) -> str:
    """压缩超限的上下文
    Args:
        context: 原始上下文
        max_tokens: 最大 token 限制
    Returns:
        str: 压缩后的上下文
    """
    current_tokens = self._count_tokens(context)
    if current_tokens <= max_tokens:
        return context  # 无需压缩
    print(f"[ContextBuilder] 上下文超限({current_tokens} > {max_tokens}),执行压缩")
    # 分区压缩:保持结构完整性
        if current_total + section_tokens <= max_tokens:
            # 完整保留
        else:
            # 部分保留
    print(f"[ContextBuilder] 压缩完成: {current_tokens} -> {final_tokens} tokens")

    return compressed_context
```

## 7.3 NoteTool

**NoteTool 是为"长时程任务"提供的结构化外部记忆组件。它以 Markdown 文件作为载体，头部使用 YAML 前置元数据记录关键信息，正文用于记录状态、结论、阻塞与行动项等内容。这种设计结合了人类可读性、版本控制友好性和易于回注上下文的特性，是构建长时程智能体的重要工具。**

NoteTool 采用了 Markdown + YAML 的混合格式，这种设计兼顾了结构化和可读性。

```yaml
---
id: note_20250119_153000_0
title: 项目进展 - 第一阶段
---
# 项目进展 - 第一阶段
已完成数据模型层的重构,主要改动包括:

## 测试覆盖

## 下一步计划
```

NoteTool 维护一个 `notes_index.json` 文件，用于快速检索和管理笔记：

```json
{
  "note_20250119_153000_0": {
    "id": "note_20250119_153000_0",
    "title": "项目进展 - 第一阶段",
    "type": "task_state",
    "tags": ["refactoring", "phase1", "backend"],
    "created_at": "2025-01-19T15:30:00",
    "updated_at": "2025-01-19T15:30:00",
    "file_path": "./notes/note_20250119_153000_0.md"
  }
}
```

NoteTool 提供了七个核心操作，覆盖了笔记的完整生命周期管理。

（1）create：创建笔记（4）search：搜索笔记

（2）read：读取笔记（5）list：列出笔记

（3）update：更新笔记（6）summary：笔记摘要（7）delete：删除笔记

```python
def _read_note(self, note_id: str) -> Dict:
    """读取笔记内容

    Args:
        note_id: 笔记ID
    Returns:
        Dict: 包含元数据和内容的字典
    """
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # 解析 YAML 元数据和 Markdown 正文
    metadata, content = self._parse_markdown(raw_content)
    return {
        "metadata": metadata,
        "content": content
    }
def _parse_markdown(self, raw_content: str) -> Tuple[Dict, str]:
    """解析 Markdown 文件(分离 YAML 和正文)"""
    import yaml

    # 查找 YAML 分隔符
    parts = raw_content.split('---\n', 2)

    if len(parts) >= 3:
        # 有 YAML 前置元数据
        yaml_str = parts[1]
        content = parts[2].strip()
        metadata = yaml.safe_load(yaml_str)
    else:
        # 无元数据,全部作为正文
        metadata = {}
        content = raw_content.strip()

    return metadata, content
```

## 7.4 TerminalTool：即时文件系统访问

智能体需要**即时访问和探索文件系统**——查看日志文件、分析代码库结构、检索配置文件等

**需要实时、轻量级的文件系统访问，而不是预先索引和向量化**。TerminalTool 正是为这种"探索式"工作流设计的。

TerminalTool 为智能体提供了**安全的命令行执行能力**，支持常用的文件系统和文本处理命令，同时通过多层安全机制确保系统安全。这种设计实现了 9.2.2 节提到的"即时(Just-in-time, JIT)上下文"理念——智能体不需要预先加载所有文件，而是按需探索和检索。

```yaml
# 传统方式:预先索引所有文件(成本高、可能过时)
rag_tool.add_document("./project/**/*.py")  # 耗时、占用大量存储

# TerminalTool 方式:即时探索

#find 实时遍历目录，当场列出所有源码文件，实时最新，无过期问题。
terminal.run({"command": "find . -name '*.py' -type f"})  # 快速、实时
#实时递归搜索所有文件内容，只返回包含目标类名的文件 + 对应行。
terminal.run({"command": "grep -r 'class UserService' ."})  # 精确定位
#定位到目标文件后，按需读取前 50 行，只加载当前需要查看的代码，不读取整个文件。
terminal.run({"command": "head -n 50 src/services/user.py"})  # 按需查看

# 检查日志文件大小,列出文件信息
terminal.run({"command": "ls -lh /var/log/app.log"})
# 查看最新的错误日志,tail 读取文件末尾，-n 100 只取最后 100 行，日志文件动辄几百 MB，不用加载全量。
terminal.run({"command": "tail -n 100 /var/log/app.log | grep ERROR"})
# 统计错误类型分布,提取所有带 ERROR 的日志行；
terminal.run({"command": "grep ERROR /var/log/app.log | cut -d':' -f3 | sort | uniq -c"})

# 查看 CSV 文件的前几行,只读取文件前 5 行
terminal.run({"command": "head -n 5 data/sales.csv"})
# 统计行数,word count统计文本行数
terminal.run({"command": "wc -l data/*.csv"})
# 查看列名,| 管道，把表头传给后面命令tr ',' '\n'：tr 字符替换工具，把逗号 , 全部替换成换行符
terminal.run({"command": "head -n 1 data/sales.csv | tr ',' '\n'"})
```

```yaml
ALLOWED_COMMANDS = {
    # 文件列表与信息
    'ls', 'dir', 'tree',
    # 文件内容查看
    'cat', 'head', 'tail', 'less', 'more',
    # 文件搜索
    'find', 'grep', 'egrep', 'fgrep',
    # 文本处理
    'wc', 'sort', 'uniq', 'cut', 'awk', 'sed',
    # 目录操作
    'pwd', 'cd',
    # 文件信息
    'file', 'stat', 'du', 'df',
    # 其他
    'echo', 'which', 'whereis',
}
```

TerminalTool 通过多层安全机制确保系统安全：

**第一层：命令白名单**只允许安全的只读命令，完全禁止任何可能修改系统的操作：

**第二层：工作目录限制(沙箱)**TerminalTool 只能访问指定的工作目录及其子目录，无法访问系统其他部分：

**第三层：超时控制**每个命令都有执行时间限制，防止无限循环或资源耗尽：

**第四层：输出大小限制**限制命令输出的大小，防止内存溢出：

# 8. 智能体通信

**通信协议的核心价值**正是解决这些问题。它提供了一套标准化的接口规范，让智能体能够以统一的方式访问各种外部服务，而无需为每个服务编写专门的适配器。这就像互联网的 TCP/IP 协议，它让不同的设备能够相互通信，而不需要为每种设备编写专门的通信代码。

- 如果你的智能体需要访问外部服务（文件、数据库、API），选择**MCP**
- 如果你需要多个智能体相互协作完成任务，选择**A2A**
- 如果你要构建大规模的智能体生态系统，考虑**ANP**

## 8.1 MCP

**三层架构的职责：**

1. **Host（宿主层）**：Claude Desktop 作为 Host，负责接收用户提问并与 Claude 模型交互。Host 是用户直接交互的界面，它管理整个对话流程。
2. **Client（客户端层）**：当 Claude 模型决定需要访问文件系统时，Host 中内置的 MCP Client 被激活。Client 负责与适当的 MCP Server 建立连接，发送请求并接收响应。
3. **Server（服务器层）**：文件系统 MCP Server 被调用，执行实际的文件扫描操作，访问桌面目录，并返回找到的文档列表。

**完整的交互流程：**用户问题 → Claude Desktop(Host) → Claude 模型分析 → 需要文件信息 → MCP Client 连接 → 文件系统 MCP Server → 执行操作 → 返回结果 → Claude 生成回答 → 显示在 Claude Desktop 上

```python
from hello_agents.protocols import MCPClient

# 步骤1：连接到社区提供的MCP服务器（无需自己实现）
github_client = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-github"
])
fs_client = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-filesystem", "."
])
# 步骤2：统一的调用方式（与模型无关）
async with github_client:
    # 自动发现工具
    tools = await github_client.list_tools()

    # 调用工具（标准化接口）
    result = await github_client.call_tool(
        "search_repositories",
        {"query": "AI agents"}
    )
# 步骤3：任何支持MCP的模型都能使用
# OpenAI、Claude、Llama等都使用相同的MCP客户端
```

```
# 用户代码
fs_tool = MCPTool(name="fs", server_command=[...])
agent.add_tool(fs_tool)

# 内部发生的事情：
# 1. MCPTool连接到服务器，发现14个工具
# 2. 为每个工具创建包装器：
#    - fs_read_text_file (参数: path, tail, head)
#    - fs_write_file (参数: path, content)
#    - ...
# 3. 注册到Agent的工具注册表

# Agent调用
response = agent.run("读取README.md")

# Agent内部：
# 1. 识别需要调用 fs_read_text_file
# 2. 生成参数：path=README.md
# 3. 包装器转换为MCP格式：
#    {"action": "call_tool", "tool_name": "read_text_file", "arguments": {"path": "README.md"}}
# 4. 调用MCP服务器
# 5. 返回文件内容
```

```python
class MCPTool(Tool):
    """MCP (Model Context Protocol) 工具

    连接到 MCP 服务器并调用其提供的工具、资源和提示词。
    
    功能：
    - 列出服务器提供的工具
    - 调用服务器工具
    - 读取服务器资源
    - 获取提示词模板

    """
    
    def __init__(self,
                 name: str = "mcp",
                 description: Optional[str] = None,
                 server_command: Optional[List[str]] = None,
                 server_args: Optional[List[str]] = None,
                 server: Optional[Any] = None,
                 auto_expand: bool = True,
                 env: Optional[Dict[str, str]] = None,
                 env_keys: Optional[List[str]] = None):
        """
        初始化 MCP 工具

        Args:
            name: 工具名称（默认为"mcp"，建议为不同服务器指定不同名称）
            description: 工具描述（可选，默认为通用描述）
            server_command: 服务器启动命令（如 ["python", "server.py"]）
            server_args: 服务器参数列表
            server: FastMCP 服务器实例（可选，用于内存传输）
            auto_expand: 是否自动展开为独立工具（默认True）
            env: 环境变量字典（优先级最高，直接传递给MCP服务器）
            env_keys: 要从系统环境变量加载的key列表（优先级中等）

        环境变量优先级（从高到低）：
            1. 直接传递的env参数
            2. env_keys指定的环境变量
            3. 自动检测的环境变量（根据server_command）

        注意：如果所有参数都为空，将创建内置演示服务器
        """

    def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行 MCP 操作

        Args:
            parameters: 包含以下参数的字典
                - action: 操作类型 (list_tools, call_tool, list_resources, read_resource, list_prompts, get_prompt)
                  如果不指定action但指定了tool_name，会自动推断为call_tool
                - tool_name: 工具名称（call_tool 需要）
                - arguments: 工具参数（call_tool 需要）
                - uri: 资源 URI（read_resource 需要）
                - prompt_name: 提示词名称（get_prompt 需要）
                - prompt_arguments: 提示词参数（get_prompt 可选）

        Returns:
            操作结果
        """
        from hello_agents.protocols.mcp.client import MCPClient

        # 智能推断action：如果没有action但有tool_name，自动设置为call_tool
        action = parameters.get("action", "").lower()
        if not action and "tool_name" in parameters:
            action = "call_tool"
            parameters["action"] = action

        if not action:
            return "错误：必须指定 action 参数或 tool_name 参数"
        
        try:
            # 使用增强的异步客户端
            import asyncio
            from hello_agents.protocols.mcp.client import MCPClient

            async def run_mcp_operation():
                # 根据配置选择客户端创建方式
                if self.server:
                    # 使用内置服务器（内存传输）
                    client_source = self.server
                else:
                    # 使用外部服务器命令
                    client_source = self.server_command

                async with MCPClient(client_source, self.server_args, env=self.env) as client:
                    if action == "list_tools":
                        tools = await client.list_tools()
                        if not tools:
                            return "没有找到可用的工具"
                        result = f"找到 {len(tools)} 个工具:\n"
                        for tool in tools:
                            result += f"- {tool['name']}: {tool['description']}\n"
                        return result

                    elif action == "call_tool":
                        tool_name = parameters.get("tool_name")
                        arguments = parameters.get("arguments", {})
                        if not tool_name:
                            return "错误：必须指定 tool_name 参数"
                        result = await client.call_tool(tool_name, arguments)
                        return f"工具 '{tool_name}' 执行结果:\n{result}"

                    elif action == "list_resources":
                        resources = await client.list_resources()
                        if not resources:
                            return "没有找到可用的资源"
                        result = f"找到 {len(resources)} 个资源:\n"
                        for resource in resources:
                            result += f"- {resource['uri']}: {resource['name']}\n"
                        return result

                    elif action == "read_resource":
                        uri = parameters.get("uri")
                        if not uri:
                            return "错误：必须指定 uri 参数"
                        content = await client.read_resource(uri)
                        return f"资源 '{uri}' 内容:\n{content}"

                    elif action == "list_prompts":
                        prompts = await client.list_prompts()
                        if not prompts:
                            return "没有找到可用的提示词"
                        result = f"找到 {len(prompts)} 个提示词:\n"
                        for prompt in prompts:
                            result += f"- {prompt['name']}: {prompt['description']}\n"
                        return result

                    elif action == "get_prompt":
                        prompt_name = parameters.get("prompt_name")
                        prompt_arguments = parameters.get("prompt_arguments", {})
                        if not prompt_name:
                            return "错误：必须指定 prompt_name 参数"
                        messages = await client.get_prompt(prompt_name, prompt_arguments)
                        result = f"提示词 '{prompt_name}':\n"
                        for msg in messages:
                            result += f"[{msg['role']}] {msg['content']}\n"
                        return result

                    else:
                        return f"错误：不支持的操作 '{action}'"

# 运行异步操作asyncio 循环线程隔离
#一个线程只能拥有一个正在运行的事件循环，主线程有循环时，主线程内部不能再开新循环；只能新建线程，每个线程持有自己独立 loop。
            try:
                # 检查是否已有运行中的事件循环
                try:
                    loop = asyncio.get_running_loop()
                    # 如果有运行中的循环，在新线程中运行新的事件循环
                    import concurrent.futures
                    import threading

                    def run_in_thread():
                        # 在新线程中创建新的事件循环
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(run_mcp_operation())
                        finally:
                            new_loop.close()

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        return future.result()
                except RuntimeError:
                    # 没有运行中的循环，直接运行
                    return asyncio.run(run_mcp_operation())
            except Exception as e:
                return f"异步操作失败: {str(e)}"
                    
        except Exception as e:
            return f"MCP 操作失败: {str(e)}"
```



## 8.2 A2A

MCP 协议解决了智能体与工具的交互，而 A2A 协议则解决智能体之间的协作问题。在一个需要多智能体（如研究员、撰写员、编辑）协作的任务中，它们需要通信、委托任务、协商能力和同步状态。

```python
from hello_agents.protocols.a2a.implementation import A2AServer, A2A_AVAILABLE

def create_calculator_agent():
    print("🧮 创建计算器智能体")

    # 创建 A2A 服务器
    calculator = A2AServer(
        name="calculator-agent",
        description="专业的数学计算智能体",
        version="1.0.0",
        capabilities={
            "math": ["addition", "subtraction", "multiplication", "division"],
            "advanced": ["power", "sqrt", "factorial"]
        }
    )

    # 添加基础计算技能
    @calculator.skill("add")
    def add_numbers(query: str) -> str:
        """加法计算"""
        try:
            # 简单解析 "计算 5 + 3" 格式
            parts = query.replace("计算", "").replace("加", "+").replace("加上", "+")
            if "+" in parts:
                numbers = [float(x.strip()) for x in parts.split("+")]
                result = sum(numbers)
                return f"计算结果: {' + '.join(map(str, numbers))} = {result}"
            else:
                return "请使用格式: 计算 5 + 3"
        except Exception as e:
            return f"计算错误: {e}"

    @calculator.skill("multiply")
    def multiply_numbers(query: str) -> str:
        """乘法计算"""
        try:
            parts = query.replace("计算", "").replace("乘以", "*").replace("×", "*")
            if "*" in parts:
                numbers = [float(x.strip()) for x in parts.split("*")]
                result = 1
                for num in numbers:
                    result *= num
                return f"计算结果: {' × '.join(map(str, numbers))} = {result}"
            else:
                return "请使用格式: 计算 5 * 3"
        except Exception as e:
            return f"计算错误: {e}"

    @calculator.skill("info")
    def get_info(query: str) -> str:
        """获取智能体信息"""
        return f"我是 {calculator.name}，可以进行基础数学计算。支持的技能: {list(calculator.skills.keys())}"

    print(f"✅ 计算器智能体创建成功，支持技能: {list(calculator.skills.keys())}")
    return calculator
# 创建智能体
calc_agent = create_calculator_agent()
if calc_agent:
    # 测试技能
    print("\n🧪 测试智能体技能:")
    test_queries = [
        "获取信息",
        "计算 10 + 5",
        "计算 6 * 7"
    ]
    for query in test_queries:
        if "信息" in query:
            result = calc_agent.skills["info"](query)
        elif "+" in query:
            result = calc_agent.skills["add"](query)
        elif "*" in query or "×" in query:
            result = calc_agent.skills["multiply"](query)
        else:
            result = "未知查询类型"

        print(f"  📝 查询: {query}")
        print(f"  🤖 回复: {result}")
        print()
```

A2A 请求生命周期是一个序列，详细说明了请求遵循的四个主要步骤：代理发现、身份验证、发送消息 API 和发送消息流 API。下图 10.8 借鉴了官网的流程图，用来展示了操作流程，说明了客户端、A2A 服务器和身份验证服务器之间的交互。

`客户端 ↔ A2A 服务端：代理发现，获取 Agent 能力与地址`

`客户端 ↔ 认证服务器：获取访问 Token`

`客户端 → A2A 服务端：携带 Token 调用**单次消息 API**，同步获取结果`

`客户端 → A2A 服务端：携带 Token 建立长连接调用**消息流 API**，分段接收输出`

## 8.3 ANP 协议实战

在 MCP 协议解决了工具调用、A2A 协议解决点对点智能体协作之后，ANP 协议则专注于解决大规模、开放网络环境下的智能体管理问题。

当一个网络中存在大量功能各异的智能体（例如，自然语言处理、图像识别、数据分析等）时，系统会面临一系列挑战：

- **服务发现**：当新任务到达时，如何快速找到能够处理该任务的智能体？
- **智能路由**：如果多个智能体都能处理同一任务，如何选择最合适的一个（如根据负载、成本等）并向其分派任务？
- **动态扩展**：如何让新加入网络的智能体被其他成员发现和调用？

**1. 服务的发现与匹配：**首先，智能体 A 通过一个公开的发现服务，基于语义或功能描述进行查询，以定位到符合其任务需求的智能体 B。该发现服务通过预先爬取各智能体对外暴露的标准端点（`.well-known/agent-descriptions`）来建立索引，从而实现服务需求方与提供方的动态匹配。

**2. 基于 DID 的身份验证：**在交互开始时，智能体 A 使用其私钥对包含自身 DID 的请求进行签名。智能体 B 收到后，通过解析该 DID 获取对应的公钥，并以此验证签名的真实性与请求的完整性，从而建立起双方的可信通信。

**3. 标准化的服务执行：**身份验证通过后，智能体 B 响应请求，双方依据预定义的标准接口和数据格式进行数据交换或服务调用（如预订、查询等）。标准化的交互流程是实现跨平台、跨系统互操作性的基础。

总而言之，该机制的核心是利用 DID 构建了一个去中心化的信任根基，并借助标准化的描述协议实现了服务的动态发现。这套方法使得智能体能够在无需中央协调的前提下，安全、高效地在互联网上形成协作网络。

```python
from hello_agents.protocols import ANPDiscovery, register_service
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools.builtin import ANPTool
import random
from dotenv import load_dotenv

load_dotenv()
llm = HelloAgentsLLM()

# 1. 创建服务发现中心
discovery = ANPDiscovery()

# 2. 注册多个计算节点
for i in range(10):
    register_service(
        discovery=discovery,
        service_id=f"compute_node_{i}",
        service_name=f"计算节点{i}",
        service_type="compute",
        capabilities=["data_processing", "ml_training"],
        endpoint=f"http://node{i}:8000",
        metadata={
            "load": random.uniform(0.1, 0.9),
            "cpu_cores": random.choice([4, 8, 16]),
            "memory_gb": random.choice([16, 32, 64]),
            "gpu": random.choice([True, False])
        }
    )

print(f"✅ 注册了 {len(discovery.list_all_services())} 个计算节点")

# 3. 创建任务调度Agent
scheduler = SimpleAgent(
    name="任务调度器",
    llm=llm,
    system_prompt="""你是一个智能任务调度器，负责：
1. 分析任务需求
2. 选择最合适的计算节点
3. 分配任务

选择节点时考虑：负载、CPU核心数、内存、GPU等因素。"""
)

# 添加ANP工具
anp_tool = ANPTool(
    name="service_discovery",
    description="服务发现工具，可以查找和选择计算节点",
    discovery=discovery
)
scheduler.add_tool(anp_tool)

# 4. 智能任务分配
def assign_task(task_description):
    print(f"\n任务：{task_description}")
    print("=" * 50)

    # 让Agent智能选择节点
    response = scheduler.run(f"""
    请为以下任务选择最合适的计算节点：
    {task_description}

    要求：
    1. 列出所有可用节点
    2. 分析每个节点的特点
    3. 选择最合适的节点
    4. 说明选择理由
    """)

    print(response)
    print("=" * 50)

# 测试不同类型的任务
assign_task("训练一个大型深度学习模型，需要GPU支持")
assign_task("处理大量文本数据，需要高内存")
assign_task("运行轻量级数据分析任务")
```

# 9. Agentic-RL

传统的监督学习方法存在三个核心局限:一是数据质量完全决定训练质量，模型只能模仿训练数据，难以超越;二是缺乏探索能力，只能被动学习人类提供的路径;三是难以优化长期目标，无法精确优化多步推理的中间过程。

强化学习提供了新的可能性。通过让智能体自主生成多个候选答案并根据正确性获得奖励，它可以学习哪些推理路径更优、哪些步骤是关键，甚至发现比人类标注更好的解题方法[8]。这就是 Agentic RL 的核心思想:将 LLM 作为可学习策略，嵌入智能体的感知-决策-执行循环，通过强化学习优化多步任务表现。

## 9.1**LLM 训练全景图**

![image-20260630144919397](C:\Users\31461\AppData\Roaming\Typora\typora-user-images\image-20260630144919397.png)

- **预训练阶段**是 LLM 训练的第一阶段，目标是让模型学习语言的基本规律和世界知识。这个阶段使用海量的文本数据(通常是数 TB 级别)，通过自监督学习的方式训练模型：训练信号来自文本本身，例如根据上文预测下一个词。
- **后训练阶段**则是要解决预训练模型的不足。预训练后的模型虽然具备了强大的语言能力，但它只是一个"预测下一个词"的模型，并不知道如何遵循人类的指令、生成有帮助无害诚实的回答、拒绝不当的请求，以及以对话的方式与人交互。后训练阶段就是要解决这些问题，让模型对齐人类的偏好和价值观。
  - **监督微调(SFT，Supervised Fine-Tuning)**[15]，目标是让模型学会遵循指令和对话格式。训练数据是(prompt， completion)(输入，期望输出)对，训练目标与预训练类似，仍然是最大化正确输出的概率:
  - **奖励建模(RM)**。SFT 后的模型虽然能遵循指令，但生成的回答质量参差不齐。我们需要一种方式来评估回答的质量，这就是奖励模型的作用[13,14]。奖励模型的训练数据是偏好对比数据,包含同一个问题的两个回答,一个更好(chosen),一个更差(rejected)。奖励模型的训练目标是学习人类的偏好。输入是(提示，回答)对，输出是质量分数;$y_w$ 是更好的回答(chosen)，$y_l$ 是更差的回答(rejected)，$\sigma$ 是 sigmoid 函数，目标是让奖励模型给更好的回答更高的分数。
  - **强化学习微调**。有了奖励模型后，我们就可以用强化学习来优化语言模型，让它生成更高质量的回答。![image-20260630145314059](C:\Users\31461\AppData\Roaming\Typora\typora-user-images\image-20260630145314059.png)

**传统的后训练**(我们称之为 PBRFT: Preference-Based Reinforcement Fine-Tuning)主要关注单轮对话的质量优化:给定一个用户问题，模型生成一个回答，然后根据回答的质量获得奖励。这种方式适合优化对话助手，但对于需要多步推理、工具使用、长期规划的智能体任务来说，就显得力不从心了。

**Agentic RL**则是一种新的范式，它将 LLM 视为一个可学习的策略，嵌入在一个顺序决策循环中。在这个框架下，智能体需要在动态环境中与外部世界交互，执行多步行动来完成复杂任务，获得中间反馈来指导后续决策，优化长期累积奖励而非单步奖励。

- 在 PBRFT 场景中，用户问"请解释什么是强化学习"，模型生成完整回答，然后根据回答质量直接给分。而在 Agentic RL 场景中，用户请求"帮我分析这个 GitHub 仓库的代码质量"，智能体需要经历多个步骤:首先调用 GitHub API 获取仓库信息，成功获得仓库结构和文件列表，得到+0.1 的奖励;然后读取主要代码文件，成功获得代码内容，得到+0.1 的奖励;接着分析代码质量合理，得到+0.2 的奖励;最后生成分析报告质量高，得到+0.6 的奖励。总奖励是所有步骤的累积:1.0。

![image-20260630152016080](C:\Users\31461\AppData\Roaming\Typora\typora-user-images\image-20260630152016080.png)

## 9.2**自定义数据集和奖励函数**

虽然 HelloAgents 提供了 GSM8K 数据集和常用奖励函数，但在实际应用中，你可能需要使用自己的数据集或设计特定的奖励函数。本节将介绍如何扩展框架。

在使用自定义数据集之前，需要了解两种训练格式的数据要求:

**SFT 格式**:用于监督微调，需要包含以下字段:

- `prompt`: 输入提示(包含 system 和 user 消息)
- `completion`: 期望的输出
- `text`: 完整的对话文本(可选)

**RL 格式**:用于强化学习，需要包含以下字段:

- `question`: 原始问题
- `prompt`: 输入提示(包含 system 和 user 消息)
- `ground_truth`: 正确答案，客观结果
- `full_answer`: 完整答案(包含推理过程)

**SFT 的作用**是教会模型任务的基本规则。

- 学习输出格式，让模型知道如何组织答案(如使用"Step 1"， "Final Answer"等标记)。
- 学习推理模式，通过示例学习如何分解问题、逐步推导。
- 建立基线能力，为后续的强化学习提供一个合理的起点。
- 减少探索空间，强化学习不需要从零开始，可以在 SFT 的基础上优化。

**在训练过程中，我们需要监控三个关键指标。**

- 损失(Loss)应该逐渐下降，如果不下降可能是学习率太小或数据有问题，如果下降后又上升则可能是学习率太大或出现过拟合。
- 梯度范数(Gradient Norm)应该在 0.1-10 的合理范围内，过大(>100)说明出现梯度爆炸需要降低学习率，过小(<0.01)说明梯度消失需要检查模型配置。
- 学习率(Learning Rate)应该按照 warmup 策略变化，前 10%步数线性增加，然后线性衰减到 0。

**训练中常见的问题及解决方案。**

- 显存不足时可以减小 batch_size 或 max_length，使用梯度累积或更小的模型
- 训练速度慢时可以增大 batch_size，减少 logging 频率，或使用混合精度训练
- 损失不下降时可以增大学习率，检查数据格式，或增加训练轮数
- 过拟合时可以增大 weight_decay（权重衰减，防止过拟合），减少训练轮数，或使用更多数据。

**GRPO 训练过程解析**

GRPO 的训练循环包括以下步骤:

1. **采样阶段**:对于每个问题，使用当前策略生成多个答案(`num_generations`个)。这些答案构成一个"组"，用于计算相对奖励。
2. **奖励计算**:对每个生成的答案计算奖励 ri。奖励可以是准确率、长度惩罚、步骤奖励或它们的组合。
3. **相对奖励**:计算组内平均奖励 r¯=1N∑i=1Nri，然后计算相对奖励 r^i=ri−r¯。这样做的好处是减少奖励方差，使训练更稳定。
4. **策略更新**:使用相对奖励更新策略，同时添加 KL 散度惩罚，防止策略偏离参考模型太远。
5. **重复**:重复上述步骤，直到完成所有训练轮次。

## 9.3模型评估与分析

训练完成后，我们需要全面评估模型的性能，不仅要看准确率这一个指标，还要深入分析模型的推理质量、错误模式、泛化能力等。本节将介绍如何系统地评估和分析 Agentic RL 模型。

**11.5.1 评估指标体系**

一个好的评估体系应该是多维度的，从不同角度衡量模型的能力。我们将评估指标分为三类:准确性指标、效率指标、质量指标。

**（1）准确性指标**

**准确率(Accuracy)**。**Top-K 准确率**:生成 K 个答案，只要有一个正确就算对。。**数值误差(Numerical Error)**:对于数学问题，可以计算预测值与真实值的误差。

**（2）效率指标**

**平均长度(Average Length)**。**推理步骤数(Reasoning Steps)**:适当的步骤数(2-5 步)说明模型能够系统地分解问题，过多的步骤可能说明推理冗余。**推理时间(Inference Time)**:生成一个答案所需的时间。这个指标在实际部署中很重要，影响用户体验。

**（3）质量指标**

**格式正确率(Format Correctness)**。**推理连贯性(Reasoning Coherence)**:推理步骤之间是否逻辑连贯。这个指标通常需要人工评估或使用专门的评估模型。**可解释性(Explainability)**:答案是否容易理解和验证。包含清晰步骤的答案比直接给出结果的答案更具可解释性。

**错误分析**模型的错误可以分为四类:

- 计算错误(推理步骤正确但计算出错，如"48/2=25"，说明数值计算能力不足)、
- 推理错误(推理逻辑错误导致解题思路不对，如先加后除而非先除后加，说明逻辑推理能力不足)、
- 理解错误(没有正确理解问题，如问题问"总共"但只计算了一部分，说明语言理解能力不足)、
- 格式错误(答案正确但格式不符合要求，如缺少"Final Answer:"标记，说明格式学习不足)。

**数据增强**:如果数据量不足，可以考虑数据增强，如改写问题(保持答案不变)、生成相似问题、反向翻译(translate back)。但要注意保持数据质量，避免引入噪声。

**超参网格搜索配置**

- learning_rate：学习率
- lora_rank：LoRA 低秩矩阵维度，控制微调可训练参数量，w=w+w'=w+BA
- kl_coef：KL 散度损失权重（DPO/RLHF 类对齐训练常用）

# 10. agent评估

1. **BFCL**：评估工具调用能力
   - 选择理由：数据集规模适中，评估指标清晰，社区活跃
   - 适用场景：评估智能体的函数调用准确性
2. **GAIA**：评估通用 AI 助手能力
   - 选择理由：任务真实，难度分级，综合性强
   - 适用场景：评估智能体的综合问题解决能力
3. **数据生成质量评估**：评估 LLM 生成数据质量
   - 选择理由：通过这个案例可以完整体验如何使用 Agent 创造数据，评估数据的完整演示。
   - 适用场景：评估生成的训练数据、测试数据的质量
   - 评估方法：LLM Judge、Win Rate、人工验证

## 10.1 改进

- 优化智能体的工具调用能力，可以考虑使用支持原生函数调用的 LLM（如 GPT-4、Claude 等），或者改进提示词让 LLM 更好地理解工具调用格式。
- 扩展工具库，BFCL 测试中涉及各种类型的函数，可以根据测试数据集的特点，预先实现常用的工具类型，提高智能体的工具覆盖率。
- 针对不同难度级别设计不同的策略，例如在 multiple 场景下需要智能体能够规划多步骤的工具调用序列，在 parallel 场景下需要识别可以并行执行的工具调用，在 irrelevance 场景下需要判断是否真的需要调用工具。

**我们建立了一个三层评估体系，全面覆盖智能体的不同能力维度**。

- 首先是工具调用能力评估（BFCL），专注于评估智能体的函数调用准确性，包含 simple、multiple、parallel、irrelevance 四个类别，使用 AST 匹配技术进行精确评估。
- 其次是通用能力评估（GAIA），评估智能体的综合问题解决能力，包含三个难度级别共 466 个真实世界问题，关注多步推理、工具使用、文件处理等能力。
- 第三是数据生成质量评估（AIME），评估 LLM 生成数据的质量，使用 LLM Judge 和 Win Rate 两种方法，支持人工验证和综合报告生成，确保生成数据达到参考数据的质量标准。

# 11项目

## 11.1 SSE

SSE 是一种服务器推送技术，允许服务器主动向客户端发送数据，在协议章节也有所讲解。

**流程说明**：

1. **客户端发起请求**：发送 POST 请求到`/api/research`，包含研究主题
2. **服务器建立 SSE 连接**：返回`text/event-stream`响应
3. **服务器推送进度**：定期推送研究进度（规划、执行、报告）
4. **客户端接收进度**：监听 SSE 事件，更新 UI
5. **研究完成**：服务器推送最终报告，关闭连接

**后端**

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json
app = FastAPI()

async def research_stream(topic: str) -> AsyncGenerator[str, None]:
    """研究流式生成器  
    生成SSE格式的数据：
    data: {"type": "progress", "data": {...}}
    """
    try:
        # 1. 规划阶段
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'planning', 'percentage': 10, 'text': '正在规划研究任务...'})}\n\n"
        
        # 调用PlanningService
        todo_items = await planning_service.plan_todo_list(topic)
        
        yield f"data: {json.dumps({'type': 'plan', 'data': [item.dict() for item in todo_items]})}\n\n"
        
        # 2. 执行阶段
        task_summaries = []
        # 完成
        yield f"data: {json.dumps({'type': 'progress', 'stage': 'completed', 'percentage': 100, 'text': '研究完成！'})}\n\n"
        
    except Exception as e:
        # 错误处理
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/api/research")
async def research(request: ResearchRequest):
    """研究端点（SSE）"""
    return StreamingResponse(
        research_stream(request.topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**前端**

```javascript
// composables/useResearch.ts
import { ref } from 'vue'
export function useResearch() {
  const startResearch = (topic: string) => {
    // 创建EventSource
    const eventSource = new EventSource(`/api/research?topic=${encodeURIComponent(topic)}`)
    // 监听消息
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      switch (data.type) {
        case 'progress':
          progressPercentage.value = data.percentage
          progressText.value = data.text
          break
        case 'plan':
          // 显示规划结果
          console.log('规划结果:', data.data)
          break
        case 'completed':
          eventSource.close()
          isLoading.value = false
          break
      }
    }
    // 错误处理
    eventSource.onerror = (err) => {
      console.error('SSE错误:', err)
      error.value = '连接失败，请重试'
      eventSource.close()
      isLoading.value = false
    }
  }
  
  return {
    isLoading,
    progressPercentage,
    progressText,
    markdownContent,
    error,
    startResearch,
  }
}
```

渲染**markdow**：

研究结果以 Markdown 格式展示，包含标题、段落、列表、引用等元素。我们使用`marked`库将 Markdown 转换为 HTML，并添加自定义样式。

```javascript
import { marked } from 'marked'

// 配置marked
marked.setOptions({
  breaks: true,  // 支持换行
  gfm: true,     // 支持GitHub Flavored Markdown
})

// 渲染
const renderedHtml = marked(markdownContent.value)
```

