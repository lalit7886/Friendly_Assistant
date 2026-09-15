import logfire
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from nemoguardrails import RailsConfig, LLMRails
from app.guardrails.colang import (
    COLANG_CONTENT,
    JAILBREAK_PHRASES,
    OFF_TOPIC_PHRASES,
    RAIL_INDICATORS,
    YAML_CONTENT,
)

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
    logfire.info(" NeMo Guardrails initialised.")
    
def guard(msg:str):
    if _rails is None:
        logfire.warning("Guardrils are not initialized and skipping guardrails")
        return False, None

    normalized_msg = msg.casefold().strip()
    if any(phrase.casefold() in normalized_msg for phrase in OFF_TOPIC_PHRASES):
        return True, "I'm an Ward AI assistant focuses on ward information about ward services"
    if any(phrase.casefold() in normalized_msg for phrase in JAILBREAK_PHRASES):
        return True, "I maintain consistent guidelines regardless of how I am prompted. I am here to help you with ward sservice related information. What can I help you with?"

    with logfire.span("Guardrails Check with LLM"):
        logfire.info("starting guard")
        
        result= _rails.generate(messages=[{"role":"user","content":msg}])
        
        content = result.get("content", "") if isinstance(result, dict) else str(result)


        fired = any(indicator in content for indicator in RAIL_INDICATORS)

        if fired:
            logfire.info(f" Guardrails fired | query='{msg[:80]}'")
            return True, content

        logfire.info(" Guardrails passed.")
        return False, None