"""
任务执行器
支持线程池并发执行和实时进度跟踪
"""

import asyncio
import concurrent.futures
import json
import os
import redis
from functools import partial
from typing import Dict, Any, Callable, Optional
import logging
from datetime import datetime, timedelta

from task_manager import RedisTaskManager

logger = logging.getLogger(__name__)


class TaskExecutor:
    """支持线程池并发执行的任务执行器"""

    def __init__(self, max_workers: int = 4, redis_url: str = "redis://39.106.11.230:6379/0"):
        self.max_workers = max_workers
        self.redis_url = redis_url
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.task_manager = RedisTaskManager(redis_url)

    async def execute_task_async(self, task_id: str, user_input: str, task_function: Callable,
                                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        异步执行任务（通过线程池）

        Args:
            task_id: 任务ID
            user_input: 用户输入
            task_function: 实际执行任务的函数
            metadata: 额外元数据

        Returns:
            任务结果字典
        """
        # 创建任务记录
        await self.task_manager.create_task(task_id, user_input, metadata)

        # 标记为运行中
        await self.task_manager.mark_task_running(task_id, "initializing", "正在初始化任务...")

        # 获取事件循环
        loop = asyncio.get_event_loop()

        # 创建进度回调函数
        progress_callback = partial(self._progress_callback_sync, task_id)

        # 准备任务执行函数
        task_func = partial(self._execute_single_task,
                           task_id=task_id,
                           user_input=user_input,
                           task_function=task_function,
                           progress_callback=progress_callback)

        try:
            # 提交到线程池执行
            future = loop.run_in_executor(self.executor, task_func)

            # 等待执行完成
            result = await future

            # 标记任务完成
            await self.task_manager.mark_task_completed(task_id, result)

            logger.info(f"任务执行成功: {task_id}")
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"任务执行失败: {task_id} - {error_msg}")

            # 标记任务失败
            await self.task_manager.mark_task_failed(task_id, error_msg)
            raise

    def _execute_single_task(self, task_id: str, user_input: str,
                           task_function: Callable, progress_callback: Callable):
        """
        在独立线程中执行单个任务

        Args:
            task_id: 任务ID
            user_input: 用户输入
            task_function: 任务执行函数
            progress_callback: 进度回调函数
        """
        try:
            # 执行实际任务
            result = task_function(task_id, user_input, progress_callback)

            logger.info(f"线程内任务执行完成: {task_id}")
            return result

        except Exception as e:
            logger.error(f"线程内任务执行异常: {task_id} - {str(e)}")
            raise

    def _progress_callback_sync(self, task_id: str, step: str, progress: float, message: str):
        """
        完全同步的进度回调函数（在工作线程中调用）
        使用同步Redis连接进行进度更新，避免事件循环冲突

        Args:
            task_id: 任务ID
            step: 当前步骤
            progress: 进度 (0.0-1.0)
            message: 状态消息
        """
        try:
            # 创建同步Redis连接专门用于进度更新
            sync_redis = redis.from_url(self.redis_url, decode_responses=True)

            # 构建任务更新数据
            update_data = {
                "status": "running",
                "current_step": step,
                "progress": progress,
                "message": message,
                "updated_at": datetime.now().isoformat()
            }

            key = f"task:{task_id}"

            # 获取现有任务数据
            existing_data_str = sync_redis.get(key)
            if existing_data_str:
                try:
                    existing_data = json.loads(existing_data_str)
                    # 更新现有数据
                    existing_data.update(update_data)
                    # 保存更新后的数据
                    sync_redis.setex(key, 3600 * 24, json.dumps(existing_data, ensure_ascii=False))
                    logger.debug(f"进度更新成功: {task_id} - {step} ({progress:.1%}) - {message}")
                except json.JSONDecodeError as je:
                    logger.error(f"JSON解析失败: {task_id} - {str(je)}")
                    # 如果JSON解析失败，创建新的任务数据
                    task_data = {
                        "status": "running",
                        "user_input": "",
                        "current_step": step,
                        "progress": progress,
                        "message": message,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "result": None,
                        "error_message": "",
                        "completed_at": None,
                        "metadata": {}
                    }
                    sync_redis.setex(key, 3600 * 24, json.dumps(task_data, ensure_ascii=False))
                    logger.warning(f"创建新任务数据: {task_id} - {step}")
            else:
                logger.warning(f"任务不存在，无法更新进度: {task_id}")

            # 关闭同步Redis连接
            sync_redis.close()

        except Exception as e:
            logger.error(f"同步进度更新失败: {task_id} - {str(e)}")

    async def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)
        await self.task_manager.disconnect()
        logger.info("任务执行器已关闭")

    async def get_active_tasks_count(self, timeout_minutes: int = 30) -> int:
        """
        获取活跃任务数量
        
        Args:
            timeout_minutes: 任务超时时间（分钟），默认30分钟
            
        Returns:
            活跃任务数量（排除超时任务）
        """
        tasks = await self.task_manager.get_all_tasks("running")
        
        # 过滤掉超时的任务
        active_count = 0
        timeout_threshold = datetime.now() - timedelta(minutes=timeout_minutes)
        
        for task in tasks.values():
            updated_at = task.get("updated_at")
            if updated_at:
                updated_time = datetime.fromisoformat(updated_at)
                # 如果任务更新时间在超时阈值之后，则认为是活跃任务
                if updated_time >= timeout_threshold:
                    active_count += 1
                    
        return active_count

    async def get_effective_active_tasks_count(self) -> int:
        """
        获取有效的活跃任务数量（考虑系统资源和实际负载）
        
        Returns:
            有效的活跃任务数量
        """
        # 获取基本的活跃任务数量
        basic_active_count = await self.get_active_tasks_count()
        
        # 可以根据系统资源情况动态调整（这里简化处理）
        # 在实际应用中，可以根据CPU、内存等资源使用情况来调整
        
        return min(basic_active_count, self.max_workers)

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务（标记为失败）

        注意：由于任务在工作线程中执行，实际无法中断执行，
        这里只是更新状态为失败
        """
        try:
            await self.task_manager.mark_task_failed(task_id, "任务已被取消")
            logger.info(f"任务已取消: {task_id}")
            return True
        except Exception as e:
            logger.error(f"取消任务失败: {task_id} - {str(e)}")
            return False


class XiaohongshuTaskExecutor(TaskExecutor):
    """专门用于小红书任务执行的执行器"""

    def __init__(self, max_workers: Optional[int] = None, redis_url: Optional[str] = None):
        # 从环境变量读取配置
        max_workers = max_workers or int(os.getenv("MAX_CONCURRENT_TASKS", "6"))
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://39.106.11.230:6379/0")

        super().__init__(max_workers, redis_url)

    async def execute_xiaohongshu_task(self, task_id: str, user_input: str) -> Dict[str, Any]:
        """
        执行小红书内容创作任务

        Args:
            task_id: 任务ID
            user_input: 用户输入的内容需求

        Returns:
            任务执行结果
        """
        from agent_factory import ThreadSafeAgentFactory

        def task_function(task_id: str, user_input: str, progress_callback: Callable):
            """实际执行小红书任务的函数"""
            return self._execute_xiaohongshu_workflow(task_id, user_input, progress_callback)

        return await self.execute_task_async(task_id, user_input, task_function)

    def _execute_xiaohongshu_workflow(self, task_id: str, user_input: str, progress_callback: Callable) -> Dict[str, Any]:
        """
        执行小红书工作流（在工作线程中）
        包含详细的进度跟踪和错误处理

        Args:
            task_id: 任务ID
            user_input: 用户输入
            progress_callback: 进度回调函数

        Returns:
            工作流执行结果
        """
        try:
            from agent_factory import ThreadSafeAgentFactory

            # 阶段1: 初始化任务
            progress_callback("initializing", 0.05, "正在初始化小红书内容创作工作流...")

            # 创建线程安全的智能体实例，并传入进度回调
            progress_callback("creating_agents", 0.10, "正在创建智能体实例...")
            supervisor_agent = ThreadSafeAgentFactory.create_supervisor_agent(
                progress_callback=lambda task_id, step, progress, message: progress_callback(step, progress, message)
            )

            # 阶段2: 执行完整工作流
            progress_callback("workflow_start", 0.15, "开始执行小红书内容创作工作流...")

            # 执行工作流 - 这里会在各个子步骤中进行详细的进度更新
            result = supervisor_agent.invoke({
                "messages": [{"role": "user", "content": user_input}],
                "user_input": user_input,
                "task_id": task_id
            })

            # 阶段3: 结果整理和验证
            progress_callback("processing_results", 0.85, "正在处理和验证创作结果...")

            final_output = result.get("final_output")

            if final_output and final_output.get("success"):
                progress_callback("validation_success", 0.95, "结果验证通过，正在生成最终输出...")
                progress_callback("completed", 1.0, "小红书内容创作任务完成！")
                return final_output
            else:
                error_msg = final_output.get("error_message", "执行失败") if final_output else "未知错误"
                progress_callback("error", 0.0, f"工作流执行失败: {error_msg}")
                raise Exception(f"工作流执行失败: {error_msg}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"小红书工作流执行异常: {task_id} - {error_msg}")
            progress_callback("workflow_error", 0.0, f"工作流执行出现异常: {error_msg}")
            raise