#!/usr/bin/env python
"""
Generate Evaluation Report
===========================

CLI to run model quality and system health evaluation, output evaluation report.

Usage:
    python scripts/generate_eval_report.py --output-dir output/
    python scripts/generate_eval_report.py --metrics-files output/run1/metrics.json output/run2/metrics.json
    python scripts/generate_eval_report.py --output-dir output/ --ground-truth data/ground_truth.csv
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.model_quality import generate_quality_report
from src.evaluation.system_health import generate_health_report, analyze_error_distribution
from src.observability.metrics_summary import load_metrics, find_all_metrics_files

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
        description='Generate evaluation report for Phase 5 simulation outputs'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory containing simulation outputs (will find all metrics.json)'
    )
    parser.add_argument(
        '--metrics-files',
        nargs='+',
        type=str,
        help='Specific metrics.json files to evaluate'
    )
    parser.add_argument(
        '--ground-truth',
        type=str,
        default=None,
        help='Path to ground truth CSV file (optional)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='evaluation_report',
        help='Output filename prefix (default: evaluation_report)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Validate inputs
    if not args.output_dir and not args.metrics_files:
        logger.error("Must provide either --output-dir or --metrics-files")
        parser.print_help()
        sys.exit(1)

    logger.info("Starting evaluation report generation...")

    # Find metrics files
    if args.metrics_files:
        metrics_files = args.metrics_files
        output_path = Path(args.metrics_files[0]).parent.parent
    else:
        output_path = Path(args.output_dir)
        if not output_path.exists():
            logger.error(f"Output directory not found: {args.output_dir}")
            sys.exit(1)

        logger.info(f"Searching for metrics files in {output_path}...")
        metrics_files = find_all_metrics_files(str(output_path))

        if not metrics_files:
            logger.error(f"No metrics files found in {output_path}")
            sys.exit(1)

    logger.info(f"Found {len(metrics_files)} metrics file(s)")

    # Load all metrics
    logger.info("Loading metrics...")
    try:
        metrics_list = load_metrics(metrics_files)
    except Exception as e:
        logger.error(f"Error loading metrics: {e}", exc_info=True)
        sys.exit(1)

    if not metrics_list:
        logger.error("No valid metrics loaded")
        sys.exit(1)

    logger.info(f"Loaded {len(metrics_list)} metrics file(s)")

    # Generate quality report
    logger.info("Evaluating model quality...")
    try:
        quality_report = generate_quality_report(
            metrics_list,
            ground_truth_path=args.ground_truth
        )
    except Exception as e:
        logger.error(f"Error generating quality report: {e}", exc_info=True)
        sys.exit(1)

    # Generate health report (use first metrics for health)
    logger.info("Evaluating system health...")
    try:
        health_report = generate_health_report(metrics_list[0])
    except Exception as e:
        logger.error(f"Error generating health report: {e}", exc_info=True)
        sys.exit(1)

    # Analyze error distribution
    logger.info("Analyzing error distribution...")
    try:
        error_dist = analyze_error_distribution({'results': []})  # Will be empty for metrics.json
    except Exception as e:
        logger.warning(f"Error analyzing error distribution: {e}")
        error_dist = {'total_errors': 0, 'error_types': {}}

    # Combine into evaluation report
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'metrics_files_analyzed': len(metrics_list),
        'ground_truth_provided': args.ground_truth is not None,
        'quality': quality_report,
        'health': health_report,
        'error_distribution': error_dist
    }

    # Write JSON report
    json_path = output_path / f"{args.output}.json"
    logger.info(f"Writing JSON report to {json_path}...")
    try:
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"JSON report written to {json_path}")
    except Exception as e:
        logger.error(f"Error writing JSON report: {e}", exc_info=True)
        sys.exit(1)

    # Generate Markdown report
    md_path = output_path / f"{args.output}.md"
    logger.info(f"Writing Markdown report to {md_path}...")
    try:
        markdown = generate_markdown_report(report)
        with open(md_path, 'w') as f:
            f.write(markdown)
        logger.info(f"Markdown report written to {md_path}")
    except Exception as e:
        logger.error(f"Error writing Markdown report: {e}", exc_info=True)

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("EVALUATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Overall Quality Score: {quality_report['overall_quality_score']:.2%}")
    logger.info(f"Health Score: {health_report['health_score']:.2%} ({health_report['status']})")
    logger.info(f"Success Rate: {health_report['metrics']['success_rate']:.2%}")

    if quality_report.get('accuracy'):
        logger.info(f"Accuracy: {quality_report['accuracy']['score']:.2%}")

    logger.info(f"Stability Score: {quality_report['stability']['overall_stability_score']:.2%}")
    logger.info(f"ROI Reliability: {quality_report['roi_reliability']['reliability_score']:.2%}")
    logger.info("="*60)

    logger.info(f"\nReports written to {output_path}")
    logger.info("Evaluation completed successfully!")


def generate_markdown_report(report: dict) -> str:
    """Generate Markdown report from evaluation report."""
    md = []
    md.append("# Evaluation Report\n")
    md.append(f"Generated: {report['timestamp']}\n")
    md.append(f"Metrics Files Analyzed: {report['metrics_files_analyzed']}\n")
    md.append("---\n\n")

    # Quality Metrics
    md.append("## Model Quality Evaluation\n")
    quality = report.get('quality', {})

    md.append(f"**Overall Quality Score:** {quality.get('overall_quality_score', 0.0):.2%}\n\n")

    # Accuracy
    if quality.get('accuracy'):
        md.append("### Accuracy\n")
        accuracy = quality['accuracy']
        if 'error' in accuracy:
            md.append(f"*Error:* {accuracy['error']}\n\n")
        else:
            md.append(f"- **Score:** {accuracy['score']:.2%}\n")
            md.append(f"- **Ground Truth Samples:** {accuracy.get('ground_truth_samples', 0)}\n\n")

    # Stability
    md.append("### Stability\n")
    stability = quality.get('stability', {})
    md.append(f"- **Overall Stability Score:** {stability.get('overall_stability_score', 0.0):.2%}\n")
    md.append(f"- **Anomaly Rate Stability:** {stability.get('anomaly_stability_score', 0.0):.2%}\n")
    md.append(f"- **ROI Stability:** {stability.get('roi_stability_score', 0.0):.2%}\n")
    md.append(f"- **Runs Analyzed:** {stability.get('run_count', 0)}\n\n")

    # Anomaly Rate Statistics
    anomaly = stability.get('anomaly_rate', {})
    if anomaly:
        md.append("#### Anomaly Rate Statistics\n")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| Mean | {anomaly.get('mean', 0.0):.2%} |")
        md.append(f"| Std Dev | {anomaly.get('std', 0.0):.4f} |")
        md.append(f"| Min | {anomaly.get('min', 0.0):.2%} |")
        md.append(f"| Max | {anomaly.get('max', 0.0):.2%} |")
        md.append("\n")

    # Similarity Quality
    md.append("### Similarity Search Quality\n")
    md.append(f"**Score:** {quality.get('similarity_quality', 0.0):.2%}\n\n")

    # ROI Reliability
    md.append("### ROI Reliability\n")
    roi = quality.get('roi_reliability', {})
    md.append(f"- **Reliability Score:** {roi.get('reliability_score', 0.0):.2%}\n")
    md.append(f"- **Mean ROI:** ${roi.get('mean', 0.0):.2f}\n")
    md.append(f"- **Median ROI:** ${roi.get('median', 0.0):.2f}\n")
    md.append(f"- **Std Dev:** ${roi.get('std', 0.0):.2f}\n")
    md.append(f"- **Outliers Detected:** {roi.get('outlier_count', 0)}\n\n")

    # System Health
    md.append("## System Health\n")
    health = report.get('health', {})

    md.append(f"**Health Score:** {health.get('health_score', 0.0):.2%} ({health.get('status', 'unknown').upper()})\n\n")

    # Health Metrics
    md.append("### Metrics\n")
    metrics = health.get('metrics', {})
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Success Rate | {metrics.get('success_rate', 1.0):.2%} |")
    md.append(f"| Total Runs | {metrics.get('total_runs', 0)} |")
    md.append(f"| Failed Runs | {metrics.get('failed_runs', 0)} |")
    md.append(f"| Timeout Count | {metrics.get('timeout_count', 0)} |")
    md.append("\n")

    # Performance
    md.append("### Performance\n")
    perf = health.get('performance', {})
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Average Duration | {perf.get('avg_duration_sec', 0.0):.3f}s |")
    md.append(f"| Min Duration | {perf.get('min_duration_sec', 0.0):.3f}s |")
    md.append(f"| Max Duration | {perf.get('max_duration_sec', 0.0):.3f}s |")
    md.append(f"| Degradation Detected | {'Yes' if perf.get('degradation_detected') else 'No'} |")
    if perf.get('degradation_detected'):
        md.append(f"| Degradation Score | {perf.get('degradation_score', 0.0):.2%} |")
    md.append("\n")

    # Recommendations
    md.append("### Recommendations\n")
    recommendations = health.get('recommendations', [])
    for rec in recommendations:
        md.append(f"- {rec}")
    md.append("\n")

    # Error Distribution
    error_dist = report.get('error_distribution', {})
    if error_dist.get('total_errors', 0) > 0:
        md.append("## Error Distribution\n")
        md.append(f"**Total Errors:** {error_dist['total_errors']}\n")
        md.append(f"**Error Rate:** {error_dist.get('error_rate', 0.0):.2%}\n\n")

        error_types = error_dist.get('error_types', {})
        if error_types:
            md.append("### Error Types\n")
            md.append("| Error Type | Count |")
            md.append("|------------|-------|")
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                md.append(f"| {error_type} | {count} |")
            md.append("\n")

    md.append("---\n")
    md.append("*Report generated by Phase 6 Evaluation*\n")

    return "\n".join(md)


if __name__ == '__main__':
    main()
