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

