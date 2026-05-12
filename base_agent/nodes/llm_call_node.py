import sys
from pathlib import Path
project_root = Path(__file__).resolve()                          # 1. 找到“项目根”——这里以「包含 .git 或 .env 的文件夹」为根，可自行调整规则
for p in (project_root, *project_root.parents):
    if (p / '.env').exists() or (p / '.git').exists():
        project_root = p
        break
if str(project_root) not in sys.path:                            # 2. 把项目根塞进 sys.path 最前面
    sys.path.insert(0, str(project_root))
################################################################

from base_agent.models.openrouter_llm import openrouter_model
from base_agent.tools.web_search_tool import web_search_tool
from langchain.messages import SystemMessage


tools = [web_search_tool]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = openrouter_model.bind_tools(tools)

def llm_call_node(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

