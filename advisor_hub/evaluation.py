"""Standard-library evaluation utilities; dataset independence is a study design duty."""
from collections import Counter
from collections.abc import Callable, Sequence
from advisor_hub.classifier import TriageResult, classify_request
from advisor_hub.management import CATEGORIES, URGENCIES


def _validated_pairs(truth: Sequence[str], predictions: Sequence[str], labels: Sequence[str]):
    if isinstance(truth, (str, bytes)) or isinstance(predictions, (str, bytes)):
        raise ValueError("Labels must be sequences, not a single string.")
    if not truth or len(truth) != len(predictions):
        raise ValueError("Expected nonempty, equal-length truth and prediction sequences.")
    if not labels or len(labels) != len(set(labels)):
        raise ValueError("Evaluation labels must be nonempty and unique.")
    pairs = list(zip(truth, predictions))
    if any(not isinstance(value, str) or value not in labels for pair in pairs for value in pair):
        raise ValueError("Unknown evaluation label.")
    return pairs


def classification_metrics(truth: Sequence[str], predictions: Sequence[str],
                           labels: Sequence[str] = CATEGORIES) -> dict:
    """Macro-F1 averages all declared classes; zero denominators produce zero.

    Absent classes remain in the macro average, with support zero. This policy
    is explicit so comparisons cannot silently drop difficult/absent categories.
    """
    pairs = _validated_pairs(truth, predictions, labels)
    counts = Counter(pairs)
    per_class = {}
    for label in labels:
        tp = counts[label, label]
        fp = sum(counts[actual, label] for actual in labels if actual != label)
        fn = sum(counts[label, predicted] for predicted in labels if predicted != label)
        per_class[label] = {
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
            "support": tp + fn, "tp": tp, "fp": fp, "fn": fn,
        }
    return {
        "sample_count": len(pairs),
        "macro_f1": sum(row["f1"] for row in per_class.values()) / len(labels),
        "zero_division_policy": "0; all declared labels included",
        "per_class": per_class,
        "confusion_matrix": {actual: {predicted: counts[actual, predicted] for predicted in labels}
                             for actual in labels},
    }


def urgent_recall(truth: Sequence[str], predictions: Sequence[str]) -> dict:
    """High is the urgent positive class. No labeled High examples means undefined."""
    pairs = _validated_pairs(truth, predictions, URGENCIES)
    tp = sum(actual == "High" and predicted == "High" for actual, predicted in pairs)
    fn = sum(actual == "High" and predicted != "High" for actual, predicted in pairs)
    return {"positive_label": "High", "true_positives": tp, "false_negatives": fn,
            "urgent_support": tp + fn, "recall": tp / (tp + fn) if tp + fn else None}


def evaluate_requests(rows: Sequence[dict],
                      predictor: Callable[[str], TriageResult] = classify_request) -> dict:
    """Evaluate labeled rows. Caller must separately document provenance and splits.

    Each row needs unique id, text, expected_category, expected_urgency.
    A future classifier adapter can return the same TriageResult contract.
    """
    if not rows:
        raise ValueError("Evaluation dataset is empty.")
    required = ("id", "text", "expected_category", "expected_urgency")
    if any(not isinstance(row, dict) or any(key not in row or not isinstance(row[key], str)
                                          for key in required) for row in rows):
        raise ValueError("Rows need string id, text, expected_category, expected_urgency.")
    if any(not row["id"].strip() for row in rows) or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Evaluation IDs must be nonempty and unique.")
    results = [predictor(row["text"]) for row in rows]
    category_truth = [row["expected_category"] for row in rows]
    urgency_truth = [row["expected_urgency"] for row in rows]
    category_predictions = [result.category for result in results]
    urgency_predictions = [result.urgency for result in results]
    return {
        "category": classification_metrics(category_truth, category_predictions),
        "urgency": classification_metrics(urgency_truth, urgency_predictions, URGENCIES),
        "urgent_recall": urgent_recall(urgency_truth, urgency_predictions),
        "category_exact_matches": sum(a == b for a, b in zip(category_truth, category_predictions)),
        "urgency_exact_matches": sum(a == b for a, b in zip(urgency_truth, urgency_predictions)),
    }
