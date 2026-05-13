from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_workload_identity import Client
from cozeloop.decorator import observe
import requests
from functools import wraps

from graphs.state import FeishuReadInput, FeishuReadOutput


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

    def search_record(
        self,
        app_token: str,
        table_id: str,
        view_id: str | None = None,
        field_names: list[str] | None = None,
        sort: list | None = None,
        filter: dict | str | None = None,
        page_token: str | None = None,
        page_size: int | None = None,
        user_id_type: str | None = None,
    ) -> dict:
        """
        条件查询记录
        """
        params: dict = {}
        if user_id_type is not None:
            params["user_id_type"] = user_id_type
        if page_token is not None:
            params["page_token"] = page_token
        if page_size is not None:
            params["page_size"] = page_size
        body: dict = {}
        if view_id is not None:
            body["view_id"] = view_id
        if field_names is not None:
            body["field_names"] = field_names
        if sort is not None:
            body["sort"] = sort
        if filter is not None:
            body["filter"] = filter
        return self._request("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/search", params=params, json=body)


def feishu_read_node(state: FeishuReadInput, config: RunnableConfig, runtime: Runtime[Context]) -> FeishuReadOutput:
    """
    title: 历史数据读取
    desc: 从飞书多维表格B中读取已发布内容的历史数据表现
    integrations: 飞书多维表格
    """
    ctx = runtime.context
    
    # 初始化飞书客户端
    feishu_client = FeishuBitable()
    
    historical_data = []
    try:
        # 调用飞书API读取记录
        response = feishu_client.search_record(
            app_token=state.app_token_b,
            table_id=state.table_id_b,
            page_size=100  # 最多读取100条记录
        )
        
        # 提取记录数据
        items = response.get("data", {}).get("items", [])
        for item in items:
            record_data = {
                "record_id": item.get("record_id", ""),
                "fields": item.get("fields", {}),
                "last_modified_time": item.get("last_modified_time", "")
            }
            historical_data.append(record_data)
            
    except Exception as e:
        # 如果读取失败，返回空列表并记录错误
        historical_data = []
        # 可以在这里添加日志记录
    
    return FeishuReadOutput(historical_data=historical_data)
