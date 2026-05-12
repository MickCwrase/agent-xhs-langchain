import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

# 优先级：通义千问DashScope > 智谱API > OpenRouter
api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("GLM_API_KEY") or os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("DASHSCOPE_API_BASE") or os.getenv("GLM_API_BASE") or os.getenv("OPENROUTER_API_BASE")
model_selected = os.getenv("DASHSCOPE_MODEL") or os.getenv("GLM_MODEL") or os.getenv("OPENROUTER_MODEL")

# 根据API key判断使用哪个服务
if os.getenv("DASHSCOPE_API_KEY"):
    print("使用通义千问DashScope API")
    model_selected = model_selected or "qwen-turbo"
    base_url = os.getenv("DASHSCOPE_API_BASE") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
elif os.getenv("GLM_API_KEY"):
    print("使用智谱AI API")
    model_selected = model_selected or "glm-4"
    base_url = os.getenv("GLM_API_BASE") or "https://open.bigmodel.cn/api/paas/v4"
elif os.getenv("OPENROUTER_API_KEY"):
    print("使用OpenRouter API")
    model_selected = model_selected or "microsoft/wizardlm-2-8x22b"
    base_url = os.getenv("OPENROUTER_API_BASE") or "https://openrouter.ai/api/v1"
else:
    raise ValueError("请配置DASHSCOPE_API_KEY、GLM_API_KEY或OPENROUTER_API_KEY环境变量之一")

print(f"模型: {model_selected}, API地址: {base_url}")

openrouter_model = ChatOpenAI(
    model=model_selected,
    base_url=base_url,
    api_key=api_key,
    temperature=0.7,
    max_tokens=4000
)


# for test
# response = model.invoke("hello")
# print(response)



