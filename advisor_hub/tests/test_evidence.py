"""Ensure evidence is executed, complete, reproducible, and explicitly synthetic."""
import unittest
from advisor_hub.classifier import classify_request
from advisor_hub.generate_evidence import EXAMPLES, build_reports


class EvidenceTests(unittest.TestCase):
    def test_required_examples_use_actual_classifier(self):
        report = build_reports()["examples.json"]
        self.assertTrue(report["synthetic"])
        self.assertEqual([r["id"] for r in report["examples"]], ["A", "B", "C", "D"])
        for row, (_, text) in zip(report["examples"], EXAMPLES):
            result = classify_request(text)
            self.assertEqual(row["input"], text)
            self.assertEqual(row["category"], result.category)
            self.assertEqual(row["urgency"], result.urgency)
            self.assertEqual(row["matched_keywords"], result.matched_keywords)
            self.assertEqual(row["needs_review"], result.needs_review)

    def test_edge_cases_have_unique_ids_and_required_coverage(self):
        report = build_reports()["error_analysis.json"]
        self.assertTrue(report["synthetic"])
        rows = report["cases"]
        self.assertEqual(len(rows), len({r["id"] for r in rows}))
        labels = {r["case"] for r in rows}
        self.assertTrue({"Ambiguous wording", "Multiple categories", "Unrecognized question",
                         "Urgent without category", "Incidental date", "Simple negation",
                         "Empty input", "Punctuation and capitalization"} <= labels)

    def test_fixture_report_does_not_claim_held_out_performance(self):
        report = build_reports()["fixture_report.json"]
        self.assertTrue(report["synthetic"])
        self.assertFalse(report["held_out"])
        self.assertEqual(report["category"]["sample_count"], 18)
        self.assertEqual(report["category_exact_matches"], 18)
        self.assertEqual(report["urgency_exact_matches"], 18)
