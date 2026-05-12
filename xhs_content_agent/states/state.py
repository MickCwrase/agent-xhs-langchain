from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Dict, Any, List, Optional


class ContentData(TypedDict):
    """文案内容数据结构"""
    title: str
    content: str
    word_count: int
    style: str
    keywords: List[str]
    hashtags: List[str]


class ContentAgentOutput(TypedDict):
    """内容智能体输出结构"""
    agent_type: str
    agent_name: str
    success: bool
    content: ContentData
    raw_content: str
    timestamp: str
    error_message: Optional[str]


class ContentMessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]        # 消息列表
    topic_data: Dict[str, Any]                                 # 选题数据
    content: Optional[ContentData]                             # 文案内容
    finalized: bool                                            # 是否结束
    output: Optional[ContentAgentOutput]                       # API输出结构
