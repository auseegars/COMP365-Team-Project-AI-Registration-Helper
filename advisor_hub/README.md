# Advisor Hub

COMP365 AI Registration Helper component owned by the Advisor Hub and Interface
Developer. All component code, dependencies, sample data, and tests live here,
separate from teammates' work.

## Completed scope: Stages 1 and 2

Stage 1 established the package, dependencies, sample data and test directories,
classifier stub, and Streamlit placeholder in its own commit. Stage 2 adds a
working keyword-based classifier, urgency rules, and synthetic test fixtures.
This is a deterministic rules baseline, **not a trained ML model**. The interface
still displays only a project placeholder; the full dashboard is deferred.

## Local setup

Use Python 3.10 or later. From the repository root on Windows:

```powershell
py -3.12 -m venv advisor_hub/.venv
advisor_hub/.venv/Scripts/python.exe -m pip install -r advisor_hub/requirements.txt
advisor_hub/.venv/Scripts/python.exe -m unittest discover -s advisor_hub/tests -v
advisor_hub/.venv/Scripts/python.exe -m streamlit run advisor_hub/app.py
```

The classifier and all automated tests use only the Python standard library.
You can run tests without installing Streamlit:

```powershell
py -3.12 -m unittest discover -s advisor_hub/tests -v
```

Streamlit is imported only when the interface runs.

## Classifying a request

From the repository root:

```python
from dataclasses import asdict
from advisor_hub.classifier import classify_request

result = classify_request("I have a registration hold and registration closes tomorrow.")
print(asdict(result))
# category: Registration Holds
# urgency: High
# matched_keywords: ('hold',)
# urgency_reasons: ('closes tomorrow',)
```

`TriageResult` contains `category`, `urgency`, `matched_categories`,
`matched_keywords`, and `urgency_reasons`, plus a `needs_review` property.
Matched phrases explain the result; they are not probability or confidence scores.

## Category rules

| Category | Example matching words or phrases |
| --- | --- |
| Registration Holds | hold, holds, cannot register, can't register |
| Degree Planning | degree audit, degree requirements, four-year plan |
| Course Selection | which courses, choose classes, electives, prerequisites |
| Graduation | graduation, graduating, commencement, diploma |
| Appointments | appointment, advising meeting, meet with my advisor |
| Other/Needs Review | No matching category, blank input, or multiple matching categories |

Matching normalizes capitalization, Unicode compatibility characters, punctuation,
hyphens, apostrophes, and whitespace, then checks complete words or phrases.
Repeated keywords do not change the category. Multiple matching categories are
returned in `matched_categories` and routed to human review without a tie-breaker.
Non-string input raises `TypeError`. Requests are not saved by this module.

## Urgency rules

Rules are evaluated independently of category, in this order:

1. **High:** Explicit cues such as urgent, ASAP, immediately, or emergency;
   a deadline/due/closing phrase linked to today, tonight, or tomorrow;
   within/in/next 24 or 48 hours; missed deadlines, past due, or overdue.
2. **Medium:** A hold or registration block, a general deadline mention, soon,
   this week, or next week, when no High rule matches.
3. **Low:** No urgency cue. This means no rule matched, not verified low risk.

Simple negations such as "not urgent" and "not an emergency" suppress those
explicit cues. They do not suppress a separate deadline or another urgency cue.
An incidental time mention, such as "my appointment is tomorrow", is Low.

## Validation and limitations

The suite has 17 test methods, including 18 hand-labeled synthetic requests and
additional cases for category ambiguity, urgency precedence, negation, empty and
invalid inputs, word boundaries, normalization, and deterministic results.
The synthetic examples contain no real student records and are not training data.
Passing these fixtures does not establish accuracy on real advising requests.

The English rules do not understand general intent, complex negation, resolved
issues, sarcasm, arbitrary calendar dates, or relative deadlines outside the
listed patterns. Broad cues such as "hold" or "graduate" can misroute requests
in other contexts; synonyms absent from the rules can fall through to review.
Advisors should verify suggested categories and urgency before acting.

## Structure

```text
advisor_hub/
  .gitignore
  __init__.py
  app.py                  # Minimal Streamlit entry point
  classifier.py           # Keyword classification and urgency rules
  requirements.txt
  README.md
  sample_data/
    README.md
    synthetic_requests.json
  tests/
    __init__.py
    test_setup.py         # Import smoke tests
    test_classifier.py    # Behavioral tests and synthetic fixtures
```
