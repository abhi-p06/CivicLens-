import json
from pathlib import Path
import pytest
from app.modules.evaluation.evaluator import evaluator
from app.modules.nlp.classifier import CIVIC_TRAINING_CORPUS, nlp_classifier
from app.models.issue import IssueCategory, IssueCreate, ResolutionStatus
from app.core.pipeline import pipeline
from scripts.evaluate_resolution_verification import DEFAULT_BENCHMARK_PAIRS, run_evaluation

def test_nlp_training_and_heldout_split_integrity():
    """
    Verify that held-out test examples in seed_issues were NOT part of the training corpus,
    ensuring evaluation provenance and preventing data leakage.
    """
    training_texts = [text.strip().lower() for text, _ in CIVIC_TRAINING_CORPUS]
    assert len(training_texts) == 27

    seed_path = Path("data/seed_issues.json")
    assert seed_path.exists()
    with open(seed_path, "r", encoding="utf-8") as f:
        seed_data = json.load(f)

    # Assert 0% text overlap between training corpus and seed evaluation records
    for issue in seed_data:
        complaint = issue["complaintText"].strip().lower()
        assert complaint not in training_texts, f"Data leakage detected: '{complaint}' is in training corpus!"

    # Test that model still predicts correct categories for unseen seed examples
    for issue in seed_data[:3]:
        cat, conf, mode = nlp_classifier.predict_category(issue["complaintText"])
        assert cat.value == issue["category"]


def test_text_image_consistency_manifest_integrity():
    """
    Verify the text-image consistency evaluation manifest:
    - Contains distinct classes: CONSISTENT, INCONSISTENT, MANUAL REVIEW, MISSING_EVIDENCE
    - Supervised metrics calculated strictly on eligible pairs
    - Missing evidence and manual review rates tracked separately
    """
    manifest_path = Path("data/evaluation/text_image_consistency_manifest.json")
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    eligible_pairs = [item for item in manifest if item.get("evidence_status") != "MISSING_EVIDENCE"]
    missing_items = [item for item in manifest if item.get("evidence_status") == "MISSING_EVIDENCE"]

    assert len(eligible_pairs) == 6
    assert len(missing_items) == 1

    y_true = [item["ground_truth"] for item in eligible_pairs]
    y_pred = [
        pipeline.analyze(IssueCreate(
            complaintText=item["complaintText"],
            imageUrl=item.get("image_path")
        ))["consistencyFlag"]
        for item in eligible_pairs
    ]

    metrics = evaluator.evaluate_text_image_consistency(
        y_true,
        y_pred,
        missing_evidence_count=len(missing_items)
    )

    # Supervised metrics on eligible pairs
    assert metrics["accuracy"] >= 0.80
    assert metrics["sample_count"] == 6
    assert "per_class" in metrics
    assert "confusion_matrix" in metrics
    assert len(metrics["confusion_matrix"]) == 3  # 3 classes: CONSISTENT, INCONSISTENT, MANUAL REVIEW
    assert metrics["manual_review_count"] >= 1
    assert metrics["manual_review_rate"] > 0.0
    assert metrics["missing_evidence_count"] == 1
    assert metrics["missing_evidence_rate"] > 0.0


def test_resolution_verification_controlled_benchmark_integrity():
    """
    Verify the controlled resolution benchmark:
    - Exactly 5 reference fixture pairs
    - Failed/corrupt images NEVER produce false resolution (LIKELY_RESOLVED)
    - Ambiguous framing produces MANUAL_VERIFICATION
    """
    assert len(DEFAULT_BENCHMARK_PAIRS) == 5

    res = run_evaluation(DEFAULT_BENCHMARK_PAIRS, verbose=False)
    results = res["results"]

    for record in results:
        gt = record["ground_truth"]
        status = record["automated_status"]

        if gt == "RESOLVED":
            assert status == "LIKELY_RESOLVED"
        elif gt == "UNRESOLVED":
            assert status == "STILL_PRESENT"
        elif gt == "AMBIGUOUS":
            assert status == "REQUIRES_MANUAL_VERIFICATION"
            # Crucial safety check: Ambiguous/corrupt cases must never be marked LIKELY_RESOLVED
            assert status != "LIKELY_RESOLVED"

    # Verify contingency table metrics
    assert res["total_pairs"] == 5
    assert res["metrics"]["precision"] == 1.0
    assert res["metrics"]["recall"] == 1.0
    assert res["metrics"]["manual_review_rate"] == 0.6
    assert res["metrics"]["expected_match_accuracy"] == 1.0
