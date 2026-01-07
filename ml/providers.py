import os
from pathlib import Path
from typing import Any

import streamlit as st

from ml.settings import Settings


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
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        check_embedding_ctx_length=False
    )


def _create_gemini():
    api_key_path = Path(__file__).parent / "api_key.txt"
    with open(api_key_path) as f:
        api_key = f.read().strip()
    
    if not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = api_key
    
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def _get_device() -> str:
    import torch
    
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def _create_local(model_name: str):
    from langchain_huggingface import HuggingFaceEmbeddings
    
    hf_model = LOCAL_MODELS.get(model_name, LOCAL_MODELS["minilm"])
    device = _get_device()
    print(f"Loading local model: {hf_model} on {device}")
    
    return HuggingFaceEmbeddings(
        model_name=hf_model,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True}
    )


@st.cache_resource
def get_embeddings(provider: str, local_model: str) -> Any:
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
    settings = Settings()
    return get_embeddings(settings.provider, settings.local_model)


def clear_embeddings_cache():
    get_embeddings.clear()
