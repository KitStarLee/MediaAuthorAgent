"""
飞书表格读取节点 - 适配表B具体结构
"""
import os
import sys
import logging
from typing import Dict, List, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import FeishuReadInput, FeishuReadOutput

logger = logging.getLogger(__name__)

# 导入共享的飞书工具
sys.path.insert(0, os.path.join(os.getenv("COZE_WORKSPACE_PATH"), "src"))
from tools.feishu_bitable_tool import get_or_create_client


def feishu_read_node(state: FeishuReadInput, config: RunnableConfig, runtime: Runtime[Context]) -> FeishuReadOutput:
    """
    title: 读取历史数据（表B）
    desc: 从飞书多维表格B读取已发布内容的历史数据表现
    integrations: 飞书多维表格
    """
    ctx = runtime.context
    
    try:
        # 使用共享工具创建或获取飞书客户端
        client, current_token = get_or_create_client(
            app_id=state.feishu_app_id,
            app_secret=state.feishu_app_secret,
            cached_token=state.feishu_access_token
        )
        
        # 读取历史数据 - 表B结构：标识、平台、内容ID、点赞、收藏、评论、分享
        records = []
        page_token = None
        
        while True:
            result = client.search_record(
                app_token=state.app_token,
                table_id=state.table_id_b,
                page_token=page_token,
                page_size=100
            )
            
            items = result.get("data", {}).get("items", [])
            for item in items:
                fields = item.get("fields", {})
                # 标准化数据结构
                record = {
                    "record_id": item.get("record_id", ""),
                    "platform": fields.get("平台", ""),
                    "content_id": fields.get("内容ID", ""),
                    "likes": fields.get("点赞", 0),
                    "favorites": fields.get("收藏", 0),
                    "comments": fields.get("评论", 0),
                    "shares": fields.get("分享", 0),
                    "fields": fields  # 保留原始字段
                }
                records.append(record)
            
            page_token = result.get("data", {}).get("page_token")
            if not page_token:
                break
        
        return FeishuReadOutput(
            historical_data=records,
            feishu_access_token=current_token
        )
        
    except Exception as e:
        error_msg = f"读取飞书表格失败: {str(e)}"
        logger.error(error_msg)
        # 出错时返回空数据，但不中断流程
        return FeishuReadOutput(
            historical_data=[],
            feishu_access_token=state.feishu_access_token
        )
