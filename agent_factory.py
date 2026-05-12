"""
智能体工厂
提供线程安全的智能体实例化
"""

import sys
from pathlib import Path
from typing import Any, Dict
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, AIMessage

# 导入原有的智能体模块
from xhs_supervisor_agent.states.state import SupervisorState
from xhs_flow_agent.agent import xhs_flow_agent
from xhs_topic_agent.agent import xhs_topic_agent
from xhs_content_agent.agent import xhs_content_agent
from xhs_picture_agent.agent import xhs_picture_agent
from xhs_review_agent.agent import xhs_review_agent


class ThreadSafeAgentFactory:
    """线程安全的智能体工厂"""

    @staticmethod
    def create_supervisor_agent(progress_callback=None):
        """
        创建独立的Supervisor智能体实例
        每个任务使用独立的实例，避免线程安全问题

        Args:
            progress_callback: 进度回调函数，用于实时更新任务进度

        Returns:
            编译后的supervisor智能体实例
        """
        # 导入节点函数
        from xhs_supervisor_agent.agent import (
            initialize_workflow, run_flow_agent, run_topic_agent,
            run_content_agent, run_picture_agent, run_review_agent, finalize_workflow
        )

        # 创建带进度回调的节点函数
        def initialize_workflow_with_progress(state):
            result = initialize_workflow(state)
            # 更新进度：初始化完成 (5%)
            if progress_callback:
                task_id = state.get("task_id", "unknown")
                progress_callback(task_id, "workflow_initialized", 0.20, "工作流初始化完成，开始流程指派...")
            return result

        def run_flow_agent_with_progress(state):
            result = run_flow_agent(state)
            # 更新进度：流程指派完成 (25%)
            if progress_callback:
                task_id = state.get("task_id", "unknown")
                progress_callback(task_id, "flow_assigned", 0.25, "流程指派完成，开始选题策划...")
            return result

        def run_topic_agent_with_progress(state):
            result = run_topic_agent(state)
            # 更新进度：选题完成 (40%)
            if progress_callback:
                task_id = state.get("task_id", "unknown")
                progress_callback(task_id, "topic_generated", 0.40, "选题策划完成，开始内容创作...")
            return result

        def run_content_agent_with_progress(state):
            result = run_content_agent(state)
            # 更新进度：内容创作完成 (60%)
            if progress_callback:
                task_id = state.get("task_id", "unknown")
                progress_callback(task_id, "content_created", 0.60, "内容创作完成，开始图片设计...")
            return result

        def run_picture_agent_with_progress(state):
            result = run_picture_agent(state)
            # 更新进度：图片设计完成 (75%)
            if progress_callback:
                task_id = state.get("task_id", "unknown")
                progress_callback(task_id, "picture_designed", 0.75, "图片设计完成，开始内容审查...")
            return result

        def run_review_agent_with_progress(state):
            result = run_review_agent(state)
            # 更新进度：内容审查完成 (90%)
            if progress_callback:
                task_id = state.get("task_id", "unknown")
                progress_callback(task_id, "review_completed", 0.90, "内容审查完成，正在生成最终结果...")
            return result

        def finalize_workflow_with_progress(state):
            result = finalize_workflow(state)
            # 更新进度：工作流完全完成 (95%，剩余5%留给外部处理)
            if progress_callback:
                task_id = state.get("task_id", "unknown")
                progress_callback(task_id, "workflow_finalized", 0.95, "工作流执行完成，正在进行最终整理...")
            return result

        # 创建新的工作流构建器
        builder = StateGraph(SupervisorState)

        # 添加节点 - 使用带进度回调的节点函数
        builder.add_node("initialize_workflow", initialize_workflow_with_progress)
        builder.add_node("run_flow_agent", run_flow_agent_with_progress)
        builder.add_node("run_topic_agent", run_topic_agent_with_progress)
        builder.add_node("run_content_agent", run_content_agent_with_progress)
        builder.add_node("run_picture_agent", run_picture_agent_with_progress)
        builder.add_node("run_review_agent", run_review_agent_with_progress)
        builder.add_node("finalize_workflow", finalize_workflow_with_progress)

        # 添加边
        builder.add_edge(START, "initialize_workflow")
        builder.add_edge("initialize_workflow", "run_flow_agent")
        builder.add_edge("run_flow_agent", "run_topic_agent")
        builder.add_edge("run_topic_agent", "run_content_agent")
        builder.add_edge("run_content_agent", "run_picture_agent")
        builder.add_edge("run_picture_agent", "run_review_agent")
        builder.add_edge("run_review_agent", "finalize_workflow")
        builder.add_edge("finalize_workflow", END)

        # 编译并返回新实例
        return builder.compile()

    @staticmethod
    def create_flow_agent():
        """创建独立的流程指派智能体实例"""
        from xhs_flow_agent.agent import xhs_flow_agent_builder

        # 创建新的构建器实例
        builder = StateGraph(xhs_flow_agent_builder.get_state_class())

        # 复制所有节点和边
        for node_name, node_func in xhs_flow_agent_builder.nodes.items():
            builder.add_node(node_name, node_func)

        for edge in xhs_flow_agent_builder.edges:
            builder.add_edge(edge.source, edge.target)

        return builder.compile()

    @staticmethod
    def create_topic_agent():
        """创建独立的选题智能体实例"""
        from xhs_topic_agent.agent import xhs_topic_agent_builder

        # 创建新的构建器实例
        builder = StateGraph(xhs_topic_agent_builder.get_state_class())

        # 复制所有节点和边
        for node_name, node_func in xhs_topic_agent_builder.nodes.items():
            builder.add_node(node_name, node_func)

        for edge in xhs_topic_agent_builder.edges:
            builder.add_edge(edge.source, edge.target)

        return builder.compile()

    @staticmethod
    def create_content_agent():
        """创建独立的内容创作智能体实例"""
        from xhs_content_agent.agent import xhs_content_agent_builder

        # 创建新的构建器实例
        builder = StateGraph(xhs_content_agent_builder.get_state_class())

        # 复制所有节点和边
        for node_name, node_func in xhs_content_agent_builder.nodes.items():
            builder.add_node(node_name, node_func)

        for edge in xhs_content_agent_builder.edges:
            builder.add_edge(edge.source, edge.target)

        return builder.compile()

    @staticmethod
    def create_picture_agent():
        """创建独立的图片设计智能体实例"""
        from xhs_picture_agent.agent import xhs_picture_agent_builder

        # 创建新的构建器实例
        builder = StateGraph(xhs_picture_agent_builder.get_state_class())

        # 复制所有节点和边
        for node_name, node_func in xhs_picture_agent_builder.nodes.items():
            builder.add_node(node_name, node_func)

        for edge in xhs_content_agent_builder.edges:
            builder.add_edge(edge.source, edge.target)

        return builder.compile()

    @staticmethod
    def create_review_agent():
        """创建独立的审查智能体实例"""
        from xhs_review_agent.agent import xhs_review_agent_builder

        # 创建新的构建器实例
        builder = StateGraph(xhs_review_agent_builder.get_state_class())

        # 复制所有节点和边
        for node_name, node_func in xhs_review_agent_builder.nodes.items():
            builder.add_node(node_name, node_func)

        for edge in xhs_review_agent_builder.edges:
            builder.add_edge(edge.source, edge.target)

        return builder.compile()

    @staticmethod
    def create_llm_instance():
        """创建独立的LLM实例"""
        from base_agent.models.dashscope_llm import dashscope_llm

        # 返回新的LLM实例，而不是共享单例
        return dashscope_llm()


# 为了向后兼容，提供便捷的函数
def create_supervisor_agent():
    """便捷函数：创建Supervisor智能体"""
    return ThreadSafeAgentFactory.create_supervisor_agent()

def create_flow_agent():
    """便捷函数：创建流程指派智能体"""
    return ThreadSafeAgentFactory.create_flow_agent()

def create_topic_agent():
    """便捷函数：创建选题智能体"""
    return ThreadSafeAgentFactory.create_topic_agent()

def create_content_agent():
    """便捷函数：创建内容创作智能体"""
    return ThreadSafeAgentFactory.create_content_agent()

def create_picture_agent():
    """便捷函数：创建图片设计智能体"""
    return ThreadSafeAgentFactory.create_picture_agent()

def create_review_agent():
    """便捷函数：创建审查智能体"""
    return ThreadSafeAgentFactory.create_review_agent()