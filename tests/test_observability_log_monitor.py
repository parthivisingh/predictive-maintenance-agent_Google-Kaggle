"""
Test Log Monitor
================

Test log parsing, error aggregation, and anomaly trend detection.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.observability.log_monitor import (
    parse_logs,
    aggregate_errors,
    detect_anomaly_trends,
    extract_latency_stats,
    generate_log_summary
)


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_json_logs(temp_log_dir):
    """Create sample JSON log file."""
    log_file = temp_log_dir / 'test.log'

    logs = [
        {
            'timestamp': '2025-12-01T10:00:00Z',
            'level': 'INFO',
            'message': 'Processing sensor data',
            'duration_seconds': 0.5
        },
        {
            'timestamp': '2025-12-01T10:00:01Z',
            'level': 'ERROR',
            'message': 'Connection timeout',
            'error_type': 'TimeoutError',
            'duration_seconds': 2.0
        },
        {
            'timestamp': '2025-12-01T10:00:02Z',
            'level': 'INFO',
            'message': 'Detected anomaly in sensor A123',
            'duration_seconds': 0.3
        },
        {
            'timestamp': '2025-12-01T10:00:03Z',
            'level': 'INFO',
            'message': 'Sensor B456 is normal',
            'duration_seconds': 0.4
        },
        {
            'timestamp': '2025-12-01T10:00:04Z',
            'level': 'CRITICAL',
            'message': 'System failure',
            'error_type': 'SystemError',
            'duration_seconds': 5.0
        }
    ]

    with open(log_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')

    return log_file


def test_parse_logs_json(sample_json_logs):
    """Test parsing JSON log files."""
    records = parse_logs(str(sample_json_logs))

    assert len(records) == 5
    assert all('timestamp' in r for r in records)
    assert all('level' in r for r in records)
    assert all('message' in r for r in records)


def test_parse_logs_directory(temp_log_dir, sample_json_logs):
    """Test parsing directory of log files."""
    # Create another log file
    log_file2 = temp_log_dir / 'test2.log'
    with open(log_file2, 'w') as f:
        f.write(json.dumps({'level': 'INFO', 'message': 'Test'}) + '\n')

    records = parse_logs(str(temp_log_dir))

    assert len(records) >= 6  # 5 from first file + 1 from second


def test_parse_logs_text_fallback(temp_log_dir):
    """Test parsing non-JSON text logs."""
    log_file = temp_log_dir / 'text.log'
    with open(log_file, 'w') as f:
        f.write('This is a text log line\n')
        f.write('Another line\n')

    records = parse_logs(str(log_file))

    assert len(records) == 2
    assert records[0]['message'] == 'This is a text log line'


def test_aggregate_errors(sample_json_logs):
    """Test error aggregation."""
    records = parse_logs(str(sample_json_logs))
    errors = aggregate_errors(records)

    assert 'TimeoutError' in errors
    assert 'SystemError' in errors
    assert errors['TimeoutError'] == 1
    assert errors['SystemError'] == 1
    assert errors['ERROR'] == 1
    assert errors['CRITICAL'] == 1


def test_aggregate_errors_empty():
    """Test error aggregation with no errors."""
    records = [
        {'level': 'INFO', 'message': 'All good'}
    ]

    errors = aggregate_errors(records)
    assert len(errors) == 0


def test_detect_anomaly_trends(sample_json_logs):
    """Test anomaly trend detection."""
    records = parse_logs(str(sample_json_logs))
    trends = detect_anomaly_trends(records)

    assert 'anomaly_rate' in trends
    assert 'total_anomalies' in trends
    assert 'total_normal' in trends
    assert 'timeseries' in trends

    assert trends['total_anomalies'] == 1
    assert trends['total_normal'] == 1
    assert trends['anomaly_rate'] == 0.5

    assert len(trends['timeseries']) == 2


def test_detect_anomaly_trends_no_data():
    """Test anomaly trends with no anomaly data."""
    records = [{'level': 'INFO', 'message': 'Test'}]
    trends = detect_anomaly_trends(records)

    assert trends['anomaly_rate'] == 0.0
    assert trends['total_anomalies'] == 0
    assert trends['total_normal'] == 0


def test_extract_latency_stats(sample_json_logs):
    """Test latency statistics extraction."""
    records = parse_logs(str(sample_json_logs))
    latency = extract_latency_stats(records)

    assert latency['count'] == 5
    assert latency['min'] == 0.3
    assert latency['max'] == 5.0
    assert 0 < latency['avg'] < 2
    assert latency['p95'] > 0
    assert 'outliers' in latency


def test_extract_latency_stats_no_data():
    """Test latency stats with no duration data."""
    records = [{'level': 'INFO', 'message': 'Test'}]
    latency = extract_latency_stats(records)

    assert latency['count'] == 0
    assert latency['min'] == 0.0
    assert latency['max'] == 0.0


def test_generate_log_summary(sample_json_logs):
    """Test complete log summary generation."""
    summary = generate_log_summary(str(sample_json_logs))

    assert 'total_records' in summary
    assert 'error_counts' in summary
    assert 'anomaly_trends' in summary
    assert 'latency_stats' in summary
    assert 'analysis_timestamp' in summary

    assert summary['total_records'] == 5
    assert len(summary['error_counts']) > 0
    assert summary['latency_stats']['count'] == 5


def test_generate_log_summary_nonexistent():
    """Test log summary with nonexistent path."""
    summary = generate_log_summary('/nonexistent/path')

    assert summary['total_records'] == 0
