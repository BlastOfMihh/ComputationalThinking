from langchain_community.vectorstores import FAISS


def search_by_text(query: str, vectorstore: FAISS, k: int = 5) -> list[tuple[str, str, float]]:
    from ml.providers import get_current_embeddings
    
    # Need to embed the query text - this loads the model
    embeddings_model = get_current_embeddings()
    query_vector = embeddings_model.embed_query(query)
    
    results = vectorstore.similarity_search_with_score_by_vector(query_vector, k=k)
    return [
        (doc.metadata["book_id"], doc.metadata.get("title", ""), score) 
        for doc, score in results
    ]


def search_by_vector(embedding: list[float], vectorstore: FAISS, k: int = 5) -> list[tuple[str, str, float]]:
    if embedding is None:
        return []
    
    if hasattr(embedding, 'tolist'):
        embedding = embedding.tolist()
    
    # No model needed - we already have the vector
    results = vectorstore.similarity_search_with_score_by_vector(embedding, k=k)
    return [
        (doc.metadata["book_id"], doc.metadata.get("title", ""), score) 
        for doc, score in results
    ]
