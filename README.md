# Evaluation (owner: Jarren Woodward)

Scores each project component against the targets in the team pitch.

| Aim | Component | Metric | Target |
|---|---|---|---|
| 1 | Schedule builder / graduation planner | valid schedules; graduation term matches or beats advisor plan | 100%; >= 90% |
| 2 | Elective recommender | precision@5 vs most-popular baseline; eligibility | beats baseline; 100% |
| 3 | Cited Q&A assistant | answered correctly; cited correctly | >= 85%; >= 90% |
| 4 | Triage classifier | macro-F1; urgent recall | >= 0.80; >= 95% |

## Run it
```
python evaluate.py selftest              # checks the metric math on tiny made-up data
python evaluate.py triage  triage.csv
python evaluate.py qa      qa_results.csv
python evaluate.py recs    recs.json
python evaluate.py sched   schedules.csv
```
Input formats are documented in the comments above each function in `evaluate.py`.
Only the Python standard library is used.

## Test set
- `profiles_template.json` - format for the 40 hand-verified test student profiles (15 transfers)
- `questions_template.csv` - format for the 120 test questions (gold answer + official source URL)

Status: PARTIAL - see the checkpoint report for how many are done.

## Tools disclosure
`evaluate.py` was drafted with Claude (AI assistant) and tested/reviewed by Jarren Woodward.
