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
from base_agent.states.state import MessagesState
from base_agent.nodes.llm_call_node import llm_call_node
from base_agent.nodes.tool_call_node import tool_call_node
from base_agent.utils.edge import should_continue

# Build workflow
base_agent_builder = StateGraph(MessagesState)

# Add nodes
base_agent_builder.add_node("llm_call_node", llm_call_node)
base_agent_builder.add_node("tool_call_node", tool_call_node)

# Add edges
base_agent_builder.add_edge(START, "llm_call_node")
base_agent_builder.add_conditional_edges(
    "llm_call_node",
    should_continue,
    ["tool_call_node", END]
)
base_agent_builder.add_edge("tool_call_node", "llm_call_node")

# Compile the agent
base_agent = base_agent_builder.compile()

# Show the agent
# 网站：https://mermaid.live
# print(agent.get_graph(xray=True).draw_mermaid())

# Invoke
# from langchain.messages import HumanMessage
# messages = [HumanMessage(content="大连的旅游景点")]
# messages = base_agent.invoke({"messages": messages})
# for m in messages["messages"]:
#     m.pretty_print()
