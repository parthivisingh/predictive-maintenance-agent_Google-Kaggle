"""
Prometheus Metrics for Tool Monitoring
=======================================

Metrics tracked:
- Request counts by tool
- Request durations
- Error rates
- Anomaly detection rates
- Database query performance
- ML model prediction times
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY
import time
from functools import wraps
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

# Create separate registry for our metrics
# (allows for easier testing and isolation)
custom_registry = CollectorRegistry()

# ============================================================================
# Define Metrics
# ============================================================================

# Request metrics
tool_requests_total = Counter(
    'tool_requests_total',
    'Total tool requests',
    ['tool_name', 'status'],
    registry=custom_registry
)

tool_request_duration = Histogram(
    'tool_request_duration_seconds',
    'Tool request duration in seconds',
    ['tool_name'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=custom_registry
)

# Anomaly detection metrics
anomalies_detected_total = Counter(
    'anomalies_detected_total',
    'Total anomalies detected',
    ['severity'],
    registry=custom_registry
)

anomaly_scores = Histogram(
    'anomaly_scores',
    'Distribution of anomaly scores',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=custom_registry
)

# Database metrics
database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=custom_registry
)

database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['query_type', 'status'],
    registry=custom_registry
)

database_results_count = Histogram(
    'database_results_count',
    'Number of results returned from database queries',
    ['query_type'],
    buckets=[0, 1, 5, 10, 20, 50, 100],
    registry=custom_registry
)

# ML model metrics
ml_model_prediction_duration = Histogram(
    'ml_model_prediction_duration_seconds',
    'ML model prediction duration',
    ['model_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=custom_registry
)

ml_model_predictions_total = Counter(
    'ml_model_predictions_total',
    'Total ML model predictions',
    ['model_type', 'prediction'],
    registry=custom_registry
)

# ROI calculation metrics
roi_calculations_total = Counter(
    'roi_calculations_total',
    'Total ROI calculations',
    ['recommendation'],
    registry=custom_registry
)

roi_savings = Histogram(
    'roi_expected_savings_dollars',
    'Expected savings from ROI calculations',
    buckets=[0, 100, 500, 1000, 5000, 10000, 50000],
    registry=custom_registry
)

# Work order metrics
work_orders_generated_total = Counter(
    'work_orders_generated_total',
    'Total work orders generated',
    ['priority'],
    registry=custom_registry
)

work_order_costs = Histogram(
    'work_order_estimated_cost_dollars',
    'Estimated work order costs',
    buckets=[0, 100, 500, 1000, 5000, 10000],
    registry=custom_registry
)

# System metrics
active_requests = Gauge(
    'active_requests',
    'Number of currently active requests',
    ['tool_name'],
    registry=custom_registry
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=custom_registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=custom_registry
)


# ============================================================================
# Decorator for Tracking Requests
# ============================================================================

def track_request(tool_name: str) -> Callable:
    """
    Decorator to track tool requests with metrics.

    Usage:
    ------
    @track_request('sensor_analyzer')
    def analyze_sensors(...):
        ...

    Parameters:
    -----------
    tool_name : str
        Name of the tool being tracked

    Returns:
    --------
    Callable
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Increment active requests
            active_requests.labels(tool_name=tool_name).inc()

            # Start timing
            start = time.time()
            status = 'success'
            result = None

            try:
                # Call function
                result = func(*args, **kwargs)

                # Check if result indicates failure
                if isinstance(result, dict) and not result.get('success', True):
                    status = 'error'

                return result

            except Exception as e:
                status = 'exception'
                logger.error(f"Exception in {tool_name}: {e}", exc_info=True)
                raise

            finally:
                # Calculate duration
                duration = time.time() - start

                # Record metrics
                tool_requests_total.labels(
                    tool_name=tool_name,
                    status=status
                ).inc()

                tool_request_duration.labels(
                    tool_name=tool_name
                ).observe(duration)

                # Decrement active requests
                active_requests.labels(tool_name=tool_name).dec()

                # Log performance
                if duration > 2.0:
                    logger.warning(
                        f"Slow request detected",
                        extra={
                            'tool_name': tool_name,
                            'duration_seconds': duration,
                            'status': status
                        }
                    )

        return wrapper

    return decorator


def track_database_query(query_type: str) -> Callable:
    """
    Decorator to track database queries.

    Usage:
    ------
    @track_database_query('similarity_search')
    def search_similar_failures(...):
        ...

    Parameters:
    -----------
    query_type : str
        Type of database query

    Returns:
    --------
    Callable
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            status = 'success'
            result = None

            try:
                result = func(*args, **kwargs)

                # Record result count if result is a list
                if isinstance(result, list):
                    database_results_count.labels(
                        query_type=query_type
                    ).observe(len(result))

                return result

            except Exception as e:
                status = 'error'
                raise

            finally:
                duration = time.time() - start

                database_query_duration.labels(
                    query_type=query_type
                ).observe(duration)

                database_queries_total.labels(
                    query_type=query_type,
                    status=status
                ).inc()

        return wrapper

    return decorator


def track_ml_prediction(model_type: str) -> Callable:
    """
    Decorator to track ML model predictions.

    Usage:
    ------
    @track_ml_prediction('IsolationForest')
    def predict_anomaly(...):
        ...

    Parameters:
    -----------
    model_type : str
        Type of ML model

    Returns:
    --------
    Callable
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()

            result = func(*args, **kwargs)

            duration = time.time() - start

            ml_model_prediction_duration.labels(
                model_type=model_type
            ).observe(duration)

            # Track prediction result if available
            if hasattr(result, 'anomaly_detected'):
                prediction = 'anomaly' if result.anomaly_detected else 'normal'
                ml_model_predictions_total.labels(
                    model_type=model_type,
                    prediction=prediction
                ).inc()

            return result

        return wrapper

    return decorator


# ============================================================================
# Helper Functions
# ============================================================================

def record_anomaly(severity: str, score: float) -> None:
    """
    Record an anomaly detection event.

    Parameters:
    -----------
    severity : str
        Anomaly severity level
    score : float
        Anomaly score (0-1)
    """
    anomalies_detected_total.labels(severity=severity).inc()
    anomaly_scores.observe(score)


def record_roi_calculation(
    recommendation: str,
    expected_savings: float
) -> None:
    """
    Record an ROI calculation.

    Parameters:
    -----------
    recommendation : str
        Recommendation (e.g., "RECOMMENDED", "NOT_RECOMMENDED")
    expected_savings : float
        Expected savings in dollars
    """
    roi_calculations_total.labels(recommendation=recommendation).inc()
    roi_savings.observe(expected_savings)


def record_work_order(
    priority: str,
    estimated_cost: float
) -> None:
    """
    Record a work order generation event.

    Parameters:
    -----------
    priority : str
        Work order priority
    estimated_cost : float
        Estimated cost in dollars
    """
    work_orders_generated_total.labels(priority=priority).inc()
    work_order_costs.observe(estimated_cost)


def record_cache_hit(cache_type: str) -> None:
    """
    Record a cache hit.

    Parameters:
    -----------
    cache_type : str
        Type of cache
    """
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """
    Record a cache miss.

    Parameters:
    -----------
    cache_type : str
        Type of cache
    """
    cache_misses_total.labels(cache_type=cache_type).inc()


def get_metrics_registry() -> CollectorRegistry:
    """
    Get the metrics registry.

    Returns:
    --------
    CollectorRegistry
        Prometheus registry
    """
    return custom_registry
