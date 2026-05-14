import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import TopicGenerationInput, TopicGenerationOutput


def topic_generation_node(state: TopicGenerationInput, config: RunnableConfig, runtime: Runtime[Context]) -> TopicGenerationOutput:
    """
    title: 选题生成
    desc: 根据用户需求严格生成指定数量的选题，网感强、自带流量属性
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
    
    # 使用jinja2模板渲染提示词
    up_tpl = Template(up)
    user_prompt_content = up_tpl.render({
        "user_demand": state.user_demand,
        "background": state.background,
        "content_count": state.content_count,
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
        temperature=llm_config.get("temperature", 0.7),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 2000),
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
    topics = []
    try:
        # 尝试直接解析JSON
        result = json.loads(content_text)
        if isinstance(result, dict) and "topics" in result:
            topics = result["topics"]
        elif isinstance(result, list):
            topics = result
    except json.JSONDecodeError:
        # 如果直接解析失败，尝试从文本中提取
        import re
        # 尝试查找JSON格式
        json_match = re.search(r'\{[\s\S]*\}', content_text)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                if isinstance(result, dict) and "topics" in result:
                    topics = result["topics"]
                elif isinstance(result, list):
                    topics = result
            except json.JSONDecodeError:
                pass
        
        # 如果还是没有，尝试按行分割
        if not topics:
            lines = [line.strip() for line in content_text.split('\n') if line.strip()]
            # 过滤掉空行和非选题行
            topics = [line for line in lines if len(line) > 5]
    
    # 严格确保选题数量等于content_count
    if len(topics) == 0:
        # 如果没有生成任何选题，生成默认选题
        for i in range(state.content_count):
            topics.append(f"{state.user_demand[:10]}相关选题第{i+1}个")
    elif len(topics) < state.content_count:
        # 如果生成的选题不够，复制已有选题或生成补充
        original_len = len(topics)
        for i in range(state.content_count - original_len):
            topics.append(f"{topics[i % original_len]}（变种{i+1}）")
    elif len(topics) > state.content_count:
        # 如果生成的选题太多，只取前content_count个
        topics = topics[:state.content_count]
    
    return TopicGenerationOutput(topics=topics)
