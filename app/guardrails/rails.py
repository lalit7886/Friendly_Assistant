import logfire
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from nemoguardrails import RailsConfig, LLMRails
from app.guardrails.colang import COLANG_CONTENT, YAML_CONTENT, RAIL_INDICATORS

_rails: LLMRails | None = None

def initialize_rails() ->None:
    global _rails
    
    guard_llm=ChatGoogleGenerativeAI(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        temperature=0
    )
    
    config=RailsConfig.from_content(
        COLANG_CONTENT,
        YAML_CONTENT
    )
    
    _rails = LLMRails(config, llm=guard_llm)
    logfire.info("🛡️ NeMo Guardrails initialised (deep-research-pro-preview-12-2025).")
    
def guard(msg:str):
    if _rails is None:
        logfire.warning("Guardrils are not initialized and skipping guardrails")
        return False, None
    with logfire.span("Guardrails Check"):
        logfire.info("starting guard")
        
        result= _rails.generate(messages=[{"role":"user","content":msg}])
        
        content = result.get("content", "") if isinstance(result, dict) else str(result)

        fired = any(indicator in content for indicator in RAIL_INDICATORS)

        if fired:
            logfire.info(f"🛡️ Guardrails fired | query='{msg[:80]}'")
            return True, content

        logfire.info("✅ Guardrails passed.")
        return False, None