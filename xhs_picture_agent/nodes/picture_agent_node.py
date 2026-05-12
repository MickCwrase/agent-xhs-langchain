import re
import json
from datetime import datetime
from typing import Dict, Any, Optional
from langchain.messages import AIMessage

from base_agent.models.openrouter_llm import openrouter_model
from base_agent.models.doubao_llm import enhance_text_prompt, generate_image_from_text
from base_agent.utils.edge import clean_llm_response, validate_agent_output

from xhs_picture_agent.states.state import (
    PictureMessagesState, PictureDesign, PictureAgentOutput,
    GeneratedImages, ImageGenerationResult
)
from xhs_picture_agent.prompt.prompt import PICTURE_DESIGN_PROMPT


def picture_design_node(state: PictureMessagesState) -> dict:
    """图片设计节点"""
    topic_data = state.get("topic_data", {})
    content_data = state.get("content_data", {})

    # 提取内容摘要
    content_text = content_data.get("content", "")
    content_summary = content_text[:200] + "..." if len(content_text) > 200 else content_text

    prompt = PICTURE_DESIGN_PROMPT.format(
        topic_data=json.dumps(topic_data, ensure_ascii=False),
        content_summary=content_summary
    )

    # 第一步：使用通义千问生成设计方案
    response = openrouter_model.invoke(prompt)
    print(f"图片智能体回答：{response.content}")

    design_data: PictureDesign
    error_message = None

    try:
        # 清理LLM响应
        cleaned_response = clean_llm_response(response.content)
        design_json = json.loads(cleaned_response)

        design_data = {
            "cover_image": design_json.get("cover_image", "默认封面设计"),
            "content_images": design_json.get("content_images", []),
            "design_style": design_json.get("design_style", "清新自然"),
            "color_scheme": design_json.get("color_scheme", "自然色彩"),
            "layout_suggestions": design_json.get("layout_suggestions", [])
        }
        # 存储清理后的原始JSON字符串，避免再次序列化导致转义
        structured_raw_content = cleaned_response
    except json.JSONDecodeError as e:
        error_message = f"JSON解析失败: {str(e)}"
        design_data = {
            "cover_image": "设计生成失败",
            "content_images": ["配图1", "配图2", "配图3"],
            "design_style": "默认风格",
            "color_scheme": "默认配色",
            "layout_suggestions": ["建议1", "建议2"]
        }
        structured_raw_content = response.content

    # 第二步：使用豆包文案生成模型增强提示词并生成图片
    generated_images = generate_images_with_doubao(design_data)

    # 创建API输出结构
    api_output: PictureAgentOutput = {
        "agent_type": "picture_agent",
        "agent_name": "平面设计专家",
        "success": error_message is None and generated_images is not None,
        "design": design_data,
        "generated_images": generated_images if generated_images else create_empty_generated_images(),
        "structured_raw_content": structured_raw_content,
        "timestamp": datetime.now().isoformat(),
        "error_message": error_message
    }

    # 验证和清理输出数据
    validated_output = validate_agent_output(api_output, "picture_agent")

    return {
        "messages": [response],
        "design": design_data,
        "generated_images": generated_images,
        "finalized": True,
        "output": validated_output
    }


def generate_images_with_doubao(design_data: PictureDesign) -> Optional[GeneratedImages]:
    """使用豆包大模型生成图片"""
    try:
        # 生成封面图片
        cover_prompt = design_data["cover_image"]
        enhanced_cover_prompt = enhance_text_prompt(cover_prompt)
        cover_image_url = generate_image_from_text(enhanced_cover_prompt)

        cover_result: ImageGenerationResult = {
            "prompt": cover_prompt,
            "enhanced_prompt": enhanced_cover_prompt,
            "image_url": cover_image_url,
            "success": cover_image_url is not None,
            "error_message": None if cover_image_url else "封面图片生成失败"
        }

        # 生成内容图片
        content_images_results = []
        for i, content_image_prompt in enumerate(design_data["content_images"]):
            try:
                enhanced_content_prompt = enhance_text_prompt(content_image_prompt)
                content_image_url = generate_image_from_text(enhanced_content_prompt)

                content_result: ImageGenerationResult = {
                    "prompt": content_image_prompt,
                    "enhanced_prompt": enhanced_content_prompt,
                    "image_url": content_image_url,
                    "success": content_image_url is not None,
                    "error_message": None if content_image_url else f"内容图片{i+1}生成失败"
                }
                content_images_results.append(content_result)
            except Exception as e:
                print(f"内容图片{i+1}生成失败: {str(e)}")
                content_result: ImageGenerationResult = {
                    "prompt": content_image_prompt,
                    "enhanced_prompt": content_image_prompt,
                    "image_url": None,
                    "success": False,
                    "error_message": str(e)
                }
                content_images_results.append(content_result)

        generated_images: GeneratedImages = {
            "cover_image": cover_result,
            "content_images": content_images_results
        }

        return generated_images

    except Exception as e:
        print(f"豆包图片生成整体失败: {str(e)}")
        return None


def create_empty_generated_images() -> GeneratedImages:
    """创建空的图片生成结果"""
    empty_cover: ImageGenerationResult = {
        "prompt": "",
        "enhanced_prompt": "",
        "image_url": None,
        "success": False,
        "error_message": "图片生成未执行"
    }

    empty_content: ImageGenerationResult = {
        "prompt": "",
        "enhanced_prompt": "",
        "image_url": None,
        "success": False,
        "error_message": "图片生成未执行"
    }

    return {
        "cover_image": empty_cover,
        "content_images": [empty_content]
    }
