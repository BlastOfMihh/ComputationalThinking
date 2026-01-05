import os
import streamlit as st
from books_reader import read_books
from books_reader import normalize_text
from books_reader import normalize_title_for_sort
from image_downloader import get_book_cover

# ---------- Data ----------
books = read_books("books.csv")
COVERS_DIR = "covers"

# ---------- Helper UI functions ----------

def rating_to_stars(rating, max_stars=5):
    if rating is None:
        return "No rating"

    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    empty_stars = max_stars - full_stars - (1 if half_star else 0)

    stars = "⭐" * full_stars
    if half_star:
        stars += "⭐" 
    stars += "✰" * empty_stars

    return f"{rating:.1f}/5  {stars}"


def display_book(book):
    col1, col2 = st.columns([1, 3])

    cover_path = get_book_cover(book)

    with col1:
        if cover_path:
            st.image(cover_path, width=120)
        else:
            st.image("https://via.placeholder.com/120x180?text=No+Cover")

    with col2:
        st.markdown(f"### {book['title']}")
        st.markdown(f"**Author:** {book['author']}")
        st.markdown(f"**Rating:** {rating_to_stars(book['rating'])}")
        st.markdown(f"**Pages:** {book['pages'] or 'N/A'}")
        st.markdown(f"**Price:** {book['price'] if book['price'] else 'N/A'}")
        st.markdown("---")


def paginate_items(items, page_key, page_input_key, items_per_page):
    total_pages = max(1, (len(items) - 1) // items_per_page + 1)

    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    if page_input_key not in st.session_state:
        st.session_state[page_input_key] = 1

    def go_to_page():
        st.session_state[page_key] = st.session_state[page_input_key] - 1

    def prev_page():
        st.session_state[page_key] = (
            st.session_state[page_key] - 1
            if st.session_state[page_key] > 0
            else total_pages - 1
        )
        st.session_state[page_input_key] = st.session_state[page_key] + 1

    def next_page():
        st.session_state[page_key] = (
            st.session_state[page_key] + 1
            if st.session_state[page_key] < total_pages - 1
            else 0
        )
        st.session_state[page_input_key] = st.session_state[page_key] + 1

    st.number_input(
        "Go to page:",
        min_value=1,
        max_value=total_pages,
        step=1,
        key=page_input_key,
        on_change=go_to_page
    )

    col_prev, col_info, col_next = st.columns([1, 10, 1], vertical_alignment="bottom")

    with col_prev:
        st.button("⬅ Previous", on_click=prev_page, key=f"{page_key}_prev")

    with col_info:
        st.markdown(
            f"Page {st.session_state[page_key]+1} of {total_pages}",
            text_alignment="center"
        )

    with col_next:
        st.button("Next ➡", on_click=next_page, key=f"{page_key}_next")

    start = st.session_state[page_key] * items_per_page
    end = start + items_per_page

    st.markdown("---")

    return items[start:end]


# ---------- Helper Functions --------

def search_by_title(title, books_list):
    title_norm = normalize_text(title)
    results = [
        b for b in books_list
        if title_norm in normalize_text(b["title"])
    ]
    return results


def filter_by_author(author, books_list):
    author_norm = normalize_text(author)
    results = [
        b for b in books_list
        if author_norm in b.get("author_normalized", "")
    ]
    return results

def sort_by_title(books_list):
    sorted_list = sorted(
        books_list,
        key=lambda x: normalize_title_for_sort(x["title"])
    )
    return sorted_list

# ---------- App UI ----------

st.set_page_config(page_title="Bookscape", layout="wide")

st.title("📚 Bookscape")
st.caption("thousands of books at your fingertips, through this digital librarian")

option = st.radio(
    "Choose an option:",
    ("Search by title", "Filter by author", "Sort alphabetically"),
    horizontal=True
)

# ---------- OPTION 1: Search ----------
if option == "Search by title":

    col_query, col_case, col_per_page = st.columns([2, 1, 1], vertical_alignment="bottom")

    with col_query:
        query = st.text_input("Search title (min. 3 characters)")

    with col_case:
        case_sensitive = st.checkbox("Case sensitive")

    with col_per_page:
        BOOKS_PER_PAGE = st.selectbox("Books per page", [5, 10, 20], index=1)

    if "search_page" not in st.session_state:
        st.session_state.search_page = 0

    if "last_query" not in st.session_state:
        st.session_state.last_query = ""

    if query and len(query.strip()) < 3:
        st.warning("Please enter at least 3 characters")
        st.stop()

    if query != st.session_state.last_query:
        st.session_state.last_query = query
        st.session_state.search_page = 0

    if query:
        if case_sensitive:
            results = [
                b for b in books
                if b["title"] and query in b["title"]
            ]
        else:
            query_norm = query.lower()
            results = [
                b for b in books
                if b["title"] and query_norm in b["title"].lower()
            ]

        if not results:
            st.error("No books found ❌")
            st.stop()

        paginated_results = paginate_items(
            results,
            page_key="search_page",
            page_input_key="search_page_input",
            items_per_page=BOOKS_PER_PAGE
        )

        for book in paginated_results:
            display_book(book)


# ---------- OPTION 2: Filter by author ----------
elif option == "Filter by author":
    col_author, col_page, col_per_page= st.columns([2, 1, 1], vertical_alignment="bottom")

    with col_author:
        author = st.text_input("Enter author name")

    with col_per_page:
        BOOKS_PER_PAGE = st.selectbox("Books per page", [5, 10, 20], index=1)

    if "author_page" not in st.session_state:
        st.session_state.author_page = 0

    if "last_author" not in st.session_state:
        st.session_state.last_author = ""

    if author:
        if not author.strip():
            st.error("Please enter an author name")
            st.stop()

        if author != st.session_state.last_author:
            st.session_state.last_author = author
            st.session_state.author_page = 0

        found_books = filter_by_author(author, books)

        if not found_books:
            st.warning("No books found")
            st.stop()

        found_books = sort_by_title(found_books)

        paginated_books = paginate_items(
            found_books,
            page_key="author_page",
            page_input_key="author_page_input",
            items_per_page=BOOKS_PER_PAGE
        )

        for book in paginated_books:
            display_book(book)


# ---------- OPTION 3: Sort ----------
elif option == "Sort alphabetically":
    col_letter, col_page, col_per_page= st.columns([2, 1, 1], vertical_alignment="bottom")

    with col_per_page:
        BOOKS_PER_PAGE = st.selectbox("Books per page", [5, 10, 20], index=1)

    sorted_books = sort_by_title(books)

    if "page" not in st.session_state:
        st.session_state.page = 0

    if "letter" not in st.session_state:
        st.session_state.letter = "All"

    letters = ["All"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    with col_letter:
        selected_letter = st.selectbox(
            "Jump to letter:",
            letters,
            index=letters.index(st.session_state.letter)
        )

    if selected_letter != st.session_state.letter:
        st.session_state.letter = selected_letter
        st.session_state.page = 0

    if selected_letter != "All":
        filtered_books = [
            b for b in sorted_books
            if normalize_title_for_sort(b["title"]).startswith(selected_letter.lower())
        ]
    else:
        filtered_books = sorted_books

    paginated_books = paginate_items(
        filtered_books,
        page_key="page",
        page_input_key="page_input",
        items_per_page=BOOKS_PER_PAGE
    )

    for book in paginated_books:
        display_book(book)
        