"""
小红书多智能体API服务器 - Redis版本
支持并发任务处理和实时状态查询
基于LangChain架构，直接返回结构化数据给后端
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 导入新的组件
from task_manager import RedisTaskManager
from task_executor import XiaohongshuTaskExecutor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic模型定义
class XiaohongshuTaskRequest(BaseModel):
    """小红书任务请求"""
    user_input: str = Field(..., description="用户输入的内容需求", example="帮我创作一个关于咖啡的笔记")
    task_mode: str = Field("auto_output", description="任务模式", example="auto_output")
    options: Dict[str, Any] = Field(default_factory=dict, description="额外选项")


class XiaohongshuTaskResponse(BaseModel):
    """任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    estimated_duration: int = Field(..., description="预估耗时(秒)")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    current_step: str
    progress: float
    message: str
    created_at: str
    updated_at: str


# 创建全局组件实例（从环境变量读取配置）
task_manager = RedisTaskManager()
task_executor = XiaohongshuTaskExecutor()  # 从环境变量读取配置


# 任务执行函数已移至XiaohongshuTaskExecutor中


# 全局变量用于存储后台任务引用
background_cleanup_task = None

async def periodic_task_cleanup():
    """定期清理卡住的任务"""
    while True:
        try:
            # 每5分钟清理一次卡住的任务
            await asyncio.sleep(300)
            logger.info("开始定期清理卡住的任务...")
            cleaned_count = await task_manager.cleanup_stuck_tasks()
            logger.info(f"定期清理完成，共清理 {cleaned_count} 个卡住的任务")
        except Exception as e:
            logger.error(f"定期任务清理出错: {e}")

# FastAPI应用配置
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("小红书多智能体API服务器启动中...")

    # 启动时初始化连接
    try:
        await task_manager.connect()
        logger.info("Redis连接已建立")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        raise

    # 启动后台定时清理任务
    global background_cleanup_task
    background_cleanup_task = asyncio.create_task(periodic_task_cleanup())
    logger.info("后台定时任务清理器已启动")

    yield

    # 关闭时清理资源
    logger.info("小红书多智能体API服务器关闭")
    
    # 取消后台定时任务
    if background_cleanup_task:
        background_cleanup_task.cancel()
        try:
            await background_cleanup_task
        except asyncio.CancelledError:
            pass
    
    await task_executor.shutdown()
    await task_manager.disconnect()


app = FastAPI(
    title="小红书多智能体API",
    description="基于LangChain架构的小红书内容创作多智能体API，直接返回结构化数据",
    version="1.0.0",
    lifespan=lifespan
)

# 配置FastAPI使用自定义JSON编码器，避免转义特殊字符
from fastapi.responses import JSONResponse

class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            separators=(',', ':'),
            indent=None  # 保持紧凑格式
        ).encode('utf-8')

# 为所有路由设置默认响应类
app.router.default_response_class = CustomJSONResponse

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API路由
@app.post("/api/v1/xiaohongshu/tasks", response_model=XiaohongshuTaskResponse)
async def create_xiaohongshu_task(request: XiaohongshuTaskRequest):
    """创建小红书内容创作任务"""
    try:
        # 生成任务ID
        task_id = f"xhs_{uuid.uuid4().hex[:16]}"

        # 定期清理卡住的任务（每100个请求清理一次）
        import random
        if random.randint(1, 100) == 1:
            await task_manager.cleanup_stuck_tasks()

        # 检查当前活跃任务数量，避免过载
        active_tasks = await task_executor.get_active_tasks_count()
        if active_tasks >= task_executor.max_workers:
            # 在拒绝请求前再次尝试清理卡住的任务
            await task_manager.cleanup_stuck_tasks()
            # 重新检查活跃任务数量
            active_tasks = await task_executor.get_active_tasks_count()
            
            # 如果仍然超过限制，则拒绝请求
            if active_tasks >= task_executor.max_workers:
                raise HTTPException(
                    status_code=429,
                    detail=f"服务器忙碌中，请稍后再试。当前活跃任务: {active_tasks}"
                )

        # 异步执行任务（使用线程池）
        asyncio.create_task(
            task_executor.execute_xiaohongshu_task(task_id, request.user_input)
        )

        logger.info(f"任务创建成功: {task_id}, 当前活跃任务: {active_tasks}")

        return XiaohongshuTaskResponse(
            task_id=task_id,
            status="pending",
            message="任务创建成功，正在处理中...",
            estimated_duration=180  # 预估3分钟
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@app.get("/api/v1/xiaohongshu/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        status = await task_manager.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="任务未找到")

        return TaskStatusResponse(
            task_id=task_id,
            status=status["status"],
            current_step=status.get("current_step", ""),
            progress=status.get("progress", 0.0),
            message=status.get("message", ""),
            created_at=status.get("created_at", ""),
            updated_at=status.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@app.get("/api/v1/xiaohongshu/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """获取任务结果"""
    try:
        result = await task_manager.get_task_result(task_id)
        if result is None:
            # 检查任务是否存在
            status = await task_manager.get_task_status(task_id)
            if not status:
                raise HTTPException(status_code=404, detail="任务未找到")
            else:
                raise HTTPException(status_code=404, detail="任务结果未找到或任务未完成")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}")


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    try:
        # 获取活跃任务数量
        active_tasks = await task_executor.get_active_tasks_count()

        # 测试Redis连接
        await task_manager.connect()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "xiaohongshu-multi-agent-api-redis",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": active_tasks,
        "max_concurrent_tasks": task_executor.max_workers,
        "redis_status": redis_status
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "小红书多智能体API - Redis版本",
        "version": "2.0.0",
        "description": "基于LangChain架构，支持并发任务处理和实时状态查询",
        "features": [
            "并发任务处理 (线程池)",
            "实时进度跟踪",
            "Redis状态存储",
            "多进程部署支持"
        ],
        "docs": "/docs",
        "health": "/api/v1/health",
        "create_task": "POST /api/v1/xiaohongshu/tasks",
        "max_concurrent_tasks": task_executor.max_workers
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
