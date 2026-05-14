from typing import Literal, Optional, List
from pydantic import BaseModel, Field

# ==================== 全局状态 ====================
class GlobalState(BaseModel):
    """全局状态定义 - 简化版，仅保留内容生成相关"""
    core_topic: str = Field(..., description="核心主题词，用于生成选题")
    historical_data: Optional[List[dict]] = Field(default=None, description="历史数据，用于复盘优化（可为空）")
    content_count: int = Field(default=3, description="创建内容的数量")
    
    topics: Optional[List[str]] = Field(default=None, description="生成的选题列表")
    optimization_strategy: Optional[dict] = Field(default=None, description="优化策略")
    contents: Optional[List[dict]] = Field(default=None, description="生成的内容列表")

# ==================== 图输入/输出 ====================
class GraphInput(BaseModel):
    """工作流的输入"""
    core_topic: str = Field(..., description="核心主题词，用于生成选题")
    historical_data: Optional[List[dict]] = Field(default=None, description="历史数据，用于复盘优化（可为空）")
    content_count: int = Field(default=3, description="创建内容的数量，默认3篇")

class GraphOutput(BaseModel):
    """工作流的输出"""
    topics: List[str] = Field(..., description="生成的选题列表")
    contents: List[dict] = Field(..., description="生成的内容列表，每篇包含标题、内容、话题")
    optimization_strategy: Optional[dict] = Field(default=None, description="优化策略（如有）")

# ==================== 节点输入/输出 ====================

# --- 选题生成节点 ---
class TopicGenerationInput(BaseModel):
    """选题生成节点的输入"""
    core_topic: str = Field(..., description="核心主题词")
    historical_data: Optional[List[dict]] = Field(default=None, description="历史数据（可选）")
    optimization_strategy: Optional[dict] = Field(default=None, description="优化策略（如有）")

class TopicGenerationOutput(BaseModel):
    """选题生成节点的输出"""
    topics: List[str] = Field(..., description="生成的选题列表")

# --- 内容生成节点 ---
class ContentGenerationInput(BaseModel):
    """内容生成节点的输入"""
    core_topic: str = Field(..., description="核心主题词")
    topics: List[str] = Field(..., description="选题列表")
    content_count: int = Field(default=3, description="要生成的内容数量")
    historical_data: Optional[List[dict]] = Field(default=None, description="历史数据（可选）")
    optimization_strategy: Optional[dict] = Field(default=None, description="优化策略（如有）")

class ContentGenerationOutput(BaseModel):
    """内容生成节点的输出"""
    contents: List[dict] = Field(..., description="生成的内容列表，每篇包含标题、内容、话题")

# --- 分析优化节点 ---
class AnalysisOptimizationInput(BaseModel):
    """分析优化节点的输入"""
    historical_data: Optional[List[dict]] = Field(default=None, description="历史数据")

class AnalysisOptimizationOutput(BaseModel):
    """分析优化节点的输出"""
    optimization_strategy: Optional[dict] = Field(default=None, description="优化策略")
    has_data: bool = Field(default=False, description="是否有历史数据")

# --- 是否需要分析的条件判断 ---
class ShouldAnalyzeInput(BaseModel):
    """是否需要分析的输入"""
    historical_data: Optional[List[dict]] = Field(default=None, description="历史数据")
