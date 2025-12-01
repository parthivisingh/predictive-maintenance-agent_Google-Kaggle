"""
Grafana Exporter
================

Export metrics to Grafana JSON format for dashboard visualization (optional).
Provides timeseries and dashboard JSON generation.
"""

import json
import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def export_timeseries(metrics: Dict, output_path: str) -> None:
    """
    Convert metrics to Grafana JSON timeseries format.

    Parameters:
    -----------
    metrics : Dict
        Metrics dictionary from Phase 5 outputs
    output_path : str
        Path to write Grafana timeseries JSON

    Returns:
    --------
    None
        Writes JSON file to output_path
    """
    timeseries_data = {
        "meta": {
            "type": "timeseries-many",
            "source": "predictive-maintenance-agent",
            "version": "1.0"
        },
        "series": []
    }

    # Extract timestamp
    timestamp = metrics.get('timestamp', datetime.utcnow().isoformat())
    if 'Z' not in timestamp:
        timestamp += 'Z'

    # Parse timestamp to milliseconds
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        timestamp_ms = int(dt.timestamp() * 1000)
    except:
        timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

    # Anomaly rate series
    anomaly_metrics = metrics.get('anomaly_metrics', {})
    timeseries_data['series'].append({
        "target": "anomaly_rate",
        "datapoints": [
            [anomaly_metrics.get('anomaly_rate', 0.0), timestamp_ms]
        ]
    })

    # Success rate series
    execution = metrics.get('execution', {})
    timeseries_data['series'].append({
        "target": "success_rate",
        "datapoints": [
            [execution.get('success_rate', 1.0), timestamp_ms]
        ]
    })

    # Duration series
    performance = metrics.get('performance_metrics', {})
    timeseries_data['series'].append({
        "target": "avg_duration_sec",
        "datapoints": [
            [performance.get('avg_duration_sec', 0.0), timestamp_ms]
        ]
    })

    # Priority series
    priority_metrics = metrics.get('priority_metrics', {})
    for level in ['critical', 'high', 'medium', 'low']:
        timeseries_data['series'].append({
            "target": f"priority_{level}",
            "datapoints": [
                [priority_metrics.get(level, 0), timestamp_ms]
            ]
        })

    # ROI series
    roi_metrics = metrics.get('roi_metrics', {})
    timeseries_data['series'].append({
        "target": "roi_mean",
        "datapoints": [
            [roi_metrics.get('mean', 0.0), timestamp_ms]
        ]
    })

    # Write to file
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(timeseries_data, f, indent=2)

        logger.info(f"Exported timeseries to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting timeseries: {e}")
        raise


def generate_dashboard_json(metrics: Dict) -> Dict:
    """
    Generate Grafana dashboard JSON with 3 panels.

    Parameters:
    -----------
    metrics : Dict
        Metrics dictionary or aggregated metrics

    Returns:
    --------
    Dict
        Grafana dashboard JSON
    """
    # Extract metrics for panels
    anomaly_metrics = metrics.get('anomaly_metrics', {})
    priority_metrics = metrics.get('priority_metrics', {})
    roi_metrics = metrics.get('roi_metrics', {})

    dashboard = {
        "dashboard": {
            "title": "Predictive Maintenance Dashboard",
            "tags": ["predictive-maintenance", "phase5", "observability"],
            "timezone": "utc",
            "schemaVersion": 16,
            "version": 1,
            "refresh": "30s",
            "panels": [
                # Panel 1: Anomaly Rate
                {
                    "id": 1,
                    "title": "Anomaly Rate Over Time",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "target": "anomaly_rate"
                        }
                    ],
                    "yaxes": [
                        {
                            "label": "Rate",
                            "format": "percentunit",
                            "min": 0,
                            "max": 1
                        },
                        {
                            "format": "short"
                        }
                    ],
                    "lines": True,
                    "fill": 1,
                    "linewidth": 2,
                    "points": False,
                    "pointradius": 5,
                    "bars": False,
                    "stack": False,
                    "percentage": False,
                    "legend": {
                        "show": True,
                        "values": True,
                        "current": True,
                        "alignAsTable": True
                    },
                    "nullPointMode": "null",
                    "tooltip": {
                        "shared": True,
                        "sort": 0,
                        "value_type": "individual"
                    }
                },
                # Panel 2: Priority Distribution
                {
                    "id": 2,
                    "title": "Priority Distribution",
                    "type": "bargauge",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {"refId": "A", "target": "priority_critical"},
                        {"refId": "B", "target": "priority_high"},
                        {"refId": "C", "target": "priority_medium"},
                        {"refId": "D", "target": "priority_low"}
                    ],
                    "options": {
                        "orientation": "horizontal",
                        "displayMode": "gradient",
                        "showUnfilled": True
                    },
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 5},
                                    {"color": "red", "value": 10}
                                ]
                            }
                        }
                    }
                },
                # Panel 3: ROI Histogram
                {
                    "id": 3,
                    "title": "ROI Distribution",
                    "type": "histogram",
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                    "targets": [
                        {
                            "refId": "A",
                            "target": "roi_mean"
                        }
                    ],
                    "options": {
                        "bucketOffset": 0,
                        "bucketSize": 10
                    },
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "hideFrom": {
                                    "tooltip": False,
                                    "viz": False,
                                    "legend": False
                                }
                            }
                        }
                    }
                }
            ],
            "time": {
                "from": "now-6h",
                "to": "now"
            },
            "timepicker": {
                "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
            }
        },
        "overwrite": True
    }

    return dashboard


def export_dashboard(metrics: Dict, output_path: str) -> None:
    """
    Generate and export Grafana dashboard JSON.

    Parameters:
    -----------
    metrics : Dict
        Metrics dictionary from Phase 5
    output_path : str
        Path to write dashboard JSON

    Returns:
    --------
    None
        Writes dashboard JSON to output_path
    """
    dashboard = generate_dashboard_json(metrics)

    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        logger.info(f"Exported Grafana dashboard to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting dashboard: {e}")
        raise


def generate_markdown_dashboard(metrics: Dict) -> str:
    """
    Generate Markdown dashboard as lightweight alternative to Grafana.

    Parameters:
    -----------
    metrics : Dict
        Metrics dictionary or aggregated metrics

    Returns:
    --------
    str
        Markdown-formatted dashboard
    """
    # Extract metrics
    anomaly_metrics = metrics.get('anomaly_metrics', {})
    execution = metrics.get('execution', {})
    priority_metrics = metrics.get('priority_metrics', {})
    roi_metrics = metrics.get('roi_metrics', {})
    research_metrics = metrics.get('research_metrics', {})

    md = []
    md.append("# Predictive Maintenance Dashboard\n")
    md.append(f"Generated: {datetime.utcnow().isoformat()}Z\n")
    md.append("---\n\n")

    # Anomaly Metrics
    md.append("## Anomaly Metrics\n")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Anomaly Rate | {anomaly_metrics.get('anomaly_rate', 0.0):.2%} |")
    md.append(f"| Total Anomalies | {anomaly_metrics.get('total_anomalies', 0)} |")
    md.append(f"| Total Normal | {anomaly_metrics.get('total_normal', 0)} |")
    md.append("\n")

    # Execution Metrics
    md.append("## Execution Metrics\n")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Success Rate | {execution.get('success_rate', 1.0):.2%} |")
    md.append(f"| Total Runs | {execution.get('total_runs', 0)} |")
    md.append(f"| Successful Runs | {execution.get('successful_runs', 0)} |")
    md.append(f"| Failed Runs | {execution.get('failed_runs', 0)} |")
    md.append(f"| Duration | {execution.get('duration_sec', 0.0):.2f}s |")
    md.append("\n")

    # Priority Distribution
    md.append("## Priority Distribution\n")
    md.append("| Priority | Count |")
    md.append("|----------|-------|")
    md.append(f"| Critical | {priority_metrics.get('critical', 0)} |")
    md.append(f"| High | {priority_metrics.get('high', 0)} |")
    md.append(f"| Medium | {priority_metrics.get('medium', 0)} |")
    md.append(f"| Low | {priority_metrics.get('low', 0)} |")
    md.append("\n")

    # ROI Metrics
    md.append("## ROI Metrics\n")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Mean ROI | ${roi_metrics.get('mean', 0.0):.2f} |")
    md.append(f"| Median ROI | ${roi_metrics.get('median', 0.0):.2f} |")
    md.append(f"| Min ROI | ${roi_metrics.get('min', 0.0):.2f} |")
    md.append(f"| Max ROI | ${roi_metrics.get('max', 0.0):.2f} |")
    md.append("\n")

    # Research Metrics
    md.append("## Research Metrics\n")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Similarity Hit Rate | {research_metrics.get('similarity_hit_rate', 0.0):.2%} |")
    md.append(f"| Avg Similarity Hits | {research_metrics.get('avg_similarity_hits', 0.0):.2f} |")
    md.append("\n")

    return "\n".join(md)


def export_markdown_dashboard(metrics: Dict, output_path: str) -> None:
    """
    Export Markdown dashboard to file.

    Parameters:
    -----------
    metrics : Dict
        Metrics dictionary
    output_path : str
        Path to write Markdown file

    Returns:
    --------
    None
        Writes Markdown to output_path
    """
    markdown = generate_markdown_dashboard(metrics)

    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(markdown)

        logger.info(f"Exported Markdown dashboard to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting Markdown dashboard: {e}")
        raise
