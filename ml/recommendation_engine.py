import pandas as pd
from typing import Optional

import streamlit as st

from ml.settings import Settings
from ml.search import search_by_text, search_by_vector


@st.cache_resource
def get_recommendation_engine() -> "RecommendationEngine":
    return RecommendationEngine()


class RecommendationEngine:
    def __init__(self):
        self._settings = Settings()
        self._vectorstore = None
        self._embeddings_cache = None
    
    def _ensure_initialized(self):
        if self._vectorstore is not None:
            return
        
        from ml.cache import get_current_vectorstore, get_current_embeddings_cache, initialize_vectorstore
        
        self._vectorstore = get_current_vectorstore()
        self._embeddings_cache = get_current_embeddings_cache()
        
        if self._vectorstore is None:
            books_df = pd.read_csv(self._settings.books_path)
            self._vectorstore = initialize_vectorstore(books_df)
            self._embeddings_cache = get_current_embeddings_cache()
    
    def recommend_by_text(self, text: str, count: int = 5) -> list[tuple[str, str, float]]:
        self._ensure_initialized()
        return search_by_text(text.lower(), self._vectorstore, k=count)
    
    def recommend_by_book_id(self, book_id: str, count: int = 5) -> list[tuple[str, str, float]]:
        self._ensure_initialized()
        embedding = self._embeddings_cache.get(book_id)
        
        if embedding is None:
            return []
        
        return search_by_vector(embedding, self._vectorstore, k=count)


def clear_engine_cache():
    get_recommendation_engine.clear()
