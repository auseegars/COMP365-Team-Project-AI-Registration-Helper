# Owner: Kamryn Schmidt

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "information_assistant"
RAW = DATA / "raw"

SOURCES = {
    "registration.txt":
        "https://www.ncat.edu/registrar/registration.php",
}


def chunk_text(text, size=180, overlap=30):
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Invalid chunk size or overlap")

    words = text.split()
    chunks = []

    step = size - overlap

    for start in range(0, len(words), step):
        piece = words[start:start + size]

        if not piece:
            break

        chunks.append(" ".join(piece))

        if start + size >= len(words):
            break

    return chunks


def main():
    records = []

    for filename, url in SOURCES.items():
        path = RAW / filename

        if not path.exists():
            print(f"Skipping missing file: {filename}")
            continue

        text = path.read_text(encoding="utf-8")

        for number, chunk in enumerate(chunk_text(text)):
            records.append({
                "id": f"{path.stem}_{number}",
                "title": path.stem.replace("_", " ").title(),
                "source_url": url,
                "text": chunk,
            })

    output = DATA / "chunks.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Created {len(records)} chunks")
    print(f"Saved to {output}")


if __name__ == "__main__":
    main()
