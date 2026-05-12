import sys
from pathlib import Path
project_root = Path(__file__).resolve()
for p in (project_root, *project_root.parents):
    if (p / '.env').exists() or (p / '.git').exists():
        project_root = p
        break
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

#################################################################

from langgraph.graph import StateGraph, START, END
from xhs_picture_agent.states.state import PictureMessagesState
from xhs_picture_agent.nodes.picture_agent_node import picture_design_node


# Build workflow
xhs_picture_agent_builder = StateGraph(PictureMessagesState)

# Add nodes
xhs_picture_agent_builder.add_node("picture_design_node", picture_design_node)

# Add edges
xhs_picture_agent_builder.add_edge(START, "picture_design_node")
xhs_picture_agent_builder.add_edge("picture_design_node", END)

# Compile
xhs_picture_agent = xhs_picture_agent_builder.compile()

# 网站：https://mermaid.live
# print(xhs_picture_agent.get_graph(xray=True).draw_mermaid())

# 导出智能体实例供外部使用
__all__ = ['xhs_picture_agent']

# 使用示例:
# from langchain.messages import HumanMessage
# result = xhs_picture_agent.invoke({
#     "messages": [HumanMessage(content="设计图片")],
#     "topic_data": {"title": "测试选题"},
#     "content_data": {"content": "测试内容..."}
# })
# print(result["output"])  # 获取API输出结构
