"""
Test Metrics Summary
====================

Test cross-run metrics aggregation and stability computation.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.observability.metrics_summary import (
    load_metrics,
    compute_stability,
    generate_summary,
    find_all_metrics_files,
    generate_observability_summary
)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create run directories with metrics
        for i in range(3):
            run_dir = output_dir / f'run{i+1}'
            run_dir.mkdir()

            metrics = {
                'anomaly_metrics': {
                    'anomaly_rate': 0.8 + i * 0.05,
                    'total_anomalies': 8 + i,
                    'total_normal': 2 - i
                },
                'execution': {
                    'success_rate': 1.0,
                    'total_runs': 10,
                    'successful_runs': 10,
                    'failed_runs': 0,
                    'duration_sec': 5.0 + i * 0.5
                },
                'performance_metrics': {
                    'avg_duration_sec': 0.5 + i * 0.1,
                    'min_duration_sec': 0.3,
                    'max_duration_sec': 1.0 + i * 0.2
                },
                'priority_metrics': {
                    'critical': i,
                    'high': 2 + i,
                    'medium': 5,
                    'low': 3 - i
                },
                'research_metrics': {
                    'similarity_hit_rate': 0.3 + i * 0.1,
                    'avg_similarity_hits': 3.0 + i
                },
                'roi_metrics': {
                    'mean': 100.0 + i * 10,
                    'median': 95.0 + i * 10,
                    'min': 50.0,
                    'max': 150.0 + i * 20,
                    'std': 20.0 + i * 2
                },
                'timestamp': f'2025-12-01T10:0{i}:00Z'
            }

            with open(run_dir / 'metrics.json', 'w') as f:
                json.dump(metrics, f)

        yield output_dir


def test_load_metrics_from_files(temp_output_dir):
    """Test loading metrics from file paths."""
    metrics_files = [
        str(temp_output_dir / 'run1' / 'metrics.json'),
        str(temp_output_dir / 'run2' / 'metrics.json')
    ]

    metrics_list = load_metrics(metrics_files)

    assert len(metrics_list) == 2
    assert all('anomaly_metrics' in m for m in metrics_list)
    assert all('execution' in m for m in metrics_list)


def test_load_metrics_from_directories(temp_output_dir):
    """Test loading metrics from directory paths."""
    run_dirs = [
        str(temp_output_dir / 'run1'),
        str(temp_output_dir / 'run2')
    ]

    metrics_list = load_metrics(run_dirs)

    assert len(metrics_list) == 2


def test_find_all_metrics_files(temp_output_dir):
    """Test finding all metrics files in directory."""
    metrics_files = find_all_metrics_files(str(temp_output_dir))

    assert len(metrics_files) == 3
    assert all('metrics.json' in str(f) for f in metrics_files)


def test_compute_stability(temp_output_dir):
    """Test stability computation."""
    metrics_files = find_all_metrics_files(str(temp_output_dir))
    metrics_list = load_metrics(metrics_files)

    stability = compute_stability(metrics_list)

    assert 'anomaly_rate' in stability
    assert 'roi' in stability
    assert 'success_rate' in stability
    assert 'run_count' in stability

    assert stability['run_count'] == 3

    # Check anomaly rate stability
    anomaly_stability = stability['anomaly_rate']
    assert 'mean' in anomaly_stability
    assert 'std' in anomaly_stability
    assert 'variance' in anomaly_stability
    assert 'stability_score' in anomaly_stability
    assert 0 <= anomaly_stability['stability_score'] <= 1


def test_compute_stability_empty():
    """Test stability with no metrics."""
    stability = compute_stability([])

    assert stability['anomaly_rate']['stability_score'] == 0.0
    assert stability['roi']['stability_score'] == 0.0


def test_compute_stability_single():
    """Test stability with single metric."""
    metrics = [{
        'anomaly_metrics': {'anomaly_rate': 0.8},
        'roi_metrics': {'mean': 100.0},
        'execution': {'success_rate': 1.0}
    }]

    stability = compute_stability(metrics)

    # Single value should have perfect stability
    assert stability['anomaly_rate']['stability_score'] == 1.0


def test_generate_summary(temp_output_dir):
    """Test summary generation."""
    metrics_files = find_all_metrics_files(str(temp_output_dir))
    metrics_list = load_metrics(metrics_files)

    summary = generate_summary(metrics_list)

    assert summary['run_count'] == 3
    assert 'anomaly_metrics' in summary
    assert 'execution' in summary
    assert 'performance' in summary
    assert 'priority' in summary
    assert 'research' in summary
    assert 'roi' in summary

    # Check anomaly metrics structure
    anomaly = summary['anomaly_metrics']['anomaly_rate']
    assert 'mean' in anomaly
    assert 'median' in anomaly
    assert 'min' in anomaly
    assert 'max' in anomaly


def test_generate_summary_empty():
    """Test summary with no metrics."""
    summary = generate_summary([])

    assert summary['run_count'] == 0


def test_generate_observability_summary(temp_output_dir):
    """Test complete observability summary generation."""
    summary = generate_observability_summary(str(temp_output_dir))

    assert 'cross_run_stats' in summary
    assert 'stability_scores' in summary
    assert 'metrics_files_analyzed' in summary
    assert 'output_dir' in summary
    assert 'timestamp' in summary

    assert summary['metrics_files_analyzed'] == 3

    # Verify cross-run stats
    cross_run = summary['cross_run_stats']
    assert cross_run['run_count'] == 3

    # Verify stability scores
    stability = summary['stability_scores']
    assert 'anomaly_rate' in stability
    assert 'roi' in stability


def test_generate_observability_summary_empty():
    """Test observability summary with empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        summary = generate_observability_summary(tmpdir)

        assert 'error' in summary
        assert summary['metrics_files_found'] == 0
