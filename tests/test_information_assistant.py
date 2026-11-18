# Owner: Kamryn Schmidt


import pytest

from src.information_assistant.chunk import chunk_text


def test_short_document():
    text = "Students should meet with their advisor."
    chunks = chunk_text(text, size=10, overlap=2)

    assert chunks == [text]


def test_chunk_overlap():
    text = " ".join(f"word{i}" for i in range(20))
    chunks = chunk_text(text, size=10, overlap=2)

    assert len(chunks) > 1
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]


def test_invalid_size():
    with pytest.raises(ValueError):
        chunk_text("Example", size=0)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("Example", size=10, overlap=10)
