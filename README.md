# Computational Thinking Course

This is a mock library app project with thousands of books that allows sorting, filtering, searching, as well as computational methods, plots and statistics. It is separated into 4 iterations, each with its own functionality:

Iteration 1. Created a small project using streamlit, used mock library with 15 books

Iteration 2. Changed the dataset with a bigger and better one which is more suited for the following functionalities. Also improved the design, added images and alignment. The new dataset contains 52478 books, with 25 fields each, collected from Goodreads using a webscaper and both the source code for the webscraper and the data can be found [here](https://github.com/scostap/goodreads_bbe_dataset/tree/main).

Iteration 3. in ce an au aparut cele mai multe carti, cele mai putine, ce editura are cele mai multe carti publicate - plotturi, cel mai relevant autor in ultimii ani

Iteration 4. Data processing, predictions OR machine learning method OR regression and probability

### Tech requirements:

- make sure to install all dependencies with:

`python -m pip install [packages]`

- to run the app write this in terminal:

`python -m streamlit run yourscript.py`

---

## ML Features (Iteration 4)

AI-powered book recommendations using semantic search.

### Configuration

Edit `ml/settings.json`:

```json
{
    "ml_enabled": true,
    "provider": "local",
    "local_model": "minilm"
}
```

### Disable ML

Set `"ml_enabled": false` to hide all ML features.

### Providers

| Provider | Setup |
|----------|-------|
| `local` | No setup needed. Models: `minilm`, `gemma-300m`, `qwen-0.6b`, `qwen-8b` |
| `lmstudio` | Run [LM Studio](https://lmstudio.ai/) server on port 1234 |
| `gemini` | Add API key to `ml/api_key.txt` |

First run generates embeddings for all books (~5 min). Cached for subsequent runs.

---

notes for me :

is to lower case actually relevant?? in practice
