"""
Embedding provider factory.
Uses Streamlit's cache_resource for proper lifecycle management.
"""
import os
from pathlib import Path
from typing import Any

import streamlit as st

from ml.settings import Settings


# Model mappings
LOCAL_MODELS = {
    "qwen-0.6b": "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
    "gemma-300m": "BAAI/bge-small-en-v1.5",
    "qwen-8b": "Alibaba-NLP/gte-Qwen2-7B-instruct",
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
}

LOCAL_MODEL_TO_CACHE = {
    "qwen-0.6b": "cache-qwen0.6",
    "gemma-300m": "cache-gemma0.3",
    "qwen-8b": "cache-qwen8",
    "minilm": "cache-minilm",
}

CACHE_TO_LOCAL_MODEL = {v: k for k, v in LOCAL_MODEL_TO_CACHE.items()}


def _create_lmstudio():
    """Create LM Studio embeddings (requires server running)."""
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        check_embedding_ctx_length=False
    )


def _create_gemini():
    """Create Google Gemini embeddings."""
    api_key_path = Path(__file__).parent / "api_key.txt"
    with open(api_key_path) as f:
        api_key = f.read().strip()
    
    if not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = api_key
    
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def _create_local(model_name: str):
    """Create local HuggingFace embeddings."""
    from langchain_huggingface import HuggingFaceEmbeddings
    
    hf_model = LOCAL_MODELS.get(model_name, LOCAL_MODELS["minilm"])
    print(f"Loading local model: {hf_model}")
    
    return HuggingFaceEmbeddings(
        model_name=hf_model,
        model_kwargs={"device": "mps"},  # Metal on Mac
        encode_kwargs={"normalize_embeddings": True}
    )


@st.cache_resource
def get_embeddings(provider: str, local_model: str) -> Any:
    """
    Get or create embeddings model.
    Cached by Streamlit - changes to args will create new instance.
    
    Args:
        provider: "lmstudio", "gemini", or "local"
        local_model: Model name for local provider
        
    Returns:
        LangChain embeddings model
    """
    print(f"Creating embeddings: provider={provider}, local_model={local_model}")
    
    if provider == "lmstudio":
        return _create_lmstudio()
    elif provider == "gemini":
        return _create_gemini()
    elif provider == "local":
        return _create_local(local_model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_current_embeddings() -> Any:
    """Get embeddings model for current settings."""
    settings = Settings()
    return get_embeddings(settings.provider, settings.local_model)


def clear_embeddings_cache():
    """Clear the embeddings cache to force reload."""
    get_embeddings.clear()
