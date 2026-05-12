import requests
from bs4 import BeautifulSoup
import trafilatura
import os

SAVE_DIR = "data/raw/pages"

os.makedirs(SAVE_DIR, exist_ok=True)

with open("data/urls.txt", "r", encoding="utf-8") as f:
    urls = [u.strip() for u in f.readlines() if u.strip()]

headers = {
    "User-Agent": "Mozilla/5.0"
}

for i, url in enumerate(urls):

    try:

        print("Fetching:", url)

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        html = response.text

        text = trafilatura.extract(html)

        if not text:
            continue

        filename = (
            url.replace("https://", "")
            .replace("/", "_")
            .replace("?", "_")
        )

        path = os.path.join(
            SAVE_DIR,
            f"{filename}.txt"
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        print("Saved:", filename)

    except Exception as e:
        print("ERROR:", e)