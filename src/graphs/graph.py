from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)

from graphs.nodes.topic_generation_node import topic_generation_node
from graphs.nodes.content_generation_node import content_generation_node
from graphs.nodes.feishu_write_node import feishu_write_node
from graphs.nodes.feishu_read_node import feishu_read_node
from graphs.nodes.analysis_optimization_node import analysis_optimization_node


# 创建状态图
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点
builder.add_node(
    "feishu_read", 
    feishu_read_node
)
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
builder.add_node(
    "feishu_write", 
    feishu_write_node
)

# 设置入口点 - 先读取历史数据
builder.set_entry_point("feishu_read")

# 添加边 - 数据流向
builder.add_edge("feishu_read", "analysis_optimization")
builder.add_edge("analysis_optimization", "topic_generation")
builder.add_edge("topic_generation", "content_generation")
builder.add_edge("content_generation", "feishu_write")
builder.add_edge("feishu_write", END)

# 编译图
main_graph = builder.compile()
