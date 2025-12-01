"""
Test Grafana Exporter
=====================

Test Grafana JSON export and Markdown dashboard generation.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.observability.grafana_exporter import (
    export_timeseries,
    generate_dashboard_json,
    export_dashboard,
    generate_markdown_dashboard,
    export_markdown_dashboard
)


@pytest.fixture
def sample_metrics():
    """Sample metrics for testing."""
    return {
        'timestamp': '2025-12-01T10:00:00Z',
        'anomaly_metrics': {
            'anomaly_rate': 0.85,
            'total_anomalies': 85,
            'total_normal': 15
        },
        'execution': {
            'success_rate': 1.0,
            'total_runs': 100,
            'successful_runs': 100,
            'failed_runs': 0,
            'duration_sec': 50.0
        },
        'performance_metrics': {
            'avg_duration_sec': 0.5,
            'min_duration_sec': 0.3,
            'max_duration_sec': 1.2
        },
        'priority_metrics': {
            'critical': 5,
            'high': 15,
            'medium': 45,
            'low': 20
        },
        'research_metrics': {
            'similarity_hit_rate': 0.35,
            'avg_similarity_hits': 3.5
        },
        'roi_metrics': {
            'mean': 125.50,
            'median': 120.00,
            'min': 50.0,
            'max': 200.0,
            'std': 25.5
        }
    }


def test_export_timeseries(sample_metrics):
    """Test timeseries export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'timeseries.json'

        export_timeseries(sample_metrics, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'meta' in data
        assert 'series' in data
        assert data['meta']['type'] == 'timeseries-many'
        assert len(data['series']) > 0

        # Check for expected series
        targets = [s['target'] for s in data['series']]
        assert 'anomaly_rate' in targets
        assert 'success_rate' in targets
        assert 'avg_duration_sec' in targets


def test_generate_dashboard_json(sample_metrics):
    """Test dashboard JSON generation."""
    dashboard = generate_dashboard_json(sample_metrics)

    assert 'dashboard' in dashboard
    assert 'overwrite' in dashboard

    dash = dashboard['dashboard']
    assert dash['title'] == 'Predictive Maintenance Dashboard'
    assert 'panels' in dash
    assert len(dash['panels']) == 3

    # Check panel titles
    panel_titles = [p['title'] for p in dash['panels']]
    assert 'Anomaly Rate Over Time' in panel_titles
    assert 'Priority Distribution' in panel_titles
    assert 'ROI Distribution' in panel_titles


def test_export_dashboard(sample_metrics):
    """Test full dashboard export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'dashboard.json'

        export_dashboard(sample_metrics, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'dashboard' in data


def test_generate_markdown_dashboard(sample_metrics):
    """Test Markdown dashboard generation."""
    markdown = generate_markdown_dashboard(sample_metrics)

    assert isinstance(markdown, str)
    assert '# Predictive Maintenance Dashboard' in markdown
    assert '## Anomaly Metrics' in markdown
    assert '## Execution Metrics' in markdown
    assert '## Priority Distribution' in markdown
    assert '## ROI Metrics' in markdown
    assert '## Research Metrics' in markdown

    # Check for data values
    assert '85.00%' in markdown  # anomaly rate
    assert '100.00%' in markdown  # success rate
    assert '$125.50' in markdown  # mean ROI


def test_export_markdown_dashboard(sample_metrics):
    """Test Markdown dashboard export to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'dashboard.md'

        export_markdown_dashboard(sample_metrics, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            content = f.read()

        assert '# Predictive Maintenance Dashboard' in content


def test_markdown_dashboard_with_zeros():
    """Test Markdown dashboard with zero values."""
    metrics = {
        'anomaly_metrics': {'anomaly_rate': 0.0, 'total_anomalies': 0, 'total_normal': 100},
        'execution': {'success_rate': 1.0, 'total_runs': 100, 'successful_runs': 100, 'failed_runs': 0, 'duration_sec': 10.0},
        'priority_metrics': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
        'roi_metrics': {'mean': 0.0, 'median': 0.0, 'min': 0.0, 'max': 0.0},
        'research_metrics': {'similarity_hit_rate': 0.0, 'avg_similarity_hits': 0.0}
    }

    markdown = generate_markdown_dashboard(metrics)

    assert '0.00%' in markdown
    assert '$0.00' in markdown
