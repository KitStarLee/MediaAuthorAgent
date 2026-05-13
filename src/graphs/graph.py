"""
自媒体内容生产系统主图编排
"""
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
    ShouldAnalyzeInput
)

from graphs.nodes.topic_generation_node import topic_generation_node
from graphs.nodes.content_generation_node import content_generation_node
from graphs.nodes.feishu_write_node import feishu_write_node
from graphs.nodes.feishu_read_node import feishu_read_node
from graphs.nodes.analysis_optimization_node import analysis_optimization_node


def should_analyze_data(state: ShouldAnalyzeInput) -> str:
    """
    条件判断函数：根据参数和数据决定是否进行分析
    返回值是中文分支名，用于 path_map 匹配
    """
    if not state.enable_analysis:
        return "跳过分析"
    
    # 检查历史数据是否为空
    if not state.historical_data or len(state.historical_data) == 0:
        return "跳过分析"
    
    return "进行分析"


# 创建状态图 - 指定输入和输出 schema
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

# 设置入口点
builder.set_entry_point("feishu_read")

# 添加条件分支：从读取数据后决定是否进行分析
builder.add_conditional_edges(
    source="feishu_read",
    path=should_analyze_data,
    path_map={
        "进行分析": "analysis_optimization",
        "跳过分析": "topic_generation"
    }
)

# 添加边：分析完成后到选题生成
builder.add_edge("analysis_optimization", "topic_generation")

# 添加后续边
builder.add_edge("topic_generation", "content_generation")
builder.add_edge("content_generation", "feishu_write")
builder.add_edge("feishu_write", END)

# 编译图
main_graph = builder.compile()
