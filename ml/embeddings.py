import os
import json
from pathlib import Path

# =======================================================
# PROVIDER SELECTION (from settings.json)
# =======================================================
_SETTINGS_PATH = Path(__file__).parent / "settings.json"

with open(_SETTINGS_PATH) as f:
    _settings = json.load(f)

# Provider options: "lmstudio", "gemini", "local"
PROVIDER = _settings.get("provider", "lmstudio")

# Local model options for "local" provider (HuggingFace model IDs)
LOCAL_MODELS = {
    "qwen-0.6b": "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
    "gemma-300m": "BAAI/bge-small-en-v1.5",
    "qwen-8b": "Alibaba-NLP/gte-Qwen2-7B-instruct",
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
}


if PROVIDER == "lmstudio":
    # LM Studio server (requires LM Studio running)
    from langchain_openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",
        check_embedding_ctx_length=False
    )

elif PROVIDER == "gemini":
    # Google Gemini API
    api_key_path = Path(__file__).parent / "api_key.txt"
    with open(api_key_path) as f:
        MY_API_KEY = f.read().strip()
    if not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = MY_API_KEY

    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

elif PROVIDER == "local":
    # Local HuggingFace model (no server needed)
    from langchain_huggingface import HuggingFaceEmbeddings
    
    local_model = _settings.get("local_model", "minilm")
    model_name = LOCAL_MODELS.get(local_model, LOCAL_MODELS["minilm"])
    
    print(f"Loading local model: {model_name}")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "mps"},  # Use Metal on Mac
        encode_kwargs={"normalize_embeddings": True}
    )

else:
    raise ValueError(f"Unknown provider: {PROVIDER}")
# =======================================================
