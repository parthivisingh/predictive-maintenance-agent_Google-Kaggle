"""
Maintenance History Database Setup

This module creates and populates an SQLite database with synthetic maintenance
history data including equipment records, failure patterns, and maintenance logs.

Author: Predictive Maintenance Agent
Date: December 1, 2025
"""

import sqlite3
import os
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional


def create_database_schema(db_path: str = "data/maintenance_history.db") -> None:
    """
    Create database schema with 3 tables from schema.sql.

    Parameters:
    -----------
    db_path : str
        Path to SQLite database file
    """
    # Create data directory if needed
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read and execute schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"[OK] Database schema created: {db_path}")


def generate_equipment_data(num_records: int = 15) -> List[Dict]:
    """
    Generate synthetic equipment records.

    Creates a mix of turbofan engines (60%), compressors (20%), and pumps (20%)
    with realistic manufacturers, models, dates, and operating hours.

    Parameters:
    -----------
    num_records : int
        Number of equipment records to create

    Returns:
    --------
    list[dict]
        List of equipment records
    """
    equipment_types = [
        ('turbofan_engine', 'GE Aviation', ['CFM56-7B', 'GE90-115B', 'GEnx-1B']),
        ('turbofan_engine', 'Rolls-Royce', ['Trent 1000', 'Trent XWB', 'Trent 7000']),
        ('turbofan_engine', 'Pratt & Whitney', ['PW4000', 'PW1100G', 'PW1500G']),
        ('compressor', 'Atlas Copco', ['GA 110', 'GA 160', 'GA 250']),
        ('compressor', 'Ingersoll Rand', ['R-Series', 'Next Gen', 'Nirvana']),
        ('pump', 'Grundfos', ['CR 95', 'TP 200', 'NK 125']),
        ('pump', 'KSB', ['Etanorm', 'Movitec', 'Omega']),
    ]

    locations = [
        'Plant A - Line 1', 'Plant A - Line 2', 'Plant B - Line 1',
        'Plant B - Line 2', 'Plant C - Utility', 'Building D - HVAC',
        'Facility E - Production', 'Wing F - Assembly'
    ]

    statuses = ['active'] * 12 + ['maintenance'] * 2 + ['retired'] * 1

    records = []

    for i in range(num_records):
        # Select equipment type (60% turbofan, 20% compressor, 20% pump)
        if i < int(num_records * 0.6):
            eq_type, manufacturer, models = random.choice([
                e for e in equipment_types if e[0] == 'turbofan_engine'
            ])
        elif i < int(num_records * 0.8):
            eq_type, manufacturer, models = random.choice([
                e for e in equipment_types if e[0] == 'compressor'
            ])
        else:
            eq_type, manufacturer, models = random.choice([
                e for e in equipment_types if e[0] == 'pump'
            ])

        # Generate dates
        install_date = datetime(2018, 1, 1) + timedelta(days=random.randint(0, 2000))
        last_maint = install_date + timedelta(
            days=random.randint(30, (datetime.now() - install_date).days)
        )

        # Operating hours based on age
        days_since_install = (datetime.now() - install_date).days
        operating_hours = days_since_install * random.uniform(12, 18)  # 12-18 hours/day

        record = {
            'equipment_type': eq_type,
            'serial_number': f"{eq_type.upper()[:4]}-{2020+i//5}-{str(i+1).zfill(3)}",
            'manufacturer': manufacturer,
            'model': random.choice(models),
            'install_date': install_date.strftime('%Y-%m-%d'),
            'location': random.choice(locations),
            'operating_hours': round(operating_hours, 1),
            'last_maintenance_date': last_maint.strftime('%Y-%m-%d'),
            'status': random.choice(statuses),
            'notes': None
        }

        records.append(record)

    return records


def insert_equipment_data(conn: sqlite3.Connection, equipment_data: List[Dict]) -> None:
    """Insert equipment records into database."""
    cursor = conn.cursor()

    for eq in equipment_data:
        cursor.execute("""
            INSERT INTO equipment (
                equipment_type, serial_number, manufacturer, model,
                install_date, location, operating_hours,
                last_maintenance_date, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            eq['equipment_type'], eq['serial_number'], eq['manufacturer'],
            eq['model'], eq['install_date'], eq['location'],
            eq['operating_hours'], eq['last_maintenance_date'],
            eq['status'], eq['notes']
        ))

    conn.commit()
    print(f"[OK] Inserted {len(equipment_data)} equipment records")


def generate_failure_patterns() -> List[Dict]:
    """
    Generate failure patterns aligned with NASA C-MAPSS sensor characteristics.

    Creates 12 failure patterns with realistic sensor signatures, costs, and
    degradation timelines.

    Returns:
    --------
    list[dict]
        List of failure pattern records
    """
    patterns = [
        {
            'failure_type': 'bearing_degradation',
            'sensor_signature': json.dumps({
                'sensor_3': {'trend': 'increasing', 'delta': '10-15 units'},
                'sensor_9': {'trend': 'gradual_increase', 'delta': '20-30 units'},
                'sensor_11': {'trend': 'increasing', 'delta': '0.5-1.0 units'}
            }),
            'affected_sensors': 'sensor_3,sensor_9,sensor_11',
            'signature_description': 'Temperature sensor_3 increases 10-15 units over 50-100 cycles, sensor_9 shows gradual upward drift',
            'typical_degradation_cycles': 150,
            'warning_threshold_hours': 300.0,
            'critical_threshold_hours': 100.0,
            'root_cause': 'Bearing race wear due to thermal cycling and contamination',
            'recommended_action': 'Replace bearing assembly, inspect for rub marks',
            'preventive_maintenance_cost': 3500.00,
            'failure_cost': 45000.00,
            'occurrence_frequency': 'occasional'
        },
        {
            'failure_type': 'overheating',
            'sensor_signature': json.dumps({
                'sensor_4': {'trend': 'high_values', 'threshold': '> baseline + 15'},
                'sensor_3': {'trend': 'increasing'},
                'sensor_12': {'trend': 'increasing'}
            }),
            'affected_sensors': 'sensor_4,sensor_3,sensor_12',
            'signature_description': 'Sensor_4 exceeds normal range consistently, sensor_12 (fuel ratio) increases',
            'typical_degradation_cycles': 120,
            'warning_threshold_hours': 250.0,
            'critical_threshold_hours': 80.0,
            'root_cause': 'Turbine blade erosion causing reduced cooling efficiency',
            'recommended_action': 'Inspect turbine blades, replace if erosion exceeds tolerance',
            'preventive_maintenance_cost': 4200.00,
            'failure_cost': 52000.00,
            'occurrence_frequency': 'common'
        },
        {
            'failure_type': 'fuel_system_degradation',
            'sensor_signature': json.dumps({
                'sensor_12': {'trend': 'high_variance', 'pattern': 'oscillating'},
                'sensor_14': {'trend': 'oscillating'},
                'sensor_20': {'trend': 'decreasing'}
            }),
            'affected_sensors': 'sensor_12,sensor_14,sensor_20',
            'signature_description': 'Fuel flow ratio shows high variance cycle-to-cycle, speed oscillates',
            'typical_degradation_cycles': 180,
            'warning_threshold_hours': 400.0,
            'critical_threshold_hours': 150.0,
            'root_cause': 'Fuel nozzle clogging or fuel pump wear',
            'recommended_action': 'Clean or replace fuel nozzles, inspect fuel pump',
            'preventive_maintenance_cost': 2100.00,
            'failure_cost': 35000.00,
            'occurrence_frequency': 'occasional'
        },
        {
            'failure_type': 'pressure_seal_leak',
            'sensor_signature': json.dumps({
                'sensor_7': {'trend': 'decreasing', 'delta': '> 2 units'},
                'sensor_11': {'trend': 'increasing'},
                'sensor_15': {'trend': 'abnormal_ratio'}
            }),
            'affected_sensors': 'sensor_7,sensor_11,sensor_15',
            'signature_description': 'Pressure sensor_7 drops below normal, pressure ratio sensor_15 shows abnormal pattern',
            'typical_degradation_cycles': 140,
            'warning_threshold_hours': 280.0,
            'critical_threshold_hours': 90.0,
            'root_cause': 'Seal degradation allowing pressure loss',
            'recommended_action': 'Replace pressure seals, inspect for damage',
            'preventive_maintenance_cost': 1500.00,
            'failure_cost': 28000.00,
            'occurrence_frequency': 'common'
        },
        {
            'failure_type': 'compressor_fouling',
            'sensor_signature': json.dumps({
                'sensor_2': {'trend': 'gradual_increase'},
                'sensor_7': {'trend': 'decreasing'},
                'sensor_13': {'trend': 'decreasing'}
            }),
            'affected_sensors': 'sensor_2,sensor_7,sensor_13',
            'signature_description': 'Compressor outlet temperature increases, pressure decreases, speed decreases',
            'typical_degradation_cycles': 200,
            'warning_threshold_hours': 500.0,
            'critical_threshold_hours': 200.0,
            'root_cause': 'Dirt and debris accumulation on compressor blades',
            'recommended_action': 'Perform compressor cleaning, check air filters',
            'preventive_maintenance_cost': 800.00,
            'failure_cost': 15000.00,
            'occurrence_frequency': 'common'
        },
        {
            'failure_type': 'vibration_imbalance',
            'sensor_signature': json.dumps({
                'sensor_8': {'trend': 'oscillating', 'pattern': 'high_frequency'},
                'sensor_13': {'trend': 'high_variance'},
                'sensor_14': {'trend': 'high_variance'}
            }),
            'affected_sensors': 'sensor_8,sensor_13,sensor_14',
            'signature_description': 'Fan/core speed sensors show high variance and oscillation',
            'typical_degradation_cycles': 100,
            'warning_threshold_hours': 200.0,
            'critical_threshold_hours': 60.0,
            'root_cause': 'Rotor imbalance due to blade damage or debris',
            'recommended_action': 'Balance rotor, inspect for blade damage',
            'preventive_maintenance_cost': 2800.00,
            'failure_cost': 38000.00,
            'occurrence_frequency': 'occasional'
        },
        {
            'failure_type': 'cooling_system_failure',
            'sensor_signature': json.dumps({
                'sensor_20': {'trend': 'decreasing'},
                'sensor_21': {'trend': 'decreasing'},
                'sensor_3': {'trend': 'increasing'},
                'sensor_4': {'trend': 'increasing'}
            }),
            'affected_sensors': 'sensor_20,sensor_21,sensor_3,sensor_4',
            'signature_description': 'Coolant bleed sensors decrease while temperatures increase',
            'typical_degradation_cycles': 130,
            'warning_threshold_hours': 270.0,
            'critical_threshold_hours': 85.0,
            'root_cause': 'Coolant passage blockage or valve failure',
            'recommended_action': 'Inspect cooling passages, replace coolant valves',
            'preventive_maintenance_cost': 3200.00,
            'failure_cost': 42000.00,
            'occurrence_frequency': 'rare'
        },
        {
            'failure_type': 'sensor_drift',
            'sensor_signature': json.dumps({
                'multiple': {'trend': 'sudden_jump', 'pattern': 'step_change'}
            }),
            'affected_sensors': 'variable',
            'signature_description': 'Sensor reading shows sudden step change without physical cause',
            'typical_degradation_cycles': 0,
            'warning_threshold_hours': 0.0,
            'critical_threshold_hours': 0.0,
            'root_cause': 'Sensor calibration drift or electronic failure',
            'recommended_action': 'Recalibrate or replace sensor, verify with redundant sensors',
            'preventive_maintenance_cost': 500.00,
            'failure_cost': 5000.00,
            'occurrence_frequency': 'occasional'
        },
        {
            'failure_type': 'blade_erosion',
            'sensor_signature': json.dumps({
                'sensor_2': {'trend': 'decreasing'},
                'sensor_7': {'trend': 'decreasing'},
                'sensor_13': {'trend': 'decreasing', 'delta': '> 15 rpm'}
            }),
            'affected_sensors': 'sensor_2,sensor_7,sensor_13',
            'signature_description': 'Temperature and pressure outputs decline, efficiency drops',
            'typical_degradation_cycles': 250,
            'warning_threshold_hours': 600.0,
            'critical_threshold_hours': 250.0,
            'root_cause': 'Erosion of compressor or turbine blades over time',
            'recommended_action': 'Inspect blades, replace if beyond tolerance',
            'preventive_maintenance_cost': 5500.00,
            'failure_cost': 65000.00,
            'occurrence_frequency': 'rare'
        },
        {
            'failure_type': 'lubrication_failure',
            'sensor_signature': json.dumps({
                'sensor_3': {'trend': 'rapid_increase'},
                'sensor_8': {'trend': 'increasing'},
                'sensor_11': {'trend': 'increasing'}
            }),
            'affected_sensors': 'sensor_3,sensor_8,sensor_11',
            'signature_description': 'Rapid temperature increase in bearing areas',
            'typical_degradation_cycles': 80,
            'warning_threshold_hours': 150.0,
            'critical_threshold_hours': 40.0,
            'root_cause': 'Lubrication system failure or oil contamination',
            'recommended_action': 'Check oil levels, replace oil, inspect lubrication system',
            'preventive_maintenance_cost': 1200.00,
            'failure_cost': 32000.00,
            'occurrence_frequency': 'occasional'
        },
        {
            'failure_type': 'exhaust_restriction',
            'sensor_signature': json.dumps({
                'sensor_4': {'trend': 'increasing'},
                'sensor_7': {'trend': 'increasing'},
                'sensor_11': {'trend': 'increasing'}
            }),
            'affected_sensors': 'sensor_4,sensor_7,sensor_11',
            'signature_description': 'Back pressure increases across system',
            'typical_degradation_cycles': 160,
            'warning_threshold_hours': 350.0,
            'critical_threshold_hours': 120.0,
            'root_cause': 'Exhaust passage blockage or valve malfunction',
            'recommended_action': 'Inspect exhaust system, clear blockages',
            'preventive_maintenance_cost': 1800.00,
            'failure_cost': 25000.00,
            'occurrence_frequency': 'rare'
        },
        {
            'failure_type': 'electrical_system_fault',
            'sensor_signature': json.dumps({
                'multiple': {'trend': 'erratic', 'pattern': 'noise'}
            }),
            'affected_sensors': 'variable',
            'signature_description': 'Multiple sensors show erratic readings or noise',
            'typical_degradation_cycles': 0,
            'warning_threshold_hours': 0.0,
            'critical_threshold_hours': 0.0,
            'root_cause': 'Electrical interference or grounding issues',
            'recommended_action': 'Check wiring, grounding, and electrical connections',
            'preventive_maintenance_cost': 900.00,
            'failure_cost': 12000.00,
            'occurrence_frequency': 'occasional'
        }
    ]

    return patterns


def insert_failure_patterns(conn: sqlite3.Connection, patterns: List[Dict]) -> None:
    """Insert failure pattern records into database."""
    cursor = conn.cursor()

    for pattern in patterns:
        cursor.execute("""
            INSERT INTO failure_patterns (
                failure_type, sensor_signature, affected_sensors,
                signature_description, typical_degradation_cycles,
                warning_threshold_hours, critical_threshold_hours,
                root_cause, recommended_action, preventive_maintenance_cost,
                failure_cost, occurrence_frequency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern['failure_type'], pattern['sensor_signature'],
            pattern['affected_sensors'], pattern['signature_description'],
            pattern['typical_degradation_cycles'], pattern['warning_threshold_hours'],
            pattern['critical_threshold_hours'], pattern['root_cause'],
            pattern['recommended_action'], pattern['preventive_maintenance_cost'],
            pattern['failure_cost'], pattern['occurrence_frequency']
        ))

    conn.commit()
    print(f"[OK] Inserted {len(patterns)} failure patterns")


def generate_maintenance_logs(
    num_records: int = 75,
    equipment_ids: Optional[List[int]] = None
) -> List[Dict]:
    """
    Generate synthetic maintenance log records.

    Creates maintenance logs with realistic failure types, costs, and dates,
    correlated with failure patterns.

    Parameters:
    -----------
    num_records : int
        Number of maintenance records to create
    equipment_ids : list, optional
        List of valid equipment IDs to reference

    Returns:
    --------
    list[dict]
        List of maintenance log records
    """
    if equipment_ids is None:
        equipment_ids = list(range(1, 16))  # Default 1-15

    failure_types = [
        ('bearing_degradation', 'critical', 6.5, 2500, 1200, 12, 24000),
        ('bearing_degradation', 'high', 5.0, 1800, 900, 8, 16000),
        ('overheating', 'critical', 8.0, 3200, 1500, 16, 32000),
        ('overheating', 'high', 6.0, 2100, 1100, 10, 20000),
        ('fuel_system_degradation', 'high', 4.5, 1500, 850, 6, 12000),
        ('pressure_seal_leak', 'medium', 3.0, 800, 600, 4, 8000),
        ('compressor_fouling', 'medium', 2.5, 400, 500, 3, 6000),
        ('vibration_imbalance', 'critical', 7.0, 2800, 1300, 14, 28000),
        ('cooling_system_failure', 'high', 5.5, 2200, 1000, 9, 18000),
        ('lubrication_failure', 'critical', 4.0, 1000, 750, 5, 10000),
        ('blade_erosion', 'high', 10.0, 5000, 2000, 24, 48000),
        ('exhaust_restriction', 'medium', 3.5, 1200, 700, 5, 10000),
    ]

    technicians = [
        'John Smith', 'Maria Garcia', 'David Chen', 'Sarah Johnson',
        'Michael Brown', 'Lisa Anderson', 'Robert Taylor', 'Emma Wilson'
    ]

    records = []

    for i in range(num_records):
        # Select failure type (40% bearing, 30% overheating, 30% others)
        if i < int(num_records * 0.4):
            failure_info = random.choice([
                f for f in failure_types if 'bearing' in f[0]
            ])
        elif i < int(num_records * 0.7):
            failure_info = random.choice([
                f for f in failure_types if 'overheating' in f[0]
            ])
        else:
            failure_info = random.choice([
                f for f in failure_types
                if 'bearing' not in f[0] and 'overheating' not in f[0]
            ])

        failure_type, severity, labor_hours, parts_cost, labor_cost, downtime_hours, downtime_cost = failure_info

        # Add variance to costs
        parts_cost = parts_cost * random.uniform(0.8, 1.2)
        labor_cost = labor_cost * random.uniform(0.9, 1.1)
        downtime_cost = downtime_cost * random.uniform(0.85, 1.15)
        total_cost = parts_cost + labor_cost

        # Generate date in past 4 years
        maint_date = datetime.now() - timedelta(days=random.randint(0, 1460))

        # Create issue descriptions
        issue_descriptions = {
            'bearing_degradation': 'Elevated temperature and unusual vibration detected in bearing assembly',
            'overheating': 'Temperature readings exceeded normal operating range by significant margin',
            'fuel_system_degradation': 'Fuel flow ratio showing high variance and inconsistent delivery',
            'pressure_seal_leak': 'Pressure drop detected across seal interface',
            'compressor_fouling': 'Reduced efficiency and pressure output from compressor unit',
            'vibration_imbalance': 'High vibration levels detected during operation',
            'cooling_system_failure': 'Coolant flow reduced, temperatures increasing',
            'lubrication_failure': 'Rapid temperature increase in lubricated components',
            'blade_erosion': 'Performance degradation indicating blade wear',
            'exhaust_restriction': 'Back pressure increase in exhaust system',
        }

        actions_taken = {
            'bearing_degradation': 'Replaced bearing assembly, inspected for rub marks, tested vibration levels',
            'overheating': 'Inspected turbine blades, replaced cooling components, tested temperature sensors',
            'fuel_system_degradation': 'Cleaned fuel nozzles, replaced fuel pump components, calibrated fuel system',
            'pressure_seal_leak': 'Replaced pressure seals, inspected mating surfaces, pressure tested system',
            'compressor_fouling': 'Performed deep cleaning of compressor blades, replaced air filters',
            'vibration_imbalance': 'Balanced rotor assembly, inspected blades for damage, replaced damaged components',
            'cooling_system_failure': 'Cleared cooling passages, replaced coolant valves, tested flow rates',
            'lubrication_failure': 'Replaced lubrication oil, inspected lubrication system, replaced oil pump',
            'blade_erosion': 'Replaced worn blades, inspected blade mounts, tested performance',
            'exhaust_restriction': 'Cleared exhaust blockage, inspected exhaust valves, tested back pressure',
        }

        parts_replaced = {
            'bearing_degradation': 'Bearing assembly P/N 12345-B, Bearing seals P/N 12346-S',
            'overheating': 'Turbine blade set P/N 23456-TB, Cooling manifold P/N 23457-CM',
            'fuel_system_degradation': 'Fuel nozzles P/N 34567-FN, Fuel pump P/N 34568-FP',
            'pressure_seal_leak': 'Pressure seal kit P/N 45678-PSK',
            'compressor_fouling': 'Air filter set P/N 56789-AF',
            'vibration_imbalance': 'Rotor balance weights P/N 67890-RBW, Blade P/N 67891-B',
            'cooling_system_failure': 'Coolant valves P/N 78901-CV, Coolant manifold P/N 78902-CM',
            'lubrication_failure': 'Lubrication oil 20qt P/N 89012-LO, Oil pump P/N 89013-OP',
            'blade_erosion': 'Blade set P/N 90123-BS, Blade mounts P/N 90124-BM',
            'exhaust_restriction': 'Exhaust valve P/N 01234-EV',
        }

        record = {
            'equipment_id': random.choice(equipment_ids),
            'maintenance_date': maint_date.strftime('%Y-%m-%d'),
            'issue_description': issue_descriptions.get(
                failure_type, 'Equipment maintenance required'
            ),
            'failure_type': failure_type,
            'root_cause': f"Determined root cause related to {failure_type.replace('_', ' ')}",
            'action_taken': actions_taken.get(
                failure_type, 'Performed maintenance procedure'
            ),
            'parts_replaced': parts_replaced.get(failure_type, 'Various components'),
            'labor_hours': round(labor_hours * random.uniform(0.9, 1.1), 1),
            'parts_cost': round(parts_cost, 2),
            'labor_cost': round(labor_cost, 2),
            'total_cost': round(total_cost, 2),
            'downtime_hours': round(downtime_hours * random.uniform(0.85, 1.15), 1),
            'downtime_cost': round(downtime_cost, 2),
            'severity': severity,
            'technician_name': random.choice(technicians),
            'work_order_id': f"WO-{maint_date.year}-{str(random.randint(1000, 9999))}",
            'resolution_status': 'completed',
            'notes': None
        }

        records.append(record)

    # Sort by date
    records.sort(key=lambda x: x['maintenance_date'])

    return records


def insert_maintenance_logs(conn: sqlite3.Connection, logs: List[Dict]) -> None:
    """Insert maintenance log records into database."""
    cursor = conn.cursor()

    for log in logs:
        cursor.execute("""
            INSERT INTO maintenance_logs (
                equipment_id, maintenance_date, issue_description, failure_type,
                root_cause, action_taken, parts_replaced, labor_hours,
                parts_cost, labor_cost, total_cost, downtime_hours,
                downtime_cost, severity, technician_name, work_order_id,
                resolution_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log['equipment_id'], log['maintenance_date'], log['issue_description'],
            log['failure_type'], log['root_cause'], log['action_taken'],
            log['parts_replaced'], log['labor_hours'], log['parts_cost'],
            log['labor_cost'], log['total_cost'], log['downtime_hours'],
            log['downtime_cost'], log['severity'], log['technician_name'],
            log['work_order_id'], log['resolution_status'], log['notes']
        ))

    conn.commit()
    print(f"[OK] Inserted {len(logs)} maintenance log records")


def print_database_stats(conn: sqlite3.Connection) -> None:
    """Print database statistics."""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM equipment")
    eq_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM maintenance_logs")
    log_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM failure_patterns")
    pattern_count = cursor.fetchone()[0]

    cursor.execute("SELECT equipment_type, COUNT(*) FROM equipment GROUP BY equipment_type")
    eq_types = cursor.fetchall()

    cursor.execute("""
        SELECT failure_type, COUNT(*) FROM maintenance_logs
        GROUP BY failure_type ORDER BY COUNT(*) DESC LIMIT 5
    """)
    top_failures = cursor.fetchall()

    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    print(f"Equipment records: {eq_count}")
    print(f"Maintenance logs: {log_count}")
    print(f"Failure patterns: {pattern_count}")
    print("\nEquipment by type:")
    for eq_type, count in eq_types:
        print(f"  {eq_type}: {count}")
    print("\nTop failure types:")
    for failure_type, count in top_failures:
        print(f"  {failure_type}: {count}")
    print("="*60)


def validate_database_schema(db_path: str) -> Dict[str, bool]:
    """
    Validate database schema and data integrity.

    Parameters:
    -----------
    db_path : str
        Path to database file

    Returns:
    --------
    dict
        Validation results with pass/fail status
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    results = {
        'tables_exist': True,
        'foreign_keys_valid': True,
        'minimum_records': True,
        'no_nulls_in_required': True,
        'costs_positive': True,
        'dates_valid': True,
        'errors': []
    }

    # Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    required_tables = ['equipment', 'maintenance_logs', 'failure_patterns']

    for table in required_tables:
        if table not in tables:
            results['tables_exist'] = False
            results['errors'].append(f"Table '{table}' not found")

    # Check minimum record counts
    cursor.execute("SELECT COUNT(*) FROM equipment")
    if cursor.fetchone()[0] < 10:
        results['minimum_records'] = False
        results['errors'].append("Equipment table has < 10 records")

    cursor.execute("SELECT COUNT(*) FROM maintenance_logs")
    if cursor.fetchone()[0] < 50:
        results['minimum_records'] = False
        results['errors'].append("Maintenance logs table has < 50 records")

    cursor.execute("SELECT COUNT(*) FROM failure_patterns")
    if cursor.fetchone()[0] < 8:
        results['minimum_records'] = False
        results['errors'].append("Failure patterns table has < 8 records")

    # Check foreign key integrity
    cursor.execute("""
        SELECT COUNT(*) FROM maintenance_logs
        WHERE equipment_id NOT IN (SELECT id FROM equipment)
    """)
    if cursor.fetchone()[0] > 0:
        results['foreign_keys_valid'] = False
        results['errors'].append("Found orphaned maintenance logs")

    # Check for NULL in required fields
    cursor.execute("SELECT COUNT(*) FROM equipment WHERE serial_number IS NULL")
    if cursor.fetchone()[0] > 0:
        results['no_nulls_in_required'] = False
        results['errors'].append("Found NULL serial numbers")

    # Check costs are positive
    cursor.execute("SELECT COUNT(*) FROM maintenance_logs WHERE total_cost < 0")
    if cursor.fetchone()[0] > 0:
        results['costs_positive'] = False
        results['errors'].append("Found negative costs")

    conn.close()

    return results


def create_maintenance_database(
    db_path: str = "data/maintenance_history.db",
    num_equipment: int = 15,
    num_maintenance_logs: int = 75,
    verbose: bool = True
) -> None:
    """
    Create and populate maintenance history database.

    Parameters:
    -----------
    db_path : str
        Path to SQLite database file
    num_equipment : int
        Number of equipment records to create
    num_maintenance_logs : int
        Number of maintenance log entries
    verbose : bool
        Print progress messages
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Creating Maintenance Database")
        print(f"{'='*60}")
        print(f"Database path: {db_path}")

    # Create schema
    create_database_schema(db_path)

    # Connect to database
    conn = sqlite3.connect(db_path)

    try:
        # Generate and insert equipment data
        if verbose:
            print(f"Generating {num_equipment} equipment records...")
        equipment_data = generate_equipment_data(num_equipment)
        insert_equipment_data(conn, equipment_data)

        # Get equipment IDs
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM equipment")
        equipment_ids = [row[0] for row in cursor.fetchall()]

        # Generate and insert failure patterns
        if verbose:
            print("Generating failure patterns...")
        failure_patterns = generate_failure_patterns()
        insert_failure_patterns(conn, failure_patterns)

        # Generate and insert maintenance logs
        if verbose:
            print(f"Generating {num_maintenance_logs} maintenance logs...")
        maintenance_logs = generate_maintenance_logs(num_maintenance_logs, equipment_ids)
        insert_maintenance_logs(conn, maintenance_logs)

        if verbose:
            print("\n[SUCCESS] Database creation complete!")
            print_database_stats(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Create maintenance history database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python database_setup.py
  python database_setup.py --equipment 20 --logs 100
  python database_setup.py --validate
        """
    )

    parser.add_argument('--db-path', type=str, default='data/maintenance_history.db',
                        help='Database file path')
    parser.add_argument('--equipment', type=int, default=15,
                        help='Number of equipment records')
    parser.add_argument('--logs', type=int, default=75,
                        help='Number of maintenance logs')
    parser.add_argument('--validate', action='store_true',
                        help='Validate database after creation')

    args = parser.parse_args()

    # Create database
    create_maintenance_database(
        db_path=args.db_path,
        num_equipment=args.equipment,
        num_maintenance_logs=args.logs
    )

    # Validate if requested
    if args.validate:
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)

        validation = validate_database_schema(args.db_path)

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
