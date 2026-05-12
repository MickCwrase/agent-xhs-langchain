from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Dict, Any, List, Optional


class PictureDesign(TypedDict):
    """图片设计数据结构"""
    cover_image: str
    content_images: List[str]
    design_style: str
    color_scheme: str
    layout_suggestions: List[str]


class ImageGenerationResult(TypedDict):
    """图片生成结果"""
    prompt: str
    enhanced_prompt: str
    image_url: Optional[str]
    success: bool
    error_message: Optional[str]


class GeneratedImages(TypedDict):
    """生成的图片集合"""
    cover_image: ImageGenerationResult
    content_images: List[ImageGenerationResult]


class PictureAgentOutput(TypedDict):
    """图片智能体输出结构"""
    agent_type: str
    agent_name: str
    success: bool
    design: PictureDesign
    generated_images: GeneratedImages
    raw_content: str
    timestamp: str
    error_message: Optional[str]


class PictureMessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]        # 消息列表
    topic_data: Dict[str, Any]                                 # 选题数据
    content_data: Dict[str, Any]                               # 内容数据
    design: Optional[PictureDesign]                            # 设计方案
    generated_images: Optional[GeneratedImages]                # 生成的图片
    finalized: bool                                            # 是否结束
    output: Optional[PictureAgentOutput]                       # API输出结构
