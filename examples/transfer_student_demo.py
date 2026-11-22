"""Reproduces Figure 1 of the Practical Checkpoint 1 report.

Runs the degree audit for a SYNTHETIC Computer Science transfer student from Guilford Tech
and prints the same numbers shown in the figure.   Usage (from the repo root):

    python examples/transfer_student_demo.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "audit"))
import degree_audit as da  # noqa: E402

D = ROOT / "data"
courses = da.load_courses(D / "courses.json")
lists = da.load_lists(D / "lists.json")
tmap = da.load_transfer_map(D / "transfer" / "transfer_map.json")
cs = da.load_curriculum(D / "curricula" / "CS.json")

TRANSFER = ["ENG 111", "ENG 112", "MAT 271", "MAT 272", "CSC 151", "CSC 251", "MAT 167", "BUS 110"]
student = {"student_id": "SYN-001", "major": "CS", "completed": [],
           "transfer": [{"institution_id": "GTCC", "course": c} for c in TRANSFER]}

print("INPUT: synthetic transfer student (Guilford Tech, CS major)")
for c in TRANSFER:
    e = tmap[("GTCC", c)]                       # Guilford Tech's own row from the A&T tool
    target = " OR ".join(" + ".join(a) for a in e.get("alternatives", [e["ncat_equivalent"]]))
    print(f"  {c}  ->  {target}  ({e['credits']:g} cr)")

r = da.audit(student, cs, courses, tmap, lists)
print("\nOUTPUT: degree_audit.audit() for", cs["program_name"], f"({cs['total_credits']} cr)")
print(f"  credits applied:     {r.credits_applied:g}")
print(f"  credits remaining:   {r.credits_remaining:g}")
print(f"  requirements met:    {len(r.satisfied)}/{len(cs['requirements'])}")
print(f"  eligible now ({len(r.eligible_now)}): {', '.join(r.eligible_now)}")
print(f"  unverified prerequisites among them: {', '.join(r.unverified_prereqs)}")
print(f"  transfer courses not matched: {len(r.transfer_unmatched)}")
