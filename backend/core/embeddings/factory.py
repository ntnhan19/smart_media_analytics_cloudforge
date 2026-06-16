from config import settings
from .vector_store import VectorStore
from .pgvector_store import PGVectorStore

def get_vector_store():
    if settings.VECTOR_DB_TYPE.lower() == "pgvector":
        return PGVectorStore()
    else:
        return VectorStore()
