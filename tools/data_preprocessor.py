"""
NASA C-MAPSS Dataset Preprocessing Tool

This module processes the raw NASA C-MAPSS turbofan engine degradation dataset,
converting space-delimited data to structured CSV with column headers and
calculating Remaining Useful Life (RUL) for each time cycle.

Author: Predictive Maintenance Agent
Date: December 1, 2025
"""

import pandas as pd
import os
import numpy as np
from typing import Dict, Optional


# Column Schema Definition (26 raw columns)
COLUMN_NAMES = [
    'unit_id',           # Column 0: Engine unit identifier
    'time_cycle',        # Column 1: Operational cycle number
    'op_setting_1',      # Column 2: Operational setting 1
    'op_setting_2',      # Column 3: Operational setting 2
    'op_setting_3',      # Column 4: Operational setting 3
    'sensor_1',          # Column 5: Sensor measurement 1
    'sensor_2',          # Column 6: Sensor measurement 2
    'sensor_3',          # Column 7: Sensor measurement 3
    'sensor_4',          # Column 8: Sensor measurement 4
    'sensor_5',          # Column 9: Sensor measurement 5
    'sensor_6',          # Column 10: Sensor measurement 6
    'sensor_7',          # Column 11: Sensor measurement 7
    'sensor_8',          # Column 12: Sensor measurement 8
    'sensor_9',          # Column 13: Sensor measurement 9
    'sensor_10',         # Column 14: Sensor measurement 10
    'sensor_11',         # Column 15: Sensor measurement 11
    'sensor_12',         # Column 16: Sensor measurement 12
    'sensor_13',         # Column 17: Sensor measurement 13
    'sensor_14',         # Column 18: Sensor measurement 14
    'sensor_15',         # Column 19: Sensor measurement 15
    'sensor_16',         # Column 20: Sensor measurement 16
    'sensor_17',         # Column 21: Sensor measurement 17
    'sensor_18',         # Column 22: Sensor measurement 18
    'sensor_19',         # Column 23: Sensor measurement 19
    'sensor_20',         # Column 24: Sensor measurement 20
    'sensor_21'          # Column 25: Sensor measurement 21
]


def explore_raw_data(input_path: str) -> None:
    """
    Explore and display raw dataset statistics.

    Parameters:
    -----------
    input_path : str
        Path to raw sensor_data.csv file
    """
    print("\n" + "="*60)
    print("NASA C-MAPSS DATA EXPLORATION")
    print("="*60)

    # Read raw data
    df_raw = pd.read_csv(input_path, sep=r'\s+', header=None)

    print(f"\n1. Dataset Shape:")
    print(f"   Rows: {df_raw.shape[0]:,}")
    print(f"   Columns: {df_raw.shape[1]}")
    print(f"   Expected columns: 26")
    print(f"   Column match: {'PASS' if df_raw.shape[1] == 26 else 'FAIL'}")

    print(f"\n2. Missing Values:")
    missing_count = df_raw.isnull().sum().sum()
    print(f"   Total missing: {missing_count}")
    print(f"   Status: {'PASS - No missing values' if missing_count == 0 else 'FAIL - Has missing values'}")

    print(f"\n3. Data Types:")
    print(f"   All numeric: {'PASS' if all(df_raw.dtypes.apply(lambda x: x in ['int64', 'float64'])) else 'FAIL'}")

    print(f"\n4. Basic Statistics:")
    print(f"   Column 0 (unit_id) range: {df_raw[0].min()} to {df_raw[0].max()}")
    print(f"   Column 1 (time_cycle) max: {df_raw[1].max()}")
    print(f"   Unique units: {df_raw[0].nunique()}")

    print(f"\n5. First Row Sample:")
    print(f"   {list(df_raw.iloc[0].values[:10])}...")

    print("\n" + "="*60)


def calculate_rul(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Remaining Useful Life (RUL) for each row.

    RUL = max_cycle_for_unit - current_cycle

    For each unit (engine), the RUL decreases as the cycle number increases,
    reaching 0 at the final cycle (failure point).

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'unit_id' and 'time_cycle' columns

    Returns:
    --------
    pd.DataFrame
        Original DataFrame with 'RUL' column added
    """
    # Group by unit_id and find max cycle for each unit
    max_cycles = df.groupby('unit_id')['time_cycle'].max().reset_index()
    max_cycles.columns = ['unit_id', 'max_cycle']

    # Merge max_cycle back to original dataframe
    df = df.merge(max_cycles, on='unit_id', how='left')

    # Calculate RUL
    df['RUL'] = df['max_cycle'] - df['time_cycle']

    # Drop temporary max_cycle column
    df = df.drop('max_cycle', axis=1)

    return df


def validate_rul(df: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate RUL calculations are correct.

    Checks:
    - RUL is monotonically decreasing within each unit
    - RUL reaches 0 at final cycle for each unit
    - RUL is non-negative

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'RUL' column

    Returns:
    --------
    dict
        Validation results with pass/fail status and error messages
    """
    results = {
        'rul_non_negative': True,
        'rul_monotonic': True,
        'rul_ends_at_zero': True,
        'errors': []
    }

    # Check non-negative
    if (df['RUL'] < 0).any():
        results['rul_non_negative'] = False
        results['errors'].append('Found negative RUL values')

    # Check each unit
    for unit_id in df['unit_id'].unique():
        unit_data = df[df['unit_id'] == unit_id].sort_values('time_cycle')

        # Check monotonically decreasing
        rul_values = unit_data['RUL'].values
        if not all(rul_values[i] >= rul_values[i+1] for i in range(len(rul_values)-1)):
            results['rul_monotonic'] = False
            results['errors'].append(f'Unit {unit_id}: RUL not monotonically decreasing')
            break  # Only report first error

        # Check ends at 0
        if unit_data['RUL'].iloc[-1] != 0:
            results['rul_ends_at_zero'] = False
            results['errors'].append(f'Unit {unit_id}: Final RUL = {unit_data["RUL"].iloc[-1]}, expected 0')
            break  # Only report first error

    return results


def validate_processed_data(csv_path: str) -> Dict[str, bool]:
    """
    Validate final processed dataset meets all requirements.

    Parameters:
    -----------
    csv_path : str
        Path to processed CSV file

    Returns:
    --------
    dict
        Validation results
    """
    df = pd.read_csv(csv_path)

    results = {
        'correct_shape': df.shape == (20630, 27),
        'has_rul': 'RUL' in df.columns,
        'no_missing': df.isnull().sum().sum() == 0,
        'correct_dtypes': True,
        'rul_valid': True,
        'errors': []
    }

    # Check shape
    if df.shape != (20630, 27):
        results['errors'].append(f"Shape is {df.shape}, expected (20630, 27)")

    # Check RUL column exists
    if 'RUL' not in df.columns:
        results['errors'].append("RUL column not found")
        return results

    # Check data types
    if df['unit_id'].dtype not in ['int64', 'int32']:
        results['correct_dtypes'] = False
        results['errors'].append(f"unit_id dtype is {df['unit_id'].dtype}, expected int")

    # Check RUL range
    if df['RUL'].min() != 0:
        results['rul_valid'] = False
        results['errors'].append(f"RUL min is {df['RUL'].min()}, expected 0")

    if df['RUL'].max() < 100:
        results['rul_valid'] = False
        results['errors'].append(f"RUL max is {df['RUL'].max()}, seems too low")

    # Check missing values
    missing = df.isnull().sum().sum()
    if missing > 0:
        results['errors'].append(f"Found {missing} missing values")

    return results


def process_cmapss_data(
    input_path: str,
    output_path: str,
    add_rul: bool = True,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Convert raw NASA C-MAPSS data to structured CSV with headers and RUL.

    This is the main processing function that:
    1. Reads space-delimited raw data
    2. Validates column count (must be 26)
    3. Applies column names
    4. Calculates RUL values
    5. Validates RUL calculations
    6. Saves processed data to CSV

    Parameters:
    -----------
    input_path : str
        Path to raw sensor_data.csv
    output_path : str
        Path to save processed CSV
    add_rul : bool
        Whether to calculate and add RUL column (default: True)
    verbose : bool
        Print progress messages (default: True)

    Returns:
    --------
    pd.DataFrame
        Processed dataframe with headers and RUL

    Raises:
    -------
    FileNotFoundError : If input file doesn't exist
    ValueError : If data validation fails
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Processing NASA C-MAPSS Dataset")
        print(f"{'='*60}")
        print(f"Reading raw data from: {input_path}")

    # Check input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read raw data (space-delimited, no headers)
    df = pd.read_csv(input_path, sep=r'\s+', header=None)

    if verbose:
        print(f"Loaded data shape: {df.shape}")

    # Validate column count
    if df.shape[1] != 26:
        raise ValueError(f"Expected 26 columns, found {df.shape[1]}")

    # Apply column names
    df.columns = COLUMN_NAMES

    if verbose:
        print("[OK] Applied column names")

    # Calculate RUL if requested
    if add_rul:
        df = calculate_rul(df)
        if verbose:
            print("[OK] Calculated RUL values")

        # Validate RUL
        validation = validate_rul(df)
        if not all([validation['rul_non_negative'],
                    validation['rul_monotonic'],
                    validation['rul_ends_at_zero']]):
            raise ValueError(f"RUL validation failed: {validation['errors']}")

        if verbose:
            print("[OK] RUL validation passed")

    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        if verbose:
            print(f"[OK] Created output directory: {output_dir}")

    # Save processed data
    df.to_csv(output_path, index=False)

    if verbose:
        print(f"[OK] Saved processed data to: {output_path}")
        print(f"\nFinal Statistics:")
        print(f"  Shape: {df.shape}")
        print(f"  Units: {df['unit_id'].nunique()}")
        print(f"  Total cycles: {len(df):,}")
        print(f"  Columns: {len(df.columns)}")
        if add_rul:
            print(f"  RUL range: {df['RUL'].min()} to {df['RUL'].max()}")
        print(f"{'='*60}\n")

    return df


def test_rul_calculation():
    """
    Run automated tests on RUL calculation function.

    Returns:
    --------
    bool
        True if all tests pass
    """
    print("\n" + "="*60)
    print("Testing RUL Calculation Function")
    print("="*60)

    # Create test data
    test_df = pd.DataFrame({
        'unit_id': [1, 1, 1, 2, 2, 3, 3, 3, 3],
        'time_cycle': [1, 2, 3, 1, 2, 1, 2, 3, 4],
        'sensor_1': [100, 101, 102, 100, 101, 100, 101, 102, 103]
    })

    print("\nTest Data:")
    print(test_df)

    # Calculate RUL
    result = calculate_rul(test_df)

    print("\nResult with RUL:")
    print(result[['unit_id', 'time_cycle', 'RUL']])

    # Verify Unit 1: cycles 1,2,3 -> RUL 2,1,0
    unit1_rul = list(result[result['unit_id']==1]['RUL'].values)
    assert unit1_rul == [2, 1, 0], f"Unit 1 RUL failed: expected [2,1,0], got {unit1_rul}"
    print("[PASS] Unit 1 RUL correct: [2, 1, 0]")

    # Verify Unit 2: cycles 1,2 -> RUL 1,0
    unit2_rul = list(result[result['unit_id']==2]['RUL'].values)
    assert unit2_rul == [1, 0], f"Unit 2 RUL failed: expected [1,0], got {unit2_rul}"
    print("[PASS] Unit 2 RUL correct: [1, 0]")

    # Verify Unit 3: cycles 1,2,3,4 -> RUL 3,2,1,0
    unit3_rul = list(result[result['unit_id']==3]['RUL'].values)
    assert unit3_rul == [3, 2, 1, 0], f"Unit 3 RUL failed: expected [3,2,1,0], got {unit3_rul}"
    print("[PASS] Unit 3 RUL correct: [3, 2, 1, 0]")

    # Test validation function
    validation = validate_rul(result)
    assert all([validation['rul_non_negative'],
                validation['rul_monotonic'],
                validation['rul_ends_at_zero']]), f"Validation failed: {validation}"
    print("[PASS] RUL validation function works correctly")

    print("\n" + "="*60)
    print("All Tests Passed!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Process NASA C-MAPSS turbofan engine degradation dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python data_preprocessor.py --explore
  python data_preprocessor.py --test
  python data_preprocessor.py --input sensor_data.csv --output data/cmapss_processed.csv
        """
    )

    parser.add_argument('--input', type=str, default='sensor_data.csv',
                        help='Input CSV file path (default: sensor_data.csv)')
    parser.add_argument('--output', type=str, default='data/cmapss_processed.csv',
                        help='Output CSV file path (default: data/cmapss_processed.csv)')
    parser.add_argument('--no-rul', action='store_true',
                        help='Skip RUL calculation')
    parser.add_argument('--explore', action='store_true',
                        help='Explore raw data statistics without processing')
    parser.add_argument('--test', action='store_true',
                        help='Run automated tests on RUL calculation')
    parser.add_argument('--validate', type=str,
                        help='Validate a processed CSV file')

    args = parser.parse_args()

    # Run exploration mode
    if args.explore:
        explore_raw_data(args.input)

    # Run test mode
    elif args.test:
        test_rul_calculation()

    # Run validation mode
    elif args.validate:
        print(f"\nValidating: {args.validate}")
        validation = validate_processed_data(args.validate)

        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)

        for key, value in validation.items():
            if key != 'errors':
                status = "[PASS]" if value else "[FAIL]"
                print(f"{status} {key}: {value}")

        if validation['errors']:
            print("\nErrors:")
            for error in validation['errors']:
                print(f"  - {error}")
        else:
            print("\n[OK] All validations passed!")

        print("="*60 + "\n")

    # Run processing mode
    else:
        try:
            df_processed = process_cmapss_data(
                input_path=args.input,
                output_path=args.output,
                add_rul=not args.no_rul
            )

            print("[SUCCESS] Processing complete!")
            print(f"\nQuick verification:")
            print(f"  Sample rows from processed data:")
            print(df_processed.head(3))

        except Exception as e:
            print(f"\n[ERROR] Error during processing: {e}")
            raise
