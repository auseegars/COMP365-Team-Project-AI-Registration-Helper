"""Connect the Hub to the team's retriever and local generation API."""

import json
import logging
import re
from functools import lru_cache, partial
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parents[1] / "data" / "information_assistant"
MODEL = "llama3.2:3b"
LOGGER = logging.getLogger(__name__)


def tokens(text):
    return set(re.findall(r"\w+", text.casefold()))


def keyword_search(question, top_k=3):
    chunks = json.loads((DATA / "chunks.json").read_text(encoding="utf-8"))
    terms = tokens(question)
    ranked = [
        {**chunk, "score": len(terms & tokens(chunk["text"]))}
        for chunk in chunks
    ]
    ranked.sort(key=lambda chunk: chunk["score"], reverse=True)
    return [chunk for chunk in ranked[:top_k] if chunk["score"] > 0]


@lru_cache(maxsize=1)
def embedding_model():
    from sentence_transformers import SentenceTransformer

    from src.information_assistant.retrieve import MODEL_NAME

    return SentenceTransformer(MODEL_NAME, local_files_only=True)


def semantic_search(question, top_k=3):
    if not (DATA / "embeddings.npy").is_file():
        raise FileNotFoundError("The semantic index is missing.")
    from src.information_assistant.retrieve import search

    return search(question, top_k=top_k, model=embedding_model())


def ask(question):
    question = question.strip()
    if not 3 <= len(question) <= 500 or not any(c.isalnum() for c in question):
        raise ValueError("Enter a registration question of 3 to 500 characters.")

    method = "Semantic cosine similarity"
    try:
        excerpts = semantic_search(question)
    except (ImportError, OSError, RuntimeError, ValueError):
        reason = "Semantic search requires a usable local embedding model and index."
        LOGGER.info("Semantic retrieval unavailable", exc_info=True)
        excerpts = []
        try:
            from src.information_assistant.bm25_baseline import bm25_search

            excerpts = bm25_search(question)
            method = "BM25"
        except ImportError:
            pass
        if not excerpts:
            excerpts = keyword_search(question)
            method = "Keyword overlap"
    else:
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            response.raise_for_status()
            models = {model["name"] for model in response.json()["models"]}
            if MODEL not in models:
                reason = f"Ollama is running without {MODEL}."
            elif excerpts:
                from src.information_assistant.rag_assistant import answer_question

                # Use the same retrieved passages for the answer and displayed evidence.
                result = answer_question(question, retrieve=partial(_retrieved, excerpts))
                cited = set(re.findall(r"\[(\d+)\]", result["answer"]))
                allowed = {str(source["id"]) for source in result["sources"]}
                if cited and cited <= allowed:
                    return {**result, "excerpts": excerpts, "method": method, "reason": ""}
                reason = "The model did not return an answer with valid source references."
            else:
                reason = "Semantic retrieval returned no passages."
        except (requests.RequestException, ValueError, KeyError):
            reason = "The local Ollama service could not complete generation."
    return {"answer": None, "sources": [], "excerpts": excerpts, "method": method, "reason": reason}


def _retrieved(excerpts, question, top_k):
    return excerpts[:top_k]
