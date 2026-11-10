"""Analytically check metric formulas, validation, and future-classifier adapters."""
import unittest
from advisor_hub.classifier import classify_request
from advisor_hub.evaluation import classification_metrics, evaluate_requests, urgent_recall


class EvaluationTests(unittest.TestCase):
    def test_known_macro_f1_and_confusion_matrix(self):
        # A: TP=1 FP=0 FN=1 -> F1=2/3; B: TP=2 FP=1 FN=0 -> F1=4/5.
        result = classification_metrics(["A", "A", "B", "B"], ["A", "B", "B", "B"], ("A", "B"))
        self.assertAlmostEqual(result["macro_f1"], (2 / 3 + 4 / 5) / 2)
        self.assertEqual(result["confusion_matrix"], {"A": {"A": 1, "B": 1}, "B": {"A": 0, "B": 2}})
        self.assertEqual(result["per_class"]["A"]["support"], 2)

    def test_macro_weights_classes_equally(self):
        result = classification_metrics(["A"] * 9 + ["B"], ["A"] * 10, ("A", "B"))
        self.assertAlmostEqual(result["macro_f1"], (18 / 19) / 2)

    def test_zero_denominators_and_absent_classes(self):
        self.assertEqual(classification_metrics(["A"], ["A"], ("A", "B"))["macro_f1"], 0.5)
        self.assertEqual(classification_metrics(["A", "B"], ["B", "A"], ("A", "B"))["macro_f1"], 0)

    def test_urgent_recall_false_negatives(self):
        result = urgent_recall(["High", "High", "High", "Low"], ["High", "Low", "Medium", "High"])
        self.assertEqual(result["true_positives"], 1)
        self.assertEqual(result["false_negatives"], 2)
        self.assertAlmostEqual(result["recall"], 1 / 3)

    def test_no_urgent_support_is_undefined(self):
        self.assertIsNone(urgent_recall(["Low"], ["High"])["recall"])

    def test_invalid_labels_lengths_and_empty_data(self):
        for truth, predicted, labels in [([], [], ("A",)), (["A"], [], ("A",)),
                                         (["A"], ["B"], ("A",)), (["A"], ["A"], ("A", "A")),
                                         (["A"], ["A"], ()), ("A", "A", ("A",)),
                                         ([None], ["A"], ("A",))]:
            with self.subTest(truth=truth, predicted=predicted):
                with self.assertRaises(ValueError):
                    classification_metrics(truth, predicted, labels)
        with self.assertRaises(ValueError):
            urgent_recall(["Urgent"], ["High"])

    def test_evaluate_records_and_adapter(self):
        rows = [{"id": "SYN-EVAL", "text": "Urgent hold", "expected_category": "Registration Holds", "expected_urgency": "High"}]
        calls = []
        def adapter(text):
            calls.append(text)
            return classify_request(text)
        result = evaluate_requests(rows, adapter)
        self.assertEqual(calls, ["Urgent hold"])
        self.assertEqual(result["category_exact_matches"], 1)
        self.assertEqual(result["urgent_recall"]["recall"], 1)

    def test_invalid_evaluation_rows(self):
        good = {"id": "SYN", "text": "", "expected_category": "Other/Needs Review", "expected_urgency": "Low"}
        for rows in ([], [{}], [None], [good, good], [dict(good, id=" ")], [dict(good, text=None)],
                     [dict(good, expected_category="Unknown")], [dict(good, expected_urgency="Urgent")]):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    evaluate_requests(rows)
