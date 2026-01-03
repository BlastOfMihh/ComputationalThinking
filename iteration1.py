import streamlit as st

def display_menu():
    st.subheader("Choose an option:")
    st.write("1. Search for a book by title")
    st.write("2. Filter books by author")
    st.write("3. Sort books alphabetically")


def search_book(title, books_list):
    for book in books_list:
        if book["title"].lower() == title.lower():
            return book
    return None

def filter_by_author(author, books_list):
    filtered = []
    for book in books_list:
        if author.lower() in book["author"].lower():
            filtered.append(book)
    return filtered


# BOOK LIST


books = [
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "Tender Is the Night", "author": "F. Scott Fitzgerald"},
    {"title": "This Side of Paradise", "author": "F. Scott Fitzgerald"},
    {"title": "Pride and Prejudice", "author": "Jane Austen"},
    {"title": "Emma", "author": "Jane Austen"},
    {"title": "Sense and Sensibility", "author": "Jane Austen"},
    {"title": "Mansfield Park", "author": "Jane Austen"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"title": "Go Set a Watchman", "author": "Harper Lee"},
    {"title": "1984", "author": "George Orwell"},
    {"title": "Animal Farm", "author": "George Orwell"},
    {"title": "Homage to Catalonia", "author": "George Orwell"},
    {"title": "Moby Dick", "author": "Herman Melville"},
    {"title": "Billy Budd", "author": "Herman Melville"},
    {"title": "Bartleby, the Scrivener", "author": "Herman Melville"},
]

st.title("Library Helper")
st.write("A mini app for managing a simple library ")

display_menu()

option = st.radio(
    "Select an operation:",
    (1, 2, 3),
    format_func=lambda x: {
        1: "Search a book by title",
        2: "Filter books by author",
        3: "Sort books alphabetically",
    }[x]
)

# OPTION 1 – Search book by title

if option == 1:
    title = st.text_input("Enter the book title:", key="title_input")
    if st.button("Search"):
        result = search_book(title, books)
        if result:
            st.success(f"Book found: {result['title']} – {result['author']}")
        else:
            st.error("Book not found ❌")

# OPTION 2 – Filter by author
elif option == 2:
    author = st.text_input("Enter author name:", key="author_input")
    if st.button("Filter"):
        if author.strip() == "":
            st.error("Please enter an author name first ❗")
        else:
            found = filter_by_author(author, books)
            # Sortează aici (dacă nu ai sortat în funcție)
            found = sorted(found, key=lambda x: x["title"].lower())
            if found:
                st.success(f"Books written by '{author}':")
                for b in found:
                    st.write(f"• {b['title']} – {b['author']}")
            else:
                st.warning("No books found for this author")

# OPTION 3 – Sort books

elif option == 3:
    if st.button("Sort"):
        st.info("Books sorted alphabetically:")
        sorted_books = sorted(books, key=lambda x: x["title"])
        for b in sorted_books:
            st.write(f"• {b['title']} – {b['author']}")
