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
from xhs_review_agent.states.state import ReviewMessagesState
from xhs_review_agent.nodes.review_agent_node import content_review_node


# Build workflow
xhs_review_agent_builder = StateGraph(ReviewMessagesState)

# Add nodes
xhs_review_agent_builder.add_node("content_review_node", content_review_node)

# Add edges
xhs_review_agent_builder.add_edge(START, "content_review_node")
xhs_review_agent_builder.add_edge("content_review_node", END)

# Compile
xhs_review_agent = xhs_review_agent_builder.compile()

# 导出智能体实例供外部使用
__all__ = ['xhs_review_agent']
