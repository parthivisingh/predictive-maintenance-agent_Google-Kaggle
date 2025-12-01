"""
System Health Evaluation
=========================

Check system health: success rate, timeout rate, error distribution,
and performance degradation from Phase 5 simulation outputs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
import statistics
from datetime import datetime

logger = logging.getLogger(__name__)


def check_success_rate(batch_result: Dict) -> float:
    """
    Extract success_rate from execution metrics.

    Parameters:
    -----------
    batch_result : Dict
        Batch result or metrics dictionary

    Returns:
    --------
    float
        Success rate (0.0 to 1.0)
    """
    # Handle both batch_result and metrics.json structures
    if 'execution' in batch_result:
        return batch_result['execution'].get('success_rate', 1.0)
    elif 'metrics' in batch_result:
        return batch_result['metrics'].get('execution', {}).get('success_rate', 1.0)
    else:
        # Fallback: calculate from results
        results = batch_result.get('results', [])
        if not results:
            return 1.0

        successful = sum(1 for r in results if r.get('status') == 'success')
        return successful / len(results)


def detect_timeouts(batch_result: Dict) -> int:
    """
    Count timeout/failed runs.

    Parameters:
    -----------
    batch_result : Dict
        Batch result or metrics dictionary

    Returns:
    --------
    int
        Number of timeouts/failures
    """
    # Handle execution metrics
    if 'execution' in batch_result:
        failed = batch_result['execution'].get('failed_runs', 0)
        return failed

    # Handle results array
    results = batch_result.get('results', [])
    if not results:
        return 0

    timeout_count = 0
    for result in results:
        status = result.get('status', 'success')
        error = result.get('error', '')

        if status in ['failed', 'timeout', 'error']:
            timeout_count += 1
        elif 'timeout' in error.lower():
            timeout_count += 1

    return timeout_count


def analyze_performance(batch_result: Dict) -> Dict:
    """
    Detect performance degradation trends.

    Parameters:
    -----------
    batch_result : Dict
        Batch result or metrics dictionary

    Returns:
    --------
    Dict
        Performance analysis with degradation indicators
    """
    # Extract performance metrics
    if 'performance_metrics' in batch_result:
        perf = batch_result['performance_metrics']
        return {
            'avg_duration_sec': perf.get('avg_duration_sec', 0.0),
            'min_duration_sec': perf.get('min_duration_sec', 0.0),
            'max_duration_sec': perf.get('max_duration_sec', 0.0),
            'degradation_detected': False,
            'degradation_score': 0.0
        }

    # Analyze from results array
    results = batch_result.get('results', [])
    if not results:
        return {
            'avg_duration_sec': 0.0,
            'degradation_detected': False,
            'degradation_score': 0.0
        }

    durations = []
    for result in results:
        duration = result.get('duration_sec') or result.get('duration', 0.0)
        if duration > 0:
            durations.append(duration)

    if not durations:
        return {
            'avg_duration_sec': 0.0,
            'degradation_detected': False,
            'degradation_score': 0.0
        }

    avg_duration = statistics.mean(durations)
    min_duration = min(durations)
    max_duration = max(durations)

    # Detect degradation: check if later runs are slower
    # Split into first half and second half
    mid = len(durations) // 2
    first_half_avg = statistics.mean(durations[:mid]) if mid > 0 else 0.0
    second_half_avg = statistics.mean(durations[mid:]) if mid < len(durations) else 0.0

    # Calculate degradation
    if first_half_avg > 0:
        degradation_ratio = (second_half_avg - first_half_avg) / first_half_avg
        degradation_detected = degradation_ratio > 0.2  # 20% slower
        degradation_score = max(0.0, min(1.0, degradation_ratio))
    else:
        degradation_detected = False
        degradation_score = 0.0

    return {
        'avg_duration_sec': avg_duration,
        'min_duration_sec': min_duration,
        'max_duration_sec': max_duration,
        'median_duration_sec': statistics.median(durations),
        'first_half_avg': first_half_avg,
        'second_half_avg': second_half_avg,
        'degradation_detected': degradation_detected,
        'degradation_score': degradation_score,
        'degradation_ratio': degradation_ratio if first_half_avg > 0 else 0.0
    }


def calculate_health_score(
    success_rate: float,
    timeout_count: int,
    total_runs: int,
    performance: Dict
) -> float:
    """
    Calculate overall system health score.

    Parameters:
    -----------
    success_rate : float
        Success rate (0-1)
    timeout_count : int
        Number of timeouts
    total_runs : int
        Total number of runs
    performance : Dict
        Performance analysis dict

    Returns:
    --------
    float
        Health score (0.0 to 1.0, higher is healthier)
    """
    # Success rate component (40% weight)
    success_component = success_rate * 0.4

    # Timeout component (30% weight)
    timeout_rate = timeout_count / total_runs if total_runs > 0 else 0.0
    timeout_component = (1.0 - timeout_rate) * 0.3

    # Performance component (30% weight)
    degradation_score = performance.get('degradation_score', 0.0)
    performance_component = (1.0 - degradation_score) * 0.3

    health_score = success_component + timeout_component + performance_component

    return max(0.0, min(1.0, health_score))


def generate_health_report(batch_result: Dict) -> Dict:
    """
    Generate comprehensive system health report.

    Parameters:
    -----------
    batch_result : Dict
        Batch result or metrics dictionary

    Returns:
    --------
    Dict
        Complete health report
    """
    success_rate = check_success_rate(batch_result)
    timeout_count = detect_timeouts(batch_result)
    performance = analyze_performance(batch_result)

    # Get total runs
    if 'execution' in batch_result:
        total_runs = batch_result['execution'].get('total_runs', 0)
    else:
        total_runs = len(batch_result.get('results', []))

    health_score = calculate_health_score(
        success_rate,
        timeout_count,
        total_runs,
        performance
    )

    # Determine health status
    if health_score >= 0.9:
        status = 'excellent'
    elif health_score >= 0.75:
        status = 'good'
    elif health_score >= 0.5:
        status = 'fair'
    elif health_score >= 0.25:
        status = 'poor'
    else:
        status = 'critical'

    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'health_score': health_score,
        'status': status,
        'metrics': {
            'success_rate': success_rate,
            'timeout_count': timeout_count,
            'total_runs': total_runs,
            'failed_runs': total_runs - int(total_runs * success_rate)
        },
        'performance': performance,
        'recommendations': generate_recommendations(
            success_rate,
            timeout_count,
            performance,
            status
        )
    }


def generate_recommendations(
    success_rate: float,
    timeout_count: int,
    performance: Dict,
    status: str
) -> List[str]:
    """
    Generate health recommendations.

    Parameters:
    -----------
    success_rate : float
        Success rate
    timeout_count : int
        Timeout count
    performance : Dict
        Performance metrics
    status : str
        Health status

    Returns:
    --------
    List[str]
        List of recommendations
    """
    recommendations = []

    if status in ['excellent', 'good']:
        recommendations.append("System is healthy. Continue monitoring.")
    else:
        recommendations.append("System health needs attention.")

    if success_rate < 0.9:
        recommendations.append(
            f"Success rate is {success_rate:.1%}. "
            "Investigate failures and improve error handling."
        )

    if timeout_count > 0:
        recommendations.append(
            f"Detected {timeout_count} timeout(s). "
            "Consider increasing timeout limits or optimizing performance."
        )

    if performance.get('degradation_detected'):
        recommendations.append(
            "Performance degradation detected. "
            "Check for memory leaks, resource contention, or inefficient code paths."
        )

    if performance.get('max_duration_sec', 0) > 10.0:
        recommendations.append(
            f"Maximum duration is {performance['max_duration_sec']:.2f}s. "
            "Consider optimizing slow operations."
        )

    return recommendations


def analyze_error_distribution(batch_result: Dict) -> Dict:
    """
    Analyze error distribution from results.

    Parameters:
    -----------
    batch_result : Dict
        Batch result dictionary

    Returns:
    --------
    Dict
        Error distribution statistics
    """
    results = batch_result.get('results', [])
    if not results:
        return {
            'total_errors': 0,
            'error_types': {},
            'error_rate': 0.0
        }

    error_types = {}
    total_errors = 0

    for result in results:
        if result.get('status') != 'success':
            total_errors += 1
            error = result.get('error', 'UnknownError')

            # Extract error type (first word or line)
            error_type = error.split(':')[0].split('\n')[0]
            error_types[error_type] = error_types.get(error_type, 0) + 1

    error_rate = total_errors / len(results) if results else 0.0

    return {
        'total_errors': total_errors,
        'error_types': error_types,
        'error_rate': error_rate,
        'most_common_error': max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
    }
