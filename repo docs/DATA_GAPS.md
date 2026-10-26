# Known gaps in the curriculum/transfer data (read before relying on it)

Honest list of what is *not* yet reliable. Updated 2026-10-25.

| # | Gap | Impact | Fix |
|---|---|---|---|
| 1 | **Prerequisites known only for COMP courses (48 of 249).** 201 courses have `prereq: null` / `prereq_status: "unknown"` (`data/prereq_todo.csv`). | Engine does not block on them; it lists them in `unverified_prereqs`. Schedules/plans for EE, ME, ISE, CPE, CE can violate real prerequisites. | Copy each course's "Prerequisite" line from catalog.ncat.edu (Courses tab) into the CSV;|
| 2 | **Transfer map is a seed (28 rows) from the CS handbook, dated June 2016.** Only CS-curriculum courses; codes are NC Common Course Library codes, so they apply at all 10 colleges, but there are no college-specific rows. | Not enough for the 15 transfer test profiles in other majors; may be outdated. | Verify/extend against the UNC System Transfer Course Guide (coursetransfer.northcarolina.edu) for each of the 10 colleges and each major. |
| 3 | Catalog (Civil): course list sums to 121 credits, but the catalog states 120 and its Freshman/2nd-semester total (14) disagrees with the listed courses (15). | Documented in `CE.json` `known_discrepancies`; validator warns instead of failing. | Ask the CAEE advisor which row is stale. |
| 4 | CS curriculum comes from the **handbook** (Fall 2023 plan), not the catalog page. Other CS tracks (pre-calculus, cyber, health informatics, CC transfer) not encoded. | Main CS track only. | Save the catalog CS page and diff; add tracks if needed. |
| 5 | Gen Ed approved lists (Humanities, Social/Behavioral, African American, Global) come from the **CS handbook p.17** and are applied to all majors. | Other colleges' lists may differ slightly. | Confirm with advisors. |
| 6 | Technical/science electives for ISE, CE, and part of ME have **no machine-readable list** in the catalog guide (ISE footnote: "See your academic advisor"). They use `fill: "attest"` (profile must attest) or `fill: "partial"`. | The audit cannot auto-credit those slots. | Get the approved lists from the departments. |
| 7 | 73 courses have **inferred credits** (`credits_inferred: true`, mostly elective-list courses with no description in our sources) and 63 have **no title** (`title_missing`). | Credit counts for those electives may be off. | Fill from the catalog. |
| 8 | Not enforced: minimum grades (C / C-), non-course prerequisites (standing, permission), "max 2 per area" (EE), science Group 1/2 rule (CS). Stored as data/notes. | Audit may over-credit in rare cases. | Out of scope for the checkpoint; documented. |
| 9 | 3 title conflicts between sources (GEEN 111, COMP 160, COMP 285): catalog title kept. | Cosmetic. | none |
