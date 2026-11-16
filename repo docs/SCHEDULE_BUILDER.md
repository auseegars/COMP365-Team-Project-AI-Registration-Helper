# Schedule builder (owner: Ryan Travers)

Builds a conflict-free **next-semester** schedule for a student, on top of the degree audit
(`src/audit/degree_audit.py`, Ayana Seegars). The term-by-term plan to graduation is the graduation
planner (Caleb Milliken). That planner can call this builder one term at a time.

## Files
| Path | What it is |
|---|---|
| `src/schedule/schedule_builder.py` | Candidate selection, CP-SAT optimizer, greedy baseline, independent checker, CLI |
| `src/schedule/sections.py` | Section format, time-overlap helpers, generator for the synthetic sample term |
| `src/schedule/evaluate_schedules.py` | Runs both methods on a profile set, writes `results/schedule_results.csv` |
| `data/sections/sample_term.json` | **SYNTHETIC** sections (457) for every course in `courses.json` |
| `data/profiles/schedule_demo_profiles.json` | 15 **SYNTHETIC** demo students (all 6 majors, a transfer, in-progress, blocked times) |
| `tests/test_schedule_builder.py` | 23 tests: fixture major, checker cases, real catalog data |

## Run it
```
pip install -r requirements.txt
python src/schedule/schedule_builder.py data/profiles/schedule_demo_profiles.json SYN-CS-03
python src/schedule/schedule_builder.py data/profiles/schedule_demo_profiles.json SYN-CS-03 --greedy
python src/schedule/evaluate_schedules.py
python -m pytest -q
```

## How it works
1. **Audit.** Run the degree audit with in-progress courses assumed passed. Its remaining requirements and
   elective options are the only courses that can be scheduled, so every course counts toward the degree.
2. **Candidates.** Keep courses whose prerequisites are met and whose corequisites are done or can be
   taken alongside. The catalog's suggested term must be no more than 2 terms past the student's standing
   (standing = credits applied / 15 + 1).
3. **Optimize (CP-SAT).** Choose at most one open section per course, with no time overlaps
   (`AddNoOverlap` on meeting intervals), nothing during blocked times, and total credits at or under
   the limit (default 17). Each required course fills its requirement once. Elective slots take courses
   up to their credits (e.g. CHEM 106 + CHEM 116 into a 4-credit science slot). The objective is priority
   per credit filled: required > named elective > free elective. It adds a bonus when the catalog plans
   the course for this term or earlier, and more weight for required courses on the critical path (how
   many remaining courses depend on it).
4. **Confirm.** Re-check the answer with `check_schedule()`. If the audit would not count a chosen
   course, ban it and re-solve.

**Greedy baseline:** required courses in the audit's order (shallowest prerequisite chain first), then
elective slots in curriculum order. It takes the first open, non-conflicting section of each until the
credit limit is reached. It uses the same candidate list, so the comparison isolates the optimization.

**Checker (`check_schedule`)** is independent of both methods. A schedule is invalid if any of these
happens: a section doesn't exist or is full, a meeting falls in a blocked time, a course is duplicated
or already done, stated prerequisites are unmet, a corequisite is missing, two sections overlap, the
credit limit is exceeded, or a course does not count. "Counts" is tested with the degree audit itself:
dropping any one course must lower the credits the audit applies. This produces the `schedule_valid`
column for `evaluate.py sched` (Aim 1).

## Current results (synthetic data, not project results)
`python src/schedule/evaluate_schedules.py` on the 15 demo profiles:

| metric | CP-SAT | greedy |
|---|---|---|
| valid schedules | 100% | 93% (1 course the audit would not count) |
| avg credits | 16.6 | 15.9 |
| avg critical-path unlocks | 33.5 | 31.9 |
| avg priority score | 4297 | 4008 |

## Known limits
- **Section data is synthetic.** Replace `data/sections/sample_term.json` with a real term in the same
  format (see `sections.py`). Nothing else needs to change.
- **201 non-COMP courses have no prerequisite data** (DATA_GAPS #1). For those courses only:
  - Sequence guard: blocked while a same-department, lower-numbered required course from an earlier
    catalog term is still remaining (stops MATH 132 with MATH 131).
  - Level gate on electives: a 300/400-level elective is not offered to first-years.
  - Every such course is listed in the output as "confirm with advisor". The checker reports these as
    warnings, not violations; every demo schedule currently has at least one.
- **Lab pairing is inferred.** A course titled "Lab..." whose number is 10 above a lecture in the same
  department needs that lecture: CHEM 106/116, CHEM 107/117, PHYS 241/251, PHYS 242/252, CAEE 325/335.
  Stated `coreq` data always wins.
- `attest` elective slots (ISE, CE technical/science electives) cannot be filled automatically. The
  output tells the student to pick them with an advisor.
- Not enforced (as in the audit): minimum grades, standing/permission rules, fall-only/spring-only offerings.

## Note for the degree audit (Ayana)
Found while testing SYN-CS-03: the audit fills elective slots from leftover courses **before** applying
transfer category credit. A course on two lists (ECON 201 is on both `CS_BUSINESS` and `GENED_SOC`) gets
placed in the business slot, which the student's BUS 110 transfer credit already covers. The social
science slot is then left open. The builder works around this (step 4), but the audit could apply
category credit first, or try both lists.
