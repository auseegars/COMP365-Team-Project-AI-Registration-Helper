# Elective Recommender

**Owner:** Ryan Kevena
**Builds on:** `src/audit/degree_audit.py` (Ayana Seegars — approved elective lists and eligibility) and the student survey in `data/electives/`.

Suggests electives that fit a student's interests and still count toward their degree. It is a **hybrid**
recommender: it combines what a course is *about* (content) with how peers *rated* it (collaborative),
and it only ever recommends courses the student is actually allowed to take next.

## What it does

For a student profile and a set of interests, the recommender:

1. **Filters to eligible electives.** It calls the degree audit and uses `AuditResult.elective_options`
   — the courses that fill an *unmet* elective slot, have their prerequisites met, and are not already
   taken or in progress. Eligibility is decided entirely by Ayana's engine; this component does not
   re-implement any degree rules.
2. **Scores interest match.** Content similarity between the student's interests and each course's
   title/department. Uses sentence-transformer embeddings (`all-MiniLM-L6-v2`, the same model as the
   information assistant) when available, and falls back to a dependency-free bag-of-words cosine so it
   still runs offline and in tests.
3. **Adds peer ratings.** Average 1–5 rating from the student survey, restricted to respondents who
   share at least one of the student's interests (with the overall average as a fallback).
4. **Ranks by a hybrid score:** `0.6 * interest_similarity + 0.4 * peer_rating` (both scaled to 0–1),
   and explains each pick.

## Files

| Path | What it is |
|---|---|
| `src/electives/recommend.py` | Hybrid recommender + CLI. `recommend()` returns ranked eligible electives; `rank_pool()` is the shared scorer. |
| `src/electives/survey.py` | Interest taxonomy, survey loading, and peer-rating aggregation. |
| `src/electives/evaluate_recommender.py` | Aim 2 evaluation: precision@5 vs a most-popular baseline, plus an eligibility check. |
| `data/electives/survey_instrument.json` | The student interest + elective-rating survey. |
| `data/electives/survey_responses.json` | **Synthetic** responses for development (seeded; replace with real volunteer data before reporting). |
| `tests/test_elective_recommender.py` | Unit tests (eligibility filter, hybrid ranking, survey aggregation). |
| `requirements-electives.txt` | Optional extra dependencies (embeddings). Core code runs without them. |

## Running it

```bash
# From the repo root. Make or pick a profile with open elective slots, then:
python src/electives/recommend.py data/profiles/<profiles>.json <STUDENT_ID> --interests cybersecurity,ai_ml --top 5

# Evaluate against the synthetic survey:
python src/electives/evaluate_recommender.py

# Tests:
python -m pytest tests/test_elective_recommender.py -q
```

Interest tags: `ai_ml`, `cybersecurity`, `data_analytics`, `software_engineering`, `systems_programming`,
`networks`, `computer_graphics`, `game_design`, `theory_algorithms`, `hci_ar_vr`, `hardware_embedded`,
`simulation_modeling`, `bioinformatics_health`, `management_business` (see `survey_instrument.json`).

## How it connects to the rest of the hub

- **Input — eligibility (Ayana):** `degree_audit.audit().elective_options` and `.load_lists()`. If an
  approved list is incomplete, the audit flags it and those slots carry a warning.
- **Input — interests & ratings:** the student survey (`data/electives/`).
- **Output — Streamlit hub (Rhaiyn):** `recommend()` returns a list of
  `{code, title, score, interest_similarity, peer_rating, n_ratings, slots, why}`, ready to render on a
  student's page.
- **Output — evaluation (Jarren):** `evaluate_recommender.py` produces the precision@5 and eligibility
  numbers for Aim 2; it can feed `evaluate.py`.

## Evaluation (Aim 2)

`precision@5` of the hybrid recommender vs a most-popular baseline, leave-one-out over survey
respondents, with a respondent's 4–5 ratings treated as relevant. Target from the pitch: **beat the
baseline; 100% eligibility**. On the current synthetic survey the hybrid beats most-popular and every
recommendation is eligible. These numbers are **synthetic** and must be rerun on the team's 40 real
profiles and real survey responses before they are reported.

## Limitations and ethics

- Uses only public catalog data and **synthetic** survey responses; no real student records (FERPA).
- Peer ratings are only as good as the survey sample; sparse courses fall back to the overall average
  (or a neutral score) and are labeled as having few/no ratings.
- Interest tags are derived from course titles by keyword, so a course with a vague title may be
  under-tagged. Recommendations support a student's own judgment and their advisor; they do not replace
  either.
