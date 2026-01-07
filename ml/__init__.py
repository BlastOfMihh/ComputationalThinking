"""
ML module for book recommendations.

Public API:
    - Settings: Configuration management
    - get_current_embeddings: Get embedding model for current settings
    - get_recommendation_engine: Get cached recommendation engine
    - RecommendationEngine: Main recommendation interface
"""

from ml.settings import Settings
from ml.providers import get_current_embeddings, get_embeddings
from ml.recommendation_engine import RecommendationEngine, get_recommendation_engine

__all__ = [
    "Settings",
    "get_current_embeddings",
    "get_embeddings",
    "RecommendationEngine",
    "get_recommendation_engine",
]
