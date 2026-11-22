"""Tests for the elective recommender (owner: Ryan Kevena).  Synthetic survey data only.

Uses the shared tests/fixtures data set so it runs offline (the recommender falls back to a
bag-of-words similarity when sentence-transformers is not installed).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "audit"))
sys.path.insert(0, str(ROOT / "src" / "electives"))
import degree_audit as da  # noqa: E402
import recommend as rec  # noqa: E402
import survey as sv  # noqa: E402

FX = ROOT / "tests" / "fixtures"
fx_courses = da.load_courses(FX / "data/courses.json")
fx_cur = da.load_curriculum(FX / "data/curricula/test_major.json")

# Fixture curriculum has one elective slot (r5) approving TEST 401 / TEST 402.
# A profile that finished the prerequisites but neither elective leaves that slot open.
PROFILE = {"student_id": "T1", "major": "test_major",
           "completed": ["TEST 101", "TEST 201", "TEST 202", "TEST 301"],
           "in_progress": []}

RESPONSES = [
    {"student_id": "r1", "interests": ["game_design"], "ratings": {"TEST 402": 5}},
    {"student_id": "r2", "interests": ["game_design"], "ratings": {"TEST 402": 4}},
    {"student_id": "r3", "interests": ["software_engineering"], "ratings": {"TEST 401": 2}},
]


class EligibilityFilter(unittest.TestCase):
    def setUp(self):
        # point the recommender's curriculum loader at the fixture program
        self._orig = rec.CURRICULA
        rec.CURRICULA = FX / "data" / "curricula"

    def tearDown(self):
        rec.CURRICULA = self._orig

    def test_only_eligible_courses_recommended(self):
        by_code, res = rec.eligible_electives(PROFILE, fx_courses, {})
        # TEST 401 and TEST 402 fill the open elective slot; required/completed courses do not appear.
        self.assertIn("TEST 402", by_code)
        self.assertNotIn("TEST 101", by_code)
        recs, _ = rec.recommend(PROFILE, ["game_design"], fx_courses, {}, RESPONSES, top=5)
        self.assertTrue(recs, "expected at least one recommendation")
        for r in recs:
            self.assertIn(r["code"], by_code)   # never recommend an ineligible course

    def test_completed_elective_not_recommended_again(self):
        done = dict(PROFILE, completed=PROFILE["completed"] + ["TEST 402"])
        by_code, _ = rec.eligible_electives(done, fx_courses, {})
        self.assertNotIn("TEST 402", by_code)


class HybridRanking(unittest.TestCase):
    def test_interest_and_peer_rating_rank_first(self):
        # TEST 402 (title mentions game; rated 4-5 by game_design peers) should outrank TEST 401.
        ranked = rec.rank_pool(["TEST 401", "TEST 402"], ["game_design"], fx_courses, RESPONSES)
        self.assertEqual(ranked[0]["code"], "TEST 402")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_peer_rating_reported(self):
        ranked = rec.rank_pool(["TEST 402"], ["game_design"], fx_courses, RESPONSES)
        self.assertEqual(ranked[0]["n_ratings"], 2)
        self.assertAlmostEqual(ranked[0]["peer_rating"], 4.5, places=2)


class SurveyAggregation(unittest.TestCase):
    def test_interest_filtered_aggregate(self):
        agg = sv.aggregate(RESPONSES, ["game_design"])
        self.assertEqual(agg["TEST 402"]["n"], 2)       # only the two game_design peers
        self.assertNotIn("TEST 401", agg)               # rated only by a software_engineering peer

    def test_course_tags_from_title(self):
        self.assertIn("game_design", sv.course_tags("Game Design"))


if __name__ == "__main__":
    unittest.main()
