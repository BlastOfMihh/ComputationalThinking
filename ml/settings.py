import json
from pathlib import Path
from typing import Optional


class Settings:
    _instance: Optional["Settings"] = None
    _settings_path = Path(__file__).parent / "settings.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        with open(self._settings_path) as f:
            self._data = json.load(f)
        
        self.ml_dir = Path(__file__).parent
        self.books_path = self.ml_dir / self._data.get("books_path", "../books.csv")
        
        self.cache_dir_name = self._data.get("cache_dir", "cache")
        self.embeddings_cache_file = self._data.get("embeddings_cache_file", "embeddings_cache.pkl")
        self.faiss_index_dir = self._data.get("faiss_index_dir", "faiss_index")
        
        self.batch_size = self._data.get("batch_size", 512)
        self.batch_delay_seconds = self._data.get("batch_delay_seconds", 1)
        self.lower_embeddings = self._data.get("lower_embeddings", True)
        self.text_column = self._data.get("text_column", "description")
        
        self.provider = self._data.get("provider", "lmstudio")
        self.local_model = self._data.get("local_model", "minilm")
        self.ml_enabled = self._data.get("ml_enabled", True)
    
    @property
    def cache_dir(self) -> Path:
        return self.ml_dir / self.cache_dir_name
    
    @property
    def embeddings_cache_path(self) -> Path:
        return self.cache_dir / self.embeddings_cache_file
    
    @property
    def faiss_index_path(self) -> Path:
        return self.cache_dir / self.faiss_index_dir
    
    def reload(self):
        self._load()
    
    def save(self):
        self._data["cache_dir"] = self.cache_dir_name
        self._data["provider"] = self.provider
        self._data["local_model"] = self.local_model
        self._data["ml_enabled"] = self.ml_enabled
        
        with open(self._settings_path, "w") as f:
            json.dump(self._data, f, indent=4)
        
        self._load()
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                if key == "cache_dir_name":
                    self._data["cache_dir"] = value
                elif key in self._data:
                    self._data[key] = value
        self.save()
    
    def get_cache_options(self) -> list[str]:
        return sorted([
            d.name for d in self.ml_dir.iterdir() 
            if d.is_dir() and d.name.startswith("cache")
        ])
