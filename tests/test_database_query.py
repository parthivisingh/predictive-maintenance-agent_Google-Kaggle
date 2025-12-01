"""
Unit tests for database_query.py

Tests all database query functions including:
- Database connection and validation
- Sensor similarity search
- Maintenance history queries
- Failure statistics
"""

import unittest
import numpy as np
from tools.database_query import (
    validate_database_exists,
    extract_sensor_vector,
    cosine_similarity,
    parse_sensor_signature,
    search_similar_failures,
    get_maintenance_history,
    get_failure_statistics,
    find_parts_replaced
)


class TestDatabaseValidation(unittest.TestCase):
    """Test database validation functions."""

    def test_validate_database_exists(self):
        """Test database validation."""
        is_valid = validate_database_exists()
        self.assertTrue(is_valid)

    def test_validate_nonexistent_database(self):
        """Test validation with nonexistent database."""
        is_valid = validate_database_exists("nonexistent.db")
        self.assertFalse(is_valid)


class TestSensorVector(unittest.TestCase):
    """Test sensor vector functions."""

    def test_extract_sensor_vector(self):
        """Test sensor vector extraction."""
        sensor_values = {
            'sensor_T30': 1590.0,
            'sensor_Nc': 9050.0,
            'sensor_Ps30': 47.5
        }
        vector = extract_sensor_vector(sensor_values)

        self.assertIsInstance(vector, np.ndarray)
        self.assertEqual(len(vector), 10)  # 10 important sensors
        # Check that specified values are present
        self.assertGreater(np.sum(vector), 0)

    def test_extract_sensor_vector_missing_sensors(self):
        """Test vector extraction with missing sensors."""
        sensor_values = {'sensor_T30': 1590.0}
        vector = extract_sensor_vector(sensor_values)

        self.assertIsInstance(vector, np.ndarray)
        self.assertEqual(len(vector), 10)


class TestCosineSimilarity(unittest.TestCase):
    """Test cosine similarity calculation."""

    def test_identical_vectors(self):
        """Test similarity of identical vectors."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])

        similarity = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 1.0, places=5)

    def test_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])

        similarity = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.5, places=5)

    def test_zero_vector(self):
        """Test similarity with zero vector."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([0.0, 0.0, 0.0])

        similarity = cosine_similarity(vec1, vec2)
        self.assertEqual(similarity, 0.0)


class TestSensorSignatureParsing(unittest.TestCase):
    """Test sensor signature parsing."""

    def test_parse_range_signature(self):
        """Test parsing signature with min/max ranges."""
        signature_json = '{"sensor_T30": {"min": 1575.0, "max": 1625.0}}'

        parsed = parse_sensor_signature(signature_json)

        self.assertIn('sensor_T30', parsed)
        self.assertEqual(parsed['sensor_T30'], 1600.0)  # Midpoint

    def test_parse_value_signature(self):
        """Test parsing signature with direct values."""
        signature_json = '{"sensor_T30": {"value": 1590.0}}'

        parsed = parse_sensor_signature(signature_json)

        self.assertIn('sensor_T30', parsed)
        self.assertEqual(parsed['sensor_T30'], 1590.0)

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        parsed = parse_sensor_signature("invalid json")
        self.assertEqual(parsed, {})


class TestSearchSimilarFailures(unittest.TestCase):
    """Test similar failure search."""

    def test_search_with_valid_sensors(self):
        """Test searching with valid sensor readings."""
        sensor_readings = {
            'sensor_T30': 1615.0,
            'sensor_Nc': 9080.0,
            'sensor_Ps30': 48.2
        }

        similar = search_similar_failures(sensor_readings, top_n=3)

        self.assertIsInstance(similar, list)
        # May or may not find similar cases depending on database
        if len(similar) > 0:
            self.assertIn('similarity_score', similar[0])
            self.assertIn('failure_type', similar[0])
            self.assertGreaterEqual(similar[0]['similarity_score'], 0.0)
            self.assertLessEqual(similar[0]['similarity_score'], 1.0)

    def test_search_with_threshold(self):
        """Test search with custom threshold."""
        sensor_readings = {
            'sensor_T30': 1615.0,
            'sensor_Nc': 9080.0
        }

        similar = search_similar_failures(
            sensor_readings,
            top_n=5,
            similarity_threshold=0.8
        )

        # All results should be above threshold
        for case in similar:
            self.assertGreaterEqual(case['similarity_score'], 0.8)


class TestMaintenanceHistory(unittest.TestCase):
    """Test maintenance history queries."""

    def test_get_all_history(self):
        """Test retrieving all maintenance history."""
        history = get_maintenance_history(limit=10)

        self.assertIsInstance(history, list)
        self.assertLessEqual(len(history), 10)

        if len(history) > 0:
            self.assertIn('equipment_id', history[0])
            self.assertIn('failure_type', history[0])
            self.assertIn('total_cost', history[0])

    def test_filter_by_equipment(self):
        """Test filtering by equipment ID."""
        history = get_maintenance_history(equipment_id=1, limit=5)

        self.assertIsInstance(history, list)
        for record in history:
            self.assertEqual(record['equipment_id'], 1)

    def test_filter_by_failure_type(self):
        """Test filtering by failure type."""
        history = get_maintenance_history(failure_type='bearing_degradation', limit=5)

        self.assertIsInstance(history, list)
        for record in history:
            self.assertEqual(record['failure_type'], 'bearing_degradation')

    def test_filter_by_date_range(self):
        """Test filtering by date range."""
        history = get_maintenance_history(
            start_date='2024-01-01',
            end_date='2024-12-31',
            limit=10
        )

        self.assertIsInstance(history, list)


class TestFailureStatistics(unittest.TestCase):
    """Test failure statistics generation."""

    def test_get_overall_statistics(self):
        """Test getting overall statistics."""
        stats = get_failure_statistics()

        self.assertIsInstance(stats, dict)
        self.assertIn('failure_type_distribution', stats)
        self.assertIn('average_costs_by_type', stats)
        self.assertIn('total_maintenance_cost', stats)
        self.assertIn('total_downtime_hours', stats)
        self.assertIn('most_common_failures', stats)
        self.assertIn('equipment_with_most_failures', stats)

    def test_get_statistics_with_date_range(self):
        """Test statistics with date range filter."""
        stats = get_failure_statistics(date_range_days=365)

        self.assertIsInstance(stats, dict)
        self.assertIn('failure_type_distribution', stats)
        self.assertGreaterEqual(stats['total_maintenance_cost'], 0)

    def test_get_statistics_by_equipment_type(self):
        """Test statistics filtered by equipment type."""
        stats = get_failure_statistics(equipment_type='Turbofan Engine')

        self.assertIsInstance(stats, dict)


class TestFindPartsReplaced(unittest.TestCase):
    """Test parts replacement analysis."""

    def test_find_parts_for_valid_failure(self):
        """Test finding parts for valid failure type."""
        parts = find_parts_replaced('bearing_degradation')

        self.assertIsInstance(parts, dict)

        if 'error' not in parts:
            self.assertIn('failure_type', parts)
            self.assertIn('occurrence_count', parts)
            self.assertIn('most_common_parts', parts)
            self.assertIn('average_cost', parts)
            self.assertIn('average_downtime', parts)
            self.assertGreater(parts['occurrence_count'], 0)

    def test_find_parts_for_invalid_failure(self):
        """Test finding parts for nonexistent failure type."""
        parts = find_parts_replaced('nonexistent_failure_type')

        self.assertIsInstance(parts, dict)
        self.assertIn('error', parts)


if __name__ == '__main__':
    unittest.main()
