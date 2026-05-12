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
from xhs_topic_agent.states.state import TopicMessagesState
from xhs_topic_agent.nodes.xhs_topic_agent_node import initial_topic_generate_node

# Build workflow
xhs_topic_agent_builder = StateGraph(TopicMessagesState)

# Add nodes
xhs_topic_agent_builder.add_node("initial_topic_generate_node", initial_topic_generate_node)

# Add edges - 直接生成选题后结束，不需要人机交互
xhs_topic_agent_builder.add_edge(START, "initial_topic_generate_node")
xhs_topic_agent_builder.add_edge("initial_topic_generate_node", END)

# Compile
xhs_topic_agent = xhs_topic_agent_builder.compile()

# 网站：https://mermaid.live
# print(xhs_topic_agent.get_graph(xray=True).draw_mermaid())

# 导出智能体实例供外部使用
__all__ = ['xhs_topic_agent']

# 使用示例:
# from langchain.messages import HumanMessage
# result = xhs_topic_agent.invoke({"messages": [HumanMessage(content="大连的旅游景点")]})
# print(result["output"])  # 获取API输出结构


