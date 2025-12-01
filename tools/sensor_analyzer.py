"""
Sensor Anomaly Detection Tool
==============================

Detects anomalies in turbofan engine sensor readings using statistical
and machine learning methods.

USAGE FOR PHASE 4 AGENTS:
-------------------------

Basic usage (quick check):
>>> from tools.sensor_analyzer import analyze_sensor_data
>>>
>>> sensor_data = {
>>>     'unit_id': 1,
>>>     'time_cycle': 100,
>>>     'sensor_values': {
>>>         'sensor_T30': 1620.0,  # HPC outlet temperature
>>>         'sensor_Nc': 9080.0,   # Core speed
>>>         'sensor_Ps30': 48.2    # HPC static pressure
>>>     }
>>> }
>>>
>>> result = analyze_sensor_data(sensor_data)
>>> print(result.anomaly_detected)  # True/False
>>> print(result.severity)  # 'low', 'medium', 'high', 'critical'
>>> print(result.recommendations)  # List of actions

Advanced usage (custom thresholds):
>>> result = analyze_sensor_data(
>>>     sensor_data,
>>>     method='combined',  # Use both statistical + ML
>>>     historical_lookback=150,  # Look at last 150 cycles
>>>     thresholds={
>>>         'anomaly_score_critical': 0.9
>>>     }
>>> )

Quick check (no ML, fast):
>>> from tools.sensor_analyzer import quick_check
>>> status = quick_check({'sensor_T30': 1650.0})
>>> print(status['status'])  # 'normal', 'warning', or 'critical'

INTEGRATION WITH GOOGLE ADK:
-----------------------------
To use as an ADK tool in Phase 4:

from google.adk import Tool
from tools.sensor_analyzer import analyze_sensor_data

sensor_analyzer_tool = Tool(
    name="sensor_analyzer",
    description="Analyzes sensor data to detect equipment anomalies",
    func=analyze_sensor_data
)

# Use in agent
diagnostic_agent = Agent(
    name="diagnostic_agent",
    tools=[sensor_analyzer_tool, ...]
)
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


@dataclass
class SensorReading:
    """
    Represents a single sensor reading snapshot.

    Attributes:
    -----------
    unit_id : int
        Equipment unit identifier
    time_cycle : int
        Operational cycle number
    sensor_values : Dict[str, float]
        Sensor name -> value mapping (e.g., {"sensor_T30": 1605.2, ...})
    operational_settings : Dict[str, float]
        Operating condition settings (op_setting_1, op_setting_2, op_setting_3)
    timestamp : datetime, optional
        Reading timestamp (defaults to now)
    """
    unit_id: int
    time_cycle: int
    sensor_values: Dict[str, float]
    operational_settings: Dict[str, float] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self.validate()

    def validate(self) -> None:
        """Validate sensor reading data."""
        if not isinstance(self.unit_id, int) or self.unit_id < 1:
            raise ValueError(f"unit_id must be positive integer, got {self.unit_id}")

        if not isinstance(self.time_cycle, int) or self.time_cycle < 1:
            raise ValueError(f"time_cycle must be positive integer, got {self.time_cycle}")

        if not self.sensor_values:
            raise ValueError("sensor_values cannot be empty")

        # Check all sensor values are numeric
        for sensor, value in self.sensor_values.items():
            if not isinstance(value, (int, float)) or np.isnan(value):
                raise ValueError(f"Invalid value for {sensor}: {value}")


@dataclass
class AnomalyResult:
    """
    Results from anomaly detection analysis.

    Attributes:
    -----------
    anomaly_detected : bool
        Whether any anomaly was detected
    anomaly_score : float
        Overall anomaly score (0-1, higher = more anomalous)
    confidence : float
        Confidence level of detection (0-1)
    affected_sensors : List[str]
        List of sensors showing anomalous behavior
    anomaly_details : Dict[str, Dict]
        Detailed anomaly information per sensor
    severity : str
        Severity level: 'low', 'medium', 'high', 'critical'
    method_used : str
        Detection method: 'statistical', 'isolation_forest', 'combined'
    recommendations : List[str]
        Actionable recommendations based on anomalies
    """
    anomaly_detected: bool
    anomaly_score: float
    confidence: float
    affected_sensors: List[str]
    anomaly_details: Dict[str, Dict]
    severity: str
    method_used: str
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'anomaly_detected': self.anomaly_detected,
            'anomaly_score': round(self.anomaly_score, 4),
            'confidence': round(self.confidence, 4),
            'affected_sensors': self.affected_sensors,
            'anomaly_details': self.anomaly_details,
            'severity': self.severity,
            'method_used': self.method_used,
            'recommendations': self.recommendations
        }


# Sensor constants (from Phase 2 analysis)
CONSTANT_SENSORS = [
    'sensor_T2', 'sensor_P2', 'sensor_P15', 'sensor_epr',
    'sensor_farB', 'sensor_Nf_dmd', 'sensor_PCNfR_dmd'
]

SENSOR_RANGES = {
    # Temperature sensors (°R)
    'sensor_T2': (518.0, 519.5),
    'sensor_T24': (640.0, 645.0),
    'sensor_T30': (1575.0, 1625.0),
    'sensor_T50': (1390.0, 1410.0),

    # Pressure sensors (psia)
    'sensor_P2': (14.5, 14.75),
    'sensor_P15': (21.5, 21.75),
    'sensor_P30': (550.0, 560.0),
    'sensor_Ps30': (46.5, 48.5),

    # Speed sensors (rpm)
    'sensor_Nf': (2385.0, 2395.0),
    'sensor_Nc': (9030.0, 9100.0),
    'sensor_NRf': (2385.0, 2395.0),
    'sensor_NRc': (8120.0, 8150.0),

    # Other sensors
    'sensor_epr': (1.29, 1.31),
    'sensor_phi': (520.0, 525.0),
    'sensor_BPR': (8.35, 8.50),
    'sensor_farB': (0.029, 0.031),
    'sensor_htBleed': (388.0, 396.0),
    'sensor_W31': (38.5, 39.5),
    'sensor_W32': (23.0, 23.8)
}


def validate_sensor_reading(sensor_reading: Union[Dict, SensorReading]) -> SensorReading:
    """
    Validate and convert sensor reading to SensorReading object.

    Parameters:
    -----------
    sensor_reading : Dict or SensorReading
        Raw sensor reading data

    Returns:
    --------
    SensorReading
        Validated sensor reading object

    Raises:
    -------
    ValueError : If validation fails
    TypeError : If input type is incorrect
    """
    if isinstance(sensor_reading, SensorReading):
        return sensor_reading

    if not isinstance(sensor_reading, dict):
        raise TypeError(f"Expected dict or SensorReading, got {type(sensor_reading)}")

    # Extract required fields
    required_fields = ['unit_id', 'time_cycle', 'sensor_values']
    missing = [f for f in required_fields if f not in sensor_reading]

    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    return SensorReading(**sensor_reading)


def detect_anomalies_statistical(
    sensor_reading: SensorReading,
    historical_data: Optional[pd.DataFrame] = None,
    method: str = 'zscore',
    threshold: float = 3.0
) -> Dict[str, Dict]:
    """
    Detect anomalies using statistical methods.

    Methods:
    --------
    - 'zscore': Z-score (standard deviations from mean)
    - 'iqr': Interquartile range method
    - 'range': Simple range checking against SENSOR_RANGES

    Parameters:
    -----------
    sensor_reading : SensorReading
        Current sensor reading
    historical_data : pd.DataFrame, optional
        Historical sensor data for computing statistics
        Must have columns matching sensor names
    method : str
        Detection method ('zscore', 'iqr', 'range')
    threshold : float
        Threshold for anomaly detection:
        - zscore: number of standard deviations (default: 3.0)
        - iqr: IQR multiplier (default: 1.5)
        - range: ignored (uses SENSOR_RANGES)

    Returns:
    --------
    Dict[str, Dict]
        Anomaly details per sensor:
        {
            'sensor_T30': {
                'is_anomaly': True,
                'value': 1620.5,
                'expected_range': (1575.0, 1610.0),
                'deviation': 10.5,
                'severity_score': 0.85
            },
            ...
        }
    """
    anomalies = {}

    for sensor_name, value in sensor_reading.sensor_values.items():
        # Skip constant sensors
        if sensor_name in CONSTANT_SENSORS:
            continue

        anomaly_info = {
            'is_anomaly': False,
            'value': value,
            'expected_range': None,
            'deviation': 0.0,
            'severity_score': 0.0
        }

        if method == 'range':
            # Simple range checking
            if sensor_name in SENSOR_RANGES:
                min_val, max_val = SENSOR_RANGES[sensor_name]
                anomaly_info['expected_range'] = (min_val, max_val)

                if value < min_val or value > max_val:
                    anomaly_info['is_anomaly'] = True
                    # Calculate how far outside range
                    if value < min_val:
                        anomaly_info['deviation'] = min_val - value
                    else:
                        anomaly_info['deviation'] = value - max_val

                    # Severity: 0-1 based on how far outside
                    range_width = max_val - min_val
                    anomaly_info['severity_score'] = min(
                        anomaly_info['deviation'] / range_width,
                        1.0
                    )

        elif method == 'zscore' and historical_data is not None:
            # Z-score method
            if sensor_name in historical_data.columns:
                sensor_history = historical_data[sensor_name].dropna()

                if len(sensor_history) > 10:  # Need sufficient history
                    mean = sensor_history.mean()
                    std = sensor_history.std()

                    if std > 0:
                        z_score = abs((value - mean) / std)
                        anomaly_info['expected_range'] = (
                            mean - threshold * std,
                            mean + threshold * std
                        )
                        anomaly_info['deviation'] = z_score

                        if z_score > threshold:
                            anomaly_info['is_anomaly'] = True
                            # Severity increases with z-score
                            anomaly_info['severity_score'] = min(z_score / (threshold * 2), 1.0)

        elif method == 'iqr' and historical_data is not None:
            # IQR method (robust to outliers)
            if sensor_name in historical_data.columns:
                sensor_history = historical_data[sensor_name].dropna()

                if len(sensor_history) > 10:
                    q1 = sensor_history.quantile(0.25)
                    q3 = sensor_history.quantile(0.75)
                    iqr = q3 - q1

                    lower_bound = q1 - threshold * iqr
                    upper_bound = q3 + threshold * iqr

                    anomaly_info['expected_range'] = (lower_bound, upper_bound)

                    if value < lower_bound or value > upper_bound:
                        anomaly_info['is_anomaly'] = True
                        # Calculate deviation
                        if value < lower_bound:
                            anomaly_info['deviation'] = lower_bound - value
                        else:
                            anomaly_info['deviation'] = value - upper_bound

                        anomaly_info['severity_score'] = min(
                            anomaly_info['deviation'] / iqr if iqr > 0 else 0,
                            1.0
                        )

        anomalies[sensor_name] = anomaly_info

    return anomalies


def load_historical_data(
    unit_id: int,
    lookback_cycles: int = 100,
    dataset_path: str = "data/cmapss_processed.csv"
) -> pd.DataFrame:
    """
    Load historical sensor data for a specific unit.

    Parameters:
    -----------
    unit_id : int
        Equipment unit ID
    lookback_cycles : int
        Number of recent cycles to load
    dataset_path : str
        Path to processed C-MAPSS dataset

    Returns:
    --------
    pd.DataFrame
        Historical sensor data for unit
    """
    try:
        df = pd.read_csv(dataset_path)

        # Filter for specific unit
        unit_data = df[df['unit_id'] == unit_id].copy()

        if len(unit_data) == 0:
            return pd.DataFrame()  # Empty dataframe

        # Get most recent cycles
        unit_data = unit_data.sort_values('time_cycle', ascending=False)
        unit_data = unit_data.head(lookback_cycles)

        # Select only sensor columns
        sensor_cols = [col for col in unit_data.columns if col.startswith('sensor_')]
        return unit_data[sensor_cols]

    except Exception as e:
        print(f"Warning: Could not load historical data: {e}")
        return pd.DataFrame()


class AnomalyDetectorModel:
    """
    Machine learning anomaly detector using Isolation Forest.
    """

    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.

        Parameters:
        -----------
        contamination : float
            Expected proportion of anomalies (0.0-0.5)
            Default: 0.1 (10% of data expected to be anomalous)
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []

    def fit(self, historical_data: pd.DataFrame) -> None:
        """
        Train anomaly detector on historical data.

        Parameters:
        -----------
        historical_data : pd.DataFrame
            Historical sensor data (rows=cycles, cols=sensors)
        """
        if len(historical_data) < 20:
            raise ValueError("Need at least 20 samples to train Isolation Forest")

        # Select sensor columns only
        sensor_cols = [col for col in historical_data.columns
                      if col.startswith('sensor_') and col not in CONSTANT_SENSORS]

        X = historical_data[sensor_cols].dropna()

        if len(X) < 20:
            raise ValueError("Insufficient non-null sensor data")

        self.feature_names = sensor_cols

        # Standardize features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model.fit(X_scaled)
        self.is_fitted = True

    def predict(self, sensor_values: Dict[str, float]) -> Tuple[bool, float]:
        """
        Predict if sensor reading is anomalous.

        Parameters:
        -----------
        sensor_values : Dict[str, float]
            Current sensor readings

        Returns:
        --------
        Tuple[bool, float]
            (is_anomaly, anomaly_score)
            - is_anomaly: True if anomalous
            - anomaly_score: 0-1 (higher = more anomalous)
        """
        if not self.is_fitted:
            raise RuntimeError("Model not trained. Call fit() first.")

        # Prepare input vector
        X = np.array([[sensor_values.get(col, 0.0) for col in self.feature_names]])

        # Standardize
        X_scaled = self.scaler.transform(X)

        # Predict (-1 = anomaly, 1 = normal)
        prediction = self.model.predict(X_scaled)[0]

        # Get anomaly score (more negative = more anomalous)
        decision_score = self.model.decision_function(X_scaled)[0]

        # Convert to 0-1 scale (decision scores typically range -0.5 to 0.5)
        anomaly_score = max(0.0, min(1.0, -decision_score + 0.5))

        is_anomaly = (prediction == -1)

        return is_anomaly, anomaly_score


def detect_anomalies_ml(
    sensor_reading: SensorReading,
    historical_data: pd.DataFrame,
    contamination: float = 0.1
) -> Tuple[bool, float, Dict[str, float]]:
    """
    Detect anomalies using Isolation Forest ML model.

    Parameters:
    -----------
    sensor_reading : SensorReading
        Current sensor reading
    historical_data : pd.DataFrame
        Historical data for training
    contamination : float
        Expected proportion of anomalies

    Returns:
    --------
    Tuple[bool, float, Dict[str, float]]
        (is_anomaly, anomaly_score, feature_importance)
    """
    detector = AnomalyDetectorModel(contamination=contamination)

    try:
        detector.fit(historical_data)
        is_anomaly, score = detector.predict(sensor_reading.sensor_values)

        # Calculate feature importance (simplified)
        # In production, use permutation importance or SHAP values
        feature_importance = {
            sensor: abs(sensor_reading.sensor_values.get(sensor, 0) -
                       historical_data[sensor].mean())
            for sensor in detector.feature_names
            if sensor in sensor_reading.sensor_values
        }

        return is_anomaly, score, feature_importance

    except Exception as e:
        # Fallback if ML fails
        print(f"ML detection failed: {e}")
        return False, 0.0, {}


def analyze_sensor_data(
    sensor_readings: Union[Dict, SensorReading, List[Dict]],
    method: str = 'combined',
    historical_lookback: int = 100,
    dataset_path: str = "data/cmapss_processed.csv",
    contamination: float = 0.1,
    thresholds: Optional[Dict[str, float]] = None
) -> AnomalyResult:
    """
    Main function to analyze sensor data for anomalies.

    This is the primary function that Phase 4 agents will call.

    Parameters:
    -----------
    sensor_readings : Dict, SensorReading, or List[Dict]
        Sensor reading(s) to analyze
        If list, analyzes most recent reading
    method : str
        Detection method:
        - 'statistical': Statistical methods only (fast, no ML)
        - 'ml': Machine learning only (slower, more accurate)
        - 'combined': Use both methods (recommended)
    historical_lookback : int
        Number of recent cycles to use for comparison
    dataset_path : str
        Path to C-MAPSS processed dataset
    contamination : float
        For ML: expected proportion of anomalies
    thresholds : Dict[str, float], optional
        Custom thresholds for severity classification

    Returns:
    --------
    AnomalyResult
        Comprehensive anomaly analysis results

    Raises:
    -------
    ValueError : If input validation fails
    """
    # Default thresholds
    if thresholds is None:
        thresholds = {
            'anomaly_score_low': 0.3,
            'anomaly_score_medium': 0.5,
            'anomaly_score_high': 0.7,
            'anomaly_score_critical': 0.85
        }

    # Handle list input (take most recent)
    if isinstance(sensor_readings, list):
        if not sensor_readings:
            raise ValueError("Empty sensor readings list")
        sensor_readings = sensor_readings[-1]

    # Validate and convert to SensorReading
    reading = validate_sensor_reading(sensor_readings)

    # Load historical data
    historical_data = load_historical_data(
        reading.unit_id,
        historical_lookback,
        dataset_path
    )

    # Initialize result containers
    all_anomalies = {}
    affected_sensors = []
    recommendations = []
    method_used = method

    # Run statistical detection
    if method in ['statistical', 'combined']:
        # Try multiple statistical methods
        stat_anomalies_range = detect_anomalies_statistical(
            reading, historical_data, method='range'
        )

        if len(historical_data) > 10:
            stat_anomalies_zscore = detect_anomalies_statistical(
                reading, historical_data, method='zscore', threshold=3.0
            )

            # Merge results (anomaly if flagged by either method)
            for sensor in stat_anomalies_range:
                if stat_anomalies_range[sensor]['is_anomaly'] or \
                   stat_anomalies_zscore.get(sensor, {}).get('is_anomaly', False):
                    all_anomalies[sensor] = stat_anomalies_range[sensor]
                    all_anomalies[sensor]['detection_methods'] = []
                    if stat_anomalies_range[sensor]['is_anomaly']:
                        all_anomalies[sensor]['detection_methods'].append('range')
                    if stat_anomalies_zscore.get(sensor, {}).get('is_anomaly', False):
                        all_anomalies[sensor]['detection_methods'].append('zscore')
        else:
            # Only range-based if insufficient history
            all_anomalies = {k: v for k, v in stat_anomalies_range.items()
                           if v['is_anomaly']}
            for sensor in all_anomalies:
                all_anomalies[sensor]['detection_methods'] = ['range']

    # Run ML detection
    ml_score = 0.0
    if method in ['ml', 'combined'] and len(historical_data) >= 20:
        try:
            is_ml_anomaly, ml_score, feature_importance = detect_anomalies_ml(
                reading, historical_data, contamination
            )

            if is_ml_anomaly:
                # Add ML-detected anomalies
                for sensor, importance in sorted(
                    feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]:  # Top 5 contributing sensors
                    if sensor not in all_anomalies:
                        all_anomalies[sensor] = {
                            'is_anomaly': True,
                            'value': reading.sensor_values.get(sensor, 0),
                            'expected_range': None,
                            'deviation': importance,
                            'severity_score': min(importance / 50.0, 1.0),  # Normalize
                            'detection_methods': ['ml']
                        }
                    else:
                        all_anomalies[sensor]['detection_methods'].append('ml')
        except Exception as e:
            print(f"ML detection skipped: {e}")
            method_used = 'statistical'  # Fallback

    # Calculate overall anomaly score
    if all_anomalies:
        # Average severity of detected anomalies
        severity_scores = [info['severity_score'] for info in all_anomalies.values()]
        anomaly_score = np.mean(severity_scores)

        # Boost score if ML also detected anomaly
        if ml_score > 0:
            anomaly_score = (anomaly_score + ml_score) / 2

        affected_sensors = list(all_anomalies.keys())
        anomaly_detected = True
    else:
        anomaly_score = ml_score if ml_score > 0 else 0.0
        anomaly_detected = (anomaly_score > thresholds['anomaly_score_low'])
        affected_sensors = []

    # Determine severity
    if anomaly_score >= thresholds['anomaly_score_critical']:
        severity = 'critical'
    elif anomaly_score >= thresholds['anomaly_score_high']:
        severity = 'high'
    elif anomaly_score >= thresholds['anomaly_score_medium']:
        severity = 'medium'
    elif anomaly_score >= thresholds['anomaly_score_low']:
        severity = 'low'
    else:
        severity = 'none'

    # Calculate confidence
    # High confidence if multiple methods agree
    if method == 'combined' and all_anomalies:
        agreement_count = sum(
            1 for info in all_anomalies.values()
            if len(info.get('detection_methods', [])) > 1
        )
        confidence = 0.6 + (0.4 * agreement_count / max(len(all_anomalies), 1))
    else:
        confidence = 0.7  # Single method confidence

    confidence = min(confidence, 0.95)  # Cap at 95%

    # Generate recommendations
    if anomaly_detected:
        if 'sensor_T30' in affected_sensors or 'sensor_T50' in affected_sensors:
            recommendations.append("High temperature detected - inspect for overheating")
        if 'sensor_Nc' in affected_sensors or 'sensor_Nf' in affected_sensors:
            recommendations.append("Abnormal speed readings - check for mechanical issues")
        if 'sensor_Ps30' in affected_sensors or 'sensor_P30' in affected_sensors:
            recommendations.append("Pressure anomaly detected - inspect seals and valves")
        if 'sensor_phi' in affected_sensors:
            recommendations.append("Fuel system irregularity - check fuel delivery system")

        if severity in ['high', 'critical']:
            recommendations.append("URGENT: Schedule immediate inspection")
        elif severity == 'medium':
            recommendations.append("Schedule inspection within next maintenance window")
        else:
            recommendations.append("Monitor closely during next operational cycles")

    # Create result object
    result = AnomalyResult(
        anomaly_detected=bool(anomaly_detected),
        anomaly_score=float(anomaly_score),
        confidence=float(confidence),
        affected_sensors=affected_sensors,
        anomaly_details=all_anomalies,
        severity=severity,
        method_used=method_used,
        recommendations=recommendations
    )

    return result


def quick_check(sensor_values: Dict[str, float]) -> Dict:
    """
    Quick anomaly check without full analysis.

    Fast range-based check for immediate feedback.

    Parameters:
    -----------
    sensor_values : Dict[str, float]
        Sensor name -> value mapping

    Returns:
    --------
    Dict
        {
            'status': 'normal' | 'warning' | 'critical',
            'message': str,
            'anomalous_sensors': List[str]
        }
    """
    reading = SensorReading(unit_id=1, time_cycle=1, sensor_values=sensor_values)

    anomalies = detect_anomalies_statistical(reading, method='range')
    anomalous = [s for s, info in anomalies.items() if info['is_anomaly']]

    if not anomalous:
        return {
            'status': 'normal',
            'message': 'All sensors within normal range',
            'anomalous_sensors': []
        }

    max_severity = max(anomalies[s]['severity_score'] for s in anomalous)

    if max_severity > 0.7:
        status = 'critical'
    else:
        status = 'warning'

    return {
        'status': status,
        'message': f"{len(anomalous)} sensor(s) out of range",
        'anomalous_sensors': anomalous
    }
