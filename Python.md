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

# json

`eval()` 函数会**把字符串当作 Python 代码执行**：

- `proposal_str` 是一段合法 Python 语法的字符串（比如字典、列表、数字表达式）
- `eval(proposal_str)` 将字符串转成对应 Python 对象，赋值给 `proposal`

```
print(__file__) 输出：
D:/project/demo/test.py

os.path.dirname("D:/project/demo/test.py")
# 结果：D:/project/demo
```

```
json 库解析函数：把 JSON 格式字符串转为 Python 字典 / 列表。
③ json.loads(字符串)
```

| 内容                  | json.loads    | eval               |
| --------------------- | ------------- | ------------------ |
| `{"a":1}` 双引号      | ✅             | ✅                  |
| `{'a':1}` 单引号      | ❌ 报错        | ✅                  |
| `true / false / null` | ✅             | ❌（Python 不识别） |
| `True / False / None` | ❌             | ✅                  |
| `(1,2,3)` 元组        | ❌ JSON 无元组 | ✅                  |
| 内置函数、系统调用    | ❌             | ✅（风险）          |

`json.dumps(obj)`：**把 Python 对象（字典 / 列表等）序列化为 JSON 字符串**

对应反向函数：`json.loads(json_str)` 字符串 → Python 对象

```python
d = {"text": "研究完成"}
print(json.dumps(d))
# {"text": "\u7814\u7a76\u5b8c\u6210"}
```



## 一、多线程

 **threading（IO 密集首选，轻量）**

适合：天气接口请求、文件读取、网络爬虫、等待 API 响应

优势：开销小、共享内存；缺陷：CPU 计算无法多核加速

```
import threading
import time

def task(name, delay):
    print(f"线程{name}开始，等待{delay}s")
    time.sleep(delay)  # IO阻塞时释放GIL
    print(f"线程{name}结束")

if __name__ == "__main__":
    t1 = threading.Thread(target=task, args=("A", 2))
    t2 = threading.Thread(target=task, args=("B", 1))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("全部完成")

join() 会阻塞主线程：
先 t1.join()：主线程卡住，直到线程 A 结束；
再 t2.join()：主线程卡住，直到线程 B 结束；
```

**线程池（批量任务推荐，不用手动创建线程）**

```
from concurrent.futures import ThreadPoolExecutor

def get_weather(city):
    # 模拟请求天气API（IO等待）
    import time
    time.sleep(1)
    return f"{city}天气数据"

if __name__ == "__main__":
    cities = ["北京", "上海", "广州", "深圳"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = pool.map(get_weather, cities)
    for res in results:
        print(res)
```

## 二、多进程 

**multiprocessing（CPU 密集真并行）**

适合：数值计算、AST 批量对比、大规模数据处理、模型推理

突破 GIL，多核同时运算；开销大、进程内存隔离，不能直接共享变量

```
import multiprocessing
import time

def calc_task(n):
    # 纯CPU计算
    s = 0
    for i in range(n):
        s += i**2
    return s

if __name__ == "__main__":
    # Windows必须加if __name__ == "__main__"
    p1 = multiprocessing.Process(target=calc_task, args=(1000000,))
    p2 = multiprocessing.Process(target=calc_task, args=(1000000,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print("计算完成")
```

**进程池 ProcessPoolExecutor（批量计算标准写法）**

```
from concurrent.futures import ProcessPoolExecutor

def ast_match_task(sample):
    # 批量AST匹配，CPU密集
    pred, gold = sample
    return pred == gold

if __name__ == "__main__":
    samples = [(1,1), (2,3), (5,5), (7,2)]
    with ProcessPoolExecutor() as pool:
        outputs = pool.map(ast_match_task, samples)
    print(list(outputs))
```

## 三、异步并发

 **asyncio（高 IO、大量接口并发）**

适合：成千上百 HTTP 请求、MCP 客户端异步调用、大量网络任务

单线程内切换 IO 任务，比线程池更省资源

```
import asyncio

async def async_weather(city):
    print(f"请求{city}")
    await asyncio.sleep(1)  # 异步等待IO
    return f"{city}数据"

async def main():
    cities = ["北京", "上海", "杭州"]
    # 并发创建多个协程
    tasks = [async_weather(city) for city in cities]
    results = await asyncio.gather(*tasks)
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

## 四、第三方库

 **joblib（极简多进程，机器学习常用）**

封装 multiprocessing，一行实现并行循环，不用写进程池模板

```
from joblib import Parallel, delayed

def heavy_calc(x):
    return x ** 3

# n_jobs=-1 使用全部CPU核心
results = Parallel(n_jobs=-1)(
    delayed(heavy_calc)(i) for i in range(10)
)
print(results)
```

```
city = "北京"
# 多行三引号 f-string
prompt = f""""
你是天气专家，查询{city}的天气
工具格式：`[TOOL_CALL:amap_maps_weather:city={city}]`
"""
"""
print(prompt)

# 先定义模板，用 {city} 占位，此时不需要 city 存在
WEATHER_PROMPT = """查询{city}的天气，出行天数{days}"""

# 后期再传参填充
text = WEATHER_PROMPT.format(city="上海", days=3)
print(text)
```

# 类型

```python
from pydantic import BaseModel
from typing import int, str

class TodoItem(BaseModel):
    id: int
    title: str
    intent: str
    query: str
task = TodoItem(id=1, title="查天气", intent="天气查询", query="上海今天多少度")
print(task.model_dump())
# {'id': 1, 'title': '查天气', 'intent': '天气查询', 'query': '上海今天多少度'}

class TodoItem(BaseModel):
    # 必填：创建对象必须传id
    id: int = Field(..., gt=0, description="任务自增ID，从1开始")
    # 必填
    query: str = Field(..., min_length=1, description="用户原始查询语句")
    # 可选，不传默认1
    priority: int = Field(default=1, ge=1, le=5, description="优先级1~5")
    //desc: Optional[str] = Field(None, description="可选描述，可以为空")
```

`ge` = greater or equal → **大于等于 ≥**

`le` = less or equal → **小于等于 ≤**

`gt` = greater than → 大于 >

`lt` = less than → 小于