# README updates for the Elective Recommender (owner: Ryan Kevena)

Ready-to-paste snippets so the main `README.md` reflects the elective recommender. I did **not** edit
`README.md` directly to avoid conflicting with teammates' sections — paste these in when the team merges.

## 1. In "Current status": move the elective recommender from **Planned** to **Working**
```
- **Elective recommender** (Ryan Kevena): hybrid recommender that suggests electives matching a
  student's interests and still counting toward the degree. Eligibility comes from the degree audit
  (`elective_options`); ranking combines interest similarity (sentence-transformer embeddings with a
  bag-of-words fallback) with peer ratings from a student survey. Includes a CLI, an Aim-2 evaluation
  (precision@5 vs most-popular baseline), and unit tests. Survey data is synthetic for now.
  See `docs/ELECTIVE_RECOMMENDER.md`.
```
And remove "elective recommender" from the **Planned** line.

## 2. In "Repository contents": add these rows
```
| `src/electives/`          | Elective recommender (hybrid: interest + peer ratings, eligibility-filtered) and its evaluation |
| `data/electives/`         | Student interest/rating survey instrument and SYNTHETIC responses |
```

## 3. In "Evaluation" (owner: Jarren): Aim 2 row can note the component is implemented
Aim 2 (elective recommender) now has a runnable evaluation in
`src/electives/evaluate_recommender.py` (precision@5 vs most-popular baseline; eligibility check).
