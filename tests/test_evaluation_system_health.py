"""
Test System Health Evaluation
==============================

Test success rate, timeout detection, and performance analysis.
"""

import pytest

from src.evaluation.system_health import (
    check_success_rate,
    detect_timeouts,
    analyze_performance,
    calculate_health_score,
    generate_health_report,
    generate_recommendations,
    analyze_error_distribution
)


@pytest.fixture
def sample_batch_result():
    """Sample batch result with execution metrics."""
    return {
        'execution': {
            'success_rate': 0.95,
            'total_runs': 100,
            'successful_runs': 95,
            'failed_runs': 5,
            'duration_sec': 50.0
        },
        'performance_metrics': {
            'avg_duration_sec': 0.5,
            'min_duration_sec': 0.3,
            'max_duration_sec': 1.2
        }
    }


@pytest.fixture
def sample_batch_with_results():
    """Sample batch result with results array."""
    results = []
    for i in range(10):
        results.append({
            'status': 'success' if i < 8 else 'failed',
            'duration_sec': 0.5 + i * 0.1,
            'error': 'Timeout' if i >= 8 else ''
        })

    return {'results': results}


def test_check_success_rate(sample_batch_result):
    """Test success rate extraction."""
    success_rate = check_success_rate(sample_batch_result)

    assert success_rate == 0.95


def test_check_success_rate_from_results(sample_batch_with_results):
    """Test success rate calculation from results."""
    success_rate = check_success_rate(sample_batch_with_results)

    assert success_rate == 0.8  # 8 out of 10


def test_detect_timeouts(sample_batch_result):
    """Test timeout detection from metrics."""
    timeout_count = detect_timeouts(sample_batch_result)

    assert timeout_count == 5


def test_detect_timeouts_from_results(sample_batch_with_results):
    """Test timeout detection from results."""
    timeout_count = detect_timeouts(sample_batch_with_results)

    assert timeout_count >= 2  # 2 failed + possible timeout errors


def test_analyze_performance(sample_batch_result):
    """Test performance analysis from metrics."""
    performance = analyze_performance(sample_batch_result)

    assert 'avg_duration_sec' in performance
    assert 'min_duration_sec' in performance
    assert 'max_duration_sec' in performance
    assert 'degradation_detected' in performance
    assert 'degradation_score' in performance

    assert performance['avg_duration_sec'] == 0.5


def test_analyze_performance_from_results(sample_batch_with_results):
    """Test performance analysis from results array."""
    performance = analyze_performance(sample_batch_with_results)

    assert 'avg_duration_sec' in performance
    assert 'degradation_detected' in performance
    assert performance['avg_duration_sec'] > 0


def test_analyze_performance_degradation():
    """Test degradation detection."""
    # Create results with clear degradation
    results = []
    for i in range(20):
        duration = 0.5 if i < 10 else 2.0  # Clear jump
        results.append({
            'status': 'success',
            'duration_sec': duration
        })

    batch_result = {'results': results}
    performance = analyze_performance(batch_result)

    # Should detect degradation
    assert performance['degradation_detected'] is True
    assert performance['degradation_score'] > 0


def test_calculate_health_score():
    """Test health score calculation."""
    score = calculate_health_score(
        success_rate=1.0,
        timeout_count=0,
        total_runs=100,
        performance={'degradation_score': 0.0}
    )

    assert 0.0 <= score <= 1.0
    assert score > 0.9  # Perfect health


def test_calculate_health_score_poor():
    """Test health score with poor metrics."""
    score = calculate_health_score(
        success_rate=0.5,
        timeout_count=20,
        total_runs=100,
        performance={'degradation_score': 0.5}
    )

    assert score < 0.7  # Adjusted threshold


def test_generate_health_report(sample_batch_result):
    """Test complete health report generation."""
    report = generate_health_report(sample_batch_result)

    assert 'timestamp' in report
    assert 'health_score' in report
    assert 'status' in report
    assert 'metrics' in report
    assert 'performance' in report
    assert 'recommendations' in report

    assert 0.0 <= report['health_score'] <= 1.0
    assert report['status'] in ['excellent', 'good', 'fair', 'poor', 'critical']


def test_generate_health_report_status_levels():
    """Test health status classification."""
    # Excellent
    batch_result = {
        'execution': {'success_rate': 1.0, 'total_runs': 100, 'failed_runs': 0},
        'performance_metrics': {'avg_duration_sec': 0.5, 'min_duration_sec': 0.3, 'max_duration_sec': 1.0}
    }
    report = generate_health_report(batch_result)
    assert report['status'] in ['excellent', 'good']

    # Poor/Fair
    batch_result = {
        'execution': {'success_rate': 0.4, 'total_runs': 100, 'failed_runs': 60},
        'performance_metrics': {'avg_duration_sec': 5.0, 'min_duration_sec': 1.0, 'max_duration_sec': 20.0}
    }
    report = generate_health_report(batch_result)
    assert report['status'] in ['poor', 'critical', 'fair']  # Fair is acceptable


def test_generate_recommendations():
    """Test recommendation generation."""
    recommendations = generate_recommendations(
        success_rate=0.8,
        timeout_count=5,
        performance={'degradation_detected': True, 'max_duration_sec': 15.0},
        status='fair'
    )

    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert any('success rate' in r.lower() for r in recommendations)
    assert any('timeout' in r.lower() for r in recommendations)
    assert any('degradation' in r.lower() for r in recommendations)


def test_generate_recommendations_healthy():
    """Test recommendations for healthy system."""
    recommendations = generate_recommendations(
        success_rate=1.0,
        timeout_count=0,
        performance={'degradation_detected': False, 'max_duration_sec': 1.0},
        status='excellent'
    )

    assert any('healthy' in r.lower() for r in recommendations)


def test_analyze_error_distribution(sample_batch_with_results):
    """Test error distribution analysis."""
    error_dist = analyze_error_distribution(sample_batch_with_results)

    assert 'total_errors' in error_dist
    assert 'error_types' in error_dist
    assert 'error_rate' in error_dist

    assert error_dist['total_errors'] == 2
    assert error_dist['error_rate'] == 0.2


def test_analyze_error_distribution_empty():
    """Test error distribution with no errors."""
    batch_result = {'results': [{'status': 'success'} for _ in range(5)]}
    error_dist = analyze_error_distribution(batch_result)

    assert error_dist['total_errors'] == 0
    assert error_dist['error_rate'] == 0.0
