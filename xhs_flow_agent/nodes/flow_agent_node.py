import re
import json
from datetime import datetime
from typing import Dict, Any
from langchain.messages import AIMessage

from base_agent.models.openrouter_llm import openrouter_model
from base_agent.utils.edge import clean_llm_response, validate_agent_output

from xhs_flow_agent.states.state import FlowMessagesState, FlowAssignment, FlowAgentOutput
from xhs_flow_agent.prompt.prompt import FLOW_ASSIGNMENT_PROMPT


def flow_assignment_node(state: FlowMessagesState) -> dict:
    """流程指派节点"""
    user_input = state.get("user_input", "")
    current_step = state.get("current_step", "initial")

    prompt = FLOW_ASSIGNMENT_PROMPT.format(user_input=user_input)

    response = openrouter_model.invoke(prompt)
    print(f"流程指派智能体回答：{response.content}")

    assignment_data: FlowAssignment
    error_message = None

    try:
        # 清理LLM响应
        cleaned_response = clean_llm_response(response.content)
        assignment_json = json.loads(cleaned_response)

        assignment_data = {
            "next_step": assignment_json.get("next_step", "选题策划"),
            "next_agent": assignment_json.get("next_agent", "xiaoli"),
            "agent_input": assignment_json.get("agent_input", {}),
            "workflow_description": assignment_json.get("workflow_description", "开始创作流程")
        }
        # 存储清理后的原始JSON字符串，避免再次序列化导致转义
        structured_raw_content = cleaned_response
    except json.JSONDecodeError as e:
        error_message = f"JSON解析失败: {str(e)}"
        assignment_data = {
            "next_step": "选题策划",
            "next_agent": "xiaoli",
            "agent_input": {"需求": user_input},
            "workflow_description": "解析失败，使用默认流程"
        }
        structured_raw_content = response.content

    # 创建API输出结构
    api_output: FlowAgentOutput = {
        "agent_type": "flow_agent",
        "agent_name": "流程指派专家",
        "success": error_message is None,
        "assignment": assignment_data,
        "structured_raw_content": structured_raw_content,
        "timestamp": datetime.now().isoformat(),
        "error_message": error_message
    }

    # 验证和清理输出数据
    validated_output = validate_agent_output(api_output, "flow_agent")

    return {
        "messages": [response],
        "assignment": assignment_data,
        "finalized": True,
        "output": validated_output
    }
