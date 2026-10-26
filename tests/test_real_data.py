"""Tests against the real encoded catalog data (data/).  Synthetic students only."""
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "audit"))
import degree_audit as da, validate_data as vd

D = ROOT / "data"
courses = da.load_courses(D / "courses.json")
lists = da.load_lists(D / "lists.json")
tmap = da.load_transfer_map(D / "transfer/transfer_map.json")
cur = {p: da.load_curriculum(D / f"curricula/{p}.json") for p in ("CS", "EE", "ME", "ISE", "CPE", "CE", "CORE")}
PROGRAMS = ("CS", "EE", "ME", "ISE", "CPE", "CE")


def run(pid, profile):
    return da.audit(profile, cur[pid], courses, tmap, lists)


class RealData(unittest.TestCase):
    def test_validator_passes(self):
        self.assertEqual(vd.main(ROOT), 0)

    def test_six_programs_plus_core_present(self):
        self.assertEqual(sorted(cur), sorted(PROGRAMS + ("CORE",)))

    def test_totals_match_catalog(self):
        self.assertEqual({p: cur[p]["total_credits"] for p in PROGRAMS},
                         {"CS": 120, "EE": 122, "ME": 120, "ISE": 120, "CPE": 123, "CE": 120})

    def test_new_student_needs_every_credit(self):
        for p in PROGRAMS:
            r = run(p, {"completed": []})
            self.assertEqual(r.credits_remaining, cur[p]["total_credits"], p)

    def test_cs_first_courses_available_now(self):
        r = run("CS", {"completed": []})
        for c in ("COMP 163", "MATH 131", "ENGL 100", "COMP 121", "GEEN 111"):
            self.assertIn(c, r.eligible_now)
        self.assertNotIn("COMP 167", r.eligible_now)   # needs COMP 163

    def test_cs_prereq_chain_order(self):
        order = run("CS", {"completed": []}).remaining_courses
        for a, b in (("COMP 163", "COMP 167"), ("COMP 280", "COMP 285"), ("COMP 285", "COMP 410"),
                     ("COMP 410", "COMP 496")):
            self.assertLess(order.index(a), order.index(b), (a, b))

    def test_cs_senior_project_needs_410_corequisite_data(self):
        self.assertEqual(courses["COMP 495"]["coreq"], ["COMP 410"])

    def test_cs_transfer_student_via_generic_codes(self):
        # Guilford Tech student with the handbook's CS transfer courses
        tr = [{"institution_id": "GTCC", "course": c} for c in
              ("ENG 111", "ENG 112", "MAT 271", "MAT 272", "CSC 151", "CSC 251", "MAT 167", "BUS 110")]
        r = run("CS", {"completed": [], "transfer": tr})
        sat = set(r.satisfied)
        codes = {q["code"] for q in cur["CS"]["requirements"] if q["type"] == "course" and q["id"] in sat}
        self.assertTrue({"ENGL 100", "ENGL 101", "MATH 131", "MATH 132", "COMP 163", "COMP 167", "COMP 180"} <= codes)
        business = next(q["id"] for q in cur["CS"]["requirements"] if q.get("category") == "business")
        self.assertIn(business, sat)                      # BUS 110 -> business elective
        self.assertEqual(r.transfer_unmatched, [])
        self.assertIn("COMP 280", r.eligible_now)         # COMP 167 + COMP 180 now done

    def test_net_pair_needs_both_courses(self):
        one = run("CS", {"completed": [], "transfer": [{"institution_id": "GTCC", "course": "NET 110"}]})
        self.assertEqual(len(one.transfer_unmatched), 1)
        both = run("CS", {"completed": [], "transfer": [{"institution_id": "GTCC", "course": c} for c in ("NET 110", "NET 125")]})
        self.assertEqual(both.transfer_unmatched, [])

    def test_unmatched_cc_course_reported(self):
        r = run("CS", {"completed": [], "transfer": [{"institution_id": "GTCC", "course": "ZZZ 999"}]})
        self.assertEqual(len(r.transfer_unmatched), 1)

    def test_ee_wildcard_elective_filled(self):
        # EE-technical slots accept listed ECEN 4xx courses
        r = run("EE", {"completed": ["ECEN 449"]})
        filled = [q for q in cur["EE"]["requirements"] if q["id"] in r.satisfied and q["type"] == "elective"]
        self.assertEqual(len(filled), 1)

    def test_unverified_prereqs_are_reported_not_hidden(self):
        r = run("EE", {"completed": []})
        self.assertTrue(r.unverified_prereqs)             # EE courses have no prereq data yet
        self.assertTrue(all(courses[c]["prereq"] is None for c in r.unverified_prereqs))

    def test_attest_electives_need_attestation(self):
        q = next(q for q in cur["ISE"]["requirements"] if q.get("fill") == "attest")
        self.assertNotIn(q["id"], run("ISE", {"completed": []}).satisfied)
        self.assertIn(q["id"], run("ISE", {"completed": [], "satisfied_electives": [q["id"]]}).satisfied)

    def test_core_is_in_every_program(self):
        core = {q["code"] for q in cur["CORE"]["requirements"]}
        for p in PROGRAMS:
            have = {q["code"] for q in cur[p]["requirements"] if q["type"] == "course"}
            self.assertTrue(core <= have, p)

    def test_civil_discrepancy_is_documented(self):
        self.assertTrue(cur["CE"]["known_discrepancies"])


if __name__ == "__main__":
    unittest.main()
