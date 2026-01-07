import streamlit as st
from typing import Callable, Optional

from ml.settings import Settings
from ml.providers import LOCAL_MODEL_TO_CACHE, CACHE_TO_LOCAL_MODEL, clear_embeddings_cache
from ml.cache import clear_all_caches as clear_cache_caches
from ml.recommendation_engine import get_recommendation_engine, clear_engine_cache


def _clear_all_ml_caches():
    clear_embeddings_cache()
    clear_cache_caches()
    clear_engine_cache()


def is_ml_enabled() -> bool:
    return Settings().ml_enabled


def _get_engine():
    try:
        with st.spinner("Loading recommendation engine..."):
            engine = get_recommendation_engine()
            engine._ensure_initialized()
            return engine
    except Exception as e:
        st.error(f"⚠️ Could not load ML engine: {e}")
        return None


def render_cache_selector():
    settings = Settings()
    
    if not settings.ml_enabled:
        return
    
    providers = ["LM Studio", "Gemini API", "Local (llama-cpp)"]
    provider_map = {"LM Studio": "lmstudio", "Gemini API": "gemini", "Local (llama-cpp)": "local"}
    reverse_map = {v: k for k, v in provider_map.items()}
    
    current_provider_label = reverse_map.get(settings.provider, "LM Studio")
    
    provider_label = st.sidebar.radio(
        "🔌 Provider",
        providers,
        index=providers.index(current_provider_label),
        help="LM Studio requires server. Gemini uses API key. Local runs in-process."
    )
    new_provider = provider_map[provider_label]
    
    if new_provider == "gemini":
        selected_cache = "cache-gemini"
        selected_local_model = settings.local_model
        
    elif new_provider == "local":
        local_models = ["minilm", "bge-small", "qwen-1.5b", "qwen-7b"]
        model_labels = {
            "minilm": "MiniLM (fast, 80MB)",
            "bge-small": "BGE Small (fast, 130MB)",
            "qwen-1.5b": "Qwen2 1.5B (good, 3GB)",
            "qwen-7b": "Qwen2 7B (best, 14GB)",
        }
        
        current_index = local_models.index(settings.local_model) if settings.local_model in local_models else 0
        selected_local_model = st.sidebar.selectbox(
            "🧠 Local Model",
            local_models,
            index=current_index,
            format_func=lambda x: model_labels.get(x, x),
            help="Model will be auto-downloaded on first use"
        )
        selected_cache = LOCAL_MODEL_TO_CACHE.get(selected_local_model, f"cache-{selected_local_model}")
        
    else:
        cache_options = [
            d.name for d in settings.ml_dir.iterdir()
            if d.is_dir() and d.name.startswith("cache") and d.name != "cache-gemini"
        ]
        cache_options = sorted(cache_options)
        
        if cache_options:
            current_index = cache_options.index(settings.cache_dir_name) if settings.cache_dir_name in cache_options else 0
            selected_cache = st.sidebar.selectbox(
                "🧠 Embedding Cache",
                cache_options,
                index=current_index,
                help="Select which embedding cache to use"
            )
        else:
            selected_cache = settings.cache_dir_name
        
        selected_local_model = CACHE_TO_LOCAL_MODEL.get(selected_cache, settings.local_model)
    
    provider_changed = new_provider != settings.provider
    cache_changed = selected_cache != settings.cache_dir_name
    local_model_changed = selected_local_model != settings.local_model
    
    settings_changed = provider_changed or cache_changed or local_model_changed
    
    if settings_changed:
        settings.cache_dir_name = selected_cache
        settings.provider = new_provider
        settings.local_model = selected_local_model
        settings.save()
        
        _clear_all_ml_caches()
        
        st.sidebar.success("Settings updated. Reloading...")
        st.rerun()


def render_text_recommendations(books_dict: dict) -> Optional[list]:
    if not is_ml_enabled():
        return None
    
    st.subheader("🔮 Find Similar Books by Description")
    
    query = st.text_area(
        "Describe what kind of book you're looking for:",
        placeholder="e.g., A dystopian story about survival and rebellion against an oppressive government...",
        height=100
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        num_results = st.selectbox("Number of results", [5, 10, 15, 20], index=0)
    
    if st.button("Find Recommendations", type="primary"):
        if not query or len(query.strip()) < 10:
            st.warning("Please enter a longer description (at least 10 characters)")
            return None
        
        engine = _get_engine()
        if engine is None:
            return None
        
        try:
            with st.spinner("Finding similar books..."):
                results = engine.recommend_by_text(query, num_results)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
            return None
        
        if not results:
            st.info("No recommendations found. Try a different description.")
            return None
        
        st.success(f"Found {len(results)} recommendations!")
        return results
    
    return None


def render_similar_books(book_id: str, books_dict: dict, display_func: Callable):
    if not is_ml_enabled():
        return
    
    state_key = f"similar_{book_id}"
    
    if state_key not in st.session_state:
        st.session_state[state_key] = False
    
    col1, col2 = st.columns([1, 2])
    with col1:
        num_results = st.selectbox("How many?", [3, 5, 10, 15, 20], index=0, key=f"num_{book_id}")
    with col2:
        if st.button("Find similar books with AI", key=f"btn_{book_id}"):
            st.session_state[state_key] = True
    
    if not st.session_state[state_key]:
        return
    
    engine = _get_engine()
    if engine is None:
        return
    
    try:
        with st.spinner("Finding similar books..."):
            results = engine.recommend_by_book_id(book_id, num_results + 1)
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
        return
    
    if not results:
        st.info("No embedding available for this book.")
        return
    
    results = [(bid, title, score) for bid, title, score in results if bid != book_id][:num_results]
    
    if not results:
        st.info("No similar books found.")
        return
    
    st.markdown("#### 📖 You might also like:")
    for bid, title, score in results:
        if bid in books_dict:
            col1, col2 = st.columns([4, 1])
            with col2:
                match_pct = max(0, (1 - score) * 100)
                st.metric("Match", f"{match_pct:.0f}%")
            with col1:
                display_func(books_dict[bid])


def render_recommendation_results(results: list, books_dict: dict, display_func: Callable):
    for book_id, title, score in results:
        if book_id in books_dict:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col2:
                    st.metric("Match", f"{(1 - score) * 100:.0f}%")
                with col1:
                    display_func(books_dict[book_id])
