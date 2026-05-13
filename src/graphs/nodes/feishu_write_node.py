import datetime
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_workload_identity import Client
from cozeloop.decorator import observe
import requests
from functools import wraps

from graphs.state import FeishuWriteInput, FeishuWriteOutput


# 飞书多维表格客户端类
class FeishuBitable:
    """
    飞书多维表格（Bitable）HTTP 客户端。
    所有方法返回值均为 Feishu OpenAPI 标准响应："{\"code\": int, \"msg\": str, \"data\": any}"
    基础 URL 默认 "https://open.larkoffice.com/open-apis"。
    """
    def __init__(self, base_url: str = "https://open.larkoffice.com/open-apis", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.access_token = self._get_access_token()

    @staticmethod
    def _get_access_token() -> str:
        """
        获取飞书多维表格（Bitable）的租户访问令牌。
        """
        client = Client()
        access_token = client.get_integration_credential("integration-feishu-base")
        return access_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
            "Content-Type": "application/json; charset=utf-8",
        }

    @observe
    def _request(self, method: str, path: str, params: dict | None = None, json: dict | None = None) -> dict:
        try:
            url = f"{self.base_url}{path}"
            resp = requests.request(method, url, headers=self._headers(), params=params, json=json, timeout=self.timeout)
            resp_data = resp.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"FeishuBitable API request error: {e}")
        if resp_data.get("code") != 0:
            raise Exception(f"FeishuBitable API error: {resp_data}")
        return resp_data

    def add_records(
        self,
        app_token: str,
        table_id: str,
        records: list,
        user_id_type: str | None = None,
        client_token: str | None = None,
        ignore_consistency_check: bool | None = None,
    ) -> dict:
        """
        批量新增记录
        """
        params: dict = {}
        if user_id_type is not None:
            params["user_id_type"] = user_id_type
        if client_token is not None:
            params["client_token"] = client_token
        if ignore_consistency_check is not None:
            params["ignore_consistency_check"] = ignore_consistency_check
        body = {"records": records}
        return self._request("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create", params=params, json=body)


def feishu_write_node(state: FeishuWriteInput, config: RunnableConfig, runtime: Runtime[Context]) -> FeishuWriteOutput:
    """
    title: 飞书表格写入
    desc: 将生成的内容草稿自动写入指定的飞书多维表格A，表结构包含：编码、账户名、标题、描述、话题、文件、发布时间、发布状态、创建时间、数据表现
    integrations: 飞书多维表格
    """
    ctx = runtime.context
    
    # 初始化飞书客户端
    feishu_client = FeishuBitable()
    
    # 生成当前时间
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 准备要写入的记录 - 适配表A结构
    records = []
    for idx, content_item in enumerate(state.contents):
        title = content_item.get("title", f"内容{idx + 1}")
        content = content_item.get("content", "")
        
        # 表A字段：编码、账户名、标题、描述、话题、文件、发布时间、发布状态、创建时间、数据表现
        record = {
            "fields": {
                "账户名": state.account_name or "",
                "标题": title,
                "描述": content[:1000] if len(content) > 1000 else content,  # 限制描述长度
                "话题": state.selected_topic,
                "发布状态": "草稿",
                "创建时间": current_time
            }
        }
        records.append(record)
    
    write_result = {}
    try:
        # 调用飞书API写入记录
        response = feishu_client.add_records(
            app_token=state.app_token_a,
            table_id=state.table_id_a,
            records=records
        )
        write_result = {
            "success": True,
            "message": f"成功写入{len(records)}条内容到飞书表格",
            "data": response.get("data", {}),
            "records_written": len(records)
        }
    except Exception as e:
        write_result = {
            "success": False,
            "message": f"写入飞书表格失败: {str(e)}",
            "error": str(e),
            "records_attempted": len(records)
        }
    
    return FeishuWriteOutput(write_result=write_result)
