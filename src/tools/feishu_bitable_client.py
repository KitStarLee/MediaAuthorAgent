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

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import (
    CreateAppTableRecordRequest,
    GetAppTableRecordRequest,
    UpdateAppTableRecordRequest,
    DeleteAppTableRecordRequest,
    ListAppTableRecordRequest,
    BatchCreateAppTableRecordRequest,
    BatchUpdateAppTableRecordRequest,
    BatchDeleteAppTableRecordRequest,
    AppTableRecord,
    BatchCreateAppTableRecordRequestBody,
    BatchUpdateAppTableRecordRequestBody,
    BatchDeleteAppTableRecordRequestBody,
)
from lark_oapi.client import ClientBuilder

class FeishuBitableClient:
    """
    飞书多维表格（Bitable）HTTP 客户端 - 优化版
    支持缓存 access token，避免重复获取
    """
    def __init__(
        self,
        timeout: int = 30,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        personal_base_token: Optional[str] = None
    ):
        self.timeout = timeout
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0

        builder = ClientBuilder()

        if app_id and app_secret:
            builder = builder.app_id(app_id).app_secret(app_secret)
        elif personal_base_token:
            builder = builder.enable_set_token(True).source(personal_base_token)
        else:
            raise ValueError("必须提供 app_id/app_secret 或 personal_base_token")
        
        self.client: lark.Client = builder.build()
        
  

    def _record_to_dict(self, record: AppTableRecord) -> Dict[str, Any]:
        """将 AppTableRecord 对象转换为字典"""
        return {
            "record_id": record.record_id if record.record_id else "",
            "fields": record.fields if record.fields else {},
            "created_time": record.created_time if record.created_time else 0,
            "last_modified_time": record.last_modified_time if record.last_modified_time else 0,
            "record_url": record.record_url if record.record_url else "",
        }
    
    def create_record(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """创建记录"""
        req = CreateAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .request_body(AppTableRecord.builder().fields(fields).build())\
            .build()
        
        resp = self.client.bitable.v1.app_table_record.create(req)
        if resp.success():
            record = resp.data.record
            return {"code": 0, "data": self._record_to_dict(record)}
        else:
            print(f"API调用失败 - code: {resp.code}, msg: {resp.msg}")
            print(f"请求参数 - app_token: {app_token}, table_id: {table_id}, fields: {fields}")
            return {"code": resp.code, "msg": resp.msg, "data": {}}
    
    def get_record(self, app_token: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """获取单条记录"""
        req = GetAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .record_id(record_id)\
            .build()
        
        resp = self.client.bitable.v1.app_table_record.get(req)
        if resp.success():
            record = resp.data.record
            return {"code": 0, "data": self._record_to_dict(record)}
        else:
            return {"code": resp.code, "msg": resp.msg, "data": {}}
    
    def update_record(self, app_token: str, table_id: str, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """更新记录"""
        req = UpdateAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .record_id(record_id)\
            .request_body(AppTableRecord.builder().fields(fields).build())\
            .build()
        
        resp = self.client.bitable.v1.app_table_record.update(req)
        if resp.success():
            record = resp.data.record
            return {"code": 0, "data": self._record_to_dict(record)}
        else:
            return {"code": resp.code, "msg": resp.msg, "data": {}}
    
    def delete_record(self, app_token: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """删除记录"""
        req = DeleteAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .record_id(record_id)\
            .build()
        
        resp = self.client.bitable.v1.app_table_record.delete(req)
        if resp.success():
            return {"code": 0, "data": {"record_id": record_id}}
        else:
            return {"code": resp.code, "msg": resp.msg, "data": {}}
    
    def list_records(self, app_token: str, table_id: str, view_id: Optional[str] = None, 
                     page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
        """查询记录列表"""
        req = ListAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .page_size(page_size)
        
        if view_id:
            req = req.view_id(view_id)
        if page_token:
            req = req.page_token(page_token)
        
        resp = self.client.bitable.v1.app_table_record.list(req.build())
        if resp.success():
            items = []
            if resp.data.items:
                for item in resp.data.items:
                    items.append(self._record_to_dict(item))
            return {
                "code": 0, 
                "data": {
                    "items": items,
                    "page_token": resp.data.page_token if resp.data.page_token else "",
                    "total": resp.data.total if resp.data.total else 0
                }
            }
        else:
            return {"code": resp.code, "msg": resp.msg, "data": {}}
    
    def batch_create_records(self, app_token: str, table_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量创建记录"""
        record_list = []
        for record in records:
            record_list.append(AppTableRecord.builder().fields(record.get("fields", {})).build())
        
        req = BatchCreateAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(record_list).build())\
            .build()
        
        resp = self.client.bitable.v1.app_table_record.batch_create(req)
        if resp.success():
            items = []
            if resp.data.items:
                for item in resp.data.items:
                    items.append(self._record_to_dict(item))
            return {"code": 0, "data": {"items": items}}
        else:
            return {"code": resp.code, "msg": resp.msg, "data": {}}
    
    def batch_update_records(self, app_token: str, table_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量更新记录"""
        record_list = []
        for record in records:
            record_list.append(AppTableRecord.builder()\
                .record_id(record.get("record_id", ""))\
                .fields(record.get("fields", {}))\
                .build())
        
        req = BatchUpdateAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .request_body(BatchUpdateAppTableRecordRequestBody.builder().records(record_list).build())\
            .build()
        
        resp = self.client.bitable.v1.app_table_record.batch_update(req)
        if resp.success():
            items = []
            if resp.data.items:
                for item in resp.data.items:
                    items.append(self._record_to_dict(item))
            return {"code": 0, "data": {"items": items}}
        else:
            return {"code": resp.code, "msg": resp.msg, "data": {}}
    
    def batch_delete_records(self, app_token: str, table_id: str, record_ids: List[str]) -> Dict[str, Any]:
        """批量删除记录"""
        req = BatchDeleteAppTableRecordRequest.builder()\
            .app_token(app_token)\
            .table_id(table_id)\
            .request_body(BatchDeleteAppTableRecordRequestBody.builder().record_ids(record_ids).build())\
            .build()
        
        resp = self.client.bitable.v1.app_table_record.batch_delete(req)
        if resp.success():
            return {"code": 0, "data": {"record_ids": record_ids}}
        else:
            return {"code": resp.code, "msg": resp.msg, "data": {}}


