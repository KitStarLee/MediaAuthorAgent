"""
飞书多维表格共享工具模块
提供统一的飞书表格操作类，复用连接和token
"""
import os
import requests
import time
from typing import Optional, Dict, Any, List
from functools import wraps
from cozeloop.decorator import observe
from coze_workload_identity import Client


class FeishuBitable:
    """
    飞书多维表格（Bitable）HTTP 客户端 - 优化版
    支持缓存 access token，避免重复获取
    """
    def __init__(
        self,
        base_url: str = "https://open.larkoffice.com/open-apis",
        timeout: int = 30,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0
        
        # 初始化token
        self._init_token()

    def _init_token(self):
        """初始化访问令牌"""
        if self.app_id and self.app_secret:
            # 使用自定义认证
            self._get_custom_token()
        else:
            # 使用平台托管集成
            self._get_platform_token()

    def _get_platform_token(self) -> str:
        """
        通过平台托管集成获取访问令牌
        """
        client = Client()
        self._access_token = client.get_integration_credential("integration-feishu-base")
        if not self._access_token:
            raise ValueError("FEISHU_TENANT_ACCESS_TOKEN is not set")
        return self._access_token

    def _get_custom_token(self) -> str:
        """
        使用自定义 APP_ID 和 APP_SECRET 获取访问令牌
        参考: https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
        """
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp_data = resp.json()
            
            if resp_data.get("code") != 0:
                raise Exception(f"获取飞书租户访问令牌失败: {resp_data}")
            
            self._access_token = resp_data["tenant_access_token"]
            # 设置过期时间（提前5分钟过期）
            expire_seconds = resp_data.get("expire", 7200) - 300
            self._token_expire_time = time.time() + expire_seconds
            
            return self._access_token
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取飞书租户访问令牌网络错误: {e}")

    def _ensure_token(self):
        """确保token有效，如果过期则刷新"""
        if self.app_id and self.app_secret:
            if time.time() >= self._token_expire_time:
                self._get_custom_token()
        elif not self._access_token:
            self._get_platform_token()

    def _headers(self) -> dict:
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self._access_token}" if self._access_token else "",
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

    def get_access_token(self) -> str:
        """获取当前的访问令牌"""
        self._ensure_token()
        return self._access_token

    # ===== 数据表操作 =====

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

    def list_fields(
        self,
        app_token: str,
        table_id: str,
        view_id: str | None = None,
        text_field_as_array: bool | None = None,
        page_token: str | None = None,
        page_size: int | None = None,
    ) -> dict:
        """
        列出数据表字段
        """
        params: dict = {}
        if view_id is not None:
            params["view_id"] = view_id
        if text_field_as_array is not None:
            params["text_field_as_array"] = text_field_as_array
        if page_token is not None:
            params["page_token"] = page_token
        if page_size is not None:
            params["page_size"] = page_size
        return self._request("GET", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields", params=params)


# ===== 便捷函数 =====

def create_feishu_client(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    cached_token: Optional[str] = None
) -> FeishuBitable:
    """
    创建飞书客户端的便捷函数
    如果提供了 cached_token，可以先尝试使用缓存的token
    """
    client = FeishuBitable(app_id=app_id, app_secret=app_secret)
    return client


def get_or_create_client(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    cached_token: Optional[str] = None
) -> tuple[FeishuBitable, Optional[str]]:
    """
    获取或创建飞书客户端，并返回客户端和当前token
    """
    client = create_feishu_client(app_id, app_secret)
    current_token = client.get_access_token()
    return client, current_token
