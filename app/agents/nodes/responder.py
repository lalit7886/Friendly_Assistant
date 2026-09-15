import logfire
from app.agents.state import AgentState
from app.config import settings
from app.gateways.client import portkey_client,extract_cache_status
import json



def generate_node(state: AgentState):
    query=state["current_query"]
    history=""
    for msg in state["message"][:-1]:
        role= "User" if msg["role"]=="User" else "Assistant"
        history += f"{role} : {msg["content"]} \n"
        
    user_msg=state["message"][-1]["content"] if state["message"] else ""
    
    if query=="CONVERSATIONAL":
        logfire.info("Geenrating conversational response using memory")
        prompt = f"""
        You are a friendly and helpful Ward AI Assistant for local ward of Nepal Governments.
        Answer the user's latest message using the CONVERSATION HISTORY below.

        CONVERSATION HISTORY:
        {history}

        LATEST MESSAGE:
        "{user_msg}"
        """
        
    else:
        logfire.info("Generating Technical Response ")
        
        max_context_char=2000
        full_context = ""
        
        for doc in state["documents"]:
            if len(full_context) + len(doc) < max_context_char:
                full_context += doc + "\n"
            else:
                logfire.warning("Context truncated to fit the gemini api key")
                break
            
        prompt = f"""
        You are a experienced senior AI assistant for Ward related service for local government of Nepal.
        Answer the question using the TECHNICAL CONTEXT provided.

        TECHNICAL CONTEXT:
        {full_context}

        CONVERSATION HISTORY:
        {history}

        USER QUESTION:
        "{user_msg}"
        """
    
    with logfire.span("LLM Syntesis"):
        try:
            response = portkey_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content=response.choices[0].message.content
            cache_status = extract_cache_status(response)

            is_cache_hit = cache_status == "HIT"

            if is_cache_hit:
                logfire.info("⚡ Gateway Cache Hit — response served from Portkey cache.")
                plan_update = state["plan"] + ["Cache: Hit ⚡"]
                status = "Cache hit — instant response."
            else:
                logfire.info("✅ Response synthesised via LLM.")
                plan_update = state["plan"]
                status = "Response generated."          
            return {
                "final_answer" : content,
                "status" : "Response Generated",
                "plan" : state["plan"],
                "messages" : [{"Role":"Assistant", "content": content}]
                
            }
        except Exception as e:
            logfire.error(f" LMM generation error is occured {e}")
            

                    
            