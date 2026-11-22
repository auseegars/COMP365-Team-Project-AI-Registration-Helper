# Data dictionary (curriculum and transfer layer)

All course codes are normalised `DEPT NNN` (upper-case, one space), e.g. `COMP 167`. Wildcards: `ECEN 4XX`
(same department and hundreds digit). Use `degree_audit.norm()` on any code from outside this repo.

## data/courses.json
```json
{"courses": {"COMP 280": {
  "title": "Data Structures", "credits": 3,
  "prereq": [["COMP 167"], ["MATH 123", "COMP 180", "ECEN 227"]],   // AND of ORs
  "prereq_status": "stated" | "none_listed" | "unknown",
  "coreq": [], "prereq_note": "…non-course conditions…", "min_grade": "C",
  "formerly": "GEEN163", "credits_inferred": true, "title_missing": true,
  "used_in": ["CS","CPE"], "sources": ["catalog:CPE","handbook"]}}}
```
* `prereq: []` = no prerequisite. `prereq: null` + `prereq_status: "unknown"` = not entered yet (see DATA_GAPS #1).
* `none_listed` = source describes the course but states no prerequisite.
* `credits_inferred` / `title_missing` flag values not stated in our sources.

## data/lists.json
`{"lists": {"GENED_SOC": {"title","source","courses":[…]}}}` Named approved-course lists referenced by `list_ref`.
`EE_TECH_B` also has `groups` (the four areas; "max 2 per area" is not enforced).

## data/curricula/<ID>.json
```json
{"program_id":"CS","program_name":"B.S. Computer Science","catalog_year":"2025-2026","total_credits":120,
 "source_url":"…","source_detail":"…","retrieved":"2026-10-25",
 "min_grade":{"C":["COMP 163"],"C-":["MATH 131"]}, "notes":[…], "known_discrepancies":[…],
 "requirements":[
   {"id":"CS-01","type":"course","code":"ENGL 100","term":1},
   {"id":"CS-02","type":"elective","label":"Business Elective","category":"business","credits":3,
    "fill":"list","list_ref":"CS_BUSINESS","term":3}]}
```
* `term` = suggested semester 1-8 from the catalog (hint for the planner).
* `elective.fill`: `list` (filled from the approved pool) · `partial` (pool known incomplete) ·
  `attest` (no list in the catalog; profile must list the slot id in `satisfied_electives`) ·
  `any` (free elective).
* `validate_data.py` checks requirements sum to `total_credits` (documented discrepancies become warnings).
* `CORE.json` = courses in the first two terms of all six programs (derived; see `docs/FIRST_YEAR_CORE.md`).

## data/transfer/
`transfer_map.json`:
```json
{"institution_id":"NCCCS","cc_course":"MAT 271","credits":4,"status":"direct","ncat_equivalent":["MATH 131"],
 "also_requires":[],"source":"…","guide_year":"2016","verified":false}
```
* `status`: `direct` (satisfies listed A&T course(s)) · `category` (counts toward elective slots with that
  `category`) · `elective` (generic elective credit; free electives only) · `none`.
* `NCCCS` rows use NC Common Course Library codes and apply to every NC community college; a college-specific
  row (same `cc_course`, that college's id) takes precedence.
* `also_requires`: courses that must also be in the student's transfer list (e.g., NET 110 + NET 125).
* `institutions.json`: the team's 10 colleges and their ids.

## Student profile (input to the audit; synthetic only)
```json
{"student_id":"SYN-001","major":"CS","completed":["MATH 131"],"in_progress":["COMP 163"],
 "transfer":[{"institution_id":"GTCC","course":"CSC 151"}],"satisfied_electives":["ISE-40"]}
```

## Audit output (`audit(...).to_dict()`)
`satisfied`, `remaining`, `remaining_courses` (ordered by prerequisite depth), `eligible_now`,
`elective_options` (slot id -> courses takeable now), `credits_applied`, `credits_remaining`,
`transfer_unmatched`, `unverified_prereqs`, `warnings`.
