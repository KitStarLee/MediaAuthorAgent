from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== 全局状态定义 ====================
class GlobalState(BaseModel):
    """全局状态定义 - 包含整个工作流的所有数据"""
    core_topic: str = Field(..., description="用户提供的核心主题词")
    app_token_a: str = Field(..., description="飞书多维表格A的app_token（用于存储生成内容）")
    table_id_a: str = Field(..., description="飞书多维表格A的table_id（用于存储生成内容）")
    app_token_b: str = Field(..., description="飞书多维表格B的app_token（用于读取历史数据）")
    table_id_b: str = Field(..., description="飞书多维表格B的table_id（用于读取历史数据）")
    enable_analysis: bool = Field(default=True, description="是否启用数据分析和优化")
    account_name: Optional[str] = Field(default="", description="账户名")
    
    topics: List[str] = Field(default=[], description="生成的选题列表")
    selected_topic: str = Field(default="", description="选定的选题")
    contents: List[Dict[str, str]] = Field(default=[], description="生成的内容列表，每个元素包含title和content")
    historical_data: List[Dict[str, Any]] = Field(default=[], description="从飞书表格B读取的历史数据")
    optimization_strategy: Dict[str, Any] = Field(default={}, description="数据分析后的优化策略")
    write_result: Dict[str, Any] = Field(default={}, description="飞书表格写入结果")


# ==================== 工作流输入输出 ====================
class GraphInput(BaseModel):
    """工作流输入"""
    core_topic: str = Field(..., description="用户提供的核心主题词（约10个字）")
    app_token_a: str = Field(..., description="飞书多维表格A的app_token（用于存储生成内容）")
    table_id_a: str = Field(..., description="飞书多维表格A的table_id（用于存储生成内容）")
    app_token_b: str = Field(..., description="飞书多维表格B的app_token（用于读取历史数据）")
    table_id_b: str = Field(..., description="飞书多维表格B的table_id（用于读取历史数据）")
    enable_analysis: bool = Field(default=True, description="是否启用数据分析和优化，默认true")
    account_name: Optional[str] = Field(default="", description="账户名（可选）")


class GraphOutput(BaseModel):
    """工作流输出"""
    topics: List[str] = Field(..., description="生成的选题列表")
    contents: List[Dict[str, str]] = Field(..., description="生成的内容列表")
    optimization_strategy: Dict[str, Any] = Field(..., description="优化策略")
    write_result: Dict[str, Any] = Field(..., description="飞书表格写入结果")
    historical_data: Optional[List[Dict[str, Any]]] = Field(default=[], description="历史数据（如果读取了）")


# ==================== 各节点的输入输出 ====================

# 条件判断节点
class ShouldAnalyzeInput(BaseModel):
    """条件判断节点输入"""
    enable_analysis: bool = Field(..., description="是否启用数据分析")
    historical_data: Optional[List[Dict[str, Any]]] = Field(default=[], description="历史数据")


class ShouldAnalyzeOutput(BaseModel):
    """条件判断节点输出"""
    should_analyze: bool = Field(..., description="是否需要进行分析")
    decision: str = Field(..., description="决策结果：进行分析/跳过分析")


# 选题生成节点
class TopicGenerationInput(BaseModel):
    """选题生成节点输入"""
    core_topic: str = Field(..., description="核心主题词")
    historical_data: Optional[List[Dict[str, Any]]] = Field(default=[], description="历史数据（用于优化）")
    optimization_strategy: Optional[Dict[str, Any]] = Field(default={}, description="优化策略")


class TopicGenerationOutput(BaseModel):
    """选题生成节点输出"""
    topics: List[str] = Field(..., description="生成的3-5个选题")


# 内容生成节点
class ContentGenerationInput(BaseModel):
    """内容生成节点输入"""
    topics: List[str] = Field(..., description="选题列表")
    historical_data: Optional[List[Dict[str, Any]]] = Field(default=[], description="历史数据（用于优化）")
    optimization_strategy: Optional[Dict[str, Any]] = Field(default={}, description="优化策略")


class ContentGenerationOutput(BaseModel):
    """内容生成节点输出"""
    contents: List[Dict[str, str]] = Field(..., description="生成的内容列表，每个元素包含title和content")
    selected_topic: str = Field(..., description="选定的选题")


# 飞书表格写入节点 - 适配表A结构
class FeishuWriteInput(BaseModel):
    """飞书表格写入节点输入 - 表A结构：编码、账户名、标题、描述、话题、文件、发布时间、发布状态、创建时间、数据表现"""
    app_token_a: str = Field(..., description="飞书多维表格A的app_token")
    table_id_a: str = Field(..., description="飞书多维表格A的table_id")
    contents: List[Dict[str, str]] = Field(..., description="要写入的内容列表")
    selected_topic: str = Field(..., description="选定的选题")
    account_name: Optional[str] = Field(default="", description="账户名")


class FeishuWriteOutput(BaseModel):
    """飞书表格写入节点输出"""
    write_result: Dict[str, Any] = Field(..., description="写入结果")


# 历史数据读取节点 - 适配表B结构
class FeishuReadInput(BaseModel):
    """历史数据读取节点输入 - 表B结构：标识、平台、内容ID、点赞、收藏、评论、分享"""
    app_token_b: str = Field(..., description="飞书多维表格B的app_token")
    table_id_b: str = Field(..., description="飞书多维表格B的table_id")


class FeishuReadOutput(BaseModel):
    """历史数据读取节点输出"""
    historical_data: List[Dict[str, Any]] = Field(..., description="读取到的历史数据")


# 数据分析与策略优化节点
class AnalysisOptimizationInput(BaseModel):
    """数据分析与策略优化节点输入"""
    historical_data: List[Dict[str, Any]] = Field(..., description="历史数据")


class AnalysisOptimizationOutput(BaseModel):
    """数据分析与策略优化节点输出"""
    optimization_strategy: Dict[str, Any] = Field(..., description="优化策略")
