"""
Metrics Summary
===============

Aggregate metrics.json from multiple runs, compute cross-run statistics
and stability scores for Phase 5 simulation outputs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
import statistics
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


def load_metrics(run_paths: List[str]) -> List[Dict]:
    """
    Load all metrics.json from run directories.

    Parameters:
    -----------
    run_paths : List[str]
        List of paths to run directories or metrics.json files

    Returns:
    --------
    List[Dict]
        List of metrics dictionaries
    """
    metrics_list = []

    for run_path in run_paths:
        path_obj = Path(run_path)

        # Handle both directory and file paths
        if path_obj.is_dir():
            metrics_file = path_obj / 'metrics.json'
        elif path_obj.is_file() and path_obj.name == 'metrics.json':
            metrics_file = path_obj
        else:
            logger.warning(f"Invalid path: {run_path}")
            continue

        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    metrics_list.append(metrics)
            except Exception as e:
                logger.error(f"Error loading {metrics_file}: {e}")
        else:
            logger.warning(f"Metrics file not found: {metrics_file}")

    return metrics_list


def compute_stability(metrics_list: List[Dict]) -> Dict:
    """
    Compute variance/stddev for anomaly rate, ROI across runs.

    Parameters:
    -----------
    metrics_list : List[Dict]
        List of metrics from multiple runs

    Returns:
    --------
    Dict
        Stability scores including variance and standard deviation
    """
    if not metrics_list:
        return {
            'anomaly_rate': {'mean': 0.0, 'std': 0.0, 'variance': 0.0, 'stability_score': 0.0},
            'roi': {'mean': 0.0, 'std': 0.0, 'variance': 0.0, 'stability_score': 0.0},
            'success_rate': {'mean': 0.0, 'std': 0.0, 'variance': 0.0, 'stability_score': 1.0}
        }

    # Extract values across runs
    anomaly_rates = []
    roi_means = []
    success_rates = []

    for metrics in metrics_list:
        # Anomaly rate
        anomaly_rate = metrics.get('anomaly_metrics', {}).get('anomaly_rate', 0.0)
        anomaly_rates.append(anomaly_rate)

        # ROI mean
        roi_mean = metrics.get('roi_metrics', {}).get('mean', 0.0)
        roi_means.append(roi_mean)

        # Success rate
        success_rate = metrics.get('execution', {}).get('success_rate', 1.0)
        success_rates.append(success_rate)

    def calc_stability_stats(values: List[float]) -> Dict:
        """Calculate stability statistics for a metric."""
        if len(values) <= 1:
            return {
                'mean': values[0] if values else 0.0,
                'std': 0.0,
                'variance': 0.0,
                'stability_score': 1.0  # Perfect stability with single value
            }

        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        var_val = statistics.variance(values)

        # Stability score: 1.0 is perfect (low variance), 0.0 is unstable
        # Using coefficient of variation (CV) normalized
        if mean_val != 0:
            cv = std_val / abs(mean_val)
            stability_score = max(0.0, 1.0 - min(1.0, cv))
        else:
            stability_score = 1.0 if std_val == 0 else 0.0

        return {
            'mean': mean_val,
            'std': std_val,
            'variance': var_val,
            'stability_score': stability_score,
            'min': min(values),
            'max': max(values)
        }

    return {
        'anomaly_rate': calc_stability_stats(anomaly_rates),
        'roi': calc_stability_stats(roi_means),
        'success_rate': calc_stability_stats(success_rates),
        'run_count': len(metrics_list)
    }


def generate_summary(metrics_list: List[Dict]) -> Dict:
    """
    Aggregate mean, median, min, max across runs.

    Parameters:
    -----------
    metrics_list : List[Dict]
        List of metrics from multiple runs

    Returns:
    --------
    Dict
        Aggregated summary statistics
    """
    if not metrics_list:
        return {
            'run_count': 0,
            'anomaly_metrics': {},
            'execution': {},
            'performance': {},
            'priority': {},
            'research': {},
            'roi': {}
        }

    # Aggregate anomaly metrics
    anomaly_rates = [m.get('anomaly_metrics', {}).get('anomaly_rate', 0.0) for m in metrics_list]
    total_anomalies = [m.get('anomaly_metrics', {}).get('total_anomalies', 0) for m in metrics_list]

    # Aggregate execution metrics
    success_rates = [m.get('execution', {}).get('success_rate', 1.0) for m in metrics_list]
    durations = [m.get('execution', {}).get('duration_sec', 0.0) for m in metrics_list]
    total_runs = [m.get('execution', {}).get('total_runs', 0) for m in metrics_list]

    # Aggregate performance metrics
    avg_durations = [m.get('performance_metrics', {}).get('avg_duration_sec', 0.0) for m in metrics_list]

    # Aggregate priority metrics
    priorities = defaultdict(list)
    for m in metrics_list:
        priority_metrics = m.get('priority_metrics', {})
        for level in ['critical', 'high', 'medium', 'low']:
            priorities[level].append(priority_metrics.get(level, 0))

    # Aggregate research metrics
    similarity_rates = [m.get('research_metrics', {}).get('similarity_hit_rate', 0.0) for m in metrics_list]

    # Aggregate ROI metrics
    roi_means = [m.get('roi_metrics', {}).get('mean', 0.0) for m in metrics_list]

    def safe_stats(values: List[float]) -> Dict:
        """Compute safe statistics that handle empty lists."""
        if not values:
            return {'mean': 0.0, 'median': 0.0, 'min': 0.0, 'max': 0.0}
        return {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values)
        }

    return {
        'run_count': len(metrics_list),
        'anomaly_metrics': {
            'anomaly_rate': safe_stats(anomaly_rates),
            'total_anomalies': safe_stats(total_anomalies)
        },
        'execution': {
            'success_rate': safe_stats(success_rates),
            'duration_sec': safe_stats(durations),
            'total_runs': safe_stats(total_runs)
        },
        'performance': {
            'avg_duration_sec': safe_stats(avg_durations)
        },
        'priority': {
            level: safe_stats(values) for level, values in priorities.items()
        },
        'research': {
            'similarity_hit_rate': safe_stats(similarity_rates)
        },
        'roi': {
            'mean': safe_stats(roi_means)
        },
        'analysis_timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def find_all_metrics_files(output_dir: str) -> List[str]:
    """
    Find all metrics.json files in output directory.

    Parameters:
    -----------
    output_dir : str
        Path to output directory

    Returns:
    --------
    List[str]
        List of paths to metrics.json files
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        logger.warning(f"Output directory not found: {output_dir}")
        return []

    metrics_files = list(output_path.glob('*/metrics.json'))
    metrics_files += list(output_path.glob('**/metrics.json'))

    # Remove duplicates and return as strings
    return [str(f) for f in sorted(set(metrics_files))]


def generate_observability_summary(output_dir: str) -> Dict:
    """
    Generate complete observability summary from output directory.

    Parameters:
    -----------
    output_dir : str
        Path to output directory containing run results

    Returns:
    --------
    Dict
        Complete observability summary with cross-run stats and stability
    """
    metrics_files = find_all_metrics_files(output_dir)
    metrics_list = load_metrics(metrics_files)

    if not metrics_list:
        logger.warning(f"No metrics files found in {output_dir}")
        return {
            'error': 'No metrics files found',
            'output_dir': output_dir,
            'metrics_files_found': 0
        }

    return {
        'cross_run_stats': generate_summary(metrics_list),
        'stability_scores': compute_stability(metrics_list),
        'metrics_files_analyzed': len(metrics_list),
        'output_dir': output_dir,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
