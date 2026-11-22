# Practical Checkpoint 2 evidence — Advisor Hub

This folder records the implemented COMP365 student prototype and actual code
execution. All request text is fictional. No real student records, screenshots,
recordings, model confidence scores, or independent evaluation results are supplied.

## Reproduce from the repository root (PowerShell, Python 3.12)

```powershell
py -3.12 -m venv advisor_hub/.venv
advisor_hub/.venv/Scripts/python.exe -m pip install -r advisor_hub/requirements.txt
advisor_hub/.venv/Scripts/python.exe -m advisor_hub.generate_evidence
advisor_hub/.venv/Scripts/python.exe -m streamlit run advisor_hub/app.py --browser.gatherUsageStats false
```

The evidence command executes the classifier, evaluates the preserved fixtures,
runs the complete test suite, checks dependencies and syntax, launches a separate
loopback-only Streamlit server to probe its health endpoint, and stops that child
server. It refreshes generated files with actual output and exits nonzero for
failed/skipped tests, failed checks/startup, or an unexpected branch. It does not
change classifier rules. Tests and fixtures are reproducible; timestamps,
local paths, temporary port numbers, log timing, and test duration can vary.
The last command launches the interactive application for your own inspection.

## Evidence inventory

| File | Contents |
| --- | --- |
| `examples.json` | Required A–D inputs and executed category, urgency, matched rules, review flag |
| `error_analysis.json` | Thirteen executed synthetic edge cases with interpretations |
| `executed_cases.md` | Readable table generated from those same outputs |
| `fixture_report.json` | Explicitly non-held-out agreement, per-class support, confusion matrices, metric calculations |
| `test_results.txt` | Full actual unittest/AppTest execution log |
| `verification.json` | Test totals, dependency/syntax checks, Python/Streamlit versions, source hashes, branch and Stage 3 reference |
| `startup_probe.json` | Actual child-server command/log and HTTP health result |
| `environment.txt` | Python version and installed dependency versions from pip freeze |
| `evaluation_plan.md` | Metrics, independent labels/splits, comparison method, limits of the 18 fixtures |
| `video_guide.md` | 60–90 second script and exact manual recording clicks |
| `README.md` | Reproduction, scope, commit references, manual screenshots |

## Accomplished and verified

The original 17 tests passed before development. Stage 3 added a working
Streamlit dashboard and passed 38 tests before its commit. Stage 4 adds metric
and evidence tests; the full run in `verification.json` has 49 passing tests,
zero failures/errors, and zero skipped tests, including eight AppTest workflows.
Streamlit's expected bare-mode ScriptRunContext warning can appear in test logs;
the results have no application exceptions. Python syntax and dependency checks
pass. A local server health result is separate from UI behavior testing.

The dashboard has Overview metrics/recent requests/distributions, student request
submission and explained triage, queue filters/search/sorting/details, and saved
Open/In Progress/Resolved status changes across reruns. Appointment requests
validate fictional inputs and future UTC preferences, keep separate IDs/records,
list Pending requests, and support Pending/Reviewed/Cancelled updates. No request
is a confirmed booking. Demo loading is optional and idempotent; explicit demo
reset preserves submitted records. The original classifier and fixtures are unchanged.

The 18 regression fixtures have 18/18 category and urgency agreement. Four labeled
High fixtures are detected. These development fixtures are insufficient to claim
Macro-F1 >= 0.80 or urgent recall >= 95% on independent data. See the evaluation
plan and recorded counterexamples.

## Limits and integration status

No trained model, independent labeled test dataset, production database,
authentication, role enforcement, shared advisor/student sessions, calendar,
email, confirmed appointments, or end-to-end team integration exists. Session
records are temporary and may disappear on close/reset/restart. Status changes
are allowed between all declared statuses, including reopening; no history/audit
trail is implemented. Appointment times are explicitly UTC, with no availability
or double-booking check. Classification is English rules and has contextual,
negation, synonym, and date limitations. Advisors must verify every suggestion.

`classifier.classify_request`, `TriageResult`, `management.HubState`, and the
`evaluation.evaluate_requests` predictor adapter are potential integration points.
Degree audit, schedule building, graduation planning, elective recommendation,
and retrieval/Q&A components remain teammates' work. No unimplemented shared
interfaces are claimed. See the component README for input/output details.

## Git checkpoints

- `6cfda49`: Initialize advisor hub module (preserved).
- `799d9c2`: Implement request triage baseline (preserved).
- `684bae3f4582faf30734ea2e09a7ae4f41939357`: Build functional Streamlit advisor dashboard
  (Stage 3, committed before any Stage 4 implementation).
- Stage 4 is the commit containing this evidence, titled
  `Add advisor hub evaluation and checkpoint evidence`. A commit cannot embed
  its own SHA without changing that SHA. After committing, resolve it with:

```powershell
git log -1 --format="%H %s" -- advisor_hub/checkpoint_evidence/README.md
```

Only `feature/advisor-hub` is used. No merge or push is part of this work.

## Genuine screenshots to capture manually

No screenshots were captured: the browser host was unavailable, then Computer
Use stopped because it could not confidently determine Chrome's current URL.
AppTest interactions and the HTTP health probe were automated; visual layout,
contrast, narrow-screen behavior, keyboard navigation, and screenshots still
need manual verification. There is no fabricated terminal/application image.

1. Launch the app with the command above and open its local URL. Confirm the
   student-project notice, blue/gold accents, readable headings, and sidebar.
2. On a fresh Overview, click Load synthetic demonstration requests. Confirm the
   synthetic warning, seven submitted/Open requests, three active High requests,
   zero Resolved, one Pending appointment, recent table, and both charts.
3. Use your screenshot tool to capture only this app view. Save as
   `advisor_hub/checkpoint_evidence/screenshots/01-overview.png` (create that
   directory when capturing genuine images).
4. On Student Requests, submit `SYN-VIDEO` with required Example A. Capture the
   result with Registration Holds, High, matched rules and ID as `02-triage.png`.
5. On Advisor Queue, search `SYN-VIDEO`, select In Progress, Save request status.
   Capture the saved status and details as `03-advisor-queue.png`.
6. On Appointments, submit `SYN-APPT-VIDEO`, reason `Discuss next semester's goals`,
   and a future UTC date/time. Capture its Pending state and the unconfirmed
   request notice as `04-appointment-request.png`.
7. Resize the browser to a narrow window and test sidebar navigation, table
   scrolling, and form labels. Use Tab/Shift+Tab/Enter to check keyboard access.
   Check your browser's light/dark settings for text readability. Record any
   layout or accessibility problem honestly before recording the video.

Capture your real application with only fictional data visible. Do not substitute
mockups or generated images. The video must be recorded manually with your own
camera and voice; follow `video_guide.md`.

AI-assisted implementation and documentation: Codex. Evidence values come from
executed code and tests, with manual verification limits stated above.
