"""
Test CLI Smoke Tests
====================

Smoke tests for observability and evaluation CLI tools.
"""

import pytest
import subprocess
import sys
import json
import tempfile
from pathlib import Path


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory with sample metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create a run directory with metrics
        run_dir = output_dir / 'run1'
        run_dir.mkdir()

        metrics = {
            'anomaly_metrics': {
                'anomaly_rate': 0.8,
                'total_anomalies': 8,
                'total_normal': 2
            },
            'execution': {
                'success_rate': 1.0,
                'total_runs': 10,
                'successful_runs': 10,
                'failed_runs': 0,
                'duration_sec': 5.0
            },
            'performance_metrics': {
                'avg_duration_sec': 0.5,
                'min_duration_sec': 0.3,
                'max_duration_sec': 1.0
            },
            'priority_metrics': {
                'critical': 0,
                'high': 2,
                'medium': 5,
                'low': 3
            },
            'research_metrics': {
                'similarity_hit_rate': 0.3,
                'avg_similarity_hits': 3.0
            },
            'roi_metrics': {
                'mean': 100.0,
                'median': 95.0,
                'min': 50.0,
                'max': 150.0,
                'std': 20.0
            },
            'timestamp': '2025-12-01T10:00:00Z'
        }

        with open(run_dir / 'metrics.json', 'w') as f:
            json.dump(metrics, f)

        yield output_dir


def test_observability_cli_help():
    """Test observability CLI --help."""
    result = subprocess.run(
        [sys.executable, 'scripts/run_observability_check.py', '--help'],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert 'observability' in result.stdout.lower()


def test_observability_cli_basic(temp_output_dir):
    """Test basic observability CLI execution."""
    result = subprocess.run(
        [
            sys.executable,
            'scripts/run_observability_check.py',
            '--output-dir', str(temp_output_dir)
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Should complete without errors
    assert result.returncode == 0

    # Check output files exist
    assert (temp_output_dir / 'observability_report.json').exists()
    assert (temp_output_dir / 'observability_report.md').exists()

    # Validate JSON structure
    with open(temp_output_dir / 'observability_report.json') as f:
        report = json.load(f)

    assert 'timestamp' in report
    assert 'metrics_summary' in report


def test_observability_cli_with_grafana(temp_output_dir):
    """Test observability CLI with Grafana export."""
    result = subprocess.run(
        [
            sys.executable,
            'scripts/run_observability_check.py',
            '--output-dir', str(temp_output_dir),
            '--grafana'
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0

    # Check Grafana dashboard exists
    assert (temp_output_dir / 'grafana_dashboard.json').exists()


def test_evaluation_cli_help():
    """Test evaluation CLI --help."""
    result = subprocess.run(
        [sys.executable, 'scripts/generate_eval_report.py', '--help'],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert 'evaluation' in result.stdout.lower()


def test_evaluation_cli_basic(temp_output_dir):
    """Test basic evaluation CLI execution."""
    result = subprocess.run(
        [
            sys.executable,
            'scripts/generate_eval_report.py',
            '--output-dir', str(temp_output_dir)
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Should complete without errors
    assert result.returncode == 0

    # Check output files exist
    assert (temp_output_dir / 'evaluation_report.json').exists()
    assert (temp_output_dir / 'evaluation_report.md').exists()

    # Validate JSON structure
    with open(temp_output_dir / 'evaluation_report.json') as f:
        report = json.load(f)

    assert 'timestamp' in report
    assert 'quality' in report
    assert 'health' in report


def test_evaluation_cli_with_metrics_files(temp_output_dir):
    """Test evaluation CLI with specific metrics files."""
    metrics_file = temp_output_dir / 'run1' / 'metrics.json'

    result = subprocess.run(
        [
            sys.executable,
            'scripts/generate_eval_report.py',
            '--metrics-files', str(metrics_file)
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    assert result.returncode == 0


def test_cli_error_handling_invalid_dir():
    """Test CLI error handling with invalid directory."""
    result = subprocess.run(
        [
            sys.executable,
            'scripts/run_observability_check.py',
            '--output-dir', '/nonexistent/directory'
        ],
        capture_output=True,
        text=True,
        timeout=10
    )

    # Should fail gracefully
    assert result.returncode != 0


def test_cli_error_handling_no_args():
    """Test CLI error handling with missing arguments."""
    result = subprocess.run(
        [sys.executable, 'scripts/generate_eval_report.py'],
        capture_output=True,
        text=True,
        timeout=10
    )

    # Should show error and usage
    assert result.returncode != 0
    assert 'error' in result.stderr.lower() or 'usage' in result.stderr.lower()
