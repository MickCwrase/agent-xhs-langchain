from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Dict, Any, List, Optional


class TopicAnalysis(TypedDict):
    """选题分析数据"""
    timeliness: int
    resonance: int
    spread_potential: int
    uniqueness: int
    feasibility: int

class TopicData(TypedDict):
    """选题数据结构"""
    title: str
    hook: str
    content_outline: str
    tags: List[str]
    analysis: TopicAnalysis
    overall_score: float


class TopicAgentOutput(TypedDict):
    """选题智能体输出结构"""
    agent_type: str
    agent_name: str
    success: bool
    topics: List[TopicData]
    raw_content: str
    timestamp: str
    error_message: Optional[str]


class TopicMessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]        # 消息列表
    topic: List[TopicData]                                     # 主题数据
    finalized: bool                                            # 是否结束
    human_feedback: str                                        # 用户反馈
    output: Optional[TopicAgentOutput]                         # API输出结构