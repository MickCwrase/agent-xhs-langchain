import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

# 豆包大模型API配置
doubao_api_key = os.getenv("DOUBAO_API_KEY", "afed06c3-b44d-4b84-a581-92b3c4736de6")
doubao_base_url = "https://ark.cn-beijing.volces.com/api/v3"

# 文案生成模型ID
DOUBAO_SEED_MODEL = "doubao-seed-1-6-251015"
# 文生图模型ID
DOUBAO_SEEDREAM_MODEL = "doubao-seedream-4-5-251128"

class DoubaoAPI:
    """豆包大模型API封装"""

    def __init__(self, api_key: str, base_url: str = doubao_base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def chat_completion(self, messages: List[Dict[str, str]], model: str = DOUBAO_SEED_MODEL,
                       temperature: float = 0.7, max_tokens: int = 2000) -> Dict[str, Any]:
        """文案生成API调用"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"豆包API调用失败: {str(e)}")

    def generate_image(self, prompt: str, model: str = DOUBAO_SEEDREAM_MODEL,
                      size: str = "1920x1920", style: str = "vivid") -> Dict[str, Any]:
        """文生图API调用"""
        url = f"{self.base_url}/images/generations"

        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "style": style,
            "n": 1
        }

        try:
            # 禁用代理以避免网络问题
            proxies = {"http": None, "https": None}
            response = requests.post(url, headers=self.headers, json=payload, timeout=120, proxies=proxies)

            if response.status_code != 200:
                print(f"文生图API响应状态码: {response.status_code}")
                print(f"文生图API响应内容: {response.text}")
                print(f"文生图API请求负载: {payload}")
                print(f"文生图API请求URL: {url}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"文生图API网络错误: {str(e)}")
            raise Exception(f"豆包文生图API调用失败: {str(e)}")

# 创建豆包API实例
doubao_api = DoubaoAPI(doubao_api_key)

def enhance_text_prompt(design_description: str) -> str:
    """使用豆包文案生成模型增强图片描述文本"""
    system_prompt = """你是一个专业的文生图提示词优化专家。请根据输入的图片设计描述，生成适合AI文生图模型的详细提示词。

要求：
1. 详细描述视觉元素、构图、色彩、风格等
2. 使用具体的艺术词汇和描述性语言
3. 保持原意的核心内容
4. 优化为适合AI生成高质量图片的提示词格式

请直接输出优化后的提示词，不要添加其他说明。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请优化以下图片设计描述为文生图提示词：\n\n{design_description}"}
    ]

    try:
        response = doubao_api.chat_completion(messages, model=DOUBAO_SEED_MODEL)
        enhanced_prompt = response["choices"][0]["message"]["content"].strip()
        print(f"豆包文案增强结果：{enhanced_prompt}")
        return enhanced_prompt
    except Exception as e:
        print(f"文案增强失败，使用原文本: {str(e)}")
        return design_description

def generate_image_from_text(prompt: str, size: str = "1920x1920") -> Optional[str]:
    """使用豆包文生图模型生成图片"""
    try:
        response = doubao_api.generate_image(prompt, model=DOUBAO_SEEDREAM_MODEL, size=size)
        image_url = response["data"][0]["url"]
        print(f"豆包文生图成功：{image_url}")
        return image_url
    except Exception as e:
        print(f"文生图失败: {str(e)}")
        return None

# 为了保持向后兼容
doubao_text_model = doubao_api
doubao_image_model = doubao_api
