import os
import requests

def download_image(url, save_path, timeout=10):
    """
    Downloads an image from a URL and saves it to save_path.
    Returns True if successful, False otherwise.
    """
    if not url:
        return False

    if os.path.exists(save_path):
        # Already exists, no need to download
        return True

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(response.content)

        return True

    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False


def get_book_cover(book, output_dir="covers"):
    """
    Returns the local path of the book cover.
    Downloads it on-demand if it doesn't exist yet.
    """
    url = book.get("coverImg")
    book_id = book.get("bookId")

    if not url or not book_id:
        return None

    filename = f"{book_id}.jpg"
    save_path = os.path.join(output_dir, filename)

    # Download if necessary
    download_image(url, save_path)

    if os.path.exists(save_path):
        return save_path
    else:
        return None
