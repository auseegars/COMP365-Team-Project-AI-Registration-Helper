
# Aggies Enroll — AI Information Assistant

## Developer
Kamryn Schmidt

## Project Overview
The Information Assistant helps North Carolina A&T students find university registration information using Retrieval-Augmented Generation (RAG).

Students can ask registration-related questions and receive answers generated from retrieved university information with source references.

## My Responsibilities
- University information collection
- Document cleaning and chunking
- Semantic embedding generation
- RAG-based question answering
- Source citation handling
- BM25 keyword retrieval comparison
- Testing and evaluation

## Technologies Used
- Python
- BeautifulSoup
- Sentence Transformers
- NumPy
- Rank-BM25
- Ollama
- Llama 3.2 (3B)
- Pytest

## System Architecture
1. Collect official university registration information.
2. Split documents into searchable chunks.
3. Convert chunks into embeddings.
4. Retrieve relevant information using semantic search.
5. Generate answers using Llama 3.2 through Ollama.
6. Return answers with university source references.

## Installation

Install dependencies:

    python -m pip install -r requirements-information-assistant.txt

Install Ollama separately and download the model:

    ollama pull llama3.2:3b

## Running the Assistant

Generate document chunks:

    python src/information_assistant/chunk.py

Generate embeddings:

    python src/information_assistant/embeddings.py

Launch the assistant:

    python src/information_assistant/rag_assistant.py

## Evaluation Results

Initial five-question retrieval comparison:

- Semantic search term-match rate: 100% (5/5)
- BM25 term-match rate: 80% (4/5)

These are preliminary keyword-matching results, not verified answer accuracy.

## Automated Testing

Run:

    python -m pytest tests/test_information_assistant.py -v

Initial testing: 4 tests passed.

## Current Limitations
- Only one official university webpage has been collected.
- The university website blocked automated requests with HTTP 403 errors.
- Ollama must be installed and running locally.
- Additional evaluation is needed to establish answer and citation accuracy.
- Integration with the main Streamlit application is pending.

## Future Improvements
- Expand the university document collection.
- Improve citation validation.
- Evaluate using a larger question set.
- Integrate the assistant into the student dashboard.
