import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "audit"))
import degree_audit as da, validate_data as vd

FX = ROOT / "tests" / "fixtures"
courses = da.load_courses(FX / "data/courses.json")
cur = da.load_curriculum(FX / "data/curricula/test_major.json")
tmap = da.load_transfer_map(FX / "data/transfer/transfer_map.json")


class Audit(unittest.TestCase):
    def test_new_student_everything_remaining(self):
        r = da.audit({"completed": []}, cur, courses, tmap)
        self.assertEqual(r.credits_remaining, 15)
        self.assertEqual(r.eligible_now, ["TEST 101"])
        self.assertEqual(r.remaining_courses[0], "TEST 101")

    def test_order_follows_prereq_chain(self):
        r = da.audit({"completed": []}, cur, courses, tmap)
        order = r.remaining_courses
        self.assertLess(order.index("TEST 101"), order.index("TEST 201"))
        self.assertLess(order.index("TEST 201"), order.index("TEST 202"))

    def test_transfer_direct_credit(self):
        p = {"completed": [], "transfer": [{"institution_id": "CC1", "course": "XYZ 110"}]}
        r = da.audit(p, cur, courses, tmap)
        self.assertIn("r1", r.satisfied)
        self.assertEqual(r.eligible_now, ["TEST 201"])

    def test_transfer_elective_fills_only_unrestricted_slots(self):
        p = {"completed": [], "transfer": [{"institution_id": "CC1", "course": "XYZ 999"}]}
        r = da.audit(p, cur, courses, tmap)
        self.assertNotIn("r5", r.satisfied)  # r5 has an approved list

    def test_unmatched_transfer_reported(self):
        p = {"completed": [], "transfer": [{"institution_id": "CC1", "course": "NOPE 1"}]}
        r = da.audit(p, cur, courses, tmap)
        self.assertEqual(len(r.transfer_unmatched), 1)

    def test_one_of_and_elective_satisfied(self):
        p = {"completed": ["test-101", "TEST201", "TEST 202", "TEST 301", "TEST 401"]}
        r = da.audit(p, cur, courses, tmap)
        self.assertEqual(r.credits_remaining, 0)
        self.assertEqual(r.remaining, [])

    def test_in_progress_not_offered_again(self):
        p = {"completed": ["TEST 101"], "in_progress": ["TEST 201"]}
        r = da.audit(p, cur, courses, tmap)
        self.assertNotIn("TEST 201", r.eligible_now)

    def test_norm(self):
        self.assertEqual(da.norm("comp-167"), "COMP 167")
        self.assertEqual(da.norm("COMP167"), "COMP 167")

    def test_generic_nccc_code_applies_at_any_college(self):
        p = {"completed": [], "transfer": [{"institution_id": "CC1", "course": "ABC 100"}]}
        r = da.audit(p, cur, courses, tmap)
        self.assertEqual(r.transfer_unmatched, [])

    def test_wildcard_matching(self):
        self.assertTrue(da.matches("ECEN 452", "ECEN 4xx"))
        self.assertFalse(da.matches("ECEN 352", "ECEN 4xx"))
        self.assertFalse(da.matches("COMP 452", "ECEN 4xx"))
        self.assertEqual(da.norm("ECEN 4xx"), "ECEN 4XX")

    def test_cycle_detected(self):
        bad = {"A 1": {"credits": 1, "prereq": [["B 1"]]}, "B 1": {"credits": 1, "prereq": [["A 1"]]}}
        with self.assertRaises(ValueError):
            da.prereq_depth("A 1", bad)


class Validator(unittest.TestCase):
    def test_fixture_data_is_valid(self):
        self.assertEqual(vd.main(FX), 0)


if __name__ == "__main__":
    unittest.main()
