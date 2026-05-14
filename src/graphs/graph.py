from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)

from graphs.nodes.topic_generation_node import topic_generation_node
from graphs.nodes.content_generation_node import content_generation_node
from graphs.nodes.analysis_optimization_node import analysis_optimization_node

# ==================== 主图编排 ====================
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点
builder.add_node(
    "analysis_optimization", 
    analysis_optimization_node, 
    metadata={"type": "agent", "llm_cfg": "config/analysis_optimization_llm_cfg.json"}
)

builder.add_node(
    "topic_generation", 
    topic_generation_node, 
    metadata={"type": "agent", "llm_cfg": "config/topic_generation_llm_cfg.json"}
)

builder.add_node(
    "content_generation", 
    content_generation_node, 
    metadata={"type": "agent", "llm_cfg": "config/content_generation_llm_cfg.json"}
)

# 简化流程：总是先运行分析，再生成选题，再生成内容
# analysis_optimization 会处理没有数据的情况
builder.set_entry_point("analysis_optimization")

# 添加边
builder.add_edge("analysis_optimization", "topic_generation")
builder.add_edge("topic_generation", "content_generation")
builder.add_edge("content_generation", END)

# 编译图
main_graph = builder.compile()
