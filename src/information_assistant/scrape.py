# Owner: Kamryn Schmidt

import json
import re
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.ncat.edu/registrar/registration.php",
    "https://www.ncat.edu/registrar/student-info/q-a.php",
]

OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "data/information_assistant/pages.json"
)


def scrape_page(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    main = soup.find("main") or soup.find("article") or soup.body

    for element in main(["script", "style", "nav", "footer"]):
        element.decompose()

    text = re.sub(r"\s+", " ", main.get_text(" ", strip=True))

    return {
        "title": soup.title.get_text(" ", strip=True) if soup.title else url,
        "url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "text": text,
    }


def main():
    pages = []

    for url in URLS:
        try:
            print(f"Collecting: {url}")
            pages.append(scrape_page(url))
        except requests.RequestException as error:
            print(f"Could not collect {url}: {error}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(pages, indent=2),
        encoding="utf-8",
    )

    print(f"Successfully saved {len(pages)} pages")


if __name__ == "__main__":
    main()
