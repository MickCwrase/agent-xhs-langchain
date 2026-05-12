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
from xhs_flow_agent.states.state import FlowMessagesState
from xhs_flow_agent.nodes.flow_agent_node import flow_assignment_node


# Build workflow
xhs_flow_agent_builder = StateGraph(FlowMessagesState)

# Add nodes
xhs_flow_agent_builder.add_node("flow_assignment_node", flow_assignment_node)

# Add edges
xhs_flow_agent_builder.add_edge(START, "flow_assignment_node")
xhs_flow_agent_builder.add_edge("flow_assignment_node", END)

# Compile
xhs_flow_agent = xhs_flow_agent_builder.compile()

# 导出智能体实例供外部使用
__all__ = ['xhs_flow_agent']

# 使用示例:
# from langchain.messages import HumanMessage
# result = xhs_flow_agent.invoke({
#     "messages": [HumanMessage(content="流程指派")],
#     "user_input": "帮我创作一个关于咖啡的笔记"
# })
# print(result["output"])  # 获取流程指派结果
