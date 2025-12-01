"""
Log Monitor
===========

Parse and aggregate simulation logs, extract error patterns, latency outliers,
and anomaly trends from Phase 5 simulation outputs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


def parse_logs(log_path: str) -> List[Dict]:
    """
    Parse JSON/text logs into structured records.

    Parameters:
    -----------
    log_path : str
        Path to log file or directory containing log files

    Returns:
    --------
    List[Dict]
        List of parsed log records with timestamp, level, message, etc.
    """
    records = []
    log_path_obj = Path(log_path)

    # Handle both file and directory paths
    if log_path_obj.is_file():
        log_files = [log_path_obj]
    elif log_path_obj.is_dir():
        log_files = list(log_path_obj.glob('*.log')) + list(log_path_obj.glob('*.json'))
    else:
        logger.warning(f"Log path not found: {log_path}")
        return records

    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        # Try parsing as JSON (structured logs)
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError:
                        # Fallback to text parsing
                        record = {
                            'message': line,
                            'level': 'INFO',
                            'timestamp': None,
                            'source_file': str(log_file),
                            'line_number': line_num
                        }
                        records.append(record)
        except Exception as e:
            logger.error(f"Error parsing log file {log_file}: {e}")

    return records


def aggregate_errors(records: List[Dict]) -> Dict[str, int]:
    """
    Count errors by type/category.

    Parameters:
    -----------
    records : List[Dict]
        Parsed log records from parse_logs()

    Returns:
    --------
    Dict[str, int]
        Error counts by type/category
    """
    error_counts = defaultdict(int)

    for record in records:
        level = record.get('level', '').upper()

        if level in ['ERROR', 'CRITICAL']:
            # Extract error type
            error_type = record.get('error_type', 'UnknownError')
            error_counts[error_type] += 1

            # Also count by level
            error_counts[level] += 1

    return dict(error_counts)


def detect_anomaly_trends(records: List[Dict]) -> Dict:
    """
    Calculate anomaly rate trends over time.

    Parameters:
    -----------
    records : List[Dict]
        Parsed log records from parse_logs()

    Returns:
    --------
    Dict
        Anomaly trends including rate, timeseries, and statistics
    """
    anomaly_records = []
    normal_records = []
    timeseries = []

    for record in records:
        # Look for anomaly-related logs
        message = record.get('message', '')

        if 'anomaly' in message.lower():
            anomaly_records.append(record)

            # Try to extract timestamp
            timestamp = record.get('timestamp')
            if timestamp:
                timeseries.append({
                    'timestamp': timestamp,
                    'type': 'anomaly',
                    'message': message
                })
        elif 'normal' in message.lower() or 'healthy' in message.lower():
            normal_records.append(record)

            timestamp = record.get('timestamp')
            if timestamp:
                timeseries.append({
                    'timestamp': timestamp,
                    'type': 'normal',
                    'message': message
                })

    total = len(anomaly_records) + len(normal_records)
    anomaly_rate = len(anomaly_records) / total if total > 0 else 0.0

    # Calculate trend statistics
    trends = {
        'anomaly_rate': anomaly_rate,
        'total_anomalies': len(anomaly_records),
        'total_normal': len(normal_records),
        'timeseries': timeseries,
        'summary': {
            'has_trend_data': len(timeseries) > 0,
            'records_analyzed': len(records)
        }
    }

    return trends


def extract_latency_stats(records: List[Dict]) -> Dict:
    """
    Extract latency statistics from log records.

    Parameters:
    -----------
    records : List[Dict]
        Parsed log records

    Returns:
    --------
    Dict
        Latency statistics (min, max, avg, p95, outliers)
    """
    latencies = []

    for record in records:
        # Look for duration/latency fields
        duration = record.get('duration_seconds') or record.get('duration_sec')
        if duration is not None:
            try:
                latencies.append(float(duration))
            except (ValueError, TypeError):
                pass

    if not latencies:
        return {
            'count': 0,
            'min': 0.0,
            'max': 0.0,
            'avg': 0.0,
            'p95': 0.0,
            'outliers': []
        }

    latencies_sorted = sorted(latencies)
    p95_index = int(len(latencies) * 0.95)
    p95 = latencies_sorted[p95_index] if p95_index < len(latencies) else latencies_sorted[-1]

    # Detect outliers (> p95)
    outliers = [l for l in latencies if l > p95]

    return {
        'count': len(latencies),
        'min': min(latencies),
        'max': max(latencies),
        'avg': statistics.mean(latencies),
        'median': statistics.median(latencies),
        'p95': p95,
        'outlier_count': len(outliers),
        'outliers': sorted(outliers, reverse=True)[:10]  # Top 10 outliers
    }


def generate_log_summary(log_path: str) -> Dict:
    """
    Generate comprehensive log summary.

    Parameters:
    -----------
    log_path : str
        Path to log file or directory

    Returns:
    --------
    Dict
        Complete log summary with errors, trends, and latency stats
    """
    records = parse_logs(log_path)

    return {
        'total_records': len(records),
        'error_counts': aggregate_errors(records),
        'anomaly_trends': detect_anomaly_trends(records),
        'latency_stats': extract_latency_stats(records),
        'analysis_timestamp': datetime.utcnow().isoformat() + 'Z'
    }
