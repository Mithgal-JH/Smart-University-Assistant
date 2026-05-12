import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import trafilatura
import os

START_URL = "https://polytechnic.edu.ps/p/ar"

visited = set()

SAVE_DIR = "data/raw"

os.makedirs(SAVE_DIR, exist_ok=True)


def is_valid(url):
    parsed = urlparse(url)

    return (
        parsed.netloc.endswith("ppu.edu")
        and "/ar" in url
    )


def crawl(url):

    if url in visited:
        return

    visited.add(url)

    print("Crawling:", url)

    try:
        response = requests.get(url, timeout=10)

        html = response.text

        # extract clean text
        text = trafilatura.extract(html)

        if text and len(text) > 200:

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

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):

            next_url = urljoin(url, a["href"])

            if is_valid(next_url):
                crawl(next_url)

    except Exception as e:
        print("ERROR:", e)


crawl(START_URL)

print(f"\n✅ Crawled {len(visited)} pages")