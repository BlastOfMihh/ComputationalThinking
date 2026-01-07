"""
Main recommendation engine.
Provides high-level API for book recommendations.
"""
import pandas as pd
from typing import Optional

import streamlit as st

from ml.settings import Settings
from ml.search import search_by_text, search_by_vector


@st.cache_resource
def get_recommendation_engine() -> "RecommendationEngine":
    """Get cached recommendation engine instance."""
    return RecommendationEngine()


class RecommendationEngine:
    """
    High-level recommendation engine.
    Use get_recommendation_engine() to get cached instance.
    """
    
    def __init__(self):
        self._settings = Settings()
        self._vectorstore = None
        self._embeddings_cache = None
    
    def _ensure_initialized(self):
        """Lazy initialization of components."""
        if self._vectorstore is not None:
            return
        
        from ml.cache import get_current_vectorstore, get_current_embeddings_cache, initialize_vectorstore
        
        # Try to load existing vectorstore
        self._vectorstore = get_current_vectorstore()
        self._embeddings_cache = get_current_embeddings_cache()
        
        # If no vectorstore, initialize from books
        if self._vectorstore is None:
            books_df = pd.read_csv(self._settings.books_path)
            self._vectorstore = initialize_vectorstore(books_df)
            self._embeddings_cache = get_current_embeddings_cache()
    
    def recommend_by_text(self, text: str, count: int = 5) -> list[tuple[str, str, float]]:
        """
        Get recommendations based on text description.
        
        Args:
            text: Description of desired book
            count: Number of recommendations
            
        Returns:
            List of (book_id, title, score) tuples
        """
        self._ensure_initialized()
        return search_by_text(text.lower(), self._vectorstore, k=count)
    
    def recommend_by_book_id(self, book_id: str, count: int = 5) -> list[tuple[str, str, float]]:
        """
        Get recommendations similar to a specific book.
        
        Args:
            book_id: ID of source book
            count: Number of recommendations
            
        Returns:
            List of (book_id, title, score) tuples
        """
        self._ensure_initialized()
        embedding = self._embeddings_cache.get(book_id)
        
        if embedding is None:
            return []
        
        return search_by_vector(embedding, self._vectorstore, k=count)


def clear_engine_cache():
    """Clear the engine cache to force reload."""
    get_recommendation_engine.clear()
