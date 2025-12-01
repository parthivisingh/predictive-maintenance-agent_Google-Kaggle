"""
Test Model Quality Evaluation
==============================

Test accuracy, stability, similarity quality, and ROI reliability evaluation.
"""

import pytest
import tempfile
import csv
from pathlib import Path

from src.evaluation.model_quality import (
    load_ground_truth,
    evaluate_accuracy,
    evaluate_stability,
    evaluate_similarity_quality,
    evaluate_roi_reliability,
    generate_quality_report
)


@pytest.fixture
def sample_results():
    """Sample results for testing."""
    return [
        {
            'sensor_id': 'A123',
            'anomaly_detected': True,
            'anomaly_metrics': {'anomaly_rate': 0.85},
            'roi_metrics': {'mean': 120.0},
            'research_metrics': {'similarity_hit_rate': 0.35}
        },
        {
            'sensor_id': 'B456',
            'anomaly_detected': False,
            'anomaly_metrics': {'anomaly_rate': 0.87},
            'roi_metrics': {'mean': 125.0},
            'research_metrics': {'similarity_hit_rate': 0.40}
        },
        {
            'sensor_id': 'C789',
            'anomaly_detected': True,
            'anomaly_metrics': {'anomaly_rate': 0.83},
            'roi_metrics': {'mean': 115.0},
            'research_metrics': {'similarity_hit_rate': 0.38}
        }
    ]


@pytest.fixture
def ground_truth_file():
    """Create temporary ground truth CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=['sensor_id', 'is_anomaly'])
        writer.writeheader()
        writer.writerow({'sensor_id': 'A123', 'is_anomaly': 'true'})
        writer.writerow({'sensor_id': 'B456', 'is_anomaly': 'false'})
        writer.writerow({'sensor_id': 'C789', 'is_anomaly': 'true'})
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


def test_load_ground_truth(ground_truth_file):
    """Test ground truth loading."""
    ground_truth = load_ground_truth(ground_truth_file)

    assert len(ground_truth) == 3
    assert ground_truth['A123'] is True
    assert ground_truth['B456'] is False
    assert ground_truth['C789'] is True


def test_load_ground_truth_nonexistent():
    """Test loading nonexistent ground truth."""
    ground_truth = load_ground_truth('/nonexistent/file.csv')

    assert len(ground_truth) == 0


def test_evaluate_accuracy(sample_results, ground_truth_file):
    """Test accuracy evaluation."""
    ground_truth = load_ground_truth(ground_truth_file)
    accuracy = evaluate_accuracy(sample_results, ground_truth)

    assert 0.0 <= accuracy <= 1.0
    # All predictions match ground truth
    assert accuracy == 1.0


def test_evaluate_accuracy_partial_match():
    """Test accuracy with partial matches."""
    results = [
        {'sensor_id': 'A123', 'anomaly_detected': True},
        {'sensor_id': 'B456', 'anomaly_detected': True}  # Incorrect
    ]

    ground_truth = {
        'A123': True,
        'B456': False
    }

    accuracy = evaluate_accuracy(results, ground_truth)

    assert accuracy == 0.5


def test_evaluate_accuracy_no_ground_truth():
    """Test accuracy without ground truth."""
    accuracy = evaluate_accuracy([{'sensor_id': 'A123'}], {})

    assert accuracy == 0.0


def test_evaluate_stability(sample_results):
    """Test stability evaluation."""
    stability = evaluate_stability(sample_results)

    assert 'anomaly_rate' in stability
    assert 'roi' in stability
    assert 'anomaly_stability_score' in stability
    assert 'roi_stability_score' in stability
    assert 'overall_stability_score' in stability

    # Check ranges
    assert 0.0 <= stability['overall_stability_score'] <= 1.0
    assert stability['run_count'] == 3

    # Check statistics
    anomaly_stats = stability['anomaly_rate']
    assert 'mean' in anomaly_stats
    assert 'std' in anomaly_stats
    assert 'variance' in anomaly_stats


def test_evaluate_stability_single_result():
    """Test stability with single result."""
    results = [{
        'anomaly_metrics': {'anomaly_rate': 0.85},
        'roi_metrics': {'mean': 120.0}
    }]

    stability = evaluate_stability(results)

    # Should have perfect stability with single value
    assert stability['anomaly_rate']['variance'] == 0.0


def test_evaluate_stability_empty():
    """Test stability with no results."""
    stability = evaluate_stability([])

    assert stability['overall_stability_score'] == 0.0


def test_evaluate_similarity_quality(sample_results):
    """Test similarity quality evaluation."""
    quality = evaluate_similarity_quality(sample_results)

    assert 0.0 <= quality <= 1.0
    assert quality > 0


def test_evaluate_similarity_quality_empty():
    """Test similarity quality with no results."""
    quality = evaluate_similarity_quality([])

    assert quality == 0.0


def test_evaluate_roi_reliability(sample_results):
    """Test ROI reliability evaluation."""
    reliability = evaluate_roi_reliability(sample_results)

    assert 'reliability_score' in reliability
    assert 'mean' in reliability
    assert 'median' in reliability
    assert 'std' in reliability
    assert 'outlier_count' in reliability
    assert 'outliers' in reliability
    assert 'distribution' in reliability

    assert 0.0 <= reliability['reliability_score'] <= 1.0


def test_evaluate_roi_reliability_with_outliers():
    """Test ROI reliability with outliers."""
    results = [
        {'roi_metrics': {'mean': 100.0}},
        {'roi_metrics': {'mean': 100.0}},
        {'roi_metrics': {'mean': 100.0}},
        {'roi_metrics': {'mean': 100.0}},
        {'roi_metrics': {'mean': 100.0}},
        {'roi_metrics': {'mean': 500.0}}  # Clear outlier (5x)
    ]

    reliability = evaluate_roi_reliability(results)

    assert reliability['outlier_count'] > 0
    assert 500.0 in reliability['outliers']


def test_evaluate_roi_reliability_empty():
    """Test ROI reliability with no results."""
    reliability = evaluate_roi_reliability([])

    assert reliability['reliability_score'] == 0.0
    assert reliability['outlier_count'] == 0


def test_generate_quality_report(sample_results, ground_truth_file):
    """Test complete quality report generation."""
    report = generate_quality_report(sample_results, ground_truth_file)

    assert 'timestamp' in report
    assert 'run_count' in report
    assert 'stability' in report
    assert 'similarity_quality' in report
    assert 'roi_reliability' in report
    assert 'accuracy' in report
    assert 'overall_quality_score' in report

    assert report['run_count'] == 3
    assert 0.0 <= report['overall_quality_score'] <= 1.0

    # Check accuracy section
    assert report['accuracy'] is not None
    assert 'score' in report['accuracy']


def test_generate_quality_report_no_ground_truth(sample_results):
    """Test quality report without ground truth."""
    report = generate_quality_report(sample_results, None)

    assert report['accuracy'] is None
    assert 'overall_quality_score' in report
