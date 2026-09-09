from pydantic import BaseModel
from typing import Optional
import logfire
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from app.agents.graph import rag_agent
from app.guardrails.rails import initialize_rails, guard
from contextlib import asynccontextmanager
load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))


from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: logic before yield runs when app starts
    initialize_rails()
    yield  # The app executes here

    # Shutdown: logic after yield runs when app stops (optional)

app = FastAPI(title="Enterprise Agentic RAG API", lifespan=lifespan)

class QueryRequest(BaseModel):
    q:str
    thread_id: Optional[str] = "default_user"
    
@app.get("/")

def home():
    return {"Message": "Enterprise Level RAG was live"}

@app.get("/graph")
def get_graph_image():
    try:
        png_bytes=rag_agent.get_graph().draw_mermaid_png()
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        return {f"error is occured unable to show you a image"}
    
@app.post("/query")
def query(request:QueryRequest):
    q=request.q
    thread_id=request.thread_id
    
    initial_state={
        "message" : [{"role":"User","content":q}],
        "current_query":q,
        "documents":[],
        "plan" : ["start"],
        "status" : "initializing graph"
        
    }
    
    config = {"configurable": {"thread_id":thread_id}}

    try:
        rail_fired, rail_response = guard(q)
        if rail_fired:
            logfire.info(f"🛡️ Request blocked by guardrails | thread={thread_id}")
            return {
                "question": q,
                "answer": rail_response,
                "thought_process": ["Intent: Guardrails Fired", "Retrieval: Skipped"],
                "status": "Blocked by guardrails.",
                "sources": []
            }

        # Gate 2: LangGraph RAG pipeline
        # Run the graph synchronously to preserve Logfire context variables
        final_output = rag_agent.invoke(initial_state, config=config)
        return {
            "question":q,
            "answer":final_output.get("final_answer"),
            "thought_process":final_output.get("plan"),
            "status" : final_output.get("status"),
            "sources" : final_output.get("documents",[])
        }
        
    except Exception as e:
        logfire.error(f"Backend excution failed as errror {e}")
        raise