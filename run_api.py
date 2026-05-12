#!/usr/bin/env python3
"""
小红书多智能体API服务器启动脚本 - Redis版本
支持并发任务处理和实时状态查询
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api_server import app
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="小红书多智能体API服务器 - Redis版本")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=9999, help="服务器端口")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0", help="Redis连接URL")
    parser.add_argument("--max-concurrent", type=int, default=6, help="最大并发任务数")

    args = parser.parse_args()

    # 设置环境变量
    os.environ["REDIS_URL"] = args.redis_url
    os.environ["MAX_CONCURRENT_TASKS"] = str(args.max_concurrent)

    print("启动小红书多智能体API服务器 - Redis版本...")
    print(f"服务地址: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    print(f"健康检查: http://{args.host}:{args.port}/api/v1/health")
    print(f"最大并发任务数: {args.max_concurrent}")
    print(f"Redis连接: {args.redis_url}")
    print(f"工作进程数: {args.workers}")
    print()

    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
