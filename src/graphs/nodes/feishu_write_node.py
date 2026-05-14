"""
飞书表格写入节点 - 使用新的官方 lark-oapi SDK
"""
import logging
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import FeishuWriteInput, FeishuWriteOutput
from tools.feishu_client_helper import create_feishu_client, write_content_data

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def feishu_write_node(
    state: FeishuWriteInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> FeishuWriteOutput:
    """
    title: 写入飞书表格
    desc: 将生成的内容写入飞书多维表格A，适配新的官方SDK，表结构：编码、账户名、标题、描述、话题、文件、发布时间、发布状态、创建时间、数据表现
    integrations: 飞书多维表格
    """
    ctx = runtime.context
    
    app_token = state.app_token
    table_id_a = state.table_id_a
    feishu_app_id = state.feishu_app_id
    feishu_app_secret = state.feishu_app_secret
    contents = state.contents
    selected_topic = state.selected_topic
    account_name = state.account_name or ""
    
    logger.info(f"开始写入飞书表格: app_token={app_token}, table_id={table_id_a}")
    
    try:
        # 创建飞书客户端
        client = create_feishu_client(
            app_id=feishu_app_id,
            app_secret=feishu_app_secret
        )
        
        # 写入内容数据
        write_result = write_content_data(
            client=client,
            app_token=app_token,
            table_id=table_id_a,
            contents=contents,
            selected_topic=selected_topic,
            account_name=account_name
        )
        
        if write_result.get("success"):
            logger.info(f"成功写入飞书表格: {write_result.get('message')}")
        else:
            logger.warning(f"写入飞书表格失败: {write_result.get('message')}")
        
        return FeishuWriteOutput(
            write_result=write_result
        )
        
    except Exception as e:
        logger.error(f"写入飞书表格异常: {str(e)}")
        error_result = {
            "success": False,
            "message": f"写入飞书表格异常: {str(e)}",
            "error": str(e),
            "records_attempted": len(contents)
        }
        return FeishuWriteOutput(
            write_result=error_result
        )

