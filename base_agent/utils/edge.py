import sys
from pathlib import Path
project_root = Path(__file__).resolve()                       
for p in (project_root, *project_root.parents):
    if (p / '.env').exists() or (p / '.git').exists():
        project_root = p
        break
if str(project_root) not in sys.path:                          
    sys.path.insert(0, str(project_root))

#################################################################

import json
import re
from typing import Dict, Any, Optional, Union
from base_agent.states.state import MessagesState
from langgraph.graph import StateGraph, START, END
from typing import Literal

# Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
def should_continue(state: MessagesState) -> Literal["tool_call_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_call_node"

    # Otherwise, we stop (reply to the user)
    return END


def sanitize_text_content(text: str) -> str:
    """
    清理文本内容中的转义字符，确保文本可以直接在markdown中使用

    Args:
        text: 原始文本内容

    Returns:
        清理后的文本内容
    """
    if not isinstance(text, str):
        return str(text)

    # 反转义常见的转义序列
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '\t')
    text = text.replace('\\r', '\r')
    text = text.replace('\\"', '"')
    text = text.replace("\\'", "'")
    text = text.replace('\\\\', '\\')

    return text


def validate_json_structure(data: Dict[str, Any], required_fields: list = None) -> Dict[str, Any]:
    """
    验证和清理JSON数据结构

    Args:
        data: 要验证的数据字典
        required_fields: 必需字段列表

    Returns:
        验证和清理后的数据字典
    """
    if not isinstance(data, dict):
        return data

    cleaned_data = {}

    for key, value in data.items():
        if isinstance(value, str):
            # 清理字符串字段
            cleaned_data[key] = sanitize_text_content(value)
        elif isinstance(value, dict):
            # 递归清理嵌套字典
            cleaned_data[key] = validate_json_structure(value)
        elif isinstance(value, list):
            # 清理列表中的每个元素
            cleaned_data[key] = [
                validate_json_structure(item) if isinstance(item, dict) else
                sanitize_text_content(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            cleaned_data[key] = value

    # 检查必需字段
    if required_fields:
        for field in required_fields:
            if field not in cleaned_data:
                print(f"警告: 缺少必需字段 '{field}'")

    return cleaned_data


def clean_llm_response(raw_response: str) -> str:
    """
    清理LLM原始响应，移除markdown代码块标记，提取纯JSON

    Args:
        raw_response: LLM的原始响应

    Returns:
        清理后的响应内容
    """
    if not raw_response:
        return raw_response

    # 移除markdown代码块标记
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', raw_response, re.IGNORECASE)
    if json_match:
        return json_match.group(1).strip()

    # 如果没有代码块标记，直接返回原内容
    return raw_response.strip()


def validate_agent_output(output_data: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
    """
    验证智能体输出数据，确保数据结构完整性和数据清洁性

    Args:
        output_data: 智能体输出数据
        agent_type: 智能体类型

    Returns:
        验证和清理后的输出数据
    """
    if not isinstance(output_data, dict):
        return output_data

    # 根据智能体类型定义必需字段
    required_fields_map = {
        "flow_agent": ["agent_type", "agent_name", "success", "assignment"],
        "topic_agent": ["agent_type", "agent_name", "success", "topics"],
        "content_agent": ["agent_type", "agent_name", "success", "content"],
        "picture_agent": ["agent_type", "agent_name", "success", "design"],
        "review_agent": ["agent_type", "agent_name", "success", "review"]
    }

    required_fields = required_fields_map.get(agent_type, [])

    # 验证和清理数据
    cleaned_output = validate_json_structure(output_data, required_fields)

    # 特殊处理structured_raw_content字段
    if "structured_raw_content" in cleaned_output:
        try:
            # 确保structured_raw_content是有效的JSON字符串
            json.loads(cleaned_output["structured_raw_content"])
        except json.JSONDecodeError:
            # 如果不是有效的JSON，可能是错误情况下的原始响应，不需要警告
            pass

    return cleaned_output