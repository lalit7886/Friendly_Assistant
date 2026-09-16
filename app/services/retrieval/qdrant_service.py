import logfire
# from qdrant_client import QdrantClient
# from qdrant_client.http import models
from app.config import settings
from app.services.retrieval.embeddings import embed_query
import numpy as np
import json
from pathlib import Path



# Initialize Qdrant Client
# client = QdrantClient(
#     url=settings.QDRANT_URL,
#     api_key=settings.QDRANT_API_KEY
# )

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DATA_DIR = PROJECT_ROOT / "processed_data"

def search_enterprise_knowledge(query: str, limit: int = 5):
    """
    Performs a high-precision search in the enterprise knowledge base.
    We keep the default retrieval window tight to minimize latency while
    preserving enough context for the answerer to synthesize a correct response.
    """
    try:
        
        query_vector = embed_query(query)
        embeddings=np.load(PROCESSED_DATA_DIR / "embeddings" / "improved1.npy")

        similarity = np.asarray(query_vector) @ embeddings.T
        best_index=np.argsort(similarity)[-limit:][::-1]
        
        with open(PROCESSED_DATA_DIR / "chunks" / "improved1.json", "r", encoding="utf-8") as f:
           
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