"""
飞书表格写入节点 - 适配表A具体结构
"""
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import FeishuWriteInput, FeishuWriteOutput

logger = logging.getLogger(__name__)

# 导入共享的飞书工具
sys.path.insert(0, os.path.join(os.getenv("COZE_WORKSPACE_PATH"), "src"))
from tools.feishu_bitable_tool import get_or_create_client


def feishu_write_node(state: FeishuWriteInput, config: RunnableConfig, runtime: Runtime[Context]) -> FeishuWriteOutput:
    """
    title: 写入内容表格（表A）
    desc: 将生成的内容草稿写入飞书多维表格A
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
        
        # 表A结构：编码、账户名、标题、描述、话题、文件、发布时间、发布状态、创建时间、数据表现
        records_to_write = []
        
        for content in state.contents:
            title = content.get("title", "")
            content_text = content.get("content", "")
            
            # 构建记录 - 表A结构
            record = {
                "fields": {
                    "账户名": state.account_name or "默认账户",
                    "标题": title,
                    "描述": content_text[:2000] if content_text else "",  # 限制长度
                    "话题": state.selected_topic,
                    "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "发布状态": "待发布"
                }
            }
            records_to_write.append(record)
        
        # 写入飞书表格
        write_result = {
            "success": False,
            "message": "",
            "records_attempted": len(records_to_write),
            "records_written": 0,
            "error": None
        }
        
        if records_to_write:
            try:
                result = client.add_records(
                    app_token=state.app_token,
                    table_id=state.table_id_a,
                    records=records_to_write
                )
                
                written_records = result.get("data", {}).get("records", [])
                write_result["success"] = True
                write_result["message"] = f"成功写入 {len(written_records)} 条记录"
                write_result["records_written"] = len(written_records)
                
            except Exception as write_error:
                write_result["message"] = f"写入飞书表格失败: {str(write_error)}"
                write_result["error"] = str(write_error)
        else:
            write_result["success"] = True
            write_result["message"] = "没有内容需要写入"
        
        return FeishuWriteOutput(
            write_result=write_result,
            feishu_access_token=current_token
        )
        
    except Exception as e:
        error_msg = f"处理飞书表格写入时出错: {str(e)}"
        logger.error(error_msg)
        return FeishuWriteOutput(
            write_result={
                "success": False,
                "message": error_msg,
                "records_attempted": len(state.contents) if hasattr(state, 'contents') else 0,
                "records_written": 0,
                "error": str(e)
            },
            feishu_access_token=state.feishu_access_token
        )
