#!/usr/bin/env python
"""
Run Observability Check
=======================

CLI to run log monitoring, metrics aggregation, and generate observability report.

Usage:
    python scripts/run_observability_check.py --output-dir output/
    python scripts/run_observability_check.py --output-dir output/ --log-path output/run1/
    python scripts/run_observability_check.py --output-dir output/ --grafana
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.observability.log_monitor import generate_log_summary
from src.observability.metrics_summary import generate_observability_summary
from src.observability.grafana_exporter import (
    export_markdown_dashboard,
    export_dashboard,
    generate_markdown_dashboard
)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run observability check on Phase 5 simulation outputs'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        required=True,
        help='Directory containing simulation outputs (e.g., output/)'
    )
    parser.add_argument(
        '--log-path',
        type=str,
        default=None,
        help='Path to log files (optional, defaults to output-dir)'
    )
    parser.add_argument(
        '--grafana',
        action='store_true',
        help='Generate Grafana dashboard JSON (optional)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='observability_report',
        help='Output filename prefix (default: observability_report)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    logger.info("Starting observability check...")
    logger.info(f"Output directory: {args.output_dir}")

    # Validate output directory
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        logger.error(f"Output directory not found: {args.output_dir}")
        sys.exit(1)

    # Generate metrics summary
    logger.info("Generating metrics summary...")
    try:
        metrics_summary = generate_observability_summary(args.output_dir)
    except Exception as e:
        logger.error(f"Error generating metrics summary: {e}", exc_info=True)
        sys.exit(1)

    # Generate log summary if log path provided
    log_summary = None
    if args.log_path:
        logger.info(f"Generating log summary from {args.log_path}...")
        try:
            log_summary = generate_log_summary(args.log_path)
        except Exception as e:
            logger.error(f"Error generating log summary: {e}", exc_info=True)
    else:
        # Try to find logs in output directory
        for run_dir in output_dir.glob('*/'):
            if run_dir.is_dir():
                logger.info(f"Checking for logs in {run_dir}...")
                log_files = list(run_dir.glob('*.log'))
                if log_files:
                    try:
                        log_summary = generate_log_summary(str(run_dir))
                        break
                    except Exception as e:
                        logger.warning(f"Error parsing logs in {run_dir}: {e}")

    # Combine into observability report
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'output_dir': str(output_dir),
        'metrics_summary': metrics_summary,
        'log_summary': log_summary
    }

    # Write JSON report
    json_path = output_dir / f"{args.output}.json"
    logger.info(f"Writing JSON report to {json_path}...")
    try:
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"JSON report written to {json_path}")
    except Exception as e:
        logger.error(f"Error writing JSON report: {e}", exc_info=True)
        sys.exit(1)

    # Generate Markdown report
    md_path = output_dir / f"{args.output}.md"
    logger.info(f"Writing Markdown report to {md_path}...")
    try:
        markdown = generate_markdown_report(report)
        with open(md_path, 'w') as f:
            f.write(markdown)
        logger.info(f"Markdown report written to {md_path}")
    except Exception as e:
        logger.error(f"Error writing Markdown report: {e}", exc_info=True)

    # Generate Grafana dashboard if requested
    if args.grafana:
        logger.info("Generating Grafana dashboard...")
        try:
            # Use first metrics file for dashboard
            metrics_files = list(output_dir.glob('*/metrics.json'))
            if metrics_files:
                with open(metrics_files[0], 'r') as f:
                    metrics = json.load(f)

                grafana_path = output_dir / 'grafana_dashboard.json'
                export_dashboard(metrics, str(grafana_path))
                logger.info(f"Grafana dashboard written to {grafana_path}")
            else:
                logger.warning("No metrics files found for Grafana export")
        except Exception as e:
            logger.error(f"Error generating Grafana dashboard: {e}", exc_info=True)

    # Generate Markdown dashboard
    logger.info("Generating Markdown dashboard...")
    try:
        # Use aggregated metrics for dashboard
        if metrics_summary.get('cross_run_stats'):
            dashboard_md_path = output_dir / 'dashboard.md'
            export_markdown_dashboard(
                metrics_summary['cross_run_stats'],
                str(dashboard_md_path)
            )
            logger.info(f"Markdown dashboard written to {dashboard_md_path}")
    except Exception as e:
        logger.error(f"Error generating Markdown dashboard: {e}", exc_info=True)

    logger.info("Observability check completed successfully!")
    logger.info(f"Reports written to {output_dir}")


def generate_markdown_report(report: dict) -> str:
    """Generate Markdown report from observability report."""
    md = []
    md.append("# Observability Report\n")
    md.append(f"Generated: {report['timestamp']}\n")
    md.append(f"Output Directory: {report['output_dir']}\n")
    md.append("---\n\n")

    # Metrics Summary
    md.append("## Metrics Summary\n")
    metrics = report.get('metrics_summary', {})

    if 'error' in metrics:
        md.append(f"**Error:** {metrics['error']}\n\n")
    else:
        cross_run = metrics.get('cross_run_stats', {})
        stability = metrics.get('stability_scores', {})

        md.append(f"**Runs Analyzed:** {cross_run.get('run_count', 0)}\n\n")

        # Anomaly metrics
        md.append("### Anomaly Metrics\n")
        anomaly = cross_run.get('anomaly_metrics', {}).get('anomaly_rate', {})
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Mean Anomaly Rate | {anomaly.get('mean', 0.0):.2%} |")
        md.append(f"| Min | {anomaly.get('min', 0.0):.2%} |")
        md.append(f"| Max | {anomaly.get('max', 0.0):.2%} |")
        md.append("\n")

        # Stability scores
        md.append("### Stability Scores\n")
        md.append("| Metric | Stability Score |")
        md.append("|--------|-----------------|")
        for key, value in stability.items():
            if isinstance(value, dict) and 'stability_score' in value:
                score = value['stability_score']
                md.append(f"| {key.replace('_', ' ').title()} | {score:.2%} |")
        md.append("\n")

        # Execution metrics
        md.append("### Execution Metrics\n")
        execution = cross_run.get('execution', {})
        success = execution.get('success_rate', {})
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Mean Success Rate | {success.get('mean', 1.0):.2%} |")
        md.append(f"| Min Success Rate | {success.get('min', 1.0):.2%} |")
        md.append("\n")

    # Log Summary
    if report.get('log_summary'):
        md.append("## Log Summary\n")
        log_summary = report['log_summary']

        md.append(f"**Total Records:** {log_summary.get('total_records', 0)}\n\n")

        # Error counts
        errors = log_summary.get('error_counts', {})
        if errors:
            md.append("### Error Counts\n")
            md.append("| Error Type | Count |")
            md.append("|------------|-------|")
            for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                md.append(f"| {error_type} | {count} |")
            md.append("\n")

        # Latency stats
        latency = log_summary.get('latency_stats', {})
        if latency.get('count', 0) > 0:
            md.append("### Latency Statistics\n")
            md.append("| Metric | Value |")
            md.append("|--------|-------|")
            md.append(f"| Count | {latency['count']} |")
            md.append(f"| Min | {latency['min']:.3f}s |")
            md.append(f"| Max | {latency['max']:.3f}s |")
            md.append(f"| Average | {latency['avg']:.3f}s |")
            md.append(f"| P95 | {latency['p95']:.3f}s |")
            md.append(f"| Outliers | {latency['outlier_count']} |")
            md.append("\n")

    md.append("---\n")
    md.append("*Report generated by Phase 6 Observability Check*\n")

    return "\n".join(md)


if __name__ == '__main__':
    main()
