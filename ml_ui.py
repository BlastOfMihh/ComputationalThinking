"""
ML-powered UI components for book recommendations.
"""
import json
import streamlit as st
import sys
from pathlib import Path

# ML folder path
ML_DIR = Path(__file__).parent / "ml"
SETTINGS_PATH = ML_DIR / "settings.json"

# Add ml folder to path for imports
sys.path.insert(0, str(ML_DIR))

# Track the provider that was loaded at startup
with open(SETTINGS_PATH) as f:
    _startup_settings = json.load(f)
_LOADED_PROVIDER = _startup_settings.get("provider", "lmstudio")
_LOADED_LOCAL_MODEL = _startup_settings.get("local_model", "minilm")

from recommandation_engine import RecommandationEngine

# Lazy-load the engine to avoid slow startup
_engine = None
_current_cache = None


def _get_cache_options():
    """Get available cache directories from ml folder."""
    cache_dirs = [d.name for d in ML_DIR.iterdir() if d.is_dir() and d.name.startswith("cache")]
    return sorted(cache_dirs)


def _get_current_cache():
    """Get current cache from settings."""
    with open(SETTINGS_PATH) as f:
        settings = json.load(f)
    return settings.get("cache_dir", "cache")


def _set_cache(cache_name):
    """Update cache in settings.json."""
    with open(SETTINGS_PATH) as f:
        settings = json.load(f)
    settings["cache_dir"] = cache_name
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)


def render_cache_selector():
    """Render a cache/model selector in the sidebar."""
    global _engine, _current_cache
    
    with open(SETTINGS_PATH) as f:
        settings = json.load(f)
    
    current_cache = settings.get("cache_dir", "cache")
    current_provider = settings.get("provider", "lmstudio")
    current_local_model = settings.get("local_model", "qwen-0.6b")
    
    # Provider selection
    providers = ["LM Studio", "Gemini API", "Local (llama-cpp)"]
    provider_map = {"LM Studio": "lmstudio", "Gemini API": "gemini", "Local (llama-cpp)": "local"}
    reverse_map = {v: k for k, v in provider_map.items()}
    
    provider = st.sidebar.radio(
        "🔌 Provider",
        providers,
        index=providers.index(reverse_map.get(current_provider, "LM Studio")),
        help="LM Studio requires server. Gemini uses API key. Local runs in-process."
    )
    new_provider = provider_map[provider]
    
    # Map local models to existing cache directories
    local_model_to_cache = {
        "qwen-0.6b": "cache-qwen0.6",
        "gemma-300m": "cache-gemma0.3",
        "qwen-8b": "cache-qwen8",
        "minilm": "cache-minilm",
    }
    cache_to_local_model = {v: k for k, v in local_model_to_cache.items()}
    
    # Cache/model selection based on provider
    if new_provider == "gemini":
        selected_cache = "cache-gemini"
        selected_local_model = current_local_model
    elif new_provider == "local":
        # Show local model selector
        local_models = ["minilm", "gemma-300m", "qwen-0.6b", "qwen-8b"]
        model_labels = {
            "minilm": "MiniLM (fast, 80MB)",
            "gemma-300m": "BGE Small (fast, 130MB)",
            "qwen-0.6b": "Qwen2 1.5B (good, 3GB)",
            "qwen-8b": "Qwen2 7B (best, 14GB)",
        }
        selected_local_model = st.sidebar.selectbox(
            "🧠 Local Model",
            local_models,
            index=local_models.index(current_local_model) if current_local_model in local_models else 0,
            format_func=lambda x: model_labels.get(x, x),
            help="Model will be auto-downloaded on first use"
        )
        # Use same cache as LM Studio for same model
        selected_cache = local_model_to_cache.get(selected_local_model, f"cache-{selected_local_model}")
    else:
        # LM Studio - show cache selector (same caches work for local too)
        cache_options = [d.name for d in ML_DIR.iterdir() 
                        if d.is_dir() and d.name.startswith("cache") 
                        and d.name != "cache-gemini"]
        cache_options = sorted(cache_options)
        
        if cache_options:
            current_index = cache_options.index(current_cache) if current_cache in cache_options else 0
            selected_cache = st.sidebar.selectbox(
                "🧠 Embedding Cache",
                cache_options,
                index=current_index,
                help="Select which embedding cache to use"
            )
        else:
            selected_cache = current_cache
        # Infer local model from cache for consistency
        selected_local_model = cache_to_local_model.get(selected_cache, current_local_model)
    
    # Check if anything changed
    provider_changed = new_provider != _LOADED_PROVIDER
    local_model_changed = (new_provider == "local" and selected_local_model != _LOADED_LOCAL_MODEL)
    
    if (selected_cache != current_cache or 
        new_provider != current_provider or 
        selected_local_model != current_local_model):
        
        settings["cache_dir"] = selected_cache
        settings["provider"] = new_provider
        settings["local_model"] = selected_local_model
        
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
        
        _engine = None
        _current_cache = selected_cache
        
        # If provider or local model changed, need full restart
        if provider_changed or local_model_changed:
            st.sidebar.error("⚠️ Please restart the app (Ctrl+C, then run again)")
            st.stop()
        else:
            st.sidebar.success("Settings updated. Restarting...")
            st.rerun()


def get_engine():
    global _engine
    if _engine is None:
        try:
            with st.spinner("Loading recommendation engine..."):
                _engine = RecommandationEngine()
        except Exception as e:
            st.error(f"⚠️ Could not connect to the ML server: {e}")
            return None
    return _engine


def render_text_recommendations(books_dict):
    """
    Render a text-based recommendation search UI.
    
    Args:
        books_dict: Dict mapping book_id to book data for display
    """
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
            return
        
        engine = get_engine()
        if engine is None:
            return
        
        try:
            with st.spinner("Finding similar books..."):
                results = engine.get_book_recommandation_text_based(query.lower(), num_results)
        except Exception as e:
            st.error(f"⚠️ Error connecting to ML server: {e}")
            return
        
        if not results:
            st.info("No recommendations found. Try a different description.")
            return
        
        st.success(f"Found {len(results)} recommendations!")
        return results


def render_similar_books(book_id, books_dict, display_func):
    """
    Render similar book recommendations for a given book.
    
    Args:
        book_id: The book ID to find similar books for
        books_dict: Dict mapping book_id to book data
        display_func: Function to display a single book
    """
    # Use session state to track which books have been clicked
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
    
    engine = get_engine()
    if engine is None:
        return
    
    try:
        with st.spinner("Finding similar books..."):
            results = engine.get_book_recommandation_book_id_based(book_id, num_results + 1)
    except Exception as e:
        st.error(f"⚠️ Error connecting to ML server: {e}")
        return
    
    if not results:
        st.info("No embedding available for this book.")
        return
    
    # Filter out the source book itself
    results = [(bid, title, score) for bid, title, score in results if bid != book_id][:num_results]
    
    if not results:
        st.info("No similar books found.")
        return
    
    st.markdown("#### 📖 You might also like:")
    for bid, title, score in results:
        if bid in books_dict:
            col1, col2 = st.columns([4, 1])
            with col2:
                # FAISS L2 distance: lower = more similar. Convert to percentage.
                match_pct = max(0, (1 - score) * 100)
                st.metric("Match", f"{match_pct:.0f}%")
            with col1:
                display_func(books_dict[bid])


def render_recommendation_results(results, books_dict, display_func):
    """
    Display recommendation results.
    
    Args:
        results: List of (book_id, title, score) tuples
        books_dict: Dict mapping book_id to book data
        display_func: Function to display a single book
    """
    for book_id, title, score in results:
        if book_id in books_dict:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col2:
                    st.metric("Match", f"{(1 - score) * 100:.0f}%")
                with col1:
                    display_func(books_dict[book_id])
