"""
Search functions for book recommendations.
"""
from typing import Optional
from langchain_community.vectorstores import FAISS


def search_by_text(
    query: str, 
    vectorstore: FAISS, 
    k: int = 5
) -> list[tuple[str, str, float]]:
    """
    Search for similar books by text query.
    
    Args:
        query: Search text
        vectorstore: FAISS vectorstore
        k: Number of results
        
    Returns:
        List of (book_id, title, score) tuples
    """
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [
        (doc.metadata["book_id"], doc.metadata.get("title", ""), score) 
        for doc, score in results
    ]


def search_by_vector(
    embedding: list[float], 
    vectorstore: FAISS, 
    k: int = 5
) -> list[tuple[str, str, float]]:
    """
    Search for similar books using embedding vector.
    
    Args:
        embedding: Embedding vector
        vectorstore: FAISS vectorstore
        k: Number of results
        
    Returns:
        List of (book_id, title, score) tuples
    """
    if embedding is None:
        return []
    
    # Convert numpy array to list if needed
    if hasattr(embedding, 'tolist'):
        embedding = embedding.tolist()
    
    results = vectorstore.similarity_search_with_score_by_vector(embedding, k=k)
    return [
        (doc.metadata["book_id"], doc.metadata.get("title", ""), score) 
        for doc, score in results
    ]
