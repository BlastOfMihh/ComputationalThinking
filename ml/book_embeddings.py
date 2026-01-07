"""
Unified book embeddings module.
Embeds books once and stores both:
- Embeddings cache (book_id -> vector) for direct lookups
- Vectorstore for similarity search
"""
import json
import pickle
import time
import pandas as pd
import numpy as np
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Load settings
_SETTINGS_PATH = Path(__file__).parent / "settings.json"
with open(_SETTINGS_PATH) as f:
    _settings = json.load(f)

ML_DIR = Path(__file__).parent
BATCH_SIZE = _settings["batch_size"]
LOWER = _settings["lower_embeddings"]

# Current cache directory (can be changed at runtime)
_current_cache_dir = _settings["cache_dir"]


def get_cache_options():
    """Get available cache directories from ml folder."""
    cache_dirs = [d.name for d in ML_DIR.iterdir() if d.is_dir() and d.name.startswith("cache")]
    return sorted(cache_dirs)


def get_current_cache_dir():
    """Get the current cache directory name."""
    return _current_cache_dir


def set_cache_dir(cache_dir_name):
    """Set the cache directory to use."""
    global _current_cache_dir
    _current_cache_dir = cache_dir_name


def _get_cache_paths():
    """Get current cache paths based on settings.json (reads fresh each time)."""
    with open(_SETTINGS_PATH) as f:
        settings = json.load(f)
    cache_dir = ML_DIR / settings["cache_dir"]
    embeddings_cache_path = cache_dir / settings["embeddings_cache_file"]
    faiss_index_path = cache_dir / settings["faiss_index_dir"]
    return cache_dir, embeddings_cache_path, faiss_index_path


def _ensure_cache_dir():
    cache_dir, _, _ = _get_cache_paths()
    cache_dir.mkdir(parents=True, exist_ok=True)


def _load_pickle(path):
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def _save_pickle(obj, path):
    _ensure_cache_dir()
    with open(path, "wb") as f:
        pickle.dump(obj, f)


# =============================================================================
# Main initialization function
# =============================================================================
def initialize_book_embeddings(books_df, embeddings_model, text_column="description", batch_size=BATCH_SIZE):
    """
    Initialize both embeddings cache and vectorstore in a single pass.
    
    Args:
        books_df: DataFrame with bookId, title, and description columns
        embeddings_model: LangChain embeddings model
        text_column: Column containing text to embed
        batch_size: Number of texts to embed per API call
    
    Returns:
        Tuple of (embeddings_cache dict, vectorstore)
    """
    _, embeddings_cache_path, _ = _get_cache_paths()
    
    print("Loading embeddings cache...")
    cache = _load_pickle(embeddings_cache_path) or {}
    print(f"Loaded {len(cache)} cached embeddings.")
    
    # Collect books that need embedding
    books_to_embed = []
    for _, row in books_df.iterrows():
        book_id = row["bookId"]
        text = row.get(text_column, "")
        if pd.isna(text) or not str(text).strip():
            continue
        if book_id not in cache:
            books_to_embed.append({
                "book_id": book_id,
                "title": row.get("title", ""),
                "text": str(text).lower() if LOWER else str(text)
            })
    pass
    # Embed new books in batches
    if books_to_embed:
        # Get delay setting
        with open(_SETTINGS_PATH) as f:
            settings = json.load(f)
        batch_delay = settings.get("batch_delay_seconds", 0)
        
        print(f"Embedding {len(books_to_embed)} new books in batches of {batch_size}...")
        for i in range(0, len(books_to_embed), batch_size):
            batch = books_to_embed[i:i + batch_size]
            texts = [b["text"] for b in batch]
            
            vectors = embeddings_model.embed_documents(texts)
            for book, vector in zip(batch, vectors):
                cache[book["book_id"]] = vector
            
            _save_pickle(cache, embeddings_cache_path)
            print(f"Batch {i // batch_size + 1}/{(len(books_to_embed) - 1) // batch_size + 1} done")
            
            # Wait between batches (useful for rate-limited APIs like Gemini)
            if batch_delay > 0 and i + batch_size < len(books_to_embed):
                time.sleep(batch_delay)
        
        print(f"Embedded {len(books_to_embed)} new books.")
    
    # Build vectorstore from cache
    vectorstore = _build_vectorstore_from_cache(books_df, cache, embeddings_model, text_column)
    
    return cache, vectorstore


def _build_vectorstore_from_cache(books_df, cache, embeddings_model, text_column="description"):
    """Build vectorstore using pre-computed embeddings from cache."""
    _, _, faiss_index_path = _get_cache_paths()
    
    print("Building vectorstore from cache...")
    texts = []
    embeddings_list = []
    metadatas = []
    
    for _, row in books_df.iterrows():
        book_id = row["bookId"]
        if book_id not in cache:
            continue
        
        text = row.get(text_column, "")
        if pd.isna(text) or not str(text).strip():
            continue
        
        texts.append(str(text).lower() if LOWER else str(text))
        embeddings_list.append(cache[book_id])
        metadatas.append({"book_id": book_id, "title": row.get("title", "")})
    
    print(f"Adding {len(texts)} documents to vectorstore (using cached embeddings)...")
    vectorstore = FAISS.from_embeddings(
        text_embeddings=list(zip(texts, embeddings_list)),
        embedding=embeddings_model,
        metadatas=metadatas
    )
    
    # Save FAISS index for fast loading next time
    _ensure_cache_dir()
    vectorstore.save_local(str(faiss_index_path))
    print("Vectorstore ready and saved.")
    
    return vectorstore


# =============================================================================
# Lookup functions
# =============================================================================
def get_vectorstore(embeddings_model=None):
    """Load existing vectorstore from disk."""
    _, _, faiss_index_path = _get_cache_paths()
    if faiss_index_path.exists() and embeddings_model is not None:
        print("Loading FAISS index from disk...")
        return FAISS.load_local(str(faiss_index_path), embeddings_model, allow_dangerous_deserialization=True)
    return None


def get_embeddings_cache():
    """Load existing embeddings cache."""
    _, embeddings_cache_path, _ = _get_cache_paths()
    return _load_pickle(embeddings_cache_path) or {}


def get_embedding_by_book_id(book_id, cache=None):
    """Get embedding vector for a specific book ID."""
    if cache == None:
        cache = get_embeddings_cache()
    return cache.get(book_id)


def get_embeddings_by_book_ids(book_ids, cache=None):
    """Get embedding vectors for multiple book IDs."""
    if cache == None:
        cache = get_embeddings_cache()
    return {bid: cache[bid] for bid in book_ids if bid in cache}


def search_similar_books(query, k=5, vectorstore=None):
    """
    Search for similar books by query text.
    
    Returns:
        List of (book_id, title, score) tuples
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()
    if vectorstore is None:
        raise ValueError("Vectorstore not initialized. Call initialize_book_embeddings first.")
    
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [(doc.metadata["book_id"], doc.metadata.get("title", ""), score) for doc, score in results]


def search_similar_books_by_vector(embedding, k=5, vectorstore=None):
    """
    Search for similar books using a pre-computed embedding vector.
    
    Args:
        embedding: List of floats representing the embedding vector
        k: Number of results to return
        vectorstore: Optional vectorstore instance
    
    Returns:
        List of (book_id, title, score) tuples
    """
    if embedding is None:
        return []
    
    if vectorstore is None:
        vectorstore = get_vectorstore()
    if vectorstore is None:
        raise ValueError("Vectorstore not initialized. Call initialize_book_embeddings first.")
    
    # Ensure embedding is a list (FAISS expects list, not numpy array directly in some cases)
    if hasattr(embedding, 'tolist'):
        embedding = embedding.tolist()
    
    results = vectorstore.similarity_search_with_score_by_vector(embedding, k=k)
    return [(doc.metadata["book_id"], doc.metadata.get("title", ""), score) for doc, score in results]
