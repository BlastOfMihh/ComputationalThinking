import csv
import re
import unicodedata

# ---------- Helper parsers ----------

def parse_int(value):
    if not value:
        return None
    match = re.search(r"\d+", value)
    return int(match.group()) if match else None


def parse_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_price(value):
    if not value:
        return None

    cleaned = re.sub(r"[^\d.]", "", value)

    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_author(raw_author):
    if not raw_author:
        return None
    authors = raw_author.split(",")
    main_author = re.sub(r"\(.*?\)", "", authors[0]).strip()
    return main_author


def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()


def normalize_title_for_sort(title):
    if not title:
        return ""
    new_title = unicodedata.normalize("NFKD", title)
    new_title = "".join(c for c in new_title if not unicodedata.combining(c))
    new_title = re.sub(r"[^a-zA-Z0-9\s]", "", new_title)
    return new_title.lower().strip()

# ---------- Main reader ----------

def read_books(csv_path="books.csv"):
    """
    Reads the books CSV and returns a list of dictionaries
    containing ALL attributes with safe type conversion.
    """

    books = []

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            main_author = clean_author(row.get("author"))
            book = {
                "bookId": row.get("bookId"),
                "title": row.get("title"),
                "series": row.get("series"),
                "author": main_author,
                "author_normalized": normalize_text(main_author),
                "rating": parse_float(row.get("rating")),
                "description": row.get("description"),
                "language": row.get("language"),
                "isbn": row.get("isbn"),
                "genres": row.get("genres"),
                "characters": row.get("characters"),
                "bookFormat": row.get("bookFormat"),
                "edition": row.get("edition"),
                "pages": parse_int(row.get("pages")),
                "publisher": row.get("publisher"),
                "publishDate": row.get("publishDate"),
                "firstPublishDate": row.get("firstPublishDate"),
                "awards": row.get("awards"),
                "numRatings": parse_int(row.get("numRatings")),
                "ratingsByStars": row.get("ratingsByStars"),
                "likedPercent": parse_float(row.get("likedPercent")),
                "setting": row.get("setting"),
                "coverImg": row.get("coverImg"),
                "bbeScore": parse_float(row.get("bbeScore")),
                "bbeVotes": parse_int(row.get("bbeVotes")),
                "price": parse_price(row.get("price")),
            }

            books.append(book)

    return books