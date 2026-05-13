import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import ContentGenerationInput, ContentGenerationOutput


def content_generation_node(state: ContentGenerationInput, config: RunnableConfig, runtime: Runtime[Context]) -> ContentGenerationOutput:
    """
    title: 内容生成
    desc: 基于选定选题批量生成2-3篇完整内容草稿，结构包含痛点引入、核心价值、互动引导
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 从配置文件读取LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")
    
    # 选择第一个选题作为主要选题
    selected_topic = state.topics[0] if state.topics else ""
    
    # 使用jinja2模板渲染提示词
    up_tpl = Template(up)
    user_prompt_content = up_tpl.render({
        "selected_topic": selected_topic,
        "topics": state.topics,
        "historical_data": state.historical_data,
        "optimization_strategy": state.optimization_strategy
    })
    
    # 初始化LLM客户端
    client = LLMClient(ctx=ctx)
    
    # 组装消息
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt_content)
    ]
    
    # 调用LLM
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-2-0-lite-260215"),
        temperature=llm_config.get("temperature", 0.8),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 4000),
        thinking=llm_config.get("thinking", "disabled")
    )
    
    # 解析响应内容
    content_text = ""
    if isinstance(response.content, str):
        content_text = response.content.strip()
    elif isinstance(response.content, list):
        if response.content and isinstance(response.content[0], str):
            content_text = " ".join(response.content).strip()
        else:
            text_parts = [item.get("text", "") for item in response.content if isinstance(item, dict) and item.get("type") == "text"]
            content_text = " ".join(text_parts).strip()
    
    # 尝试从响应中提取JSON
    contents = []
    try:
        result = json.loads(content_text)
        if isinstance(result, dict) and "contents" in result:
            contents = result["contents"]
        elif isinstance(result, list):
            contents = result
    except json.JSONDecodeError:
        # 如果JSON解析失败，尝试按特定格式分割
        import re
        
        # 尝试查找JSON格式
        json_match = re.search(r'\{[\s\S]*\}', content_text)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                if isinstance(result, dict) and "contents" in result:
                    contents = result["contents"]
                elif isinstance(result, list):
                    contents = result
            except json.JSONDecodeError:
                pass
        
        # 如果还是没有，创建默认的内容结构
        if not contents:
            # 将整个响应作为一篇内容
            contents = [
                {
                    "title": selected_topic,
                    "content": content_text
                }
            ]
    
    # 确保contents的格式正确
    formatted_contents = []
    for item in contents:
        if isinstance(item, str):
            formatted_contents.append({
                "title": f"{selected_topic} - {len(formatted_contents) + 1}",
                "content": item
            })
        elif isinstance(item, dict):
            title = item.get("title", f"{selected_topic} - {len(formatted_contents) + 1}")
            content = item.get("content", "") or item.get("text", "")
            formatted_contents.append({
                "title": title,
                "content": content
            })
    
    # 确保至少有2篇内容
    if len(formatted_contents) < 2:
        # 补充默认内容
        default_content = f"""# {selected_topic}

## 痛点引入
你是否也遇到过这样的问题...

## 核心价值
今天我们就来聊聊这个话题...

## 互动引导
如果你觉得有用，欢迎点赞收藏，有问题也可以在评论区留言！"""
        
        while len(formatted_contents) < 2:
            formatted_contents.append({
                "title": f"{selected_topic} - {len(formatted_contents) + 1}",
                "content": default_content
            })
    
    return ContentGenerationOutput(
        contents=formatted_contents[:3],  # 最多3篇
        selected_topic=selected_topic
    )
