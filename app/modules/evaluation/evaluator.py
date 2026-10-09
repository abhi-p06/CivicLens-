from typing import List, Dict, Any, Optional, Sequence
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    silhouette_score
)

class CivicIntelligenceEvaluator:
    """
    Evaluation Support Suite for the Civic Issue Intelligence Platform.
    
    Computes rigorous empirical metrics strictly from actual ground-truth and prediction arrays:
    - Classification: Accuracy, Precision, Recall, Macro-F1, Weighted-F1
    - Priority Scoring: Mean Absolute Error (MAE), Top-K Precision/Recall
    - Spatial Clustering: Silhouette Score
    - Department Routing: Accuracy, Macro-F1
    - Text–Image Consistency: Accuracy, Precision, Recall, F1
    - Resolution Verification: Accuracy, Precision, Recall, F1
    
    POLICY: Zero synthetic/fabricated metric numbers. Calculates strictly from inputs.
    """

    @staticmethod
    def evaluate_classification(
        y_true: Sequence[str],
        y_pred: Sequence[str]
    ) -> Dict[str, float]:
        """Calculates multi-class classification metrics."""
        if not y_true or not y_pred or len(y_true) != len(y_pred):
            raise ValueError("y_true and y_pred must be non-empty sequences of equal length.")

        return {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "macro_precision": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "macro_recall": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "weighted_f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "sample_count": len(y_true)
        }

    @staticmethod
    def evaluate_priority(
        y_true_scores: Sequence[float],
        y_pred_scores: Sequence[float],
        top_k: int = 5
    ) -> Dict[str, float]:
        """Calculates Priority MAE and Top-K ranking overlap."""
        if len(y_true_scores) != len(y_pred_scores) or len(y_true_scores) == 0:
            raise ValueError("Arrays must be non-empty and equal length.")

        mae = float(mean_absolute_error(y_true_scores, y_pred_scores))

        # Top-K Precision / Recall: Compare the indices of highest priority issues
        n = len(y_true_scores)
        k = min(top_k, n)
        true_top_k_indices = set(np.argsort(y_true_scores)[-k:])
        pred_top_k_indices = set(np.argsort(y_pred_scores)[-k:])

        overlap = len(true_top_k_indices.intersection(pred_top_k_indices))
        top_k_precision = round(overlap / float(k), 4) if k > 0 else 0.0
        top_k_recall = round(overlap / float(k), 4) if k > 0 else 0.0

        return {
            "mae": round(mae, 4),
            "top_k": k,
            "top_k_precision": top_k_precision,
            "top_k_recall": top_k_recall,
            "sample_count": n
        }

    @staticmethod
    def evaluate_clustering(
        coordinates_rad: np.ndarray,
        cluster_labels: Sequence[int]
    ) -> Dict[str, Any]:
        """Calculates Silhouette Score for spatial clustering."""
        unique_labels = set(cluster_labels) - {-1}
        if len(unique_labels) < 2:
            return {
                "silhouette_score": None,
                "clusters_found": len(unique_labels),
                "status": "Insufficient clusters for silhouette calculation (requires >= 2 clusters)."
            }

        score = float(silhouette_score(coordinates_rad, cluster_labels, metric="haversine"))
        return {
            "silhouette_score": round(score, 4),
            "clusters_found": len(unique_labels),
            "total_points": len(cluster_labels)
        }

    @staticmethod
    def evaluate_department_routing(
        y_true_departments: Sequence[str],
        y_pred_departments: Sequence[str]
    ) -> Dict[str, float]:
        """Calculates routing accuracy and macro-F1 across municipal departments."""
        return {
            "accuracy": round(float(accuracy_score(y_true_departments, y_pred_departments)), 4),
            "macro_f1": round(float(f1_score(y_true_departments, y_pred_departments, average="macro", zero_division=0)), 4),
            "sample_count": len(y_true_departments)
        }

    @staticmethod
    def evaluate_text_image_consistency(
        y_true_levels: Sequence[str],
        y_pred_levels: Sequence[str]
    ) -> Dict[str, float]:
        """Evaluates multimodal evidence consistency classification."""
        return {
            "accuracy": round(float(accuracy_score(y_true_levels, y_pred_levels)), 4),
            "macro_precision": round(float(precision_score(y_true_levels, y_pred_levels, average="macro", zero_division=0)), 4),
            "macro_recall": round(float(recall_score(y_true_levels, y_pred_levels, average="macro", zero_division=0)), 4),
            "macro_f1": round(float(f1_score(y_true_levels, y_pred_levels, average="macro", zero_division=0)), 4),
            "sample_count": len(y_true_levels)
        }

    @staticmethod
    def evaluate_resolution_verification(
        y_true_resolution: Sequence[str],
        y_pred_resolution: Sequence[str]
    ) -> Dict[str, float]:
        """Evaluates issue closure / resolution verification accuracy."""
        return {
            "accuracy": round(float(accuracy_score(y_true_resolution, y_pred_resolution)), 4),
            "macro_precision": round(float(precision_score(y_true_resolution, y_pred_resolution, average="macro", zero_division=0)), 4),
            "macro_recall": round(float(recall_score(y_true_resolution, y_pred_resolution, average="macro", zero_division=0)), 4),
            "macro_f1": round(float(f1_score(y_true_resolution, y_pred_resolution, average="macro", zero_division=0)), 4),
            "sample_count": len(y_true_resolution)
        }

evaluator = CivicIntelligenceEvaluator()
