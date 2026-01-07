from embeddings import embeddings
from book_embeddings import get_vectorstore, get_embeddings_cache, initialize_book_embeddings
from book_embeddings import  get_embedding_by_book_id, search_similar_books, search_similar_books_by_vector
import json
import pandas as pd

from pathlib import Path

# Load settings
_SETTINGS_PATH = Path(__file__).parent / "settings.json"
with open(_SETTINGS_PATH) as f:
    _settings = json.load(f)

BOOKS_PATH = Path(__file__).parent / _settings["books_path"]

class RecommandationEngine:
    def __init__(self):
        self.embeddings = embeddings
        self.vectorstore = get_vectorstore(embeddings_model=self.embeddings)
        self.books_df=pd.read_csv(BOOKS_PATH)
        if self.vectorstore is not None:
            self.embeddings_cache = get_embeddings_cache()
        else:
            self.embeddings_cache, self.vectorstore = initialize_book_embeddings(
                books_df=self.books_df,
                embeddings_model=self.embeddings
            )

    def _get_book_embedding(self, book_id):
        return get_embedding_by_book_id(book_id, self.embeddings_cache)
    
    def get_book_recommandation_text_based(self, text, count):
        return search_similar_books(
            query=text, 
            k=count, 
            vectorstore=self.vectorstore
        )
    
    def _get_book_recommandation_embedding_based(self, embedding, count):
        return search_similar_books_by_vector(
            embedding=embedding,
            k=count,
            vectorstore=self.vectorstore
        )
    def get_book_recommandation_book_id_based(self, book_id, count):
        return self._get_book_recommandation_embedding_based(
            embedding=self._get_book_embedding(book_id),
            count=count
        )

    #def get_book_recommandations_embedding_based(self)

# engine = RecommandationEngine()
# print("Hell is over")
# print()

# # hunger_games="WINNING MEANS FAME AND FORTUNE.LOSING MEANS CERTAIN DEATH.THE HUNGER GAMES HAVE BEGUN. . . .In the ruins of a place once known as North America lies the nation of Panem, a shining Capitol surrounded by twelve outlying districts. The Capitol is harsh and cruel and keeps the districts in line by forcing them all to send one boy and once girl between the ages of twelve and eighteen to participate in the annual Hunger Games, a fight to the death on live TV.Sixteen-year-old Katniss Everdeen regards it as a death sentence when she steps forward to take her sister's place in the Games. But Katniss has been close to dead before—and survival, for her, is second nature. Without really meaning to, she becomes a contender. But if she is to win, she will have to start making choices that weight survival against humanity and life against love"
# hunger_games = "WINNING MEANS FAME AND FORTUNE"
# recomds = engine.get_book_recommandation_text_based(hunger_games, 10)
# recomds = engine._get_book_recommandation_embedding_based

# for recom in recomds:
#     print(recom)

# embeddings.embed_documents(
#     ["hunger games", "magic"]
# )

# Test with a single string first
# result = embeddings.embed_query("hunger games")
# print((result))  # Should print the vector dimension
