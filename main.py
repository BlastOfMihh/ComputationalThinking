from books_reader import read_books
from image_downloader import download_book_covers

books = read_books("books.csv")

download_book_covers(books)

print(f"Total books: {len(books)}")
print(books[0])
