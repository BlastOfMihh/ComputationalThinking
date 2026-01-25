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

def extract_year_safe(date_str):
    import re
    if not isinstance(date_str, str):
        return None
    match = re.search(r"(\d{4})", date_str)
    if match:
        year = int(match.group(1))
        if 1900 <= year <= 2024:
            return year
    return None


def get_clean_books_by_year_range(books_list, start=1900, end=2024):
    import pandas as pd
    df = pd.DataFrame(books_list)
    df["year"] = df["publishDate"].apply(extract_year_safe)
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df[(df["year"] >= start) & (df["year"] <= end)]
    return df


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
    ("Search by title", "Filter by author", "Sort alphabetically", "Top authors", "Top publishers", "Books per year"),
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

# ---------- OPTION 4: Top authors in recent years ----------

elif option == "Top authors":
    st.subheader("📚 Top Authors from the Last 10 Years (2010–2020)")

    min_books = st.slider("Minimum number of books by author", min_value=1, max_value=100, value=2)
    top_n = st.slider("How many top authors to show?", min_value=5, max_value=20, value=10)

    filtered_recent = [b for b in books if b.get("publishDate")]
    import datetime
    from books_reader import parse_float, parse_int

    def extract_year(date_str):
        import re
        if not date_str:
            return None
        match = re.search(r"(\d{4})", date_str)
        if match:
            year = int(match.group(1))
            return year if 1000 <= year <= 2020 else None
        return None

    recent_books = []
    for b in filtered_recent:
        year = extract_year(b["publishDate"])
        if year and 2010 <= year <= 2020:
            recent_books.append({
                "author": b["author"],
                "title": b["title"],
                "rating": parse_float(b.get("rating"))
            })

    import pandas as pd
    df = pd.DataFrame(recent_books)

    if df.empty:
        st.warning("No books found in this time range.")
        st.stop()

    stats = (
        df.groupby("author")
        .agg(num_books=("title", "count"), avg_rating=("rating", "mean"))
        .reset_index()
    )

    stats = stats[stats["num_books"] >= min_books]
    stats = stats.sort_values(by="num_books", ascending=False).head(top_n)

    if stats.empty:
        st.warning("No authors match the selected filters.")
        st.stop()

    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax2 = ax1.twinx()
    stats.plot(kind="bar", x="author", y="num_books", ax=ax1, color="skyblue", legend=False)
    stats.plot(kind="line", x="author", y="avg_rating", ax=ax2, color="red", marker='o', legend=False)

    ax1.set_ylabel("Number of Books")
    ax2.set_ylabel("Average Rating")
    ax1.set_title("Top Authors by Books and Rating (2010–2020)")
    ax1.set_xticklabels(stats["author"], rotation=45, ha="right")

    st.pyplot(fig)

# ---------- OPTION 5: Top publishers ----------
elif option == "Top publishers":
    st.subheader("🏢 Top Publishers by Number of Books")

    import pandas as pd
    import matplotlib.pyplot as plt

    # Convert list of books to DataFrame
    df = pd.DataFrame(books)

    # Remove missing/empty publishers
    df = df[df["publisher"].notna() & (df["publisher"].str.strip() != "")]

    if df.empty:
        st.warning("No publisher data available.")
        st.stop()

    # Group by publisher and count
    top_publishers = df["publisher"].value_counts().head(10)
    top_publisher_name = top_publishers.index[0]
    top_publisher_count = top_publishers.iloc[0]

    st.markdown(f"**Most published publisher:** `{top_publisher_name}` — **{top_publisher_count} books**")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    top_publishers.plot(kind="bar", color="skyblue", ax=ax)
    ax.set_title("Top 10 Publishers by Number of Books")
    ax.set_ylabel("Number of Books")
    ax.set_xlabel("Publisher")
    ax.set_xticklabels(top_publishers.index, rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

# ---------- OPTION 6: Books per year ----------
elif option == "Books per year":
    st.subheader("📅 Books Published per Year")

    import pandas as pd
    import matplotlib.pyplot as plt

    # Convert books to DataFrame
    df = pd.DataFrame(books)

    # Extract SAFE publication year (only 1900–2024)
    df["year"] = df["publishDate"].apply(extract_year_safe)

    # Remove invalid years
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    if df.empty:
        st.warning("No valid publication year data available.")
        st.stop()

    # Count books per year
    books_per_year = df["year"].value_counts().sort_index()

    # Force full range from 1900 to 2024, even for missing years
    import pandas as pd
    books_per_year = books_per_year.reindex(range(1900, 2025), fill_value=0)

    # Find extreme years
    most_books_year = books_per_year.idxmax()
    fewest_books_year = books_per_year.idxmin()

    st.markdown(
        f"**Year with most books published:** {most_books_year} "
        f"({books_per_year[most_books_year]} books)"
    )

    st.markdown(
        f"**Year with fewest books published:** {fewest_books_year} "
        f"({books_per_year[fewest_books_year]} books)"
    )

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))
    books_per_year.plot(kind="bar", ax=ax)

    ax.set_title("Number of Books Published per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Books")
    ax.set_xticklabels(books_per_year.index, rotation=45, ha="right")

    st.pyplot(fig)



    
        