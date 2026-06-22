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

