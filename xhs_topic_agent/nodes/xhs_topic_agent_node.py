import re
import json
from datetime import datetime
from typing import List, Dict, Any
from langchain.messages import HumanMessage, AIMessage

from base_agent.models.openrouter_llm import openrouter_model
from base_agent.utils.edge import clean_llm_response, validate_agent_output

from xhs_topic_agent.states.state import TopicMessagesState, TopicData, TopicAgentOutput
from xhs_topic_agent.prompt.prompt import TOPIC_PROMPT, REFINE_TOPIC_PROMPT


# 初始化选题
def initial_topic_generate_node(state: TopicMessagesState) -> dict:
    user_question = state["messages"][-1]
    prompt = TOPIC_PROMPT.format(user_question=user_question.content)
    response = openrouter_model.invoke(prompt)
    print(f"选题智能体回答：{response.content}")

    topics: List[TopicData] = []
    error_message = None

    try:
        # 清理LLM响应
        cleaned_response = clean_llm_response(response.content)
        topics_data = json.loads(cleaned_response)
        topics = topics_data.get("topics", [])
        # 存储清理后的原始JSON字符串，避免再次序列化导致转义
        structured_raw_content = cleaned_response
    except json.JSONDecodeError as e:
        # 如果解析失败，则将整个响应作为文本处理
        error_message = f"JSON解析失败: {str(e)}"
        topics = [{
            "title": "默认选题",
            "hook": "暂无数据",
            "content_outline": "解析错误，无法生成选题",
            "tags": ["默认"],
            "analysis": {
                "timeliness": 5,
                "resonance": 5,
                "spread_potential": 5,
                "uniqueness": 5,
                "feasibility": 5
            },
            "overall_score": 5.0
        }]
        structured_raw_content = response.content

    # 创建API输出结构
    api_output: TopicAgentOutput = {
        "agent_type": "topic_agent",
        "agent_name": "选题策划专家",
        "success": error_message is None,
        "topics": topics,
        "structured_raw_content": structured_raw_content,
        "timestamp": datetime.now().isoformat(),
        "error_message": error_message
    }

    # 验证和清理输出数据
    validated_output = validate_agent_output(api_output, "topic_agent")

    return {
        "messages": [response],
        "topic": topics,
        "finalized": True,  # 直接标记为完成，不需要人机交互
        "output": validated_output
        }
# 选题智能体现在直接生成选题后结束，不需要人机交互

