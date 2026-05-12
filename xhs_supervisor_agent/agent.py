import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
project_root = Path(__file__).resolve()
for p in (project_root, *project_root.parents):
    if (p / '.env').exists() or (p / '.git').exists():
        project_root = p
        break
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

#################################################################

import asyncio
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, AIMessage

from xhs_supervisor_agent.states.state import SupervisorState, SupervisorOutput, AgentResult
from xhs_flow_agent.agent import xhs_flow_agent
from xhs_topic_agent.agent import xhs_topic_agent
from xhs_content_agent.agent import xhs_content_agent
from xhs_picture_agent.agent import xhs_picture_agent
from xhs_review_agent.agent import xhs_review_agent


def initialize_workflow(state: SupervisorState) -> Dict[str, Any]:
    """初始化工作流"""
    print("开始小红书内容创作工作流...")

    return {
        "current_step": "flow_assignment",
        "messages": [AIMessage(content="正在分析您的需求并规划创作流程...")],
        "completed": False
    }


def run_flow_agent(state: SupervisorState) -> Dict[str, Any]:
    """运行流程指派智能体"""
    print("正在指派工作流程...")

    try:
        result = xhs_flow_agent.invoke({
            "messages": [HumanMessage(content="指派工作流程")],
            "user_input": state["user_input"]
        })

        flow_output = result.get("output", {})
        if flow_output and flow_output.get("success"):
            assignment = flow_output.get("assignment", {})
            next_agent = assignment.get("next_agent", "xiaoli")

            return {
                "current_step": f"{next_agent}_generation",
                "flow_result": flow_output,
                "messages": [AIMessage(content=f"流程已规划完成，接下来将调用{next_agent}开始创作")]
            }
        else:
            return {
                "current_step": "error",
                "messages": [AIMessage(content="流程指派失败")],
                "completed": True
            }
    except Exception as e:
        print(f"流程指派智能体执行失败: {e}")
        return {
            "current_step": "error",
            "messages": [AIMessage(content=f"流程指派出错: {str(e)}")],
            "completed": True
        }


def run_topic_agent(state: SupervisorState) -> Dict[str, Any]:
    """运行选题智能体"""
    print("正在生成选题...")

    try:
        # 调用选题智能体
        result = xhs_topic_agent.invoke({
            "messages": [HumanMessage(content=state["user_input"])],
        })

        topic_output = result.get("output", {})
        if topic_output and topic_output.get("success"):
            return {
                "current_step": "content_generation",
                "topic_result": topic_output,
                "messages": [AIMessage(content="选题生成完成，开始创作内容...")]
            }
        else:
            return {
                "current_step": "error",
                "messages": [AIMessage(content="选题生成失败")],
                "completed": True
            }
    except Exception as e:
        print(f"选题智能体执行失败: {e}")
        return {
            "current_step": "error",
            "messages": [AIMessage(content=f"选题生成出错: {str(e)}")],
            "completed": True
        }


def run_content_agent(state: SupervisorState) -> Dict[str, Any]:
    """运行内容智能体"""
    print("正在生成内容...")

    try:
        topic_data = state.get("topic_result", {}).get("topics", [{}])[0] if state.get("topic_result") else {}

        result = xhs_content_agent.invoke({
            "messages": [HumanMessage(content="生成内容")],
            "topic_data": topic_data
        })

        content_output = result.get("output", {})
        if content_output and content_output.get("success"):
            return {
                "current_step": "picture_generation",
                "content_result": content_output,
                "messages": [AIMessage(content="内容创作完成，开始设计图片...")]
            }
        else:
            return {
                "current_step": "error",
                "messages": [AIMessage(content="内容生成失败")],
                "completed": True
            }
    except Exception as e:
        print(f"内容智能体执行失败: {e}")
        return {
            "current_step": "error",
            "messages": [AIMessage(content=f"内容生成出错: {str(e)}")],
            "completed": True
        }


def run_picture_agent(state: SupervisorState) -> Dict[str, Any]:
    """运行图片智能体"""
    print("正在设计图片...")

    try:
        topic_data = state.get("topic_result", {}).get("topics", [{}])[0] if state.get("topic_result") else {}
        content_data = state.get("content_result", {}).get("content", {}) if state.get("content_result") else {}

        result = xhs_picture_agent.invoke({
            "messages": [HumanMessage(content="设计图片")],
            "topic_data": topic_data,
            "content_data": content_data
        })

        picture_output = result.get("output", {})
        if picture_output and picture_output.get("success"):
            return {
                "current_step": "review_generation",
                "picture_result": picture_output,
                "messages": [AIMessage(content="图片设计完成，开始内容审查...")]
            }
        else:
            return {
                "current_step": "error",
                "messages": [AIMessage(content="图片设计失败")],
                "completed": True
            }
    except Exception as e:
        print(f"图片智能体执行失败: {e}")
        return {
            "current_step": "error",
            "messages": [AIMessage(content=f"图片设计出错: {str(e)}")],
            "completed": True
        }


def run_review_agent(state: SupervisorState) -> Dict[str, Any]:
    """运行审查智能体"""
    print("正在审查内容...")

    try:
        content_data = state.get("content_result", {}).get("content", {}) if state.get("content_result") else {}
        picture_data = state.get("picture_result", {}).get("design", {}) if state.get("picture_result") else {}

        result = xhs_review_agent.invoke({
            "messages": [HumanMessage(content="审查内容")],
            "content_data": content_data,
            "design_data": picture_data
        })

        review_output = result.get("output", {})
        if review_output and review_output.get("success"):
            return {
                "current_step": "finalization",
                "review_result": review_output,
                "messages": [AIMessage(content="内容审查完成，生成最终结果...")]
            }
        else:
            return {
                "current_step": "error",
                "messages": [AIMessage(content="内容审查失败")],
                "completed": True
            }
    except Exception as e:
        print(f"审查智能体执行失败: {e}")
        return {
            "current_step": "error",
            "messages": [AIMessage(content=f"内容审查出错: {str(e)}")],
            "completed": True
        }


def finalize_workflow(state: SupervisorState) -> Dict[str, Any]:
    """完成工作流并生成最终输出"""
    print("正在生成最终输出...")

    try:
        # 收集所有智能体结果
        results: List[AgentResult] = []

        # 添加流程指派结果
        if state.get("flow_result"):
            results.append(AgentResult(
                agent_type="flow_agent",
                agent_name="流程指派专家",
                success=True,
                data=state["flow_result"],
                timestamp=state["flow_result"].get("timestamp", datetime.now().isoformat()),
                error_message=None
            ))

        # 添加选题结果
        if state.get("topic_result"):
            results.append(AgentResult(
                agent_type="topic_agent",
                agent_name="选题策划专家",
                success=True,
                data=state["topic_result"],
                timestamp=state["topic_result"].get("timestamp", datetime.now().isoformat()),
                error_message=None
            ))

        # 添加内容结果
        if state.get("content_result"):
            results.append(AgentResult(
                agent_type="content_agent",
                agent_name="内容设计专家",
                success=True,
                data=state["content_result"],
                timestamp=state["content_result"].get("timestamp", datetime.now().isoformat()),
                error_message=None
            ))

        # 添加图片结果
        if state.get("picture_result"):
            results.append(AgentResult(
                agent_type="picture_agent",
                agent_name="平面设计专家",
                success=True,
                data=state["picture_result"],
                timestamp=state["picture_result"].get("timestamp", datetime.now().isoformat()),
                error_message=None
            ))

        # 添加审查结果
        if state.get("review_result"):
            results.append(AgentResult(
                agent_type="review_agent",
                agent_name="合规检测专家",
                success=True,
                data=state["review_result"],
                timestamp=state["review_result"].get("timestamp", datetime.now().isoformat()),
                error_message=None
            ))

        # 生成最终输出
        final_output_data = {
            "topic": state.get("topic_result", {}).get("topics", []),
            "content": state.get("content_result", {}).get("content", {}),
            "design": state.get("picture_result", {}).get("design", {}),
            "review": state.get("review_result", {}).get("review", {})
        }

        final_output: SupervisorOutput = {
            "task_id": state.get("task_id", "unknown"),
            "success": True,
            "workflow_status": "completed",
            "results": results,
            "final_output": final_output_data,
            "timestamp": datetime.now().isoformat(),
            "error_message": None
        }

        return {
            "current_step": "completed",
            "final_output": final_output,
            "completed": True,
            "messages": [AIMessage(content="小红书内容创作完成！")]
        }

    except Exception as e:
        print(f"最终化失败: {e}")
        final_output: SupervisorOutput = {
            "task_id": state.get("task_id", "unknown"),
            "success": False,
            "workflow_status": "error",
            "results": [],
            "final_output": {},
            "timestamp": datetime.now().isoformat(),
            "error_message": str(e)
        }

        return {
            "current_step": "error",
            "final_output": final_output,
            "completed": True,
            "messages": [AIMessage(content=f"工作流执行出错: {str(e)}")]
        }


# 构建工作流
xhs_supervisor_agent_builder = StateGraph(SupervisorState)

# 添加节点
xhs_supervisor_agent_builder.add_node("initialize_workflow", initialize_workflow)
xhs_supervisor_agent_builder.add_node("run_flow_agent", run_flow_agent)
xhs_supervisor_agent_builder.add_node("run_topic_agent", run_topic_agent)
xhs_supervisor_agent_builder.add_node("run_content_agent", run_content_agent)
xhs_supervisor_agent_builder.add_node("run_picture_agent", run_picture_agent)
xhs_supervisor_agent_builder.add_node("run_review_agent", run_review_agent)
xhs_supervisor_agent_builder.add_node("finalize_workflow", finalize_workflow)

# 添加边
xhs_supervisor_agent_builder.add_edge(START, "initialize_workflow")
xhs_supervisor_agent_builder.add_edge("initialize_workflow", "run_flow_agent")
xhs_supervisor_agent_builder.add_edge("run_flow_agent", "run_topic_agent")
xhs_supervisor_agent_builder.add_edge("run_topic_agent", "run_content_agent")
xhs_supervisor_agent_builder.add_edge("run_content_agent", "run_picture_agent")
xhs_supervisor_agent_builder.add_edge("run_picture_agent", "run_review_agent")
xhs_supervisor_agent_builder.add_edge("run_review_agent", "finalize_workflow")
xhs_supervisor_agent_builder.add_edge("finalize_workflow", END)

# 编译智能体
xhs_supervisor_agent = xhs_supervisor_agent_builder.compile()

# 导出智能体实例供外部使用
__all__ = ['xhs_supervisor_agent']

# 使用示例:
# from langchain.messages import HumanMessage
# result = xhs_supervisor_agent.invoke({
#     "messages": [HumanMessage(content="帮我创作一个关于咖啡的笔记")],
#     "user_input": "帮我创作一个关于咖啡的笔记",
#     "task_id": "task_123"
# })
# print(result["final_output"])  # 获取完整的API输出结构
