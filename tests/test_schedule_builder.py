"""Tests for the schedule builder (owner: Ryan Travers).  Synthetic students and sections only."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "audit"))
sys.path.insert(0, str(ROOT / "src" / "schedule"))
import degree_audit as da  # noqa: E402
import schedule_builder as sb  # noqa: E402
from sections import sections_overlap  # noqa: E402

FX = ROOT / "tests" / "fixtures"
fx_courses = da.load_courses(FX / "data/courses.json")
fx_cur = da.load_curriculum(FX / "data/curricula/test_major.json")
fx_tmap = da.load_transfer_map(FX / "data/transfer/transfer_map.json")


def sec(crn, course, days, start, end, seats=10):
    return {"crn": crn, "course": course, "section": "001", "seats_open": seats, "capacity": 30,
            "meetings": [{"days": days, "start": start, "end": end}]}


def index(sections):
    by_course = {}
    for s in sections:
        by_course.setdefault(s["course"], []).append(s)
    return by_course, {s["crn"]: s for s in sections}


FX_SECTIONS = [
    sec("A1", "TEST 101", "MWF", "09:00", "09:50"),
    sec("B1", "TEST 201", "MWF", "10:00", "10:50"),
    sec("C1", "TEST 202", "TR", "09:30", "10:45"),
    sec("D1", "TEST 301", "TR", "11:00", "12:15"),
    sec("E1", "TEST 401", "MWF", "09:00", "09:50"),      # clashes with TEST 101
    sec("E2", "TEST 401", "MWF", "13:00", "13:50", seats=0),  # full
    sec("F1", "TEST 402", "TR", "14:00", "15:15"),
    sec("G1", "TEST 102", "TR", "08:00", "09:15"),
]
FX_BY, FX_CRN = index(FX_SECTIONS)


def fx_build(profile, fn=sb.build_schedule, courses=fx_courses, by=FX_BY):
    return fn(profile, fx_cur, courses, by, fx_tmap, {})


def fx_check(r, profile, courses=fx_courses, crn=FX_CRN):
    return sb.check_schedule(r, profile, fx_cur, courses, crn, fx_tmap, {})


class FixtureSchedules(unittest.TestCase):
    def test_new_student_gets_only_courses_with_prereqs_met(self):
        p = {"completed": []}
        codes = [it["course"] for it in fx_build(p).items]
        self.assertIn("TEST 101", codes)
        self.assertNotIn("TEST 201", codes)          # needs TEST 101
        self.assertTrue(fx_check(fx_build(p), p)["valid"])

    def test_no_time_conflicts_and_no_full_sections(self):
        r = fx_build({"completed": []})
        crns = [it["crn"] for it in r.items]
        self.assertNotIn("E2", crns)                 # full
        self.assertNotIn("E1", crns)                 # overlaps TEST 101, which matters more
        secs = [FX_CRN[c] for c in crns]
        self.assertFalse(any(sections_overlap(a, b) for i, a in enumerate(secs) for b in secs[i + 1:]))

    def test_courses_outside_the_degree_are_never_scheduled(self):
        r = fx_build({"completed": []})
        self.assertNotIn("TEST 102", [it["course"] for it in r.items])   # not in any requirement

    def test_credit_limit(self):
        p = {"completed": ["TEST 101"], "preferences": {"max_credits": 3}}
        r = fx_build(p)
        self.assertLessEqual(r.total_credits, 3)
        self.assertEqual([it["course"] for it in r.items], ["TEST 201"])  # required beats elective

    def test_avoid_times_respected(self):
        p = {"completed": [], "preferences": {"avoid_times": [{"days": "MWF", "start": "08:00", "end": "10:00"}]}}
        r = fx_build(p)
        self.assertNotIn("A1", [it["crn"] for it in r.items])
        self.assertTrue(fx_check(r, p)["valid"])

    def test_in_progress_assumed_passed(self):
        p = {"completed": [], "in_progress": ["TEST 101"]}
        codes = [it["course"] for it in fx_build(p).items]
        self.assertIn("TEST 201", codes)
        self.assertNotIn("TEST 101", codes)

    def test_corequisite_scheduled_together(self):
        courses = copy.deepcopy(fx_courses)
        courses["TEST 402"]["coreq"] = ["TEST 101"]
        r = fx_build({"completed": []}, courses=courses)
        codes = [it["course"] for it in r.items]
        if "TEST 402" in codes:
            self.assertIn("TEST 101", codes)
        # and a coreq that cannot be taken removes the course
        courses["TEST 402"]["coreq"] = ["TEST 202"]
        codes = [it["course"] for it in fx_build({"completed": []}, courses=courses).items]
        self.assertNotIn("TEST 402", codes)

    def test_greedy_baseline_runs_and_is_valid_here(self):
        p = {"completed": ["TEST 101"]}
        r = fx_build(p, fn=sb.greedy_schedule)
        self.assertEqual(r.method, "greedy")
        self.assertTrue(fx_check(r, p)["valid"])

    def test_profile_template_format_accepted(self):
        p = {"id": "P01", "completed_courses": ["TEST 101"], "transfer_credits": [],
             "preferences": {"max_credits": 15, "avoid_times": []}}
        self.assertIn("TEST 201", [it["course"] for it in fx_build(p).items])


class Checker(unittest.TestCase):
    def item(self, crn):
        return {"crn": crn, "course": FX_CRN[crn]["course"]}

    def problems(self, crns, profile=None):
        return fx_check({"items": [self.item(c) for c in crns]}, profile or {"completed": []})["problems"]

    def test_flags_missing_prereq(self):
        self.assertTrue(any("prerequisites not met" in p for p in self.problems(["B1"])))

    def test_flags_time_conflict(self):
        self.assertTrue(any("time conflict" in p for p in self.problems(["A1", "E1"])))

    def test_flags_full_section(self):
        self.assertTrue(any("full" in p for p in self.problems(["E2"])))

    def test_flags_course_not_in_degree(self):
        self.assertTrue(any("does not count" in p for p in self.problems(["G1"])))

    def test_flags_already_completed(self):
        self.assertTrue(any("already" in p for p in self.problems(["A1"], {"completed": ["TEST 101"]})))

    def test_flags_credit_limit(self):
        p = {"completed": [], "preferences": {"max_credits": 3}}
        self.assertTrue(any("exceeds" in x for x in self.problems(["A1", "F1"], p)))

    def test_clean_schedule_passes(self):
        self.assertEqual(self.problems(["A1", "F1"]), [])


class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.courses, cls.lists, cls.tmap, cls.sec_data, cls.by = sb.load_all()
        cls.crn = {s["crn"]: s for ss in cls.by.values() for s in ss}
        cls.profiles = {p["student_id"]: p for p in
                        json.load(open(ROOT / "data/profiles/schedule_demo_profiles.json"))["profiles"]}
        cls.results = {}
        for sid, p in cls.profiles.items():
            cur = sb.curriculum_for(p["major"])
            r = sb.build_schedule(p, cur, cls.courses, cls.by, cls.tmap, cls.lists)
            cls.results[sid] = (r, sb.check_schedule(r, p, cur, cls.courses, cls.crn, cls.tmap, cls.lists))

    def test_section_data_is_marked_synthetic(self):
        self.assertTrue(self.sec_data["synthetic"])

    def test_every_demo_profile_gets_a_valid_schedule(self):
        for sid, (r, chk) in self.results.items():
            self.assertTrue(chk["valid"], f"{sid}: {chk['problems']}")
            self.assertGreaterEqual(r.total_credits, sb.FULL_TIME, sid)

    def test_cs_new_student(self):
        codes = [it["course"] for it in self.results["SYN-CS-01"][0].items]
        self.assertIn("COMP 163", codes)
        self.assertNotIn("COMP 167", codes)

    def test_labs_never_without_lecture(self):
        for sid, (r, _) in self.results.items():
            codes = {it["course"] for it in r.items}
            done = sb.done_codes(sb.normalize_profile(self.profiles[sid]), self.tmap)
            for c in codes:
                lec = sb.lab_lecture(c, self.courses)
                if lec:
                    self.assertTrue(lec in codes or lec in done, f"{sid}: {c} without {lec}")

    def test_sequence_guard_blocks_calc_ii_with_calc_i(self):
        codes = [it["course"] for it in self.results["SYN-EE-01"][0].items]
        self.assertIn("MATH 131", codes)
        self.assertNotIn("MATH 132", codes)          # no prereq data, but MATH 131 comes first in the plan

    def test_blocked_mornings_respected(self):
        r, chk = self.results["SYN-CS-04"]
        self.assertTrue(chk["valid"])
        self.assertLessEqual(r.total_credits, 15)

    def test_comp_495_brings_its_corequisite(self):
        for sid, (r, _) in self.results.items():
            codes = {it["course"] for it in r.items}
            done = sb.done_codes(sb.normalize_profile(self.profiles[sid]), self.tmap)
            if "COMP 495" in codes:
                self.assertTrue("COMP 410" in codes or "COMP 410" in done, sid)


if __name__ == "__main__":
    unittest.main()
