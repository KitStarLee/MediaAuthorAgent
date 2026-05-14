import os
import json
import logging
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import ContentGenerationInput, ContentGenerationOutput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def content_generation_node(state: ContentGenerationInput, config: RunnableConfig, runtime: Runtime[Context]) -> ContentGenerationOutput:
    """
    title: 内容生成
    desc: 基于选定选题批量生成指定数量的完整内容，每篇包含标题、内容、话题（#tags）
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
    
    # 选择选题（根据内容数量选择相应数量的选题）
    num_topics = min(state.content_count, len(state.topics))
    selected_topics = state.topics[:num_topics] if state.topics else []
    
    logger.info(f"Generating {state.content_count} contents for topics: {selected_topics}")
    
    # 使用jinja2模板渲染提示词
    up_tpl = Template(up)
    user_prompt_content = up_tpl.render({
        "topics": selected_topics,
        "content_count": state.content_count,
        "historical_data": state.historical_data if hasattr(state, 'historical_data') else None,
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
    
    logger.info(f"LLM response length: {len(content_text)}")
    
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
            for i in range(state.content_count):
                topic = selected_topics[i] if i < len(selected_topics) else f"{state.core_topic} - {i + 1}"
                contents.append({
                    "title": topic,
                    "content": content_text if i == 0 else f"这是关于 {topic} 的内容...",
                    "topics": [f"#{state.core_topic.replace(' ', '')}", "#内容创作"]
                })
    
    # 确保contents的格式正确，包含title, content, topics
    formatted_contents = []
    for idx, item in enumerate(contents):
        if len(formatted_contents) >= state.content_count:
            break
            
        if isinstance(item, str):
            topic = selected_topics[idx] if idx < len(selected_topics) else f"{state.core_topic} - {idx + 1}"
            formatted_contents.append({
                "title": topic,
                "content": item,
                "topics": [f"#{state.core_topic.replace(' ', '')}", "#内容创作"]
            })
        elif isinstance(item, dict):
            title = item.get("title", selected_topics[idx] if idx < len(selected_topics) else f"{state.core_topic} - {idx + 1}")
            content = item.get("content", "") or item.get("text", "")
            topics = item.get("topics", []) or item.get("tags", [])
            
            # 确保topics是带#的格式
            formatted_topics = []
            for t in topics:
                if t and not t.startswith("#"):
                    formatted_topics.append(f"#{t}")
                elif t:
                    formatted_topics.append(t)
            
            # 如果没有话题，添加默认话题
            if not formatted_topics:
                formatted_topics = [f"#{state.core_topic.replace(' ', '')}", "#内容创作"]
            
            formatted_contents.append({
                "title": title,
                "content": content,
                "topics": formatted_topics
            })
    
    # 确保生成指定数量的内容
    while len(formatted_contents) < state.content_count:
        idx = len(formatted_contents)
        topic = selected_topics[idx] if idx < len(selected_topics) else f"{state.core_topic} - {idx + 1}"
        formatted_contents.append({
            "title": topic,
            "content": f"这是关于 {topic} 的内容...",
            "topics": [f"#{state.core_topic.replace(' ', '')}", "#内容创作"]
        })
    
    logger.info(f"Successfully generated {len(formatted_contents)} contents")
    
    return ContentGenerationOutput(
        contents=formatted_contents
    )
