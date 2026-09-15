import logfire
# from qdrant_client import QdrantClient
# from qdrant_client.http import models
from app.config import settings
from app.services.retrieval.embeddings import embed_query
import numpy as np
import json



# Initialize Qdrant Client
# client = QdrantClient(
#     url=settings.QDRANT_URL,
#     api_key=settings.QDRANT_API_KEY
# )

def search_enterprise_knowledge(query: str, limit: int = 8):
    """
    Performs a high-precision search in the enterprise knowledge base.
    Uses the modern query_points interface.
    """
    try:
        
        query_vector = embed_query(query)
        embeddings=np.load("/Users/lalitramanmishra/RAG/RAG_PROJ_1/processed_data/embeddings/improved1.npy")

        similarity = np.asarray(query_vector) @ embeddings.T
        best_index=np.argsort(similarity)[-limit:][::-1]
        
        with open("/Users/lalitramanmishra/RAG/RAG_PROJ_1/processed_data/chunks/improved1.json","r",encoding="utf-8") as f:
           
            chunks=json.load(f)
            result=[chunks[i] for i in best_index]
        
        
        

    #     # Using query_points - the modern standard for Qdrant
    #     response = client.query_points(
    #         collection_name=settings.QDRANT_COLLECTION,
    #         query=query_vector,
    #         limit=limit,
    #         with_payload=True # JSON
    #     )
        result = [
            {
                "content": chunks[i],
                "source": "wadapatra_AI_ready_formatted",
                "score": float(similarity[i])
            }
            for i in best_index
        ]

        return result
    except Exception as e:
        logfire.error(f" Local Search Failed: {e}")
        return []