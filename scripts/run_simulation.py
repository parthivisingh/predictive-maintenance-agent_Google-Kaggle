"""
Simulation CLI Entry Point
==========================

Command-line interface for running batch simulations.
Fully scriptable with exit codes (0=success, non-zero=failure).
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.simulation.batch_processor import run_batch
from src.simulation.metrics_reporter import generate_report
from tools.logging_config import initialize_logging, get_logger


# ============================================================================
# CLI Argument Parser
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run batch equipment simulations through RootAgent pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run sequential batch with default settings
  python run_simulation.py --profiles data/profiles.json

  # Run parallel batch with 4 workers
  python run_simulation.py --profiles data/profiles.json --mode parallel --max-workers 4

  # Run with deterministic seed and fail-fast error policy
  python run_simulation.py --profiles data/profiles.json --seed 42 --error-policy fail-fast

  # Custom output directory
  python run_simulation.py --profiles data/profiles.json --output output/my_batch
        """
    )

    # Required arguments
    parser.add_argument(
        "--profiles",
        required=True,
        type=str,
        help="Path to JSON file with equipment profiles"
    )

    # Execution mode
    parser.add_argument(
        "--mode",
        type=str,
        default="sequential",
        choices=["sequential", "parallel"],
        help="Execution mode (default: sequential)"
    )

    # Error handling
    parser.add_argument(
        "--error-policy",
        type=str,
        default="skip",
        choices=["skip", "fail-fast"],
        help="Error handling policy (default: skip)"
    )

    # Parallel execution options
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Max parallel workers (default: 4, only for parallel mode)"
    )

    parser.add_argument(
        "--backoff",
        type=float,
        default=0.1,
        help="Backoff seconds between parallel submits (default: 0.1)"
    )

    # Deterministic execution
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base random seed for deterministic execution (default: None)"
    )

    # Timeouts and limits
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per run in seconds (default: 300)"
    )

    # Output options
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for reports (default: output/)"
    )

    parser.add_argument(
        "--formats",
        type=str,
        nargs="+",
        default=["json", "markdown"],
        choices=["json", "markdown", "full"],
        help="Output formats (default: json markdown)"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Log file path (default: console only)"
    )

    parser.add_argument(
        "--log-format",
        type=str,
        default="json",
        choices=["json", "text"],
        help="Log format (default: json)"
    )

    return parser


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main CLI entry point."""
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Initialize logging
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    initialize_logging(
        log_level=log_level_map[args.log_level],
        log_file=args.log_file,
        json_format=(args.log_format == "json")
    )

    logger = get_logger(__name__)

    try:
        # Load profiles
        logger.info(f"Loading profiles from {args.profiles}")
        with open(args.profiles, 'r') as f:
            profiles = json.load(f)

        if not isinstance(profiles, list):
            logger.error("Profiles file must contain a JSON array")
            print("ERROR: Profiles file must contain a JSON array", file=sys.stderr)
            sys.exit(1)

        if len(profiles) == 0:
            logger.warning("No profiles to run")
            print("WARNING: No profiles to run", file=sys.stderr)
            sys.exit(0)

        logger.info(f"Loaded {len(profiles)} profiles")

        # Run batch
        logger.info(
            f"Starting batch execution",
            extra={
                "mode": args.mode,
                "error_policy": args.error_policy,
                "max_workers": args.max_workers if args.mode == "parallel" else None,
                "base_seed": args.seed,
                "timeout_per_run": args.timeout
            }
        )

        batch_result = run_batch(
            profiles=profiles,
            mode=args.mode,
            error_policy=args.error_policy,
            max_workers=args.max_workers,
            backoff_seconds=args.backoff,
            base_random_seed=args.seed,
            timeout_per_run=args.timeout
        )

        # Generate reports
        logger.info(f"Generating reports in {args.output}")
        generate_report(
            batch_result=batch_result,
            output_path=args.output,
            output_formats=args.formats
        )

        # Print summary
        print("\n" + "="*80)
        print("BATCH EXECUTION SUMMARY")
        print("="*80)
        print(f"Batch ID:        {batch_result['batch_id']}")
        print(f"Total Runs:      {batch_result['total_runs']}")
        print(f"Successful:      {batch_result['successful_runs']}")
        print(f"Failed:          {len(batch_result['failed_runs'])}")
        print(f"Duration:        {batch_result['duration_sec']:.2f}s")
        print()

        # Print metrics summary
        summary = batch_result.get('summary_metrics', {})
        print("METRICS SUMMARY")
        print("-"*80)
        print(f"Anomaly Rate:    {summary.get('anomaly_rate', 0.0):.2%}")

        roi_dist = summary.get('roi_distribution')
        if roi_dist:
            print(f"Avg ROI:         ${roi_dist.get('mean', 0.0):.2f}")
            print(f"ROI Range:       ${roi_dist.get('min', 0.0):.2f} - ${roi_dist.get('max', 0.0):.2f}")

        print(f"Similarity Hit:  {summary.get('similarity_hit_rate', 0.0):.2%}")
        print()

        # Print output locations
        print("OUTPUT FILES")
        print("-"*80)
        if "json" in args.formats:
            print(f"Metrics JSON:    {os.path.join(args.output, 'metrics.json')}")
        if "markdown" in args.formats:
            print(f"Metrics MD:      {os.path.join(args.output, 'metrics.md')}")
        if "full" in args.formats:
            print(f"Full Result:     {os.path.join(args.output, 'batch_result.json')}")
        print("="*80)
        print()

        # Exit with success
        logger.info("Batch execution completed successfully")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e.filename}")
        print(f"ERROR: File not found: {e.filename}", file=sys.stderr)
        sys.exit(1)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in profiles file: {e.msg}")
        print(f"ERROR: Invalid JSON in profiles file: {e.msg}", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Batch execution interrupted by user")
        print("\nINTERRUPTED: Batch execution cancelled by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT

    except Exception as e:
        logger.error(f"Batch execution failed: {type(e).__name__}: {str(e)}", exc_info=True)
        print(f"ERROR: Batch execution failed: {type(e).__name__}: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
