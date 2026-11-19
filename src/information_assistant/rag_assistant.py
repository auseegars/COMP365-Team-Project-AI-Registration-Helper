# Owner: Kamryn Schmidt

import requests

try:
    from .retrieve import search
except ImportError:
    from retrieve import search

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def answer_question(question):
    results = search(question, top_k=3)

    if not results:
        return {
            "answer": "I could not find relevant university information.",
            "sources": [],
        }

    context_parts = []
    sources = []

    for number, result in enumerate(results, start=1):
        context_parts.append(
            f"[{number}] {result['text']}\n"
            f"Source: {result['source_url']}"
        )

        sources.append({
            "id": number,
            "title": result["title"],
            "url": result["source_url"],
            "similarity": round(result["score"], 3),
        })

    context = "\n\n".join(context_parts)

    prompt = f"""
You are Aggies Enroll, an NC A&T registration assistant.

Answer the student's question using ONLY the provided
university information.

Rules:
- Give a clear, concise answer.
- Do not invent registration policies or requirements.
- Cite supporting passages using [1], [2], or [3].
- If the context does not contain the answer, say:
  "I could not verify that from the available university
  information. Please contact your academic advisor."

University information:
{context}

Student question:
{question}

Answer:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    response.raise_for_status()

    answer = response.json()["response"].strip()

    fallback = (
        "I could not verify that from the available "
        "university information. Please contact "
        "your academic advisor."
    )

    if fallback.lower() in answer.lower():
        return {
            "answer": fallback,
            "sources": [],
        }


    return {
        "answer": answer,
        "sources": sources,
    }


if __name__ == "__main__":
    question = input("Ask Aggies Enroll: ").strip()

    if question:
        try:
            response = answer_question(question)

            print("\nAnswer:")
            print(response["answer"])

            print("\nSources:")
            for source in response["sources"]:
                print(
                    f"[{source['id']}] "
                    f"{source['title']}: {source['url']}"
                )

        except requests.RequestException as error:
            print(f"Could not contact Ollama: {error}")
            print("Make sure Ollama is installed and running.")
