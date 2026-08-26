from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    
    message: Annotated[List[dict],operator.add]
    current_query: str
    final_answer: str
    documents: List[str]
    plan: List[str]
    status: List[str]
    
    
