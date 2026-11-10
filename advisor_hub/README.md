# Aggies Enroll — Advisor Hub

COMP365 student project prototype, not an official NC A&T service. The Advisor Hub
and Interface Developer owns student request classification, urgency triage,
request management, appointment requests, and the Streamlit interface. All work
is isolated in `advisor_hub/`; teammates' components are not implemented here.

## Implemented through Stage 3

- Overview with actual session counts, recent requests, category and priority charts.
- Student Requests: required fictional identifier and description; existing classifier
  output, matched rules, review flag, unique UUID, UTC timestamp, and Open status.
- Advisor Queue: category/urgency/status filters, text/identifier/ID search, priority
  then oldest sorting, chronological sorting, full details, and status updates.
- Requests support Open, In Progress, Resolved, including reopening. No implicit deletion.
- Appointments: validated fictional identifier/reason and future date/time in UTC,
  separate UUID records, Pending list, Reviewed/Cancelled statuses, and reopening.
  These are requests for review; nothing books or confirms an advisor appointment.
- Optional explicitly labeled synthetic demo data: seven advising requests and one
  appointment request. Repeated loading preserves IDs and statuses. Reset removes
  only loaded demo records, preserving submitted fictional records.
- Native Streamlit layout, blue headings/charts, gold accents, urgency text and alerts.

## Python 3.12 setup and launch

From the repository root in PowerShell:

```powershell
py -3.12 -m venv advisor_hub/.venv
advisor_hub/.venv/Scripts/python.exe -m pip install -r advisor_hub/requirements.txt
advisor_hub/.venv/Scripts/python.exe -m pip check
advisor_hub/.venv/Scripts/python.exe -m streamlit run advisor_hub/app.py --browser.gatherUsageStats false
```

Open the local URL printed by Streamlit (normally http://localhost:8501). Stop with
Ctrl+C. Streamlit 1.67.0 is pinned to the version installed and tested on Python
3.12. It provides the interface, charts/tables, session storage, and AppTest;
its dependencies are installed by pip. No API key, database, calendar, or email
service is needed. The classifier and management module use the standard library.

## Automated checks

```powershell
advisor_hub/.venv/Scripts/python.exe -m unittest discover -s advisor_hub/tests -v
advisor_hub/.venv/Scripts/python.exe -m compileall -q advisor_hub/app.py advisor_hub/management.py advisor_hub/classifier.py advisor_hub/tests
```

Without Streamlit, `py -3.12 -m unittest discover -s advisor_hub/tests -v`
checks the standard-library modules and explicitly skips UI tests. Run the full
suite in the installed environment before claiming UI checks passed.

The original 17 tests passed before modifications. New management and AppTest
checks cover classification integration, validation, statuses, actual counters,
search/filter/sort, duplicate load/token prevention, appointments, and reruns.
AppTest exercises widgets rather than merely checking server startup. The local
server also started and returned HTTP 200 from `/_stcore/health`. Native browser
inspection was unavailable because Computer Use could not verify Chrome's URL;
manual visual, narrow-screen, and keyboard checks remain necessary.

## Demonstration workflow

1. Open Overview: a new session has zero counts.
2. Open Student Requests. Enter `SYN-VIDEO` and
   `I have a registration hold and registration closes tomorrow.` Submit request.
3. Read Registration Holds / High, matched `hold`, `closes tomorrow`, and the ID.
4. Open Advisor Queue, view the request, select In Progress, Save request status.
5. Select Resolved and save. Overview reflects one resolved request.
6. Optionally load synthetic demonstration requests, inspect priority sorting,
   try filters, and show the ambiguous graduation/appointment review result.
7. Open Appointments, use a fictional identifier/reason and a future UTC date/time,
   then Request appointment review. Show Pending; change to Reviewed and save.
8. Reset demonstration records only when you want to remove loaded demo records.
   For an entirely fresh session, close/reset the Streamlit session.

Use no real student names, IDs, transcripts, or protected academic information.
Records live only in the current Streamlit `session_state`, survive normal widget
reruns/navigation, and are not shared between separate sessions. Closing/resetting
a session or restarting the server may remove them. Forms create records only
when submitted; tokens make replay of a submission idempotent. Explicit new
submissions can contain the same text; they are distinct requests.

## Classifier methodology and API

The preserved `classify_request(text: str) -> TriageResult` is a deterministic
English keyword baseline, not a trained ML model. The immutable result exposes
`category`, `urgency`, `matched_categories`, `matched_keywords`, `urgency_reasons`,
and `needs_review`. It does not persist data. Non-string input raises TypeError.

Category labels: Registration Holds, Degree Planning, Course Selection,
Graduation, Appointments, Other/Needs Review. Text normalization handles case,
Unicode compatibility characters, punctuation, and whitespace; matching uses
whole words/phrases. Zero or multiple category matches go to Other/Needs Review.

Urgency is independent: High for explicit urgency or supported near/missed
deadlines; Medium for holds, general deadlines, soon/this week/next week; Low
when no urgency rule matches. Simple negations suppress explicit urgency cues
without hiding a separate deadline. Incidental dates alone are Low. Matched rules
explain routing; no probabilities or confidence percentages are produced.

## Structure and integration points

- `app.py`: Streamlit entry point and four UI sections.
- `classifier.py`: existing classification API, unchanged from Stage 2.
- `management.py`: records, validation, IDs, status updates, metrics, filters, demo tools.
- `sample_data/`: 18 existing hand-labeled synthetic regression fixtures.
- `tests/test_classifier.py`, `test_setup.py`: preserved baseline checks.
- `tests/test_management.py`: business logic checks.
- `tests/test_app.py`: installed Streamlit AppTest widget workflows.
- `requirements.txt`: interface dependency; `.gitignore`: local environment/caches.

Possible future connections: another component passes English request text into
`classify_request`, consumes its category/urgency/review fields, or submits a
fictional identifier/text/token into `HubState.submit_request`. `dataclasses.asdict`
can expose record fields; an adapter must serialize datetimes to ISO 8601 and
omit internal tokens. Stable request IDs could link to future degree audit,
schedule building, graduation planning, elective recommendation, retrieval/Q&A,
and evaluation outputs. No shared schema, authentication, persistent transport,
or end-to-end team integration has been implemented or verified.

## Limitations and remaining work

Rules miss unseen synonyms, complex negation, context, sarcasm, resolved issues,
and unsupported date expressions; broad words can misroute requests. Low means
no rule matched, not verified low risk. Advisors must verify routing and urgency.
The original 18 synthetic examples test expected behavior, not generalization.
Planned independent evaluation targets are category Macro-F1 >= 0.80 and High
urgent-request recall >= 95%; neither target has been established. A future
trained classifier should be compared on the same untouched test set.

Before Checkpoint 3: collect independently labeled data with category and urgency
labels; freeze a test split before rule/model tuning; analyze errors; improve the
classifier; agree shared team interfaces; add authenticated shared persistent
storage and real appointment integration in an authorized future scope; complete
manual accessibility/responsive checks and record the demonstration with your
own voice and camera. The prototype has no authentication or production controls.

Development and documentation were AI-assisted using Codex. Outputs are checked
against executed code and automated tests; no synthetic metrics are claimed as
held-out performance.
