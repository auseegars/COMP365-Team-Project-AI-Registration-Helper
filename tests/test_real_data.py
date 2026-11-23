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

    def test_cs_transfer_student_guilford_tool_rows(self):
        # Rows taken from the A&T Transfer Articulation Tool for Guilford Tech (retrieved 2026-11-10)
        tr = [{"institution_id": "GTCC", "course": c} for c in
              ("ENG 111", "ENG 112", "MAT 271", "MAT 272", "CSC 151", "CSC 251", "MAT 167")]
        r = run("CS", {"completed": [], "transfer": tr})
        sat = set(r.satisfied)
        codes = {q["code"] for q in cur["CS"]["requirements"] if q["type"] == "course" and q["id"] in sat}
        self.assertTrue({"ENGL 100", "ENGL 101", "MATH 131", "MATH 132", "COMP 163", "COMP 167"} <= codes)
        # the 2016 handbook said MAT 167 -> COMP 180; the A&T tool says MATH 123, so COMP 180 stays open
        self.assertNotIn("COMP 180", codes)
        self.assertEqual(r.transfer_unmatched, [])

    def test_or_alternative_picks_the_one_the_curriculum_needs(self):
        # Alamance/Guilford list "CSC 151 -> COMP 163 OR CST 240"; only COMP 163 is in the CS curriculum
        gt = tmap[("GTCC", "CSC 151")]
        self.assertIn("COMP 163", gt["ncat_equivalent"])
        # a synthetic OR entry: both options real courses, the audit should take the one still needed
        fake = dict(gt, alternatives=[["COMP 163"], ["COMP 167"]], ncat_equivalent=["COMP 163"])
        m = {**tmap, ("GTCC", "CSC 151"): fake}
        r = da.audit({"completed": ["COMP 163"], "transfer": [{"institution_id": "GTCC", "course": "CSC 151"}]},
                     cur["CS"], courses, m, lists)
        self.assertIn(next(q["id"] for q in cur["CS"]["requirements"] if q.get("code") == "COMP 167"), r.satisfied)

    def test_seed_rows_still_apply_to_unlisted_colleges(self):
        # 2016 handbook seed (institution 'NCCCS') is the fallback when a college has no row of its own
        tr = [{"institution_id": "NCCCS", "course": c} for c in ("ENG 111", "MAT 167", "BUS 110")]
        r = run("CS", {"completed": [], "transfer": tr})
        sat = set(r.satisfied)
        codes = {q["code"] for q in cur["CS"]["requirements"] if q["type"] == "course" and q["id"] in sat}
        self.assertTrue({"ENGL 100", "COMP 180"} <= codes)
        business = next(q["id"] for q in cur["CS"]["requirements"] if q.get("category") == "business")
        self.assertIn(business, sat)
        self.assertEqual(r.transfer_unmatched, [])

    def test_category_transfer_credit_used_before_shared_course(self):
        # ECON 201 is on both the business and social-science lists; BUS 110 (seed row) gives business
        # category credit.  The audit must spend the category credit on business and ECON 201 on social science.
        r = run("CS", {"completed": ["ECON 201"], "transfer": [{"institution_id": "NCCCS", "course": "BUS 110"}]})
        slot = {q.get("category"): q["id"] for q in cur["CS"]["requirements"] if q["type"] == "elective"}
        self.assertIn(slot["business"], r.satisfied)
        self.assertIn(slot["social_behavioral"], r.satisfied)

    def test_course_fitting_fewer_slots_is_used_first(self):
        # Guilford BUS 110 -> MGMT 110 (business only).  With ECON 201 also done, MGMT 110 should fill
        # business and leave ECON 201 for social science.
        r = run("CS", {"completed": ["ECON 201"], "transfer": [{"institution_id": "GTCC", "course": "BUS 110"}]})
        slot = {q.get("category"): q["id"] for q in cur["CS"]["requirements"] if q["type"] == "elective"}
        self.assertIn(slot["business"], r.satisfied)
        self.assertIn(slot["social_behavioral"], r.satisfied)

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
        # every required course now has catalog data, so blank one out in a copy
        import copy
        cs = copy.deepcopy(courses)
        cs["GEEN 100"]["prereq"], cs["GEEN 100"]["prereq_status"] = None, "unknown"
        r = da.audit({"completed": []}, cur["ISE"], cs, tmap, lists)
        self.assertIn("GEEN 100", r.unverified_prereqs)
        self.assertTrue(all(cs[c]["prereq"] is None for c in r.unverified_prereqs))

    def test_no_required_course_has_unknown_prereqs(self):
        for p in PROGRAMS:
            req = {q["code"] for q in cur[p]["requirements"] if q["type"] == "course"}
            self.assertEqual([c for c in sorted(req) if courses[c]["prereq"] is None], [], p)

    def test_at_least_three_of_five_rule(self):
        self.assertTrue(da.prereqs_met("CIEN 483", courses, {"CIEN 310", "CIEN 320", "CIEN 350"}))
        self.assertFalse(da.prereqs_met("CIEN 483", courses, {"CIEN 310", "CIEN 320"}))

    # ---- catalog prerequisites for the engineering majors (data/catalog_prereqs.csv)
    def test_ee_catalog_prereq_chain_blocks_and_unlocks(self):
        r = run("EE", {"completed": []})
        self.assertIn("ECEN 101", r.eligible_now)
        self.assertNotIn("ECEN 200", r.eligible_now)       # ECEN 101 and MATH 132
        self.assertNotIn("ECEN 200", r.unverified_prereqs)
        r = run("EE", {"completed": ["ECEN 101", "MATH 131", "MATH 132"]})
        self.assertIn("ECEN 200", r.eligible_now)
        self.assertNotIn("ECEN 300", r.eligible_now)       # ECEN 200 and MATH 341

    def test_me_three_course_prereq(self):
        self.assertEqual(courses["MEEN 324"]["prereq"], [["MEEN 210"], ["MEEN 233"], ["MATH 341"]])
        self.assertTrue(da.prereqs_met("MEEN 324", courses, {"MEEN 210", "MEEN 233", "MATH 341"}))
        self.assertFalse(da.prereqs_met("MEEN 324", courses, {"MEEN 210", "MEEN 233"}))

    def test_catalog_corequisites_and_placement_courses(self):
        self.assertEqual(courses["ECEN 212"]["coreq"], ["ECEN 218"])
        self.assertEqual(courses["CAEE 231"]["prereq"], [["PHYS 241"]])   # "Corequisite: CAEE 230" kept out of prereq
        self.assertEqual(courses["CAEE 231"]["coreq"], ["CAEE 230"])
        self.assertEqual(courses["MATH 131"]["prereq"], [])                # placement score is an alternative
        self.assertIn("placement", courses["MATH 131"]["prereq_note"])

    def test_every_catalog_prereq_records_its_source(self):
        done = [c for c, v in courses.items() if "prereq_text" in v]
        self.assertGreater(len(done), 150)
        for c in done:
            self.assertIn(courses[c]["prereq_source"]["catalog_year"], ("2024-2025", "2025-2026"), c)

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
