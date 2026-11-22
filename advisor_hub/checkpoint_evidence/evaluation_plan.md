# Independent evaluation plan

The Advisor Hub currently has a preserved deterministic keyword baseline, reusable
metric code, and synthetic regression evidence. No independent labeled evaluation
has been completed. No trained classifier or comparison result exists yet.

## Measures and target definitions

**Category Macro-F1 target: at least 0.80.** For each of the six category labels,
TP means predicted and labeled as that category, FP means predicted as it but
labeled otherwise, and FN means labeled as it but predicted otherwise.

- Precision = TP / (TP + FP).
- Recall = TP / (TP + FN).
- F1 = 2 TP / (2 TP + FP + FN).
- Macro-F1 = the unweighted mean of all six category F1 scores.

Macro averaging gives small categories the same weight as large categories.
`classification_metrics` includes all declared categories. Zero denominators
produce zero, and absent classes are reported with support zero. A test split
missing a category cannot establish coverage; report that limitation explicitly.
The function also returns per-class support and a confusion matrix whose rows
are true labels and columns are predictions.

**Urgent-request recall target: at least 95%.** Define the positive class as an
independently assigned High urgency label. Recall is the number of those requests
predicted High divided by the number labeled High: TP / (TP + FN). Predicting
Medium on a labeled High request is a miss. Category routing can be wrong even
when urgency is correct, so measure these separately. `urgent_recall` returns
`None` when there are no labeled High requests; it does not report a perfect score.
Also inspect High precision, false alarms, and urgent sample counts so recall
alone does not reward marking everything High. Urgency evaluation across all
three levels is available in the same report.

**Comparison:** Freeze the baseline and compare it with a future trained
classifier on exactly the same untouched independent test rows, category set,
urgency definition, and zero-division policy. Record model/code version, training
and validation provenance, dataset hash, per-class results, error counts, and
runtime. Use `evaluate_requests(rows, predictor=adapter)`; the adapter returns the
same category/urgency fields through the TriageResult contract. The future model
has not been implemented, trained, or benchmarked here.

## Labels and study design

Each evaluation row needs a stable unique `id`, English `text`, one independently
assigned `expected_category` from the six supported labels, and one independently
assigned `expected_urgency` from High/Medium/Low. Keep labeling rationale, source,
author/group, collection date, reference time for deadlines, and split metadata
in a separate study record. Do not derive truth labels from classifier output or
matched keywords. This repository includes only fictional requests.

Define and agree the rubric before collection: multiple intents/unresolved
ambiguity should be explicitly labeled Other/Needs Review if no single route is
appropriate; unsupported questions also need review. High should reflect a real
near/missed deadline or serious need for immediate advising attention under the
agreed rubric, even when the wording omits the keyword "urgent". Low means a
human-labeled nonurgent request during evaluation; it is stronger than the
baseline's "no rule matched" meaning. Two independent labelers should label
without seeing predictions, then adjudicate disagreements and retain the rationale.

Collect a genuinely independent set of requests written without seeing the rule
list or the 18 fixtures. Include varied wording, unclear/multiple intents, false
urgency cues, unsupported intents, spelling variations, and deadlines with reference
times. Separate representative sampling from any deliberately enriched urgent
stress set and report each clearly. Do not claim either exists yet.

Before tuning, group duplicates, paraphrases, templates, and requests from the
same author/source together. Assign groups reproducibly to, for example, 60%
training, 20% validation, and 20% held-out testing, stratifying category and urgency
where feasible. Record a seed and immutable split IDs. A small dataset may need a
different design; ensure every category and enough independently labeled High
requests are represented. Use training for model learning, validation for keyword
changes/model selection, and test only for final comparison. Once test examples
influence rules or model choice, they must no longer serve as untouched test data.

Report sample sizes and uncertainty intervals before assessing the targets. Four
correct urgent examples are too few to support a 95% recall claim for new data.
Choose the study size in advance based on coverage and uncertainty needs; a point
estimate alone is insufficient evidence of reliable generalization.

## Reusable computation

From the repository root, after preparing a properly labeled JSON dataset with
a top-level `requests` array (same row fields as the existing fixtures):

```python
import json
from pathlib import Path
from advisor_hub.evaluation import evaluate_requests

rows = json.loads(Path("path/to/independent_test.json").read_text(encoding="utf-8"))["requests"]
report = evaluate_requests(rows)
print(json.dumps(report, indent=2))
```

The example path is a placeholder for a future dataset, not a supplied evaluation
file. The utilities validate labels, nonempty/equal-sized data, and unique IDs.
They cannot establish that a dataset is independent; provenance and split audits
are the evaluator's responsibility. Formula tests use hand-calculable confusion
matrices, class imbalance, absent classes, and urgent false negatives.

## Current synthetic evidence and errors

`fixture_report.json` is **fixture agreement only**, based on the existing 18
examples used during baseline development: 18/18 category and 18/18 urgency
matches, category fixture Macro-F1 1.0, and 4/4 fixture High requests detected.
These are small, hand-authored, keyword-aligned regression cases. They have no
independent holdout, realistic prevalence, broad linguistic variation, or reliable
estimate of unseen behavior. They do not establish either performance target.

`error_analysis.json` and `executed_cases.md` record real executions. Observed
limitations include a resolved hold still being Registration Holds/Medium,
complex urgency negation still producing High, an absolute graduation due date
producing Low, and "won't let me enroll" falling through to review/Low. The
required appointment-plus-graduation example goes to review because both routes
match. Registration deadline wording without a hold/category rule goes to
review even when urgency is correctly High. These outputs are preserved rather
than changing the baseline to hide errors.
