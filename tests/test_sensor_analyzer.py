"""
Unit tests for sensor_analyzer.py

Tests all anomaly detection functions including:
- Data model validation
- Statistical detection methods
- ML-based detection
- Main analysis function
"""

import unittest
import numpy as np
import pandas as pd
from tools.sensor_analyzer import (
    SensorReading,
    AnomalyResult,
    analyze_sensor_data,
    detect_anomalies_statistical,
    detect_anomalies_ml,
    quick_check,
    validate_sensor_reading,
    load_historical_data,
    AnomalyDetectorModel
)


class TestSensorReading(unittest.TestCase):
    """Test SensorReading data model."""

    def test_valid_reading(self):
        """Test creating valid sensor reading."""
        reading = SensorReading(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T30': 1590.0}
        )
        self.assertEqual(reading.unit_id, 1)
        self.assertEqual(reading.time_cycle, 100)
        self.assertIsNotNone(reading.timestamp)

    def test_invalid_unit_id(self):
        """Test invalid unit_id raises error."""
        with self.assertRaises(ValueError):
            SensorReading(unit_id=-1, time_cycle=1, sensor_values={'sensor_T30': 1590.0})

    def test_invalid_time_cycle(self):
        """Test invalid time_cycle raises error."""
        with self.assertRaises(ValueError):
            SensorReading(unit_id=1, time_cycle=0, sensor_values={'sensor_T30': 1590.0})

    def test_nan_sensor_value(self):
        """Test NaN sensor value raises error."""
        with self.assertRaises(ValueError):
            SensorReading(unit_id=1, time_cycle=1, sensor_values={'sensor_T30': np.nan})

    def test_empty_sensor_values(self):
        """Test empty sensor values raises error."""
        with self.assertRaises(ValueError):
            SensorReading(unit_id=1, time_cycle=1, sensor_values={})


class TestValidateSensorReading(unittest.TestCase):
    """Test validate_sensor_reading function."""

    def test_validate_dict(self):
        """Test validating dictionary input."""
        sensor_dict = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {'sensor_T30': 1590.0}
        }
        reading = validate_sensor_reading(sensor_dict)
        self.assertIsInstance(reading, SensorReading)
        self.assertEqual(reading.unit_id, 1)

    def test_validate_sensor_reading_object(self):
        """Test passing SensorReading object."""
        reading = SensorReading(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T30': 1590.0}
        )
        validated = validate_sensor_reading(reading)
        self.assertIs(validated, reading)

    def test_missing_fields(self):
        """Test missing required fields raises error."""
        with self.assertRaises(ValueError):
            validate_sensor_reading({'unit_id': 1})

    def test_invalid_type(self):
        """Test invalid input type raises error."""
        with self.assertRaises(TypeError):
            validate_sensor_reading("invalid")


class TestStatisticalDetection(unittest.TestCase):
    """Test statistical anomaly detection."""

    def test_range_detection_anomaly(self):
        """Test range-based anomaly detection."""
        reading = SensorReading(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T30': 1650.0}  # Above normal range
        )
        anomalies = detect_anomalies_statistical(reading, method='range')
        self.assertTrue(anomalies['sensor_T30']['is_anomaly'])
        self.assertGreater(anomalies['sensor_T30']['severity_score'], 0)

    def test_range_detection_normal(self):
        """Test normal reading not flagged."""
        reading = SensorReading(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T30': 1590.0}  # Within normal range
        )
        anomalies = detect_anomalies_statistical(reading, method='range')
        self.assertFalse(anomalies['sensor_T30']['is_anomaly'])

    def test_zscore_with_history(self):
        """Test z-score detection with historical data."""
        # Create historical data
        np.random.seed(42)
        historical = pd.DataFrame({
            'sensor_T30': np.random.normal(1590, 5, 100)
        })

        # Anomalous reading
        reading = SensorReading(
            unit_id=1,
            time_cycle=101,
            sensor_values={'sensor_T30': 1650.0}
        )

        anomalies = detect_anomalies_statistical(
            reading, historical, method='zscore', threshold=3.0
        )
        self.assertTrue(anomalies['sensor_T30']['is_anomaly'])

    def test_zscore_normal_reading(self):
        """Test z-score with normal reading."""
        np.random.seed(42)
        historical = pd.DataFrame({
            'sensor_T30': np.random.normal(1590, 5, 100)
        })

        reading = SensorReading(
            unit_id=1,
            time_cycle=101,
            sensor_values={'sensor_T30': 1592.0}  # Close to mean
        )

        anomalies = detect_anomalies_statistical(
            reading, historical, method='zscore', threshold=3.0
        )
        self.assertFalse(anomalies['sensor_T30']['is_anomaly'])

    def test_iqr_method(self):
        """Test IQR method."""
        np.random.seed(42)
        historical = pd.DataFrame({
            'sensor_T30': np.random.normal(1590, 5, 100)
        })

        reading = SensorReading(
            unit_id=1,
            time_cycle=101,
            sensor_values={'sensor_T30': 1650.0}
        )

        anomalies = detect_anomalies_statistical(
            reading, historical, method='iqr', threshold=1.5
        )
        self.assertTrue(anomalies['sensor_T30']['is_anomaly'])

    def test_constant_sensors_skipped(self):
        """Test constant sensors are skipped."""
        reading = SensorReading(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T2': 518.5}  # Constant sensor
        )
        anomalies = detect_anomalies_statistical(reading, method='range')
        # Constant sensors should not be in results
        self.assertNotIn('sensor_T2', anomalies)


class TestMLDetection(unittest.TestCase):
    """Test ML-based anomaly detection."""

    def test_isolation_forest_detection(self):
        """Test Isolation Forest detection."""
        # Normal data
        np.random.seed(42)
        historical = pd.DataFrame({
            'sensor_T30': np.random.normal(1590, 5, 100),
            'sensor_Nc': np.random.normal(9050, 10, 100)
        })

        # Anomalous reading
        reading = SensorReading(
            unit_id=1,
            time_cycle=101,
            sensor_values={'sensor_T30': 1650.0, 'sensor_Nc': 9100.0}
        )

        is_anomaly, score, importance = detect_anomalies_ml(reading, historical)
        self.assertTrue(is_anomaly)
        self.assertGreater(score, 0)
        self.assertIn('sensor_T30', importance)
        self.assertIn('sensor_Nc', importance)

    def test_ml_normal_reading(self):
        """Test ML with normal reading."""
        np.random.seed(42)
        historical = pd.DataFrame({
            'sensor_T30': np.random.normal(1590, 5, 100),
            'sensor_Nc': np.random.normal(9050, 10, 100)
        })

        reading = SensorReading(
            unit_id=1,
            time_cycle=101,
            sensor_values={'sensor_T30': 1591.0, 'sensor_Nc': 9048.0}
        )

        is_anomaly, score, importance = detect_anomalies_ml(reading, historical)
        # May or may not be anomaly depending on contamination, but should have low score
        self.assertLess(score, 0.8)

    def test_insufficient_data(self):
        """Test ML with insufficient data."""
        # Too little data
        historical = pd.DataFrame({
            'sensor_T30': [1590.0] * 10,
            'sensor_Nc': [9050.0] * 10
        })

        reading = SensorReading(
            unit_id=1,
            time_cycle=101,
            sensor_values={'sensor_T30': 1650.0, 'sensor_Nc': 9100.0}
        )

        is_anomaly, score, importance = detect_anomalies_ml(reading, historical)
        # Should fallback gracefully
        self.assertFalse(is_anomaly)
        self.assertEqual(score, 0.0)


class TestAnomalyDetectorModel(unittest.TestCase):
    """Test AnomalyDetectorModel class."""

    def test_fit_and_predict(self):
        """Test fitting and prediction."""
        np.random.seed(42)
        historical = pd.DataFrame({
            'sensor_T30': np.random.normal(1590, 5, 100),
            'sensor_Nc': np.random.normal(9050, 10, 100)
        })

        detector = AnomalyDetectorModel(contamination=0.1)
        detector.fit(historical)

        self.assertTrue(detector.is_fitted)
        self.assertGreater(len(detector.feature_names), 0)

        # Test prediction
        is_anomaly, score = detector.predict({
            'sensor_T30': 1650.0,
            'sensor_Nc': 9100.0
        })
        self.assertIsInstance(is_anomaly, (bool, np.bool_))
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_predict_before_fit_raises_error(self):
        """Test predicting before fitting raises error."""
        detector = AnomalyDetectorModel()
        with self.assertRaises(RuntimeError):
            detector.predict({'sensor_T30': 1650.0})

    def test_insufficient_samples_raises_error(self):
        """Test fitting with insufficient samples raises error."""
        historical = pd.DataFrame({
            'sensor_T30': [1590.0] * 10
        })
        detector = AnomalyDetectorModel()
        with self.assertRaises(ValueError):
            detector.fit(historical)


class TestMainFunction(unittest.TestCase):
    """Test main analyze_sensor_data function."""

    def test_combined_method(self):
        """Test combined detection method."""
        sensor_data = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {
                'sensor_T30': 1620.0,
                'sensor_Nc': 9080.0
            }
        }

        result = analyze_sensor_data(sensor_data, method='combined')
        self.assertIsInstance(result, AnomalyResult)
        self.assertIsInstance(result.anomaly_detected, bool)
        self.assertIn(result.severity, ['none', 'low', 'medium', 'high', 'critical'])
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)

    def test_statistical_method_only(self):
        """Test statistical method only."""
        sensor_data = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {
                'sensor_T30': 1650.0  # Out of range
            }
        }

        result = analyze_sensor_data(sensor_data, method='statistical')
        self.assertTrue(result.anomaly_detected)
        self.assertIn('sensor_T30', result.affected_sensors)
        self.assertEqual(result.method_used, 'statistical')

    def test_normal_reading_no_anomaly(self):
        """Test normal reading produces no anomaly."""
        sensor_data = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {
                'sensor_T30': 1590.0,  # Normal
                'sensor_Nc': 9050.0   # Normal
            }
        }

        result = analyze_sensor_data(sensor_data, method='statistical')
        self.assertFalse(result.anomaly_detected)
        self.assertEqual(result.severity, 'none')

    def test_recommendations_generated(self):
        """Test recommendations are generated for anomalies."""
        sensor_data = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {
                'sensor_T30': 1650.0  # High temperature
            }
        }

        result = analyze_sensor_data(sensor_data, method='statistical')
        self.assertTrue(result.anomaly_detected)
        self.assertGreater(len(result.recommendations), 0)
        # Should have temperature-related recommendation
        has_temp_rec = any('temperature' in rec.lower() for rec in result.recommendations)
        self.assertTrue(has_temp_rec)

    def test_severity_classification(self):
        """Test severity classification."""
        # Critical anomaly
        sensor_data = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {
                'sensor_T30': 1700.0,  # Way out of range
                'sensor_T50': 1500.0   # Way out of range
            }
        }

        result = analyze_sensor_data(sensor_data, method='statistical')
        self.assertTrue(result.anomaly_detected)
        self.assertIn(result.severity, ['high', 'critical'])

    def test_custom_thresholds(self):
        """Test custom thresholds work."""
        sensor_data = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {
                'sensor_T30': 1630.0
            }
        }

        custom_thresholds = {
            'anomaly_score_low': 0.1,
            'anomaly_score_medium': 0.3,
            'anomaly_score_high': 0.5,
            'anomaly_score_critical': 0.7
        }

        result = analyze_sensor_data(
            sensor_data,
            method='statistical',
            thresholds=custom_thresholds
        )
        self.assertIsInstance(result, AnomalyResult)

    def test_empty_list_raises_error(self):
        """Test empty list raises error."""
        with self.assertRaises(ValueError):
            analyze_sensor_data([])

    def test_list_input_uses_last(self):
        """Test list input uses last reading."""
        sensor_list = [
            {
                'unit_id': 1,
                'time_cycle': 99,
                'sensor_values': {'sensor_T30': 1590.0}
            },
            {
                'unit_id': 1,
                'time_cycle': 100,
                'sensor_values': {'sensor_T30': 1650.0}
            }
        ]

        result = analyze_sensor_data(sensor_list, method='statistical')
        # Should analyze the last reading (time_cycle=100)
        self.assertTrue(result.anomaly_detected)

    def test_to_dict_conversion(self):
        """Test AnomalyResult to_dict conversion."""
        sensor_data = {
            'unit_id': 1,
            'time_cycle': 100,
            'sensor_values': {'sensor_T30': 1620.0}
        }

        result = analyze_sensor_data(sensor_data, method='statistical')
        result_dict = result.to_dict()

        self.assertIsInstance(result_dict, dict)
        self.assertIn('anomaly_detected', result_dict)
        self.assertIn('anomaly_score', result_dict)
        self.assertIn('confidence', result_dict)
        self.assertIn('affected_sensors', result_dict)
        self.assertIn('severity', result_dict)


class TestQuickCheck(unittest.TestCase):
    """Test quick check function."""

    def test_quick_check_normal(self):
        """Test quick check with normal values."""
        sensor_values = {'sensor_T30': 1590.0}
        result = quick_check(sensor_values)

        self.assertIn('status', result)
        self.assertEqual(result['status'], 'normal')
        self.assertEqual(len(result['anomalous_sensors']), 0)

    def test_quick_check_warning(self):
        """Test quick check with warning."""
        sensor_values = {'sensor_T30': 1630.0}  # Slightly out of range
        result = quick_check(sensor_values)

        self.assertIn('status', result)
        self.assertIn(result['status'], ['warning', 'critical'])
        self.assertGreater(len(result['anomalous_sensors']), 0)

    def test_quick_check_critical(self):
        """Test quick check with critical anomaly."""
        sensor_values = {'sensor_T30': 1700.0}  # Way out of range
        result = quick_check(sensor_values)

        self.assertIn('status', result)
        self.assertEqual(result['status'], 'critical')
        self.assertIn('sensor_T30', result['anomalous_sensors'])

    def test_quick_check_multiple_sensors(self):
        """Test quick check with multiple sensors."""
        sensor_values = {
            'sensor_T30': 1650.0,
            'sensor_Nc': 9120.0,
            'sensor_Ps30': 47.0
        }
        result = quick_check(sensor_values)

        self.assertIn('status', result)
        self.assertIn('message', result)
        self.assertIn('anomalous_sensors', result)


if __name__ == '__main__':
    unittest.main()
