"""
基于Redis的任务管理器
支持并发任务管理和实时状态查询
"""

import json
import os
import redis.asyncio as redis
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RedisTaskManager:
    """基于Redis的任务管理器"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://39.106.11.230:6379/0")
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """连接Redis"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client

    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def create_task(self, task_id: str, user_input: str, metadata: Optional[Dict[str, Any]] = None):
        """创建新任务"""
        await self.connect()

        task_data = {
            "status": "pending",
            "user_input": user_input,
            "current_step": "created",
            "progress": 0.0,
            "message": "任务已创建，等待执行",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None,
            "error_message": "",
            "completed_at": None,
            "metadata": metadata or {}
        }

        key = f"task:{task_id}"
        await self.redis_client.setex(key, 3600 * 24, json.dumps(task_data, ensure_ascii=False))  # 24小时过期

        logger.info(f"任务创建成功: {task_id}")
        return task_data

    async def update_task_status(self, task_id: str, status: str, current_step: str = "",
                                progress: float = 0.0, message: str = "",
                                result: Any = None, error_message: str = ""):
        """更新任务状态"""
        await self.connect()

        key = f"task:{task_id}"
        task_data_str = await self.redis_client.get(key)

        if not task_data_str:
            logger.warning(f"任务不存在: {task_id}")
            return None

        task_data = json.loads(task_data_str)

        # 更新字段
        task_data["status"] = status
        if current_step:
            task_data["current_step"] = current_step
        if progress >= 0:
            task_data["progress"] = progress
        if message:
            task_data["message"] = message
        if result is not None:
            task_data["result"] = result
        if error_message:
            task_data["error_message"] = error_message

        task_data["updated_at"] = datetime.now().isoformat()

        if status in ["completed", "failed"]:
            task_data["completed_at"] = datetime.now().isoformat()

        # 保存回Redis
        await self.redis_client.setex(key, 3600 * 24, json.dumps(task_data, ensure_ascii=False))

        logger.info(f"任务状态更新: {task_id} -> {status} ({progress:.1%})")
        return task_data

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        await self.connect()

        key = f"task:{task_id}"
        task_data_str = await self.redis_client.get(key)

        if not task_data_str:
            return None

        return json.loads(task_data_str)

    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果"""
        task_data = await self.get_task_status(task_id)
        if not task_data:
            return None

        # 只有完成状态的任务才返回结果
        if task_data.get("status") != "completed":
            return None

        return task_data.get("result")

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        await self.connect()

        key = f"task:{task_id}"
        result = await self.redis_client.delete(key)

        logger.info(f"任务删除: {task_id}")
        return result > 0

    async def get_all_tasks(self, status_filter: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取所有任务"""
        await self.connect()

        # 获取所有task:*键
        keys = await self.redis_client.keys("task:*")
        tasks = {}

        for key in keys:
            task_data_str = await self.redis_client.get(key)
            if task_data_str:
                task_data = json.loads(task_data_str)
                task_id = key.replace("task:", "")

                # 状态过滤
                if status_filter and task_data.get("status") != status_filter:
                    continue

                tasks[task_id] = task_data

        return tasks

    async def cleanup_expired_tasks(self):
        """清理过期任务（Redis会自动过期，这里主要是为了清理可能的异常数据）"""
        await self.connect()

        # 获取所有任务
        tasks = await self.get_all_tasks()

        cleaned_count = 0
        for task_id, task_data in tasks.items():
            # 删除超过7天的完成/失败任务
            if task_data.get("status") in ["completed", "failed"]:
                completed_at = task_data.get("completed_at")
                if completed_at:
                    completed_time = datetime.fromisoformat(completed_at)
                    if (datetime.now() - completed_time).days > 7:
                        await self.delete_task(task_id)
                        cleaned_count += 1

        logger.info(f"清理过期任务: {cleaned_count} 个")
        return cleaned_count

    async def cleanup_stuck_tasks(self, timeout_minutes: int = 30):
        """
        清理卡住的任务（长时间处于running状态的任务）
        
        Args:
            timeout_minutes: 任务超时时间（分钟），默认30分钟
        """
        await self.connect()
        
        # 获取所有任务
        tasks = await self.get_all_tasks("running")
        
        cleaned_count = 0
        timeout_threshold = datetime.now() - timedelta(minutes=timeout_minutes)
        
        for task_id, task_data in tasks.items():
            # 检查任务是否超时
            updated_at = task_data.get("updated_at")
            if updated_at:
                updated_time = datetime.fromisoformat(updated_at)
                if updated_time < timeout_threshold:
                    # 标记任务为失败
                    await self.mark_task_failed(
                        task_id, 
                        f"任务执行超时（超过{timeout_minutes}分钟），已被系统自动终止"
                    )
                    cleaned_count += 1
                    
        logger.info(f"清理卡住的任务: {cleaned_count} 个")
        return cleaned_count

    # 便捷方法
    async def mark_task_running(self, task_id: str, step: str = "", message: str = ""):
        """标记任务为运行中"""
        return await self.update_task_status(
            task_id, "running", step or "running", 0.1, message or "任务执行中..."
        )

    async def mark_task_completed(self, task_id: str, result: Any):
        """标记任务为完成"""
        return await self.update_task_status(
            task_id, "completed", "completed", 1.0, "任务执行完成", result
        )

    async def mark_task_failed(self, task_id: str, error_message: str):
        """标记任务为失败"""
        return await self.update_task_status(
            task_id, "failed", "failed", 0.0, f"任务执行失败: {error_message}",
            error_message=error_message
        )