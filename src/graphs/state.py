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


class GraphOutput(BaseModel):
    """工作流输出"""
    topics: List[str] = Field(..., description="生成的选题列表")
    contents: List[Dict[str, str]] = Field(..., description="生成的内容列表")
    optimization_strategy: Dict[str, Any] = Field(..., description="优化策略")
    write_result: Dict[str, Any] = Field(..., description="飞书表格写入结果")


# ==================== 各节点的输入输出 ====================

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


# 飞书表格写入节点
class FeishuWriteInput(BaseModel):
    """飞书表格写入节点输入"""
    app_token_a: str = Field(..., description="飞书多维表格A的app_token")
    table_id_a: str = Field(..., description="飞书多维表格A的table_id")
    contents: List[Dict[str, str]] = Field(..., description="要写入的内容列表")
    selected_topic: str = Field(..., description="选定的选题")


class FeishuWriteOutput(BaseModel):
    """飞书表格写入节点输出"""
    write_result: Dict[str, Any] = Field(..., description="写入结果")


# 历史数据读取节点
class FeishuReadInput(BaseModel):
    """历史数据读取节点输入"""
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
