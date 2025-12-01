"""
Example usage of the Phase 4 multi-agent system.

Demonstrates the full pipeline from sensor data to work order generation.
This script shows how to use the root agent to orchestrate diagnostic,
research, and recommendation agents in sequence.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import from agents
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.root_agent import RootAgent


def print_section_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    """
    Main example demonstrating multi-agent pipeline execution.
    """
    print_section_header("PHASE 4 MULTI-AGENT MAINTENANCE SYSTEM - DEMO")

    # Initialize root agent
    root_agent = RootAgent()
    print("\n[OK] Root agent initialized")
    print("  - Diagnostic Agent: Ready")
    print("  - Research Agent: Ready")
    print("  - Recommendation Agent: Ready")

    # Sample sensor data (from NASA Turbofan Engine dataset)
    sensor_values = {
        "sensor_T30": 1605.2,
        "sensor_T50": 1450.8,
        "sensor_T2": 643.1,
        "sensor_T24": 1526.8,
        "sensor_T50_2": 1350.5,
        "sensor_P2": 551.2,
        "sensor_P15": 8.4,
        "sensor_P30": 390.1,
        "sensor_Nf": 2388.1,
        "sensor_Nc": 9046.2,
        "sensor_epr": 1.0,
        "sensor_Ps30": 1.02,
        "sensor_phi": 521.3,
        "sensor_NRf": 2388.1,
        "sensor_NRc": 8120.8,
        "sensor_BPR": 8.4,
        "sensor_farB": 0.03,
        "sensor_htBleed": 391.2,
        "sensor_Nf_dmd": 2388.0,
        "sensor_PCNfR_dmd": 100.0,
        "sensor_W31": 39.1,
        "sensor_W32": 23.3
    }

    print(f"\n[OK] Sample sensor data loaded ({len(sensor_values)} sensors)")

    # Execute pipeline with custom configuration
    print("\n[...] Executing multi-agent maintenance pipeline...")

    result = root_agent.execute_pipeline(
        unit_id=1,
        time_cycle=100,
        sensor_values=sensor_values,
        config={
            "diagnostic_method": "combined",
            "similarity_top_n": 3,
            "similarity_threshold": 0.6,
            "assigned_to": "Maintenance Team A"
        }
    )

    print("[OK] Pipeline execution completed")

    # =========================================================================
    # Display Results
    # =========================================================================

    print_section_header("PIPELINE EXECUTION RESULTS")

    print(f"\n{'Status':<25} {'[OK] SUCCESS' if result['success'] else '[FAIL] FAILED'}")
    print(f"{'Execution Time':<25} {result['execution_metadata']['total_time_ms']:.2f} ms")
    print(f"{'Agents Called':<25} {', '.join(result['execution_metadata']['agents_called'])}")

    if result['execution_metadata']['errors_encountered']:
        print(f"{'Errors':<25} {len(result['execution_metadata']['errors_encountered'])}")
        for error in result['execution_metadata']['errors_encountered']:
            print(f"  - {error}")

    # =========================================================================
    # Diagnostic Results
    # =========================================================================
    print_section_header("1. DIAGNOSTIC ANALYSIS")

    diagnostic = result['pipeline_results']['diagnostic']

    print(f"\n{'Anomaly Detected':<25} {'YES' if diagnostic['anomaly_detected'] else 'NO'}")
    print(f"{'Severity':<25} {diagnostic['severity'].upper()}")
    print(f"{'Anomaly Score':<25} {diagnostic['anomaly_score']:.4f}")
    print(f"{'Confidence':<25} {diagnostic['confidence']:.2%}")
    print(f"{'Method Used':<25} {diagnostic['method_used']}")

    if diagnostic['affected_sensors']:
        print(f"\n{'Affected Sensors':<25} {len(diagnostic['affected_sensors'])} sensors")
        for i, sensor in enumerate(diagnostic['affected_sensors'][:5], 1):
            print(f"  {i}. {sensor}")
        if len(diagnostic['affected_sensors']) > 5:
            print(f"  ... and {len(diagnostic['affected_sensors']) - 5} more")

    if diagnostic['top_recommendation']:
        print(f"\n{'Top Recommendation':<25} {diagnostic['top_recommendation']}")

    # =========================================================================
    # Research Results
    # =========================================================================
    if 'research' in result['pipeline_results']:
        print_section_header("2. SIMILAR FAILURES RESEARCH")

        research = result['pipeline_results']['research']
        print(f"\n{'Matches Found':<25} {research['matches_found']}")

        if research['matches_found'] > 0:
            print("\nHistorical Failure Analysis:")
            for i, match in enumerate(research['similar_failures'], 1):
                print(f"\n  Match #{i}:")
                print(f"    {'Similarity Score':<23} {match['similarity_score']:.2%}")
                print(f"    {'Failure Type':<23} {match['failure_type']}")
                print(f"    {'Root Cause':<23} {match['root_cause']}")
                print(f"    {'Action Taken':<23} {match['action_taken']}")

                if match.get('parts_replaced'):
                    parts = ', '.join(match['parts_replaced'][:3])
                    print(f"    {'Parts Replaced':<23} {parts}")

                print(f"    {'Average Cost':<23} ${match['avg_cost']:.2f}")
                print(f"    {'Average Downtime':<23} {match['avg_downtime']:.1f} hours")
        else:
            print("\n  No similar historical failures found in database.")

    # =========================================================================
    # Recommendation Results
    # =========================================================================
    if 'recommendation' in result['pipeline_results']:
        print_section_header("3. RECOMMENDATIONS & ROI ANALYSIS")

        recommendation = result['pipeline_results']['recommendation']

        if recommendation.get('roi_analysis'):
            print("\nROI Analysis:")
            roi = recommendation['roi_analysis']
            print(f"  {'Preventive Cost':<25} ${roi['estimated_preventive_cost']:,.2f}")
            print(f"  {'Reactive Cost':<25} ${roi['estimated_reactive_cost']:,.2f}")
            print(f"  {'Expected Savings':<25} ${roi['expected_savings']:,.2f}")
            print(f"  {'ROI Percentage':<25} {roi['roi_percentage']:.1f}%")
            print(f"  {'Recommendation':<25} {roi['recommendation'].upper()}")

        if recommendation.get('work_order'):
            print("\nWork Order Generated:")
            wo = recommendation['work_order']
            print(f"  {'Work Order ID':<25} {wo['work_order_id']}")
            print(f"  {'Priority':<25} {wo['priority'].upper()}")
            print(f"  {'Estimated Cost':<25} ${wo['estimated_cost']:,.2f}")
            print(f"  {'Estimated Duration':<25} {wo['estimated_duration']:.1f} hours")

            print(f"\n  {'Issue Summary':<25}")
            print(f"    {wo['issue_summary']}")

            if wo.get('recommended_actions'):
                print(f"\n  {'Recommended Actions':<25}")
                for i, action in enumerate(wo['recommended_actions'], 1):
                    print(f"    {i}. {action}")
        elif recommendation.get('message'):
            print(f"\n  {recommendation['message']}")

    # =========================================================================
    # Final Decision
    # =========================================================================
    print_section_header("4. FINAL DECISION")

    decision = result['final_decision']

    print(f"\n{'Action Required':<25} {'YES' if decision['action_required'] else 'NO'}")
    print(f"{'Priority':<25} {decision['priority'].upper()}")

    if decision.get('work_order_id'):
        print(f"{'Work Order ID':<25} {decision['work_order_id']}")

    if decision.get('estimated_cost'):
        print(f"{'Estimated Cost':<25} ${decision['estimated_cost']:,.2f}")

    print(f"\n{'Summary':<25}")
    print(f"  {decision['summary']}")

    if decision.get('recommended_actions'):
        print(f"\n{'Recommended Actions':<25}")
        for i, action in enumerate(decision['recommended_actions'], 1):
            print(f"  {i}. {action}")

    # =========================================================================
    # Save Results
    # =========================================================================
    print_section_header("OUTPUT FILE")

    output_file = Path(__file__).parent / "pipeline_results.json"

    # Convert result to JSON-serializable format
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n[OK] Full results saved to: {output_file}")
    print(f"  File size: {output_file.stat().st_size:,} bytes")

    # =========================================================================
    # Summary Statistics
    # =========================================================================
    print_section_header("SUMMARY STATISTICS")

    print(f"\n{'Equipment Unit ID':<25} {result['unit_id']}")
    print(f"{'Time Cycle':<25} {result['time_cycle']}")
    print(f"{'Sensors Analyzed':<25} {len(sensor_values)}")
    print(f"{'Agents Executed':<25} {len(result['execution_metadata']['agents_called'])}")
    print(f"{'Total Execution Time':<25} {result['execution_metadata']['total_time_ms']:.2f} ms")

    if result['success']:
        print("\n[OK] Pipeline completed successfully")
    else:
        print("\n[FAIL] Pipeline completed with errors")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error running example: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
