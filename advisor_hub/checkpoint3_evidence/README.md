# Practical Checkpoint 3 evidence

Rhaiyn Newby · Advisor Hub and Interface Developer · November 22, 2026

Checkpoint 2 shipped the advising and appointment workflows, the rule-based triage baseline, temporary session storage, and 49 passing tests. Checkpoint 3 integrates the four teammate tools into the same blue-and-gold Streamlit Hub. The academic examples use fictional profiles, generated sections and synthetic ratings. The Information Assistant uses a saved NC A&T Registrar page.

| Evidence | Scope |
| --- | --- |
| [Test log](test_results.txt) | Full pytest run. 118 passed, 0 failed, 0 skipped, 0 blocked. Pytest separately reported 92 passing subtests. The local generation tests used mocked HTTP responses and retriever output. |
| [Executed examples](executed_examples.json) | Actual adapter and engine outputs for advising triage, retrieval, transfer audit, both schedulers, and elective recommendations. |
| [Retrieval comparison](retrieval_comparison.json) | All three methods, ranking and passage IDs via content hashes, question-level term coverage and dataset hashes. |
| [Semantic adapter probe](semantic_probe.json) | Actual MiniLM retrieval and the Ollama-unreachable fallback, with model and index metadata. |
| [Chrome smoke test](browser_smoke.json) | HTTP 200 health, actual source link, elective result, advisor queue, and zero uncaught browser errors. Screenshots show [Overview](overview.png), [Information Assistant](information.png), [Elective Recommendations](electives.png), and [Advisor Queue](advisor_queue.png). |
| [Team runner](team_evaluation.json) and [schedule rows](schedule_results.csv) | Jarren's runner output with the audit tests, metric self-test, and schedule comparison. |
| [Elective experiment](elective_evaluation.txt) | Ryan Kevena's leave-one-out on synthetic responses. The offline run scored 0.436 vs 0.329 precision@5 and 75/75 eligible outputs. |
| [Readiness](readiness.md), [video script](video_script.md), [recording checklist](recording_checklist.md), [defense](technical_defense.md) | Owners, rehearsal actions, and presentation preparation. |

## Actual checks and error analysis

- **Degree Audit.** The fictional CS transfer profile `SYN-CS-03` applied 26 of 120 credits. The UI displays mapped and unmatched transfer data, and flags missing prerequisites separately from stored-rule eligibility.
- **Schedule Builder.** Jarren's runner checked 15 synthetic profiles per solver. CP-SAT passed 15/15 and averaged 16.6 credits. Greedy passed 14/15 and averaged 15.9. For `SYN-CS-03`, greedy returned 15 credits but placed ECON 201 in a slot that the audit would not apply. The checker surfaced that failure. CP-SAT returned 17 checked credits. Every evaluated schedule included courses with incomplete prerequisite data.
- **Electives.** In the offline test configuration, `SYN-CS-02` with Cybersecurity ranked COMP 320 first. The app displays the open degree slots, interest similarity, synthetic peer score and rating count. Missing prerequisites and incomplete elective lists require review.
- **Advisor Hub.** The fictional input “I have a registration hold and registration closes tomorrow.” was categorized as Registration Holds, High urgency, and Open. Tests cover duplicate submissions, queue status changes, appointments and demo reset. Keyword rules can overtriage negation and struggle with mixed intent.
- **Information Assistant.** The recorded retrieval-only request used the repository snapshot and returned actual excerpts. Ollama was absent from PATH and the usual install path, and port 11434 did not respond. Live Llama generation is one blocked verification scenario outside the automated test counts. Mocked tests verified prompt context, source rendering, unavailable models, unreachable service, and session history.

## Retrieval benchmark

The same five questions searched 11 stored passages from one Registrar page, with a maximum of three results per question. All-term coverage counts questions for which the combined passages contain every expected term. Mean term coverage averages the fraction found per question. The matcher uses case-insensitive whole terms and does not stem words.

| Method | How it ranks | All-term hits at 3 | Mean coverage at 3 |
| --- | --- | --- | --- |
| Keyword overlap | Counts shared unique query words. Simple and easy to inspect. | 4/5 | 90% |
| BM25 | Weights term frequency, corpus rarity, and passage length. Useful lexical baseline for exact terms. | 4/5 | 90% |
| Semantic | Ranks normalized MiniLM vectors by cosine similarity. Can align paraphrases and requires a local model and index. | 4/5 | 90% |

The methods tied on both diagnostics and did not always rank the same passages first. All three missed the exact term `hold` on the registration-hold question. The corpus contains the plural `holds`, which this matcher treats as a different term. These fixtures contain expected terms only, so Recall@3, MRR, and answer accuracy remain unmeasured. Human passage-level judgments and broader questions are needed before selecting a winner.

## Reproduction

From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv-cp3
$python = ".\.venv-cp3\Scripts\python.exe"
& $python -m pip install -r advisor_hub/requirements.txt -r requirements.txt rank-bm25
& $python -m pytest -q -ra
& $python evaluation_checkpoint3.py
& $python src/electives/evaluate_recommender.py
& $python -m streamlit run advisor_hub/app.py --browser.gatherUsageStats false
```

For the semantic comparison:

```powershell
& $python -m pip install -r requirements-information-assistant.txt
& $python -m src.information_assistant.embeddings
& $python -m advisor_hub.retrieval_comparison --output advisor_hub/checkpoint3_evidence/retrieval_comparison.json
```

The embedding command downloads MiniLM if needed and writes the ignored `embeddings.npy`. For generation, an existing local Ollama installation must be running with `llama3.2:3b` available. The browser experience still supports retrieval without it. The comparison exits nonzero and records which method was blocked if an optional prerequisite is absent.

The full run used Python 3.12, Streamlit 1.67.0, pytest 9.2.0, OR-Tools 9.15.6755, and rank-bm25 0.2.2. The test log and lexical browser run used an environment without Sentence Transformers. A second full run in the model-enabled environment passed the same 118 tests and 92 subtests. Live generation was blocked in both environments. The semantic probe records the installed model revision and index hash.

## Ownership and repository history

Ayana Seegars owns curriculum and degree audit. Ryan Travers owns scheduling and its independent checker. Kamryn Schmidt owns the RAG and retrieval methods. Ryan Kevena owns elective ranking and synthetic survey fixtures. Jarren Woodward owns the evaluation runner. Rhaiyn Newby owns the Advisor Hub, the Streamlit adapters and page integration, the common retrieval diagnostic, and this evidence package. Caleb Milliken's graduation planner role was identified in team documentation. No implementation was verified in the integrated branch.

| Revision | Work |
| --- | --- |
| `6cfda49`, `799d9c2`, `684bae3`, `6049f97` | Advisor Hub foundations through Checkpoint 2 |
| `44f5e72` | Merge team main at `de5a163` with PRs #1–#4 |
| `0d2eadb` | Information Assistant adapter and UI |
| `23e58eb` | Degree Audit and Schedule Builder |
| `2c89085` | Elective Recommendations |
| `d649bd7` | Unified integration coverage and common retrieval diagnostic |

No instructor feedback was found in the workspace search. Checkpoint 2 evidence and team meeting notes were present.
