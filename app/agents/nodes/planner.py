from app.agents.state import AgentState
from app.gateways.client import get_langchain_llm
import logfire


llm = get_langchain_llm(feature="planner")


def planner_node(state: AgentState):

    # Keep only recent context
    recent_messages = state["message"][-5:-1]

    history = "\n".join(
        f"{'User' if msg['role'] == 'User' else 'Assistant'}: {msg['content']}"
        for msg in recent_messages
    )

    user_message = (
        state["message"][-1]["content"]
        if state["message"]
        else ""
    )

    prompt = f"""
You are a planner for a Nepal local-government ward assistant.

Conversation:
{history}

Latest user message:
{user_message}

Rules:
1. Return CONVERSATIONAL if the message is:
   - a greeting
   - casual conversation
   - answerable from the conversation context

2. Otherwise return a concise search query for:
   - Nepal ward/municipality services
   - procedures
   - required documents
   - fees
   - eligibility
   - application/process information

Output ONLY:
CONVERSATIONAL

OR:
a concise search query.

Do not explain your answer.
"""

    with logfire.span("Planner Decision"):

        response = llm.invoke(prompt)

        decision = response.content.strip()

        logfire.info(
            f"Intent is identified as {decision}"
        )

    if decision == "CONVERSATIONAL":
        return {
            "current_query": "CONVERSATIONAL",
            "status": "Handling conversationally using memory",
            "plan": [
                "Intent: Conversational/Memory",
                "Retrieval: Skipped"
            ]
        }

    return {
        "current_query": decision,
        "status": f"Technical research needed. Searching for: {decision}",
        "plan": [
            "Intent: Technical",
            f"Search Term: {decision}"
        ]
    }