from langchain.messages import ToolMessage
from base_agent.tools.web_search_tool import web_search_tool

tools = [web_search_tool]
tools_by_name = {tool.name: tool for tool in tools}


def tool_call_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}