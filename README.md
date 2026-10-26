# Aggies Enroll

A web hub for N.C. A&T College of Engineering students and advisors. Today a student's curriculum guide,
advisor, and registration portal live in separate places, so transfer students and underclassmen struggle to
tell which courses keep them on track, which electives count, and where the rules on overrides, holds, and
transfer credit are explained. Aggies Enroll combines those pieces and adds AI/ML components that a static
portal cannot provide.

Course project for COMP 365 (Project X).

## What the hub is designed to do
| Component | Goal | Method |
|---|---|---|
| Degree audit | Compare a student's record (including transfer credit) with their curriculum and list what remains | Rule engine over encoded curricula |
| Schedule builder | Conflict-free next-semester schedule respecting prerequisites, credit limits, open seats | Constraint optimization (OR-Tools CP-SAT) |
| Graduation planner | Term-by-term plan to graduation along the prerequisite chain | Prerequisite-ordered planning vs. greedy baseline |
| Elective recommender | Suggest electives that fit a student's interests and still count toward the degree | Embeddings + peer ratings, filtered by eligibility |
| Information assistant | Answer registration/policy questions with citations to official pages | Retrieval-augmented generation |
| Advisor triage | Sort student requests by topic and urgency into an advisor queue | Text classification |
| Streamlit hub | Student view and advisor view for all of the above | Streamlit |

## Current status

### Working
- **Curricula for 6 majors** (Computer Science, Electrical, Mechanical, Industrial & Systems, Computer
  Engineering, Civil) from the 2025-2026 catalog, plus a derived 5-course **first-year core**.
- **Course catalog data:** 249 courses with credits, titles, and sources.
- **Prerequisites for all COMP courses** (AND-of-OR form), including corequisites and notes.
- **Approved-course lists** for Gen Ed categories, CS electives, and EE/CPE technical electives.
- **Degree-audit engine:** given a student profile it returns requirements satisfied and remaining, remaining
  courses ordered along the prerequisite chain, courses takeable now, options for open elective slots,
  and credits remaining. Handles wildcard electives (e.g. `ECEN 4xx`) and community-college transfer credit.
- **Transfer-credit seed:** 29 equivalencies for the CS curriculum using NC Common Course Library codes
  (valid at all NC community colleges), with 10 target colleges registered.
- **Data validator and 27 unit tests.**

### In progress
- Prerequisites for the 201 non-COMP courses (`data/prereq_todo.csv` lists them).
- Verifying and extending the transfer map against the UNC System Transfer Course Guide, for all majors.
- Approved elective lists for ISE, Civil, and part of ME (the catalog gives no machine-readable list).

### Planned
- Schedule builder, graduation planner, elective recommender, information assistant, triage classifier,
  and the Streamlit hub (see the table above).

## Repository contents
| Path | What it contains |
|---|---|
| `data/courses.json` | Every course: title, credits, prerequisites, corequisites, notes, where it was sourced |
| `data/curricula/` | One file per program (`CS`, `EE`, `ME`, `ISE`, `CPE`, `CE`) plus `CORE` (first-year core) |
| `data/lists.json` | Named approved-course lists used by elective slots |
| `data/transfer/` | `transfer_map.json` (community college to A&T equivalencies) and `institutions.json` |
| `data/prereq_todo.csv` | Worksheet of courses whose prerequisites still need to be entered |
| `src/audit/degree_audit.py` | The degree-audit engine |
| `src/audit/validate_data.py` | Consistency checks for every data file |
| `tests/` | Unit tests; `tests/fixtures/` is a small synthetic data set |
| `docs/` | Data dictionary and known data gaps |


## Data sources
- N.C. A&T 2025-2026 Undergraduate Catalog curriculum guides (catalog.ncat.edu)
- N.C. A&T Computer Science Undergraduate Handbook (rev. 6/25/2025), used for the CS curriculum and COMP prerequisites
- Planned: UNC System Transfer Course Guide (coursetransfer.northcarolina.edu), public registrar and advising pages

Each data file records its source and retrieval date.

## Known limitations
See `docs/DATA_GAPS.md`. In short: prerequisites exist only for COMP courses so far, the transfer map is a
seed, and minimum-grade and standing/permission rules are stored but not enforced. Catalog and transfer
information change every year, so outputs must be confirmed with the registrar or an advisor.

## Data and ethics
Only public catalog data is used. No real student records (FERPA): all test and demo profiles are synthetic.
The hub supports advisors; it does not replace them.
