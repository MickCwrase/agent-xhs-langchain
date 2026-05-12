from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Dict, Any, List, Optional


class FlowAssignment(TypedDict):
    """流程指派数据结构"""
    next_step: str
    next_agent: str
    agent_input: Dict[str, Any]
    workflow_description: str


class FlowAgentOutput(TypedDict):
    """流程指派智能体输出结构"""
    agent_type: str
    agent_name: str
    success: bool
    assignment: FlowAssignment
    raw_content: str
    timestamp: str
    error_message: Optional[str]


class FlowMessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]        # 消息列表
    user_input: str                                           # 用户输入
    current_step: str                                         # 当前步骤
    assignment: Optional[FlowAssignment]                      # 流程指派结果
    finalized: bool                                           # 是否结束
    output: Optional[FlowAgentOutput]                         # API输出结构
