"""
ML Model Calibration and Threshold Optimization
================================================

Reduces false positive rates by:
1. Calibrating anomaly score thresholds
2. Cross-validating on labeled data
3. Optimizing precision/recall tradeoff
"""

import numpy as np
from typing import Dict, Tuple, Optional
from sklearn.metrics import roc_curve, precision_recall_curve, auc
import logging

logger = logging.getLogger(__name__)


class ModelCalibrator:
    """Calibrates anomaly detection models."""

    def __init__(self, target_false_positive_rate: float = 0.15):
        """
        Initialize calibrator.

        Parameters:
        -----------
        target_false_positive_rate : float
            Target FPR (default: 15%)
        """
        self.target_fpr = target_false_positive_rate
        self.optimal_threshold = None
        self.calibration_curve = None

    def calibrate_threshold(
        self,
        model,
        X_val,
        y_val_true
    ) -> float:
        """
        Find optimal anomaly score threshold.

        Parameters:
        -----------
        model : Trained IsolationForest or similar
            Model with decision_function method
        X_val : array-like
            Validation data
        y_val_true : array-like
            True labels (1=normal, -1=anomaly)

        Returns:
        --------
        float : Optimal threshold
        """
        # Get decision scores
        scores = model.decision_function(X_val)

        # Convert labels to binary (1=positive class=normal, 0=negative class=anomaly)
        y_binary = (y_val_true == 1).astype(int)

        # Calculate FPR/TPR at various thresholds
        # Note: sklearn's roc_curve expects positive class to be 1
        # For anomaly detection, we want low scores to indicate anomalies
        # So we negate the scores
        fpr, tpr, thresholds = roc_curve(
            y_binary,
            -scores  # Negative because lower scores = more anomalous
        )

        # Store calibration curve
        self.calibration_curve = {
            'fpr': fpr,
            'tpr': tpr,
            'thresholds': thresholds
        }

        # Find threshold closest to target FPR
        idx = np.argmin(np.abs(fpr - self.target_fpr))
        self.optimal_threshold = thresholds[idx]

        logger.info(f"Optimal threshold: {self.optimal_threshold:.4f}")
        logger.info(f"  FPR: {fpr[idx]:.3f}")
        logger.info(f"  TPR: {tpr[idx]:.3f}")

        # Calculate AUC
        roc_auc = auc(fpr, tpr)
        logger.info(f"  ROC AUC: {roc_auc:.3f}")

        return self.optimal_threshold

    def validate_model(
        self,
        model,
        X_test,
        y_test_true
    ) -> Dict[str, float]:
        """
        Calculate validation metrics.

        Parameters:
        -----------
        model : Trained model
        X_test : array-like
            Test data
        y_test_true : array-like
            True labels (1=normal, -1=anomaly)

        Returns:
        --------
        Dict with precision, recall, f1, fpr, etc.
        """
        predictions = model.predict(X_test)

        # Calculate confusion matrix components
        true_positives = np.sum((predictions == -1) & (y_test_true == -1))
        false_positives = np.sum((predictions == -1) & (y_test_true == 1))
        true_negatives = np.sum((predictions == 1) & (y_test_true == 1))
        false_negatives = np.sum((predictions == 1) & (y_test_true == -1))

        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0
        specificity = true_negatives / (true_negatives + false_positives) if (true_negatives + false_positives) > 0 else 0

        # Calculate accuracy
        accuracy = (true_positives + true_negatives) / len(y_test_true)

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "accuracy": round(accuracy, 4),
            "false_positive_rate": round(fpr, 4),
            "specificity": round(specificity, 4),
            "true_positives": int(true_positives),
            "false_positives": int(false_positives),
            "true_negatives": int(true_negatives),
            "false_negatives": int(false_negatives)
        }

    def apply_threshold(
        self,
        scores: np.ndarray,
        threshold: Optional[float] = None
    ) -> np.ndarray:
        """
        Apply threshold to decision scores.

        Parameters:
        -----------
        scores : np.ndarray
            Decision function scores
        threshold : float, optional
            Threshold to apply. If None, uses optimal_threshold

        Returns:
        --------
        np.ndarray : Predictions (1=normal, -1=anomaly)
        """
        if threshold is None:
            if self.optimal_threshold is None:
                raise ValueError("No threshold set. Run calibrate_threshold first.")
            threshold = self.optimal_threshold

        # Lower scores (more negative) indicate anomalies
        # So we predict -1 when score < -threshold
        predictions = np.where(scores < -threshold, -1, 1)
        return predictions

    def get_score_percentile(
        self,
        scores: np.ndarray,
        percentile: float
    ) -> float:
        """
        Get score threshold at given percentile.

        Parameters:
        -----------
        scores : np.ndarray
            Decision function scores
        percentile : float
            Percentile (0-100)

        Returns:
        --------
        float : Score threshold
        """
        return np.percentile(scores, percentile)

    def calculate_precision_recall_curve(
        self,
        model,
        X_val,
        y_val_true
    ) -> Dict[str, np.ndarray]:
        """
        Calculate precision-recall curve.

        Parameters:
        -----------
        model : Trained model
        X_val : array-like
            Validation data
        y_val_true : array-like
            True labels (1=normal, -1=anomaly)

        Returns:
        --------
        Dict with precision, recall, thresholds
        """
        # Get decision scores
        scores = model.decision_function(X_val)

        # Convert labels to binary (1=anomaly, 0=normal for PR curve)
        y_binary = (y_val_true == -1).astype(int)

        # Calculate precision-recall curve
        precision, recall, thresholds = precision_recall_curve(
            y_binary,
            -scores  # Negative because lower scores = anomalies
        )

        # Calculate F1 scores
        f1_scores = 2 * (precision * recall) / (precision + recall)
        f1_scores = np.nan_to_num(f1_scores)

        # Find best F1 threshold
        best_f1_idx = np.argmax(f1_scores)

        return {
            'precision': precision,
            'recall': recall,
            'thresholds': thresholds,
            'f1_scores': f1_scores,
            'best_f1_threshold': thresholds[best_f1_idx] if len(thresholds) > best_f1_idx else 0,
            'best_f1_score': f1_scores[best_f1_idx]
        }

    def adjust_threshold_for_cost(
        self,
        false_positive_cost: float,
        false_negative_cost: float,
        fpr_array: Optional[np.ndarray] = None,
        tpr_array: Optional[np.ndarray] = None,
        thresholds: Optional[np.ndarray] = None
    ) -> float:
        """
        Find optimal threshold based on cost of errors.

        Parameters:
        -----------
        false_positive_cost : float
            Cost of false positive (unnecessary maintenance)
        false_negative_cost : float
            Cost of false negative (missed failure)
        fpr_array : np.ndarray, optional
            False positive rates (uses calibration curve if None)
        tpr_array : np.ndarray, optional
            True positive rates (uses calibration curve if None)
        thresholds : np.ndarray, optional
            Thresholds (uses calibration curve if None)

        Returns:
        --------
        float : Optimal threshold
        """
        if self.calibration_curve is None:
            raise ValueError("No calibration curve available. Run calibrate_threshold first.")

        if fpr_array is None:
            fpr_array = self.calibration_curve['fpr']
        if tpr_array is None:
            tpr_array = self.calibration_curve['tpr']
        if thresholds is None:
            thresholds = self.calibration_curve['thresholds']

        # Calculate expected cost for each threshold
        # FNR = 1 - TPR
        fnr_array = 1 - tpr_array
        expected_costs = (fpr_array * false_positive_cost +
                         fnr_array * false_negative_cost)

        # Find threshold with minimum expected cost
        min_cost_idx = np.argmin(expected_costs)
        optimal_threshold = thresholds[min_cost_idx]

        logger.info(f"Cost-optimal threshold: {optimal_threshold:.4f}")
        logger.info(f"  FPR: {fpr_array[min_cost_idx]:.3f}")
        logger.info(f"  TPR: {tpr_array[min_cost_idx]:.3f}")
        logger.info(f"  Expected cost: {expected_costs[min_cost_idx]:.2f}")

        return optimal_threshold


def create_synthetic_validation_set(
    normal_samples: np.ndarray,
    contamination: float = 0.1,
    anomaly_multiplier: float = 2.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create synthetic validation set with known anomalies.

    Parameters:
    -----------
    normal_samples : np.ndarray
        Normal samples
    contamination : float
        Fraction of anomalies to inject
    anomaly_multiplier : float
        How much to scale anomalies

    Returns:
    --------
    Tuple[X, y] : Validation data and labels
    """
    n_samples = len(normal_samples)
    n_anomalies = int(n_samples * contamination)
    n_normal = n_samples - n_anomalies

    # Create normal samples
    X_normal = normal_samples[:n_normal]
    y_normal = np.ones(n_normal)

    # Create anomalies by scaling some samples
    anomaly_indices = np.random.choice(len(normal_samples), n_anomalies, replace=False)
    X_anomalies = normal_samples[anomaly_indices] * anomaly_multiplier
    y_anomalies = -np.ones(n_anomalies)

    # Combine
    X_val = np.vstack([X_normal, X_anomalies])
    y_val = np.concatenate([y_normal, y_anomalies])

    # Shuffle
    shuffle_idx = np.random.permutation(len(X_val))
    X_val = X_val[shuffle_idx]
    y_val = y_val[shuffle_idx]

    return X_val, y_val


def evaluate_model_stability(
    model,
    X_test,
    y_test,
    n_iterations: int = 10
) -> Dict[str, float]:
    """
    Evaluate model stability across multiple runs.

    Parameters:
    -----------
    model : Trained model
    X_test : array-like
        Test data
    y_test : array-like
        Test labels
    n_iterations : int
        Number of evaluation iterations

    Returns:
    --------
    Dict with mean and std of metrics
    """
    calibrator = ModelCalibrator()
    results = []

    for i in range(n_iterations):
        # Add small noise to test data
        X_noisy = X_test + np.random.normal(0, 0.01, X_test.shape)

        # Evaluate
        metrics = calibrator.validate_model(model, X_noisy, y_test)
        results.append(metrics)

    # Calculate statistics
    stats = {}
    for key in results[0].keys():
        if isinstance(results[0][key], (int, float)):
            values = [r[key] for r in results]
            stats[f"{key}_mean"] = np.mean(values)
            stats[f"{key}_std"] = np.std(values)

    return stats
