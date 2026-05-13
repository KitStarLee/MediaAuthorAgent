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


# 条件判断函数 - 用于条件边
def should_analyze(state: GlobalState) -> str:
    """
    title: 是否需要分析
    desc: 根据enable_analysis参数和historical_data是否为空，判断是否需要进行数据分析和优化
    """
    # 如果enable_analysis为False，直接跳过分析
    if not state.enable_analysis:
        return "跳过分析"
    
    # 如果enable_analysis为True，但历史数据为空，也跳过分析
    if not state.historical_data or len(state.historical_data) == 0:
        return "跳过分析"
    
    # 否则进行分析
    return "进行分析"


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

# 添加条件分支
builder.add_conditional_edges(
    source="feishu_read",
    path=should_analyze,
    path_map={
        "进行分析": "analysis_optimization",
        "跳过分析": "topic_generation"
    }
)

# 分析完成后到选题生成
builder.add_edge("analysis_optimization", "topic_generation")

# 后续流程
builder.add_edge("topic_generation", "content_generation")
builder.add_edge("content_generation", "feishu_write")
builder.add_edge("feishu_write", END)

# 编译图
main_graph = builder.compile()
