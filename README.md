# Bookscape

This is a library app project with thousands of books that allows sorting, filtering, searching, as well as computational methods, plots and statistics, recommandation engine and semantic search.

It is separated into 4 iterations, each with its own functionality:

### Iteration 1 : MVP

Developed small project using Streamlit, based on a mock library consisting of 15 books. We also implemented basic operations for managing the collection of entities, including searching, filtering and sorting.

### Iteration 2 : New Dataset and Cleaning

Changed the dataset with a bigger and better one which is more suited for the following functionalities. Also improved the design, added images and alignment. The new dataset contains 52478 books, with 25 fields each, collected from Goodreads using a webscaper and both the source code for the webscraper and the data can be found [here](https://github.com/scostap/goodreads_bbe_dataset/tree/main).

### Iteration 3 : Visual Insights

This iteration extends the core features by adding visual insights and filtering tools:

- _Top Authors (2010–2020)_ — bar + line chart with book count and average rating.
- _Top Publishers_ — shows top 10 publishers by number of books.
- _Books per Year_ — full range (1900–2024), with year filtering and highlight of most/least active years.
- Improved data cleaning for invalid years and missing publishers.

### Iteration 4 : AI-powered book recommendations and semantic search

#### Caching

Used cached embeddings and Vectorized DB in order to ensure scalability and performance.

When using for the first time the AI features there will be a cold start for the caching(the progress can be tracked in the terminal).

#### Configuration File

Edit `ml/settings.json`:

```json
{
  "ml_enabled": true,
  "provider": "local",
  "local_model": "minilm"
}
```

#### Multiple Providers(for your usecase)

| Provider   | Setup                                                                   |
| ---------- | ----------------------------------------------------------------------- |
| `local`    | No setup needed. Models: `minilm`, `gemma-300m`, `qwen-0.6b`, `qwen-8b` |
| `lmstudio` | Run [LM Studio](https://lmstudio.ai/) server on port 1234               |
| `gemini`   | Add API key to `ml/api_key.txt`                                         |

First run generates embeddings for all books (~5 min). Cached for subsequent runs.

## Tech requirements:

- create a virtual environment for python with:
  - open Git Bash and go to folder path

  ```bash
  cd /d/Documents/MASTER/DS/sem1/computationalThinking/ComputationalThinking/
  ```

  - create environment

  ```bash
  python -m venv .venv
  source .venv/Scripts/activate
  ```

- make sure to install all dependencies with:

`python -m pip install [packages]`

or

`pip install -r requirements.txt`

- to run the app write this in terminal:

`python -m streamlit run yourscript.py`
