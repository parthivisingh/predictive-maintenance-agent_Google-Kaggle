"""
Maintenance Database Query Tool
================================

Query historical maintenance data to find similar failures and analyze patterns.

USAGE FOR PHASE 4 AGENTS:
-------------------------

Basic usage (search similar failures):
>>> from tools.database_query import search_similar_failures
>>>
>>> sensor_readings = {
>>>     'sensor_T30': 1615.0,
>>>     'sensor_Nc': 9080.0,
>>>     'sensor_Ps30': 48.2
>>> }
>>>
>>> similar_cases = search_similar_failures(sensor_readings, top_n=3)
>>> for case in similar_cases:
>>>     print(f"Failure: {case['failure_type']}, Similarity: {case['similarity_score']}")

Query maintenance history:
>>> from tools.database_query import get_maintenance_history
>>>
>>> history = get_maintenance_history(
>>>     equipment_id=1,
>>>     start_date='2024-01-01',
>>>     limit=10
>>> )

Get failure statistics:
>>> from tools.database_query import get_failure_statistics
>>>
>>> stats = get_failure_statistics(date_range_days=365)
>>> print(f"Total cost: ${stats['total_maintenance_cost']}")

INTEGRATION WITH GOOGLE ADK:
-----------------------------
To use as an ADK tool in Phase 4:

from google.adk import Tool
from tools.database_query import search_similar_failures

db_query_tool = Tool(
    name="search_similar_failures",
    description="Finds historical maintenance cases with similar sensor signatures",
    func=search_similar_failures
)
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
import json
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from pydantic import BaseModel, field_validator
import logging

logger = logging.getLogger(__name__)

# Database path
DEFAULT_DB_PATH = "data/maintenance_history.db"


# ============================================================================
# Sensor Vector Schema Validation (Phase 3.5 Enhancement)
# ============================================================================

class SensorVectorSchema(BaseModel):
    """Schema for sensor vectors with validation."""

    sensor_T24: float = 0.0
    sensor_T30: float = 0.0
    sensor_T50: float = 0.0
    sensor_P30: float = 0.0
    sensor_Ps30: float = 0.0
    sensor_Nc: float = 0.0
    sensor_Nf: float = 0.0
    sensor_phi: float = 0.0
    sensor_W31: float = 0.0
    sensor_W32: float = 0.0

    @field_validator('*')
    @classmethod
    def validate_numeric(cls, v):
        """Ensure all values are finite."""
        if not np.isfinite(v):
            raise ValueError(f"Sensor value must be finite, got {v}")
        return float(v)

    def to_vector(self) -> np.ndarray:
        """Convert to numpy array in fixed order."""
        return np.array([
            self.sensor_T24,
            self.sensor_T30,
            self.sensor_T50,
            self.sensor_P30,
            self.sensor_Ps30,
            self.sensor_Nc,
            self.sensor_Nf,
            self.sensor_phi,
            self.sensor_W31,
            self.sensor_W32
        ], dtype=np.float64)


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH):
    """
    Context manager for database connections.

    Usage:
    ------
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment")

    Parameters:
    -----------
    db_path : str
        Path to SQLite database

    Yields:
    -------
    sqlite3.Connection
        Database connection
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        yield conn
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def validate_database_exists(db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Validate that database exists and has required tables.

    Parameters:
    -----------
    db_path : str
        Path to database

    Returns:
    --------
    bool
        True if valid, False otherwise
    """
    import os

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False

    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

            required_tables = {'equipment', 'maintenance_logs', 'failure_patterns'}
            missing = required_tables - tables

            if missing:
                print(f"Missing tables: {missing}")
                return False

            # Check minimum data
            cursor.execute("SELECT COUNT(*) FROM equipment")
            eq_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM maintenance_logs")
            log_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM failure_patterns")
            pattern_count = cursor.fetchone()[0]

            if eq_count < 5 or log_count < 20 or pattern_count < 5:
                print(f"Insufficient data: {eq_count} equipment, "
                      f"{log_count} logs, {pattern_count} patterns")
                return False

            return True

    except Exception as e:
        print(f"Validation error: {e}")
        return False


def extract_sensor_vector(sensor_values: Dict[str, float]) -> np.ndarray:
    """
    Convert sensor readings to validated, normalized vector.

    NOW WITH (Phase 3.5 Enhancement):
    - Schema validation
    - L2 normalization
    - Explicit ordering

    Parameters:
    -----------
    sensor_values : Dict[str, float]
        Sensor readings

    Returns:
    --------
    np.ndarray
        Validated, normalized sensor vector

    Raises:
    -------
    ValueError
        If sensor values are invalid (inf, nan, etc.)
    """
    # Validate schema
    schema = SensorVectorSchema(**sensor_values)

    # Get vector in fixed order
    vector = schema.to_vector()

    # L2 normalize
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    else:
        logger.warning("Zero-norm vector detected, returning unnormalized")

    return vector


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity with validation.

    NOW WITH (Phase 3.5 Enhancement):
    - Input validation
    - Dimension checking
    - Numerical stability

    Parameters:
    -----------
    vec1, vec2 : np.ndarray
        Vectors to compare

    Returns:
    --------
    float
        Similarity score (0-1, higher = more similar)

    Raises:
    -------
    ValueError
        If vectors have mismatched dimensions or contain invalid values
    """
    # Validate inputs
    if vec1.shape != vec2.shape:
        raise ValueError(f"Vector dimension mismatch: {vec1.shape} vs {vec2.shape}")

    if len(vec1) == 0:
        raise ValueError("Cannot compute similarity of empty vectors")

    # Check for NaN/inf
    if not np.all(np.isfinite(vec1)) or not np.all(np.isfinite(vec2)):
        raise ValueError("Vectors contain NaN or infinite values")

    # Compute norms
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    # Handle zero vectors
    if norm1 < 1e-10 or norm2 < 1e-10:
        logger.warning("Near-zero vector detected in similarity calculation")
        return 0.0

    # Compute similarity (numerically stable)
    similarity = np.dot(vec1, vec2) / (norm1 * norm2)

    # Clip to [-1, 1] to handle floating point errors
    similarity = np.clip(similarity, -1.0, 1.0)

    # Normalize to [0, 1]
    similarity = (similarity + 1.0) / 2.0

    return float(similarity)


def parse_sensor_signature(signature_json: str) -> Dict[str, float]:
    """
    Parse JSON sensor signature from database.

    Parameters:
    -----------
    signature_json : str
        JSON string with sensor signature

    Returns:
    --------
    Dict[str, float]
        Parsed sensor values (using midpoints of ranges)
    """
    try:
        signature = json.loads(signature_json)

        sensor_values = {}

        for sensor, info in signature.items():
            if isinstance(info, dict):
                # Extract numeric value
                if 'max' in info and 'min' in info:
                    # Use midpoint of range
                    sensor_values[sensor] = (info['max'] + info['min']) / 2
                elif 'value' in info:
                    sensor_values[sensor] = info['value']
            elif isinstance(info, (int, float)):
                sensor_values[sensor] = info

        return sensor_values

    except json.JSONDecodeError:
        return {}


def search_similar_failures(
    sensor_readings: Dict[str, float],
    top_n: int = 3,
    similarity_threshold: float = 0.6,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict]:
    """
    Find historical failures with similar sensor signatures.

    Uses cosine similarity to match current sensor readings
    against historical failure patterns and maintenance logs.

    Parameters:
    -----------
    sensor_readings : Dict[str, float]
        Current sensor readings
        Example: {'sensor_T30': 1605.2, 'sensor_Nc': 9075.5, ...}
    top_n : int
        Number of similar cases to return (default: 3)
    similarity_threshold : float
        Minimum similarity score 0-1 (default: 0.6)
    db_path : str
        Path to database

    Returns:
    --------
    List[Dict]
        List of similar maintenance events, each containing:
        - similarity_score (float): 0-1 similarity score
        - failure_type (str): Type of failure
        - issue_description (str): Problem description
        - root_cause (str): Determined root cause
        - action_taken (str): Actions performed
        - parts_replaced (str): Parts that were replaced
        - total_cost (float): Total maintenance cost
        - downtime_hours (float): Equipment downtime
        - maintenance_date (str): When it occurred
        - equipment_id (int): Which equipment
        - matched_sensors (List[str]): Which sensors matched
    """
    # Convert current readings to vector
    current_vector = extract_sensor_vector(sensor_readings)

    results = []

    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Query all failure patterns
            cursor.execute("""
                SELECT
                    fp.id,
                    fp.failure_type,
                    fp.sensor_signature,
                    fp.affected_sensors,
                    fp.signature_description,
                    fp.root_cause,
                    fp.recommended_action,
                    fp.preventive_maintenance_cost,
                    fp.failure_cost
                FROM failure_patterns fp
            """)

            patterns = cursor.fetchall()

            # Calculate similarity for each pattern
            pattern_similarities = []

            for pattern in patterns:
                pattern_sensors = parse_sensor_signature(pattern['sensor_signature'])

                if not pattern_sensors:
                    continue

                pattern_vector = extract_sensor_vector(pattern_sensors)
                similarity = cosine_similarity(current_vector, pattern_vector)

                if similarity >= similarity_threshold:
                    pattern_similarities.append({
                        'failure_type': pattern['failure_type'],
                        'similarity': similarity,
                        'root_cause': pattern['root_cause'],
                        'recommended_action': pattern['recommended_action'],
                        'affected_sensors': pattern['affected_sensors']
                    })

            # Sort by similarity
            pattern_similarities.sort(key=lambda x: x['similarity'], reverse=True)

            # For each similar pattern, find actual maintenance logs
            for pattern in pattern_similarities[:top_n]:
                cursor.execute("""
                    SELECT
                        ml.id,
                        ml.equipment_id,
                        ml.maintenance_date,
                        ml.issue_description,
                        ml.failure_type,
                        ml.root_cause,
                        ml.action_taken,
                        ml.parts_replaced,
                        ml.total_cost,
                        ml.downtime_hours,
                        ml.severity,
                        e.equipment_type,
                        e.manufacturer,
                        e.model
                    FROM maintenance_logs ml
                    JOIN equipment e ON ml.equipment_id = e.id
                    WHERE ml.failure_type = ?
                    ORDER BY ml.maintenance_date DESC
                    LIMIT 2
                """, (pattern['failure_type'],))

                logs = cursor.fetchall()

                for log in logs:
                    results.append({
                        'similarity_score': round(pattern['similarity'], 3),
                        'failure_type': log['failure_type'],
                        'issue_description': log['issue_description'],
                        'root_cause': log['root_cause'],
                        'action_taken': log['action_taken'],
                        'parts_replaced': log['parts_replaced'],
                        'total_cost': log['total_cost'],
                        'downtime_hours': log['downtime_hours'],
                        'maintenance_date': log['maintenance_date'],
                        'equipment_id': log['equipment_id'],
                        'equipment_type': log['equipment_type'],
                        'manufacturer': log['manufacturer'],
                        'model': log['model'],
                        'severity': log['severity'],
                        'matched_sensors': pattern['affected_sensors'].split(',') if pattern['affected_sensors'] else [],
                        'pattern_root_cause': pattern['root_cause'],
                        'pattern_recommendation': pattern['recommended_action']
                    })

            # If we have more than top_n results, trim to top_n
            # Sort by similarity score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = results[:top_n]

            return results

    except Exception as e:
        print(f"Error searching similar failures: {e}")
        return []


def get_maintenance_history(
    equipment_id: Optional[int] = None,
    failure_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict]:
    """
    Retrieve maintenance history with optional filters.

    Parameters:
    -----------
    equipment_id : int, optional
        Filter by specific equipment
    failure_type : str, optional
        Filter by failure type
    start_date : str, optional
        Start date (YYYY-MM-DD)
    end_date : str, optional
        End date (YYYY-MM-DD)
    limit : int
        Maximum records to return
    db_path : str
        Database path

    Returns:
    --------
    List[Dict]
        Chronological maintenance records
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Build query with filters
            query = """
                SELECT
                    ml.*,
                    e.equipment_type,
                    e.manufacturer,
                    e.model,
                    e.serial_number
                FROM maintenance_logs ml
                JOIN equipment e ON ml.equipment_id = e.id
                WHERE 1=1
            """
            params = []

            if equipment_id is not None:
                query += " AND ml.equipment_id = ?"
                params.append(equipment_id)

            if failure_type is not None:
                query += " AND ml.failure_type = ?"
                params.append(failure_type)

            if start_date is not None:
                query += " AND ml.maintenance_date >= ?"
                params.append(start_date)

            if end_date is not None:
                query += " AND ml.maintenance_date <= ?"
                params.append(end_date)

            query += " ORDER BY ml.maintenance_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error retrieving maintenance history: {e}")
        return []


def get_failure_statistics(
    date_range_days: Optional[int] = None,
    equipment_type: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict:
    """
    Generate failure statistics and trends.

    Parameters:
    -----------
    date_range_days : int, optional
        Number of days to look back (None = all time)
    equipment_type : str, optional
        Filter by equipment type
    db_path : str
        Database path

    Returns:
    --------
    Dict
        Statistics including:
        - failure_type_distribution: Count by failure type
        - average_costs_by_type: Average costs per failure type
        - total_maintenance_cost: Total cost in period
        - total_downtime_hours: Total downtime
        - most_common_failures: Top 5 failure types
        - equipment_with_most_failures: Equipment IDs with most issues
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Build base WHERE clause
            where_clause = "WHERE 1=1"
            params = []

            if date_range_days is not None:
                cutoff_date = (datetime.now() - timedelta(days=date_range_days)).strftime('%Y-%m-%d')
                where_clause += " AND ml.maintenance_date >= ?"
                params.append(cutoff_date)

            if equipment_type is not None:
                where_clause += " AND e.equipment_type = ?"
                params.append(equipment_type)

            # Failure type distribution
            cursor.execute(f"""
                SELECT
                    ml.failure_type,
                    COUNT(*) as count
                FROM maintenance_logs ml
                JOIN equipment e ON ml.equipment_id = e.id
                {where_clause}
                GROUP BY ml.failure_type
                ORDER BY count DESC
            """, params)
            failure_distribution = {row['failure_type']: row['count']
                                  for row in cursor.fetchall()}

            # Average costs by type
            cursor.execute(f"""
                SELECT
                    ml.failure_type,
                    AVG(ml.total_cost) as avg_cost,
                    AVG(ml.downtime_hours) as avg_downtime
                FROM maintenance_logs ml
                JOIN equipment e ON ml.equipment_id = e.id
                {where_clause}
                GROUP BY ml.failure_type
            """, params)
            cost_stats = {
                row['failure_type']: {
                    'avg_cost': round(row['avg_cost'], 2),
                    'avg_downtime': round(row['avg_downtime'], 2)
                }
                for row in cursor.fetchall()
            }

            # Total costs
            cursor.execute(f"""
                SELECT
                    SUM(ml.total_cost) as total_cost,
                    SUM(ml.downtime_hours) as total_downtime
                FROM maintenance_logs ml
                JOIN equipment e ON ml.equipment_id = e.id
                {where_clause}
            """, params)
            totals = cursor.fetchone()

            # Equipment with most failures
            cursor.execute(f"""
                SELECT
                    ml.equipment_id,
                    e.equipment_type,
                    e.serial_number,
                    COUNT(*) as failure_count
                FROM maintenance_logs ml
                JOIN equipment e ON ml.equipment_id = e.id
                {where_clause}
                GROUP BY ml.equipment_id
                ORDER BY failure_count DESC
                LIMIT 5
            """, params)
            top_equipment = [
                {
                    'equipment_id': row['equipment_id'],
                    'equipment_type': row['equipment_type'],
                    'serial_number': row['serial_number'],
                    'failure_count': row['failure_count']
                }
                for row in cursor.fetchall()
            ]

            return {
                'failure_type_distribution': failure_distribution,
                'average_costs_by_type': cost_stats,
                'total_maintenance_cost': round(totals['total_cost'] or 0, 2),
                'total_downtime_hours': round(totals['total_downtime'] or 0, 2),
                'most_common_failures': sorted(
                    failure_distribution.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                'equipment_with_most_failures': top_equipment
            }

    except Exception as e:
        print(f"Error generating statistics: {e}")
        return {}


def find_parts_replaced(
    failure_type: str,
    db_path: str = DEFAULT_DB_PATH
) -> Dict:
    """
    Find common parts replaced for a specific failure type.

    Parameters:
    -----------
    failure_type : str
        Failure type to analyze
    db_path : str
        Database path

    Returns:
    --------
    Dict
        Aggregated data:
        - failure_type: str
        - occurrence_count: int
        - most_common_parts: List[str]
        - average_cost: float
        - average_downtime: float
        - typical_root_causes: List[str]
        - typical_actions: List[str]
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Get maintenance logs for this failure type
            cursor.execute("""
                SELECT
                    parts_replaced,
                    root_cause,
                    action_taken,
                    total_cost,
                    downtime_hours
                FROM maintenance_logs
                WHERE failure_type = ?
            """, (failure_type,))

            logs = cursor.fetchall()

            if not logs:
                return {'error': f"No records found for failure type: {failure_type}"}

            # Extract parts
            all_parts = []
            for log in logs:
                if log['parts_replaced']:
                    # Split by common separators
                    parts = log['parts_replaced'].replace(',', '\n').split('\n')
                    all_parts.extend([p.strip() for p in parts if p.strip()])

            # Count occurrences
            parts_counter = Counter(all_parts)

            # Calculate averages
            avg_cost = np.mean([log['total_cost'] for log in logs if log['total_cost']])
            avg_downtime = np.mean([log['downtime_hours'] for log in logs if log['downtime_hours']])

            # Extract unique root causes and actions
            root_causes = list(set(log['root_cause'] for log in logs if log['root_cause']))
            actions = list(set(log['action_taken'] for log in logs if log['action_taken']))

            # Get failure pattern info
            cursor.execute("""
                SELECT
                    recommended_action,
                    preventive_maintenance_cost,
                    failure_cost
                FROM failure_patterns
                WHERE failure_type = ?
            """, (failure_type,))

            pattern = cursor.fetchone()

            return {
                'failure_type': failure_type,
                'occurrence_count': len(logs),
                'most_common_parts': [part for part, count in parts_counter.most_common(5)],
                'average_cost': round(avg_cost, 2),
                'average_downtime': round(avg_downtime, 2),
                'typical_root_causes': root_causes[:3],
                'typical_actions': actions[:3],
                'pattern_recommendation': pattern['recommended_action'] if pattern else None,
                'preventive_cost': pattern['preventive_maintenance_cost'] if pattern else None,
                'failure_cost': pattern['failure_cost'] if pattern else None
            }

    except Exception as e:
        print(f"Error finding parts: {e}")
        return {'error': str(e)}
