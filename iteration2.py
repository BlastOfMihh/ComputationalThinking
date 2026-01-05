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
        stars += "✰"
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

st.set_page_config(page_title="Library Helper", layout="wide")

st.title("📚 Library Helper")
st.caption("A mini app for managing a simple library")

option = st.radio(
    "Choose an option:",
    ("Search by title", "Filter by author", "Sort alphabetically"),
    horizontal=True
)

# ---------- OPTION 1: Search ----------
if option == "Search by title":
    title = st.text_input("Enter the book title")
    if st.button("Search"):
        result = next(
            (b for b in books if b["title"] and b["title"].lower() == title.lower()),
            None
        )

        if result:
            st.success("Book found")
            display_book(result)
        else:
            st.error("Book not found ❌")

# ---------- OPTION 2: Filter by author ----------
elif option == "Filter by author":     
    author = st.text_input("Enter author name")
    if st.button("Filter"):
        if not author.strip(): 
            st.error("Please enter an author name") 
        else: 
            found_books = filter_by_author(author, books)
            if found_books:
                st.success(f"Found {len(found_books)} books")
                for book in sort_by_title(found_books):
                    display_book(book)
            else:
                st.warning("No books found")


# ---------- OPTION 3: Sort ----------
elif option == "Sort alphabetically":
    col_per_page, col_letter, col_page= st.columns([1, 2, 1])

    with col_per_page:
        BOOKS_PER_PAGE = st.selectbox("Books per page", [5, 10, 20], index=1)

    sorted_books = sort_by_title(books)

    # ---------- Session state ----------
    if "page" not in st.session_state:
        st.session_state.page = 0

    if "letter" not in st.session_state:
        st.session_state.letter = "All"

    # ---------- A–Z Quick Jump ----------
    letters = ["All"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    with col_letter:
        selected_letter = st.selectbox(
            "Jump to letter:",
            letters,
            index=letters.index(st.session_state.letter)
        )

    # Reset page if letter changes
    if selected_letter != st.session_state.letter:
        st.session_state.letter = selected_letter
        st.session_state.page = 0

    # Filter by starting letter
    if selected_letter != "All":
        filtered_books = [
            b for b in sorted_books
            if normalize_title_for_sort(b["title"]).startswith(selected_letter.lower())
        ]
    else:
        filtered_books = sorted_books

    # ---------- Pagination ----------
    total_pages = max(1, (len(filtered_books) - 1) // BOOKS_PER_PAGE + 1)

    with col_page:
        st.number_input(
            "Go to page:",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.page + 1,
            step=1,
            key="page_input"
        )

    st.session_state.page = st.session_state.page_input - 1

    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("⬅ Previous"): 
            if st.session_state.page > 0: 
                st.session_state.page -= 1 
            else: 
                st.session_state.page = total_pages - 1

    with col_next:
        if st.button("Next ➡") and st.session_state.page < total_pages - 1:
            st.session_state.page += 1

    with col_info:
        st.markdown(f"**Page {st.session_state.page + 1} of {total_pages}**")

    # ---------- Display ----------
    start = st.session_state.page * BOOKS_PER_PAGE
    end = start + BOOKS_PER_PAGE

    st.markdown("---")

    for book in filtered_books[start:end]:
        display_book(book)


