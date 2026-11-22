# Transfer map: how it was built and what to watch for

**Source:** saved pages of the N.C. A&T Transfer Articulation Tool (cms-apps.ncat.edu/transfer-articulation), retrieved
2026-11-10, for the 10 target colleges. The tool is an unofficial guide; a grade of C or higher is required.

**Rebuild:** `python tools/build_transfer.py <folder with the saved pages>` (the pages are not stored in the repo).

**Rules used**
* A row is kept only if at least one A&T course it maps to is in `courses.json` (our 6 curricula).
* `X AND Y` = both A&T courses are awarded (e.g. CHM 151 -> CHEM 106 + CHEM 116).
* `X OR Y` = one of them; stored as `alternatives`. The audit chooses the one that fills an open requirement.
  Alternatives that are not in our curricula are dropped but noted in `note`.
* College rows override the generic `NCCCS` seed rows.

**Differences to be aware of**
* The 2016 handbook seed is out of date in places (MAT 167 -> MATH 123 in the tool, not COMP 180).
* Colleges differ: e.g. PHY 251 gives PHYS 241 + PHYS 251 (lab) at most colleges but only PHYS 241 at Piedmont;
  Guilford Tech (GTCC) and Forsyth Tech (FTCC) have the most engineering equivalencies.
* A&T credits that differ from `courses.json`: MATH 110 (tool 4, catalog data 3) and ECEN 206 (tool 3, data 1).
  The audit uses `courses.json`. Check the catalog.
* Alamance was built from copied text, so its OR/AND grouping was rebuilt page by page; re-save the page as HTML to
  make it exact.
