from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Dict, Any, List, Optional


class AgentResult(TypedDict):
    """单个智能体结果"""
    agent_type: str
    agent_name: str
    success: bool
    data: Dict[str, Any]
    timestamp: str
    error_message: Optional[str]


class SupervisorOutput(TypedDict):
    """Supervisor输出结构"""
    task_id: str
    success: bool
    workflow_status: str
    results: List[AgentResult]
    final_output: Dict[str, Any]
    timestamp: str
    error_message: Optional[str]


class SupervisorState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]          # 消息列表
    current_step: str                                            # 当前步骤
    user_input: str                                              # 用户输入
    task_id: str                                                 # 任务ID
    flow_result: Optional[Dict[str, Any]]                       # 流程指派结果
    topic_result: Optional[Dict[str, Any]]                      # 选题结果
    content_result: Optional[Dict[str, Any]]                    # 内容结果
    picture_result: Optional[Dict[str, Any]]                    # 图片结果
    review_result: Optional[Dict[str, Any]]                     # 审查结果
    final_output: Optional[SupervisorOutput]                    # 最终API输出
    completed: bool                                              # 是否完成