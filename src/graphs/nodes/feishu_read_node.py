"""
历史数据读取节点 - 使用新的官方 lark-oapi SDK
"""
import logging
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import FeishuReadInput, FeishuReadOutput
from tools.feishu_client_helper import create_feishu_client, read_historical_data

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def feishu_read_node(
    state: FeishuReadInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> FeishuReadOutput:
    """
    title: 读取历史数据
    desc: 从飞书多维表格B读取已发布内容的历史数据表现，适配新的官方SDK
    integrations: 飞书多维表格
    """
    ctx = runtime.context
    
    app_token = state.app_token
    table_id_b = state.table_id_b
    feishu_app_id = state.feishu_app_id
    feishu_app_secret = state.feishu_app_secret
    
    logger.info(f"开始读取飞书历史数据: app_token={app_token}, table_id={table_id_b}")
    
    try:
        # 创建飞书客户端
        client = create_feishu_client(
            app_id=feishu_app_id,
            app_secret=feishu_app_secret
        )
        
        # 读取历史数据
        historical_data = read_historical_data(
            client=client,
            app_token=app_token,
            table_id=table_id_b
        )
        
        logger.info(f"成功读取 {len(historical_data)} 条历史数据")
        
        return FeishuReadOutput(
            historical_data=historical_data
        )
        
    except Exception as e:
        logger.error(f"读取飞书历史数据失败: {str(e)}")
        # 出错时返回空列表，让流程继续
        return FeishuReadOutput(
            historical_data=[]
        )

