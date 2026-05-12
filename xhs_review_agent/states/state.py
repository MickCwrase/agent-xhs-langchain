from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Dict, Any, List, Optional


class ReviewResult(TypedDict):
    """审查结果数据结构"""
    overall_score: int  # 1-10分
    compliance_status: str  # "通过" or "不通过"
    issues: List[str]
    suggestions: List[str]
    risk_level: str  # "低风险" "中风险" "高风险"
    highlighted_content: str  # 高亮标记了风险点的文案内容


class ReviewAgentOutput(TypedDict):
    """审查智能体输出结构"""
    agent_type: str
    agent_name: str
    success: bool
    review: ReviewResult
    raw_content: str
    timestamp: str
    error_message: Optional[str]


class ReviewMessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]        # 消息列表
    content_data: Dict[str, Any]                               # 内容数据
    design_data: Dict[str, Any]                                # 设计数据
    review: Optional[ReviewResult]                             # 审查结果
    finalized: bool                                            # 是否结束
    output: Optional[ReviewAgentOutput]                        # API输出结构
