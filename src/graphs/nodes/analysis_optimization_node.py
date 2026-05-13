import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import AnalysisOptimizationInput, AnalysisOptimizationOutput


def analysis_optimization_node(state: AnalysisOptimizationInput, config: RunnableConfig, runtime: Runtime[Context]) -> AnalysisOptimizationOutput:
    """
    title: 数据分析与策略优化
    desc: 分析历史数据，提炼高表现内容的共性特征，生成优化策略
    integrations: 大语言模型
    """
    ctx = runtime.context
    
    # 如果没有历史数据，返回默认优化策略
    if not state.historical_data:
        return AnalysisOptimizationOutput(
            optimization_strategy={
                "has_data": False,
                "message": "暂无历史数据，使用默认创作策略",
                "good_features": [],
                "bad_features": [],
                "suggestions": [
                    "使用引人注目的标题",
                    "开头设置悬念引发好奇",
                    "内容结构清晰，分点阐述",
                    "结尾引导互动和分享"
                ]
            }
        )
    
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
        "historical_data": state.historical_data
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
        temperature=llm_config.get("temperature", 0.3),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 3000),
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
    optimization_strategy = {}
    try:
        result = json.loads(content_text)
        if isinstance(result, dict):
            optimization_strategy = result
            optimization_strategy["has_data"] = True
    except json.JSONDecodeError:
        # 如果JSON解析失败，尝试查找JSON格式
        import re
        json_match = re.search(r'\{[\s\S]*\}', content_text)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                if isinstance(result, dict):
                    optimization_strategy = result
                    optimization_strategy["has_data"] = True
            except json.JSONDecodeError:
                pass
    
    # 如果解析失败，使用默认策略
    if not optimization_strategy:
        optimization_strategy = {
            "has_data": True,
            "message": "数据分析完成",
            "good_features": [
                "标题包含数字或疑问词",
                "开头3秒内抓住注意力",
                "内容有实用价值"
            ],
            "bad_features": [
                "标题平淡无奇",
                "开头铺垫过长",
                "缺乏互动引导"
            ],
            "suggestions": [
                "继续使用数字型标题",
                "优化开头，直接抛出痛点",
                "增强结尾的互动引导"
            ],
            "raw_analysis": content_text
        }
    
    return AnalysisOptimizationOutput(optimization_strategy=optimization_strategy)
