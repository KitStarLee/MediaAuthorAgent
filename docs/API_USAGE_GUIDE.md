# 工作流 API 使用指南

## 目录
1. [在 Python 中调用工作流](#1-在-python-中调用工作流)
2. [多用户调用与 Token 管理](#2-多用户调用与-token-管理)
3. [HTTP API 调用方式](#3-http-api-调用方式)
4. [完整的调用示例](#4-完整的调用示例)

---

## 1. 在 Python 中调用工作流

### 1.1 直接导入调用

工作流可以直接在 Python 代码中调用，不需要通过 HTTP 服务。

```python
import sys
import os
import asyncio
import json

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.main import service
from coze_coding_utils.runtime_ctx.context import new_context


async def call_workflow_direct():
    """直接调用工作流的示例"""
    
    # 构建 payload
    payload = {
        "user_demand": "我想做一个关于AI工具的自媒体账号",
        "background": "目标受众是职场人士",
        "historical_data": None,
        "content_count": 2
    }
    
    # 创建 context
    ctx = new_context(method="python_call")
    
    # 调用服务
    result = await service.run(payload, ctx)
    
    return result


# 运行
if __name__ == "__main__":
    result = asyncio.run(call_workflow_direct())
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 1.2 使用封装的客户端

也可以使用我们提供的封装客户端（参见 `examples/python_call_example.py`）：

```python
from examples.python_call_example import WorkflowClient
import asyncio


async def main():
    client = WorkflowClient()
    
    result = await client.call_workflow(
        user_demand="我想做美食类内容",
        background="目标受众是上班族",
        content_count=2
    )
    
    print(result)


asyncio.run(main())
```

---

## 2. 多用户调用与 Token 管理

### 2.1 当前工作流的特点

当前工作流是**无状态**的，具有以下特点：

1. **不存储用户信息**：工作流本身不记录或区分不同用户
2. **每次调用独立**：每次调用都是独立的执行
3. **LLM Token 消耗**：工作流内部使用的 LLM 的 Token 消耗由配置决定

### 2.2 多用户使用的架构设计

如果你需要支持用户 A、B、C 各自调用，并且消耗各自的 Token，需要在应用层进行管理：

```
用户A ──┐
         │
用户B ──┼──> 你的应用层 ──> Token 管理 ──> 工作流
         │
用户C ──┘
```

### 2.3 实现方案示例

```python
import asyncio
from typing import Dict, Any
from examples.python_call_example import WorkflowClient


class UserTokenManager:
    """用户 Token 管理器"""
    
    def __init__(self):
        # 存储用户的 Token 配置
        self.user_tokens: Dict[str, Dict[str, Any]] = {}
    
    def register_user(self, user_id: str, llm_config: Dict[str, Any]):
        """
        注册用户，设置其 LLM 配置
        
        注意：当前工作流的 LLM 配置在 config/*.json 文件中
        如果需要每个用户使用不同的 Token，需要修改工作流代码
        """
        self.user_tokens[user_id] = llm_config
    
    def get_user_config(self, user_id: str) -> Dict[str, Any]:
        """获取用户的配置"""
        return self.user_tokens.get(user_id, {})


class MultiUserService:
    """多用户服务"""
    
    def __init__(self):
        self.token_manager = UserTokenManager()
        # 工作流客户端是共享的
        self.workflow_client = WorkflowClient()
    
    async def call_for_user(
        self,
        user_id: str,
        user_demand: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        为用户调用工作流
        
        注意：当前实现中，所有用户共享相同的 LLM Token
        如果需要每个用户使用各自的 Token，需要修改工作流代码
        """
        # 记录用户调用（可以在这里做计费、限流等）
        print(f"用户 {user_id} 调用工作流")
        
        # 调用工作流
        result = await self.workflow_client.call_workflow(
            user_demand=user_demand,
            user_id=user_id,
            **kwargs
        )
        
        return result


# 使用示例
async def main():
    service = MultiUserService()
    
    # 用户A调用
    result_a = await service.call_for_user(
        user_id="user_a",
        user_demand="我想做科技类内容",
        content_count=1
    )
    
    # 用户B调用
    result_b = await service.call_for_user(
        user_id="user_b",
        user_demand="我想做旅游类内容",
        content_count=1
    )


asyncio.run(main())
```

### 2.4 如果需要每个用户使用各自的 Token

如果需要实现"谁调用消耗谁的 Token"，需要修改工作流代码：

1. **修改配置加载方式**：让 LLM 配置可以从参数传入，而不是只从文件读取
2. **在节点中使用用户的配置**：每个节点函数接收用户的 Token 配置

这需要对工作流进行较大的修改，如果你需要这个功能，可以告诉我，我来帮你实现。

---

## 3. HTTP API 调用方式

### 3.1 启动 HTTP 服务

```bash
cd /workspace/projects
bash scripts/http_run.sh -m http -p 5000
```

### 3.2 API 端点

#### POST /run
同步调用工作流

```bash
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_demand": "我想做一个关于AI工具的自媒体账号",
    "background": "目标受众是职场人士",
    "historical_data": null,
    "content_count": 2
  }'
```

#### POST /stream_run
流式调用工作流（SSE）

```bash
curl -X POST http://localhost:5000/stream_run \
  -H "Content-Type: application/json" \
  -d '{
    "user_demand": "我想做美食类内容",
    "content_count": 2
  }'
```

#### GET /health
健康检查

```bash
curl http://localhost:5000/health
```

#### GET /graph_parameter
获取输入输出 Schema

```bash
curl http://localhost:5000/graph_parameter
```

---

## 4. 完整的调用示例

### 4.1 Python 异步调用

```python
import asyncio
import json
from examples.python_call_example import WorkflowClient


async def complete_example():
    """完整的调用示例"""
    
    print("=" * 70)
    print("工作流完整调用示例")
    print("=" * 70)
    
    # 创建客户端
    client = WorkflowClient()
    
    # 调用参数
    params = {
        "user_demand": """我想要做一个关于Python编程的自媒体账号，
        专门分享实用的Python技巧、代码片段和最佳实践。
        内容要通俗易懂，适合初学者和中级开发者。""",
        
        "background": """目标受众是Python初学者和中级开发者，
        他们希望通过学习实用的技巧来提高编程效率，
        解决实际工作中的问题。内容风格要轻松有趣，
        避免过于学术化的表达。""",
        
        "historical_data": None,
        
        "content_count": 3
    }
    
    print(f"\n调用参数:")
    print(f"  用户需求: {params['user_demand'][:50]}...")
    print(f"  背景描述: {params['background'][:50]}...")
    print(f"  生成数量: {params['content_count']}")
    
    # 调用工作流
    print("\n正在调用工作流...")
    result = await client.call_workflow(**params)
    
    # 输出结果
    print("\n" + "=" * 70)
    print("调用成功！")
    print("=" * 70)
    
    # 打印选题
    print(f"\n📝 生成的选题 ({len(result.get('topics', []))} 个):")
    for i, topic in enumerate(result.get('topics', []), 1):
        print(f"  {i}. {topic}")
    
    # 打印内容
    contents = result.get('contents', [])
    print(f"\n📄 生成的内容 ({len(contents)} 篇):")
    for i, content in enumerate(contents, 1):
        print(f"\n  --- 第 {i} 篇 ---")
        print(f"  标题: {content.get('title', '无标题')}")
        print(f"  内容长度: {len(content.get('content', ''))} 字符")
        print(f"  话题标签: {', '.join(content.get('topics', []))}")
    
    # 完整结果
    print("\n" + "=" * 70)
    print("完整 JSON 结果:")
    print("=" * 70)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    asyncio.run(complete_example())
```

### 4.2 多用户并发调用示例

```python
import asyncio
from examples.python_call_example import MultiUserWorkflowManager


async def multi_user_concurrent_example():
    """多用户并发调用示例"""
    
    print("=" * 70)
    print("多用户并发调用示例")
    print("=" * 70)
    
    manager = MultiUserWorkflowManager()
    
    # 定义多个用户的任务
    user_tasks = [
        ("user_a", "我想做科技类内容，分享AI工具使用技巧", "目标受众是科技爱好者"),
        ("user_b", "我想做美食类内容，分享家常菜做法", "目标受众是上班族"),
        ("user_c", "我想做健身类内容，分享家庭健身方法", "目标受众是想在家健身的人"),
    ]
    
    # 并发调用
    print("\n开始并发调用...")
    tasks = []
    for user_id, demand, background in user_tasks:
        task = manager.call_for_user(
            user_id=user_id,
            user_demand=demand,
            background=background,
            content_count=1
        )
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 输出结果
    print("\n" + "=" * 70)
    print("调用结果:")
    print("=" * 70)
    for i, (user_id, _, _) in enumerate(user_tasks):
        result = results[i]
        if isinstance(result, Exception):
            print(f"\n用户 {user_id}: 失败 - {result}")
        else:
            contents = result.get('contents', [])
            print(f"\n用户 {user_id}: 成功生成 {len(contents)} 篇内容")
            for content in contents:
                print(f"  - {content.get('title', '无标题')}")


if __name__ == "__main__":
    asyncio.run(multi_user_concurrent_example())
```

---

## 总结

1. **Python 调用**：可以直接在 Python 代码中调用，参考 `examples/python_call_example.py`
2. **多用户使用**：当前工作流是无状态的，所有用户共享配置。如需每个用户使用各自的 Token，需要修改工作流代码
3. **HTTP API**：也可以通过 HTTP 服务调用，支持同步和流式两种方式

如果你需要实现"每个用户使用各自 Token"的功能，请告诉我，我可以帮你修改工作流代码来支持这个功能！
