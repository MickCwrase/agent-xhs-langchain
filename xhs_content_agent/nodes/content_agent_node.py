import re
import json
from datetime import datetime
from typing import Dict, Any
from langchain.messages import HumanMessage, AIMessage

from base_agent.models.openrouter_llm import openrouter_model
from base_agent.utils.edge import clean_llm_response, validate_agent_output

from xhs_content_agent.states.state import ContentMessagesState, ContentData, ContentAgentOutput
from xhs_content_agent.prompt.prompt import CONTENT_GENERATION_PROMPT, CONTENT_REFINEMENT_PROMPT


def content_generation_node(state: ContentMessagesState) -> dict:
    """内容生成节点"""
    topic_data = state.get("topic_data", {})
    prompt = CONTENT_GENERATION_PROMPT.format(topic_data=json.dumps(topic_data, ensure_ascii=False))

    response = openrouter_model.invoke(prompt)
    print(f"内容智能体回答：{response.content}")

    content_data: ContentData
    error_message = None

    try:
        # 清理LLM响应
        cleaned_response = clean_llm_response(response.content)
        content_json = json.loads(cleaned_response)

        content_data = {
            "title": content_json.get("title", "默认标题"),
            "content": content_json.get("content", ""),
            "word_count": content_json.get("word_count", 0),
            "style": content_json.get("style", "轻松自然"),
            "keywords": content_json.get("keywords", []),
            "hashtags": content_json.get("hashtags", [])
        }
        # 存储清理后的原始JSON字符串，避免再次序列化导致转义
        structured_raw_content = cleaned_response
    except json.JSONDecodeError as e:
        error_message = f"JSON解析失败: {str(e)}"
        content_data = {
            "title": "内容生成失败",
            "content": response.content,
            "word_count": len(response.content),
            "style": "原始输出",
            "keywords": ["生成失败"]
        }
        structured_raw_content = response.content

    # 创建API输出结构
    api_output: ContentAgentOutput = {
        "agent_type": "content_agent",
        "agent_name": "内容设计专家",
        "success": error_message is None,
        "content": content_data,
        "structured_raw_content": structured_raw_content,
        "timestamp": datetime.now().isoformat(),
        "error_message": error_message
    }

    # 验证和清理输出数据
    validated_output = validate_agent_output(api_output, "content_agent")

    return {
        "messages": [response],
        "content": content_data,
        "finalized": True,
        "output": validated_output
    }


def content_refinement_node(state: ContentMessagesState) -> dict:
    """内容优化节点"""
    original_content = state.get("content", {})
    feedback = state.get("feedback", "")

    prompt = CONTENT_REFINEMENT_PROMPT.format(
        original_content=json.dumps(original_content, ensure_ascii=False),
        feedback=feedback
    )

    response = openrouter_model.invoke(prompt)
    print(f"内容智能体优化回答：{response.content}")

    content_data: ContentData
    error_message = None

    try:
        # 清理LLM响应
        cleaned_response = clean_llm_response(response.content)
        content_json = json.loads(cleaned_response)

        content_data = {
            "title": content_json.get("title", "优化标题"),
            "content": content_json.get("content", ""),
            "word_count": content_json.get("word_count", 0),
            "style": content_json.get("style", "轻松自然"),
            "keywords": content_json.get("keywords", [])
        }
        # 存储清理后的原始JSON字符串，避免再次序列化导致转义
        structured_raw_content = cleaned_response
    except json.JSONDecodeError as e:
        error_message = f"JSON解析失败: {str(e)}"
        content_data = {
            "title": "内容优化失败",
            "content": response.content,
            "word_count": len(response.content),
            "style": "原始输出",
            "keywords": ["优化失败"],
            "hashtags": ["#优化失败"]
        }
        structured_raw_content = response.content

    # 创建API输出结构
    api_output: ContentAgentOutput = {
        "agent_type": "content_agent",
        "agent_name": "内容设计专家",
        "success": error_message is None,
        "content": content_data,
        "structured_raw_content": structured_raw_content,
        "timestamp": datetime.now().isoformat(),
        "error_message": error_message
    }

    # 验证和清理输出数据
    validated_output = validate_agent_output(api_output, "content_agent")

    return {
        "messages": [response],
        "content": content_data,
        "finalized": True,
        "output": validated_output
    }
