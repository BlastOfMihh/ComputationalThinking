import pickle
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from langchain_community.vectorstores import FAISS

from ml.settings import Settings


def _ensure_cache_dir():
    Settings().cache_dir.mkdir(parents=True, exist_ok=True)


@st.cache_resource
def load_embeddings_cache(cache_dir_name: str) -> dict:
    settings = Settings()
    cache_path = settings.ml_dir / cache_dir_name / settings.embeddings_cache_file
    
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            cache = pickle.load(f)
        print(f"Loaded {len(cache)} cached embeddings from {cache_path}")
        return cache
    
    print(f"No cache found at {cache_path}, starting fresh")
    return {}


@st.cache_resource
def load_vectorstore(cache_dir_name: str, provider: str, local_model: str) -> Optional[FAISS]:
    from ml.providers import get_embeddings
    
    settings = Settings()
    faiss_path = settings.ml_dir / cache_dir_name / settings.faiss_index_dir
    
    if faiss_path.exists():
        print(f"Loading FAISS index from {faiss_path}...")
        embeddings_model = get_embeddings(provider, local_model)
        return FAISS.load_local(
            str(faiss_path),
            embeddings_model,
            allow_dangerous_deserialization=True
        )
    
    return None


def get_current_embeddings_cache() -> dict:
    settings = Settings()
    return load_embeddings_cache(settings.cache_dir_name)


def get_current_vectorstore() -> Optional[FAISS]:
    settings = Settings()
    return load_vectorstore(settings.cache_dir_name, settings.provider, settings.local_model)


def save_embeddings_cache(cache: dict):
    _ensure_cache_dir()
    settings = Settings()
    
    with open(settings.embeddings_cache_path, "wb") as f:
        pickle.dump(cache, f)


def initialize_vectorstore(books_df: pd.DataFrame) -> FAISS:
    from ml.providers import get_current_embeddings
    
    settings = Settings()
    embeddings_model = get_current_embeddings()
    cache = dict(get_current_embeddings_cache())
    
    books_to_embed = []
    for _, row in books_df.iterrows():
        book_id = row["bookId"]
        text = row.get(settings.text_column, "")
        
        if pd.isna(text) or not str(text).strip():
            continue
        if book_id not in cache:
            books_to_embed.append({
                "book_id": book_id,
                "title": row.get("title", ""),
                "text": str(text).lower() if settings.lower_embeddings else str(text)
            })
    
    if books_to_embed:
        _embed_books(books_to_embed, embeddings_model, cache, settings)
    
    vectorstore = _build_vectorstore(books_df, embeddings_model, cache, settings)
    
    load_embeddings_cache.clear()
    load_vectorstore.clear()
    
    return vectorstore


def _embed_books(books: list[dict], embeddings_model, cache: dict, settings: Settings):
    batch_size = settings.batch_size
    delay = settings.batch_delay_seconds
    
    print(f"Embedding {len(books)} new books in batches of {batch_size}...")
    
    for i in range(0, len(books), batch_size):
        batch = books[i:i + batch_size]
        texts = [b["text"] for b in batch]
        
        vectors = embeddings_model.embed_documents(texts)
        
        for book, vector in zip(batch, vectors):
            cache[book["book_id"]] = vector
        
        save_embeddings_cache(cache)
        
        batch_num = i // batch_size + 1
        total_batches = (len(books) - 1) // batch_size + 1
        print(f"Batch {batch_num}/{total_batches} done")
        
        if delay > 0 and i + batch_size < len(books):
            time.sleep(delay)
    
    print(f"Embedded {len(books)} new books.")


def _build_vectorstore(books_df: pd.DataFrame, embeddings_model, cache: dict, settings: Settings) -> FAISS:
    print("Building vectorstore from cache...")
    
    texts = []
    embeddings_list = []
    metadatas = []
    
    for _, row in books_df.iterrows():
        book_id = row["bookId"]
        if book_id not in cache:
            continue
        
        text = row.get(settings.text_column, "")
        if pd.isna(text) or not str(text).strip():
            continue
        
        processed_text = str(text).lower() if settings.lower_embeddings else str(text)
        texts.append(processed_text)
        embeddings_list.append(cache[book_id])
        metadatas.append({"book_id": book_id, "title": row.get("title", "")})
    
    print(f"Adding {len(texts)} documents to vectorstore...")
    
    vectorstore = FAISS.from_embeddings(
        text_embeddings=list(zip(texts, embeddings_list)),
        embedding=embeddings_model,
        metadatas=metadatas
    )
    
    _ensure_cache_dir()
    vectorstore.save_local(str(settings.faiss_index_path))
    print("Vectorstore saved.")
    
    return vectorstore


def clear_all_caches():
    load_embeddings_cache.clear()
    load_vectorstore.clear()
