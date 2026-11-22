"""Behavioral tests using only fictional advising requests."""

from dataclasses import asdict
import json
from pathlib import Path
import unittest

from advisor_hub.classifier import OTHER, classify_request


class ClassificationTests(unittest.TestCase):
    def test_synthetic_examples(self):
        path = Path(__file__).resolve().parents[1] / "sample_data" / "synthetic_requests.json"
        fixture = json.loads(path.read_text(encoding="utf-8"))
        self.assertIs(fixture["synthetic"], True)
        examples = fixture["requests"]
        self.assertEqual(len({row["id"] for row in examples}), len(examples))
        self.assertEqual(
            {row["expected_category"] for row in examples},
            {"Registration Holds", "Degree Planning", "Course Selection",
             "Graduation", "Appointments", OTHER},
        )
        for row in examples:
            with self.subTest(synthetic_id=row["id"]):
                self.assertTrue(row["id"].startswith("SYN-"))
                result = classify_request(row["text"])
                self.assertEqual(result.category, row["expected_category"])
                self.assertEqual(result.urgency, row["expected_urgency"])

    def test_case_punctuation_whitespace_and_unicode(self):
        for text in (
            "  WHICH\nCOURSES\tshould I take??? ",
            "Which courses should I take?",
            "ＷＨＩＣＨ ＣＯＵＲＳＥＳ should I take?",
        ):
            with self.subTest(text=text):
                self.assertEqual(classify_request(text).category, "Course Selection")

    def test_blank_and_unmatched_requests_need_review(self):
        for text in ("", " \t\n", "?!...", "Where is the library?", "你好"):
            with self.subTest(text=text):
                result = classify_request(text)
                self.assertEqual(result.category, OTHER)
                self.assertTrue(result.needs_review)
                self.assertEqual(result.matched_categories, ())
                self.assertEqual(result.urgency, "Low")

    def test_keywords_do_not_match_inside_other_words(self):
        for text in ("threshold shareholder", "undergraduate newsletter", "urgentlyish asapish"):
            with self.subTest(text=text):
                result = classify_request(text)
                self.assertEqual(result.category, OTHER)
                self.assertEqual(result.urgency, "Low")

    def test_multiple_categories_need_review_with_explanation(self):
        result = classify_request("An urgent appointment about my degree audit, please.")
        self.assertEqual(result.category, OTHER)
        self.assertEqual(result.matched_categories, ("Degree Planning", "Appointments"))
        self.assertEqual(result.urgency, "High")
        self.assertIn("appointment", result.matched_keywords)
        self.assertIn("degree audit", result.matched_keywords)

    def test_repeated_keywords_do_not_override_ambiguity(self):
        result = classify_request("appointment appointment appointment graduation")
        self.assertEqual(result.category, OTHER)

    def test_repeated_calls_are_deterministic_and_serializable(self):
        request = "My graduation application is due today."
        self.assertEqual(classify_request(request), classify_request(request))
        decoded = json.loads(json.dumps(asdict(classify_request(request))))
        self.assertEqual(decoded["category"], "Graduation")
        self.assertIn("due today", decoded["urgency_reasons"])

    def test_non_string_input_is_rejected(self):
        for text in (None, 123, True, [], {}, b"appointment"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(TypeError, "must be a string"):
                    classify_request(text)


class UrgencyTests(unittest.TestCase):
    def test_explicit_high_urgency(self):
        for cue in ("URGENT", "urgently", "ASAP", "immediately", "emergency"):
            with self.subTest(cue=cue):
                result = classify_request(f"Please help {cue}.")
                self.assertEqual(result.urgency, "High")
                self.assertTrue(result.urgency_reasons)
                self.assertTrue(result.needs_review)

    def test_near_or_missed_deadlines(self):
        for text in (
            "My application is due today.", "The deadline is tomorrow.",
            "Registration closes tonight.", "The deadline for my form is today.",
            "Tomorrow is the deadline.", "I need a reply within 24 hours.",
            "Please respond in 48 hours.", "I missed my deadline.",
            "My application is past due.", "My paperwork is overdue.",
        ):
            with self.subTest(text=text):
                self.assertEqual(classify_request(text).urgency, "High")

    def test_medium_urgency(self):
        for text in (
            "I have a hold.", "I can’t register.", "I need help soon.",
            "Can we meet this week?", "What is the deadline next month?",
        ):
            with self.subTest(text=text):
                self.assertEqual(classify_request(text).urgency, "Medium")

    def test_high_urgency_takes_precedence(self):
        result = classify_request("I have a hold, and registration closes tomorrow.")
        self.assertEqual(result.category, "Registration Holds")
        self.assertEqual(result.urgency, "High")

    def test_incidental_time_mentions_are_low(self):
        for text in (
            "I read the catalog today.", "I have an appointment tomorrow.",
            "My graduation ceremony is next year.",
        ):
            with self.subTest(text=text):
                self.assertEqual(classify_request(text).urgency, "Low")

    def test_simple_negated_urgency(self):
        for text in (
            "This is not urgent.", "It isn't urgent.", "This is not an emergency.",
            "There is no emergency.", "This is not urgent; I need an appointment.",
        ):
            with self.subTest(text=text):
                self.assertEqual(classify_request(text).urgency, "Low")

    def test_negated_urgency_does_not_hide_deadlines_or_other_cues(self):
        for text in (
            "Not urgent, but my application is due today.",
            "This is not an emergency, but I need help ASAP.",
        ):
            with self.subTest(text=text):
                self.assertEqual(classify_request(text).urgency, "High")


if __name__ == "__main__":
    unittest.main()
