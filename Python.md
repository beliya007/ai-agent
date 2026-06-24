```python
def get_weather(city: str) -> str:
    #多行注释，用来给开发者看函数功能，IDE 悬浮会显示这段说明。
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    #模板字符串`${}`
    url = f"https://wttr.in/{city}?format=j1" 
    try:
        # 发起网络请求
        response = requests.get(url)
        # 检查响应状态码是否为200 (成功)
        response.raise_for_status() 
        # 解析返回的JSON数据
        data = response.json()
        # 数组类型的对象data
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C'] 
        # 格式化成自然语言返回
        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"    
    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"
```

```python
        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")
        
```

```python
match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
```

- `.*Action:`（贪婪）

  匹配结果：`Thought: aaa Action: 111 Thought: bbb Action:`

  一直吃到最后一个 `Action:`

- `.*?Action:`（非贪婪）

  匹配结果：`Thought: aaa Action:`

  只匹配到**第一个**`Action:` 就停下

- `\n`：换行符（下一行开头）
- `\s*`：任意空白（空格、缩进、Tab，0 个或多个）
- `(?:...)`：非捕获分组，只用来分组多选，不生成单独分组
- `Thought:|Action:|Observation:`：三选一，匹配下一段的头部标识
- `(?=xxx)` 正向前瞻，结合前边的`.*?``
- ``re.DOTALL`不加这个 flag 时：`.`**不能匹配换行符 `\n`**，只能取同一行 Action 后面文字；加上后：`.` 可以匹配换行，Action 后面多行内容都会被一并捕获。

```
字典 `.get(key, 默认值)`

- 去 `tools` 里找键 `name`；
- 如果存在：返回对应的工具子字典 `{"func": xxx, ...}`；
- 如果不存在该工具：**返回空字典 `{}`**，而不是抛 `KeyError`。
```

```
BaseModel 是 Pydantic 的数据载体基类，只需声明字段类型，自动完成类型校验、类型转换、字典 / JSON 互转、对象解析，是 Python 结构化数据处理、Web 接口开发最常用工具。
```

```python
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

//后续别的方法还要读取这个值 → 赋值 self.xxx
//只在当前函数里只用一次，之后不再使用 → 普通局部变量，不加 self
```

```
类方法和实例方法
# 执行 Config.from_env()
# cls 就是 Config
def from_env(cls):
    # cls(...) = Config(...)，创建一个全新配置对象
    new_config = Config(
        debug=xxx,
        temperature=xxx
    )
    return new_config
    
# 先有实例 cfg = Config()
# cfg.to_dict() 时 self 就是 cfg 对象本身
def to_dict(self):
    # self 身上已经有所有配置字段，直接序列化
    return self.dict()
```

```python
//抽象类：@abstractmethod子类必须重写
//class ChatAgent(Agent):。。。。
//开发规范：如果希望子类必须实现，一定要加上 @abstractmethod；不加就代表提供默认空实现，不做强制约束。
    
"""Agent基类"""
from abc import ABC, abstractmethod
from typing import Optional, Any
from .message import Message
from .llm import HelloAgentsLLM
from .config import Config

class Agent(ABC):
    """Agent基类"""
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self._history: list[Message] = []
    
    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """运行Agent"""
        pass
    
    def add_message(self, message: Message):
        """添加消息到历史记录"""
        self._history.append(message)
    
    def clear_history(self):
        """清空历史记录"""
        self._history.clear()
    
    def get_history(self) -> list[Message]:
        """获取历史记录"""
        return self._history.copy()
    
    def __str__(self) -> str:
        return f"Agent(name={self.name}, provider={self.llm.provider})"
```

