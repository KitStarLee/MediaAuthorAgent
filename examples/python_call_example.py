#!/usr/bin/env python3
"""
工作流 Python 调用示例
展示如何在 Python 代码中直接调用工作流，以及多用户使用的架构
"""

import sys
import os
import asyncio
import json
from typing import Dict, Any, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class WorkflowClient:
    """
    工作流客户端封装类
    支持在 Python 代码中直接调用工作流
    """
    
    def __init__(self, user_token: Optional[str] = None):
        """
        初始化工作流客户端
        
        Args:
            user_token: 用户的 token（如果需要区分不同用户）
        """
        self.user_token = user_token
        self._load_graph()
    
    def _load_graph(self):
        """
        内部方法：加载工作流图
        """
        from graphs.graph import main_graph
        from coze_coding_utils.runtime_ctx.context import new_context
        
        self.graph = main_graph
        self.new_context = new_context
    
    async def call_workflow(
        self,
        user_demand: str,
        background: Optional[str] = None,
        historical_data: Optional[list] = None,
        content_count: int = 3,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调用工作流
        
        Args:
            user_demand: 用户具体需求描述
            background: 背景描述（可选）
            historical_data: 历史数据（可选）
            content_count: 生成内容数量
            user_id: 用户ID（可选，用于区分不同用户）
            
        Returns:
            工作流执行结果
        """
        # 构建 payload
        payload = {
            "user_demand": user_demand,
            "background": background,
            "historical_data": historical_data,
            "content_count": content_count
        }
        
        # 如果需要区分用户，可以在这里设置相关信息
        # 注意：当前工作流本身是无状态的，不直接处理用户token
        # Token 消耗由工作流内部使用的 LLM 决定
        
        # 创建 context
        ctx = self.new_context(method="python_call")
        if user_id:
            ctx.run_id = f"{user_id}_{ctx.run_id}"
        
        # 导入需要的模块
        from src.main import service
        
        # 调用服务
        try:
            result = await service.run(payload, ctx)
            return result
        except Exception as e:
            print(f"工作流调用失败: {e}")
            raise


class MultiUserWorkflowManager:
    """
    多用户工作流管理器
    用于管理不同用户的调用，每个用户消耗自己的token
    """
    
    def __init__(self):
        self.user_clients: Dict[str, WorkflowClient] = {}
    
    def register_user(self, user_id: str, user_token: Optional[str] = None) -> WorkflowClient:
        """
        注册用户
        
        Args:
            user_id: 用户ID
            user_token: 用户的 token
            
        Returns:
            用户的工作流客户端
        """
        if user_id not in self.user_clients:
            self.user_clients[user_id] = WorkflowClient(user_token)
        return self.user_clients[user_id]
    
    async def call_for_user(
        self,
        user_id: str,
        user_demand: str,
        background: Optional[str] = None,
        historical_data: Optional[list] = None,
        content_count: int = 3
    ) -> Dict[str, Any]:
        """
        为特定用户调用工作流
        
        Args:
            user_id: 用户ID
            user_demand: 用户具体需求描述
            background: 背景描述（可选）
            historical_data: 历史数据（可选）
            content_count: 生成内容数量
            
        Returns:
            工作流执行结果
        """
        # 获取或创建用户的客户端
        client = self.register_user(user_id)
        
        # 调用工作流
        result = await client.call_workflow(
            user_demand=user_demand,
            background=background,
            historical_data=historical_data,
            content_count=content_count,
            user_id=user_id
        )
        
        return result


# ============================================
# 使用示例
# ============================================

async def example_single_user_call():
    """
    示例1：单个用户直接调用
    """
    print("=" * 60)
    print("示例1：单个用户直接调用")
    print("=" * 60)
    
    # 创建客户端
    client = WorkflowClient()
    
    # 调用工作流
    result = await client.call_workflow(
        user_demand="我想做一个关于Python编程技巧的自媒体账号，分享实用的Python技巧和最佳实践",
        background="目标受众是Python初学者和中级开发者，他们想通过学习实用技巧来提高编程效率",
        content_count=2
    )
    
    # 输出结果
    print("\n生成结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


async def example_multi_user_call():
    """
    示例2：多用户调用管理
    """
    print("\n" + "=" * 60)
    print("示例2：多用户调用管理")
    print("=" * 60)
    
    # 创建多用户管理器
    manager = MultiUserWorkflowManager()
    
    # 用户A调用
    print("\n--- 用户A调用 ---")
    result_a = await manager.call_for_user(
        user_id="user_a",
        user_demand="我想做美食类内容，分享简单又好吃的家常菜做法",
        background="目标受众是上班族和新手厨师，想快速做出美味的家常菜",
        content_count=1
    )
    print(f"用户A生成了 {len(result_a.get('contents', []))} 篇内容")
    
    # 用户B调用
    print("\n--- 用户B调用 ---")
    result_b = await manager.call_for_user(
        user_id="user_b",
        user_demand="我想做健身类内容，分享家庭健身训练方法",
        background="目标受众是想在家健身但不知道怎么开始的人",
        content_count=1
    )
    print(f"用户B生成了 {len(result_b.get('contents', []))} 篇内容")


async def main():
    """
    主函数：运行所有示例
    """
    print("\n" + "=" * 60)
    print("工作流 Python 调用示例")
    print("=" * 60)
    
    try:
        # 示例1：单个用户调用
        await example_single_user_call()
        
        # 示例2：多用户调用
        await example_multi_user_call()
        
    except Exception as e:
        print(f"\n示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
