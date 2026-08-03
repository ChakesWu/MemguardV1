"""Initial graph registration; business nodes are added in later tasks."""

from langgraph.graph import END, START, MessagesState, StateGraph


def _unconfigured_agent(state: MessagesState) -> dict:
    return {
        "messages": [
            {
                "role": "assistant",
                "content": "The customer-support agent is being configured.",
            }
        ]
    }


_builder = StateGraph(MessagesState)
_builder.add_node("agent", _unconfigured_agent)
_builder.add_edge(START, "agent")
_builder.add_edge("agent", END)
customer_support_agent = _builder.compile()
