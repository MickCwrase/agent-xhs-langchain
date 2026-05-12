import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

# 通义千问DashScope API配置
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
dashscope_api_base = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
dashscope_model = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

if not dashscope_api_key:
    raise ValueError("请配置DASHSCOPE_API_KEY环境变量")

print(f"使用通义千问DashScope API，模型: {dashscope_model}，API地址: {dashscope_api_base}")

# 通义千问兼容OpenAI格式的API
dashscope_model = ChatOpenAI(
    model=dashscope_model,
    base_url=dashscope_api_base,
    api_key=dashscope_api_key,
    temperature=0.7,
    max_tokens=4000
)

# 为了保持向后兼容，保留openrouter_model的名称
openrouter_model = dashscope_model

# for test
# response = model.invoke("hello")
# print(response)
