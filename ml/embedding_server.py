"""
Embedding server using llama-cpp-python.
Fully self-contained - no external apps needed.

Supports:
- Qwen3 Embedding 0.6B
- EmbeddingGemma 300M
- Qwen3 Embedding 8B

Requirements:
    pip install llama-cpp-python huggingface-hub flask

Usage:
    python ml/embedding_server.py [model_name]
    
    model_name options:
        - qwen-0.6b (default)
        - gemma-300m
        - qwen-8b

The server exposes an OpenAI-compatible API at http://localhost:1234/v1
"""
import os
import sys
import argparse
from pathlib import Path

# Models configuration - HuggingFace repo and filename
MODELS = {
    "qwen-0.6b": {
        "repo": "Qwen/Qwen3-Embedding-0.6B-GGUF",
        "filename": "Qwen3-Embedding-0.6B-f16.gguf",
        "description": "Qwen3 Embedding 0.6B (fast, lightweight)"
    },
    "gemma-300m": {
        "repo": "lmstudio-community/embeddinggemma-300m-qat-GGUF",
        "filename": "embeddinggemma-300m-qat-Q4_0.gguf",
        "description": "EmbeddingGemma 300M (very fast)"
    },
    "qwen-8b": {
        "repo": "Qwen/Qwen3-Embedding-8B-GGUF",
        "filename": "Qwen3-Embedding-8B-Q4_K_M.gguf",
        "description": "Qwen3 Embedding 8B (highest quality, slower)"
    },
}

MODELS_DIR = Path(__file__).parent / "models"


def ensure_dependencies():
    """Install required packages if missing."""
    required = ["llama_cpp", "huggingface_hub", "flask"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg.replace("_", "-"))
    
    if missing:
        import subprocess
        print(f"Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)


def download_model(model_name):
    """Download model from HuggingFace if not present."""
    from huggingface_hub import hf_hub_download
    
    if model_name not in MODELS:
        print(f"Unknown model: {model_name}")
        print(f"Available: {list(MODELS.keys())}")
        sys.exit(1)
    
    model_info = MODELS[model_name]
    model_path = MODELS_DIR / model_info["filename"]
    
    if model_path.exists():
        print(f"✓ Model already downloaded: {model_path}")
        return str(model_path)
    
    print(f"Downloading {model_name}...")
    print(f"  Repo: {model_info['repo']}")
    print(f"  File: {model_info['filename']}")
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    downloaded_path = hf_hub_download(
        repo_id=model_info["repo"],
        filename=model_info["filename"],
        local_dir=MODELS_DIR,
        local_dir_use_symlinks=False
    )
    
    print(f"✓ Downloaded to: {downloaded_path}")
    return downloaded_path


def start_server(model_path, host="0.0.0.0", port=1234):
    """Start OpenAI-compatible embedding server."""
    from flask import Flask, request, jsonify
    from llama_cpp import Llama
    
    print(f"Loading model: {model_path}")
    llm = Llama(
        model_path=model_path,
        embedding=True,
        n_ctx=512,  # Context for embeddings
        n_batch=512,
        verbose=False
    )
    print("✓ Model loaded")
    
    app = Flask(__name__)
    
    @app.route("/v1/embeddings", methods=["POST"])
    def embeddings():
        data = request.json
        input_text = data.get("input", [])
        
        if isinstance(input_text, str):
            input_text = [input_text]
        
        results = []
        for i, text in enumerate(input_text):
            try:
                embedding = llm.embed(text)
                results.append({
                    "object": "embedding",
                    "index": i,
                    "embedding": embedding
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        return jsonify({
            "object": "list",
            "data": results,
            "model": Path(model_path).stem,
            "usage": {"prompt_tokens": 0, "total_tokens": 0}
        })
    
    @app.route("/v1/models", methods=["GET"])
    def list_models():
        return jsonify({
            "object": "list",
            "data": [{"id": k, "object": "model"} for k in MODELS.keys()]
        })
    
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "model": Path(model_path).stem})
    
    print()
    print("=" * 50)
    print(f"Embedding server running at http://{host}:{port}")
    print("=" * 50)
    print()
    print("Configure your embeddings.py with:")
    print(f'  base_url="http://localhost:{port}/v1"')
    print()
    
    app.run(host=host, port=port, debug=False, threaded=True)


def main():
    parser = argparse.ArgumentParser(description="Embedding server using llama-cpp-python")
    parser.add_argument(
        "model",
        nargs="?",
        default="qwen-0.6b",
        choices=list(MODELS.keys()),
        help="Model to use (default: qwen-0.6b)"
    )
    parser.add_argument("--port", type=int, default=1234, help="Port (default: 1234)")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--list", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available models:")
        for name, info in MODELS.items():
            print(f"  {name}: {info['description']}")
        return
    
    print("=" * 50)
    print("llama-cpp-python Embedding Server")
    print("=" * 50)
    print()
    
    ensure_dependencies()
    model_path = download_model(args.model)
    start_server(model_path, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
