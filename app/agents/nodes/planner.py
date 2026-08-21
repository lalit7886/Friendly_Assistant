from app.agents.state import AgentState
from app.config import settings

import logfire
from langchain_google_genai import ChatGoogleGenerativeAI

llm=ChatGoogleGenerativeAI(api_key=settings.GEMINI_API_KEY,model=settings.GEMINI_MODEL)


def planner_node(state:AgentState):
    history=""
    for msg in state["message"][:-1]:
        role="User" if msg["role"]=="User" else "Assistant"
        history += f"{role} : {msg["content"]}\n"
        
    user_message= state["message"][-1]["content"] if state["message"] else ""
    
    prompt = f'''
    you are helpful and intelligent Assistant Planner.
    Analyze the conversation history and latest user message.
    
    Conversation history:
    {history}
    
    Latest Message:
    {user_message}
    
    Task:
    1. If the latest message is a greeting (hi, hello) or a question that can be answered using ONLY the conversation history above (e.g., "what is my name"), respond with 'CONVERSATIONAL'.
    2. If it is a technical question about Kubernetes, Intel, or Networking that requires fresh documentation, output a refined search query.
    
    Output ONLY 'CONVERSATIONAL' or the search query.
    '''
    
    with logfire.span("Planner Decision"):
        decision=llm.invoke(prompt).content[0]
        logfire.info(f"Intent is identified as {decision}")
        
        if decision=="CONVERSATIONAL":
            return {
                "current_query" : "CONVERSATIONAL",
                "status" : "Handilling conversationally using memory",
                "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
                
            }

        else:
            return{
                "current_query" : decision,
                "status": f"Technical research needed. Searching for: {decision}",
                "plan": ["Intent: Technical", f"Search Term: {decision}"]
            }
        
        