"""
飞书客户端辅助模块
提供统一的客户端初始化和操作接口
"""
from typing import Optional, Dict, Any, List
from tools.feishu_bitable_client import FeishuBitableClient


def create_feishu_client(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    timeout: int = 30
) -> FeishuBitableClient:
    """
    创建飞书多维表格客户端
    
    Args:
        app_id: 飞书应用ID（可选）
        app_secret: 飞书应用密钥（可选）
        timeout: 请求超时时间（秒）
        
    Returns:
        FeishuBitableClient: 初始化好的客户端实例
    """
    if app_id and app_secret:
        # 使用自定义认证
        return FeishuBitableClient(
            timeout=timeout,
            app_id=app_id,
            app_secret=app_secret
        )
    else:
        # 如果没有提供认证信息，这里可以使用平台托管的方式
        # 目前我们要求用户必须提供 app_id 和 app_secret
        raise ValueError("必须提供 feishu_app_id 和 feishu_app_secret")


def read_historical_data(
    client: FeishuBitableClient,
    app_token: str,
    table_id: str,
    page_size: int = 100
) -> List[Dict[str, Any]]:
    """
    读取历史数据（表B）
    
    Args:
        client: 飞书客户端
        app_token: 应用token
        table_id: 表格ID
        page_size: 每页大小
        
    Returns:
        历史数据列表
    """
    result = []
    
    try:
        # 使用官方SDK的方式读取记录
        page_token = None
        has_more = True
        
        while has_more:
            resp = client.list_records(
                app_token=app_token,
                table_id=table_id,
                page_size=page_size,
                page_token=page_token
            )
            
            if resp.get("code") == 0:
                data = resp.get("data", {})
                items = data.get("items", [])
                
                for item in items:
                    fields = item.get("fields", {})
                    result.append({
                        "record_id": item.get("record_id", ""),
                        "platform": fields.get("平台", ""),
                        "content_id": fields.get("内容ID", ""),
                        "likes": fields.get("点赞", 0),
                        "favorites": fields.get("收藏", 0),
                        "comments": fields.get("评论", 0),
                        "shares": fields.get("分享", 0)
                    })
                
                page_token = data.get("page_token")
                has_more = bool(page_token)
            else:
                raise Exception(f"读取历史数据失败: {resp.get('msg', '未知错误')}")
                
    except Exception as e:
        raise Exception(f"读取历史数据异常: {str(e)}")
    
    return result


def write_content_data(
    client: FeishuBitableClient,
    app_token: str,
    table_id: str,
    contents: List[Dict[str, str]],
    selected_topic: str,
    account_name: str = ""
) -> Dict[str, Any]:
    """
    写入内容数据（表A）
    
    Args:
        client: 飞书客户端
        app_token: 应用token
        table_id: 表格ID
        contents: 内容列表
        selected_topic: 选定的选题
        account_name: 账户名
        
    Returns:
        写入结果
    """
    import datetime
    
    records = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for content in contents:
        title = content.get("title", "")
        content_text = content.get("content", "")
        
        record_data = {
            "账户名": account_name,
            "标题": title,
            "描述": content_text[:200] if len(content_text) > 200 else content_text,
            "话题": selected_topic,
            "发布时间": now,
            "发布状态": "待发布",
        }
        
        records.append({
            "fields": record_data
        })
    
    try:
        # 批量创建记录
        resp = client.batch_create_records(
            app_token=app_token,
            table_id=table_id,
            records=records
        )
        
        if resp.get("code") == 0:
            items = resp.get("data", {}).get("items", [])
            record_ids = [item.get("record_id", "") for item in items]
            
            return {
                "success": True,
                "message": f"成功写入 {len(records)} 条记录",
                "records_written": len(records),
                "record_ids": record_ids
            }
        else:
            return {
                "success": False,
                "message": f"写入飞书表格失败: {resp.get('msg', '未知错误')}",
                "error": f"code: {resp.get('code')}, msg: {resp.get('msg')}",
                "records_attempted": len(records)
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"写入飞书表格异常: {str(e)}",
            "error": str(e),
            "records_attempted": len(records)
        }

