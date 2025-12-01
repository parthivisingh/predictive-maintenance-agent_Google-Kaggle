"""
Model Quality Evaluation
=========================

Evaluate predictive quality, anomaly stability, similarity hit-rate,
and ROI reliability from Phase 5 simulation outputs.
"""

import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Optional
import statistics
from datetime import datetime

logger = logging.getLogger(__name__)


def load_ground_truth(ground_truth_path: str) -> Dict[str, bool]:
    """
    Load ground truth CSV file.

    Expected format: sensor_id, is_anomaly

    Parameters:
    -----------
    ground_truth_path : str
        Path to ground truth CSV file

    Returns:
    --------
    Dict[str, bool]
        Dictionary mapping sensor IDs to anomaly status
    """
    ground_truth = {}

    try:
        with open(ground_truth_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sensor_id = row.get('sensor_id') or row.get('id')
                is_anomaly = row.get('is_anomaly', 'false').lower() in ['true', '1', 'yes']
                ground_truth[sensor_id] = is_anomaly
    except Exception as e:
        logger.error(f"Error loading ground truth: {e}")

    return ground_truth


def evaluate_accuracy(results: List[Dict], ground_truth: Dict) -> float:
    """
    Compute accuracy if ground-truth CSV provided.

    Parameters:
    -----------
    results : List[Dict]
        List of prediction results from batch processing
    ground_truth : Dict
        Ground truth dictionary from load_ground_truth()

    Returns:
    --------
    float
        Accuracy score (0.0 to 1.0)
    """
    if not ground_truth or not results:
        logger.warning("No ground truth or results provided")
        return 0.0

    correct = 0
    total = 0

    for result in results:
        sensor_id = result.get('sensor_id') or result.get('id')
        if sensor_id not in ground_truth:
            continue

        predicted_anomaly = result.get('anomaly_detected', False)
        actual_anomaly = ground_truth[sensor_id]

        if predicted_anomaly == actual_anomaly:
            correct += 1
        total += 1

    accuracy = correct / total if total > 0 else 0.0
    return accuracy


def evaluate_stability(results: List[Dict]) -> Dict:
    """
    Compute anomaly rate variance, ROI stddev across seeds.

    Parameters:
    -----------
    results : List[Dict]
        List of results from multiple runs (with different seeds)

    Returns:
    --------
    Dict
        Stability metrics including variance and standard deviation
    """
    if not results:
        return {
            'anomaly_rate': {'variance': 0.0, 'std': 0.0, 'mean': 0.0},
            'roi': {'variance': 0.0, 'std': 0.0, 'mean': 0.0},
            'anomaly_stability_score': 0.0,
            'roi_stability_score': 0.0,
            'overall_stability_score': 0.0,
            'run_count': 0
        }

    # Extract anomaly rates
    anomaly_rates = []
    roi_values = []

    for result in results:
        # Handle both direct metrics and nested structures
        if 'anomaly_metrics' in result:
            anomaly_rate = result['anomaly_metrics'].get('anomaly_rate', 0.0)
        else:
            anomaly_rate = result.get('anomaly_rate', 0.0)

        anomaly_rates.append(anomaly_rate)

        # Extract ROI
        if 'roi_metrics' in result:
            roi = result['roi_metrics'].get('mean', 0.0)
        else:
            roi = result.get('roi', 0.0)

        roi_values.append(roi)

    def calc_variance_stats(values: List[float]) -> Dict:
        """Calculate variance statistics."""
        if len(values) <= 1:
            return {
                'mean': values[0] if values else 0.0,
                'std': 0.0,
                'variance': 0.0,
                'min': values[0] if values else 0.0,
                'max': values[0] if values else 0.0
            }

        return {
            'mean': statistics.mean(values),
            'std': statistics.stdev(values),
            'variance': statistics.variance(values),
            'min': min(values),
            'max': max(values)
        }

    anomaly_stats = calc_variance_stats(anomaly_rates)
    roi_stats = calc_variance_stats(roi_values)

    # Calculate overall stability score (0-1, higher is more stable)
    # Using coefficient of variation (CV) inverted
    anomaly_cv = anomaly_stats['std'] / anomaly_stats['mean'] if anomaly_stats['mean'] != 0 else 0
    roi_cv = roi_stats['std'] / abs(roi_stats['mean']) if roi_stats['mean'] != 0 else 0

    # Normalize CV to stability score (1 = stable, 0 = unstable)
    anomaly_stability = max(0.0, 1.0 - min(1.0, anomaly_cv))
    roi_stability = max(0.0, 1.0 - min(1.0, roi_cv))

    overall_stability = (anomaly_stability + roi_stability) / 2

    return {
        'anomaly_rate': anomaly_stats,
        'roi': roi_stats,
        'anomaly_stability_score': anomaly_stability,
        'roi_stability_score': roi_stability,
        'overall_stability_score': overall_stability,
        'run_count': len(results)
    }


def evaluate_similarity_quality(results: List[Dict]) -> float:
    """
    Compute similarity hit-rate stability.

    Parameters:
    -----------
    results : List[Dict]
        List of results from multiple runs

    Returns:
    --------
    float
        Similarity quality score (0.0 to 1.0)
    """
    if not results:
        return 0.0

    similarity_rates = []

    for result in results:
        # Handle nested structure
        if 'research_metrics' in result:
            hit_rate = result['research_metrics'].get('similarity_hit_rate', 0.0)
        else:
            hit_rate = result.get('similarity_hit_rate', 0.0)

        similarity_rates.append(hit_rate)

    if not similarity_rates:
        return 0.0

    # Quality is based on mean hit rate and stability
    mean_rate = statistics.mean(similarity_rates)

    if len(similarity_rates) > 1:
        std_rate = statistics.stdev(similarity_rates)
        cv = std_rate / mean_rate if mean_rate != 0 else 0
        stability = max(0.0, 1.0 - min(1.0, cv))
    else:
        stability = 1.0

    # Quality score combines both rate and stability
    quality_score = (mean_rate + stability) / 2

    return quality_score


def evaluate_roi_reliability(results: List[Dict]) -> Dict:
    """
    Evaluate ROI reliability with outlier detection.

    Parameters:
    -----------
    results : List[Dict]
        List of results from multiple runs

    Returns:
    --------
    Dict
        ROI reliability metrics
    """
    if not results:
        return {
            'reliability_score': 0.0,
            'outlier_count': 0,
            'outliers': [],
            'distribution': {}
        }

    roi_values = []

    for result in results:
        if 'roi_metrics' in result:
            roi = result['roi_metrics'].get('mean', 0.0)
        else:
            roi = result.get('roi', 0.0)

        roi_values.append(roi)

    if not roi_values:
        return {
            'reliability_score': 0.0,
            'outlier_count': 0,
            'outliers': [],
            'distribution': {}
        }

    # Calculate statistics
    mean_roi = statistics.mean(roi_values)
    median_roi = statistics.median(roi_values)

    if len(roi_values) > 1:
        std_roi = statistics.stdev(roi_values)

        # Detect outliers (beyond 2 standard deviations)
        outliers = [roi for roi in roi_values if abs(roi - mean_roi) > 2 * std_roi]
        outlier_count = len(outliers)

        # Reliability score (lower variance = higher reliability)
        cv = std_roi / abs(mean_roi) if mean_roi != 0 else 0
        reliability = max(0.0, 1.0 - min(1.0, cv))
    else:
        std_roi = 0.0
        outliers = []
        outlier_count = 0
        reliability = 1.0

    return {
        'reliability_score': reliability,
        'mean': mean_roi,
        'median': median_roi,
        'std': std_roi,
        'min': min(roi_values),
        'max': max(roi_values),
        'outlier_count': outlier_count,
        'outliers': sorted(outliers, reverse=True),
        'distribution': {
            'count': len(roi_values),
            'range': max(roi_values) - min(roi_values)
        }
    }


def generate_quality_report(
    results: List[Dict],
    ground_truth_path: Optional[str] = None
) -> Dict:
    """
    Generate comprehensive model quality report.

    Parameters:
    -----------
    results : List[Dict]
        List of results from multiple runs
    ground_truth_path : str, optional
        Path to ground truth CSV file

    Returns:
    --------
    Dict
        Complete quality evaluation report
    """
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'run_count': len(results),
        'stability': evaluate_stability(results),
        'similarity_quality': evaluate_similarity_quality(results),
        'roi_reliability': evaluate_roi_reliability(results)
    }

    # Add accuracy if ground truth provided
    if ground_truth_path:
        try:
            ground_truth = load_ground_truth(ground_truth_path)
            accuracy = evaluate_accuracy(results, ground_truth)
            report['accuracy'] = {
                'score': accuracy,
                'ground_truth_samples': len(ground_truth)
            }
        except Exception as e:
            logger.error(f"Error evaluating accuracy: {e}")
            report['accuracy'] = {
                'error': str(e)
            }
    else:
        report['accuracy'] = None

    # Calculate overall quality score
    scores = [
        report['stability']['overall_stability_score'],
        report['similarity_quality'],
        report['roi_reliability']['reliability_score']
    ]

    if report['accuracy']:
        scores.append(report['accuracy']['score'])

    report['overall_quality_score'] = statistics.mean(scores)

    return report
