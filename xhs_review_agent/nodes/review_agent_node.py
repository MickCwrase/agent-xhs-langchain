import re
import json
from datetime import datetime
from typing import Dict, Any
from langchain.messages import AIMessage

from base_agent.models.openrouter_llm import openrouter_model
from base_agent.utils.edge import clean_llm_response, validate_agent_output

from xhs_review_agent.states.state import ReviewMessagesState, ReviewResult, ReviewAgentOutput


def content_review_node(state: ReviewMessagesState) -> dict:
    """内容审查节点"""
    content_data = state.get("content_data", {})
    design_data = state.get("design_data", {})

    prompt = f"""
    你是 AI 创意团队的**合规检测专家（小于）**，你的职责是**对选题、文案内容进行合规性检测**，确保最终内容符合平台发布规范。

    文案标题：{content_data.get('title', '')}
    文案内容：{content_data.get('content', '')[:500]}...

    设计方案：{json.dumps(design_data, ensure_ascii=False)}

    请对内容进行全面的合规性检测：

    1. 极限词：如：最、第一、唯一、顶级等
    2. 医疗/保健：如：虚假疗效、专业暗示等
    3. 引流/联系方式：如：微信号、二维码、外部链接等
    4. 其他违规：如：色情、暴力、政治敏感等

    返回JSON格式：
    {{
      "overall_score": 8,
      "compliance_status": "通过",
      "issues": ["问题1", "问题2"],
      "suggestions": ["建议1", "建议2"],
      "risk_level": "低风险",
      "highlighted_content": "高亮标记了风险点的文案内容"
    }}
    """

    response = openrouter_model.invoke(prompt)
    print(f"审查智能体回答：{response.content}")

    review_data: ReviewResult
    error_message = None

    try:
        # 清理LLM响应
        cleaned_response = clean_llm_response(response.content)
        review_json = json.loads(cleaned_response)

        review_data = {
            "overall_score": review_json.get("overall_score", 5),
            "compliance_status": review_json.get("compliance_status", "待定"),
            "issues": review_json.get("issues", []),
            "suggestions": review_json.get("suggestions", []),
            "risk_level": review_json.get("risk_level", "中风险"),
            "highlighted_content": review_json.get("highlighted_content", "")
        }
        # 存储清理后的原始JSON字符串，避免再次序列化导致转义
        structured_raw_content = cleaned_response
    except json.JSONDecodeError as e:
        error_message = f"JSON解析失败: {str(e)}"
        review_data = {
            "overall_score": 5,
            "compliance_status": "待定",
            "issues": ["解析失败"],
            "suggestions": ["需要重新审查"],
            "risk_level": "中风险",
            "highlighted_content": "内容解析失败，无法进行合规检测"
        }
        structured_raw_content = response.content

    # 创建API输出结构
    api_output: ReviewAgentOutput = {
        "agent_type": "review_agent",
        "agent_name": "合规检测专家",
        "success": error_message is None,
        "review": review_data,
        "structured_raw_content": structured_raw_content,
        "timestamp": datetime.now().isoformat(),
        "error_message": error_message
    }

    # 验证和清理输出数据
    validated_output = validate_agent_output(api_output, "review_agent")

    return {
        "messages": [response],
        "review": review_data,
        "finalized": True,
        "output": validated_output
    }
