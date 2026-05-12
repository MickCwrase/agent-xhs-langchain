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

from typing import Literal
from langgraph.graph import StateGraph, START, END
from xhs_content_agent.states.state import ContentMessagesState
from xhs_content_agent.nodes.content_agent_node import content_generation_node, content_refinement_node


def should_continue(state: ContentMessagesState) -> Literal["content_refinement_node", END]:
    """
    决定是否需要优化内容
    """
    # 简单逻辑：如果有反馈就优化，否则结束
    if state.get("needs_refinement", False):
        return "content_refinement_node"
    else:
        return END


# Build workflow
xhs_content_agent_builder = StateGraph(ContentMessagesState)

# Add nodes
xhs_content_agent_builder.add_node("content_generation_node", content_generation_node)
xhs_content_agent_builder.add_node("content_refinement_node", content_refinement_node)

# Add edges
xhs_content_agent_builder.add_edge(START, "content_generation_node")
xhs_content_agent_builder.add_conditional_edges(
    "content_generation_node",
    should_continue,
    ["content_refinement_node", END]
)
xhs_content_agent_builder.add_edge("content_refinement_node", END)

# Compile
xhs_content_agent = xhs_content_agent_builder.compile()

# 网站：https://mermaid.live
# print(xhs_content_agent.get_graph(xray=True).draw_mermaid())

# 导出智能体实例供外部使用
__all__ = ['xhs_content_agent']

# 使用示例:
# from langchain.messages import HumanMessage
# result = xhs_content_agent.invoke({
#     "messages": [HumanMessage(content="生成内容")],
#     "topic_data": {"title": "测试选题", "hook": "测试hook"}
# })
# print(result["output"])  # 获取API输出结构
