"""
Prometheus Metrics Server
==========================

Exposes metrics for scraping by Prometheus.
"""

from prometheus_client import make_wsgi_app, generate_latest
from tools.metrics import get_metrics_registry
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def create_metrics_app():
    """
    Create WSGI app for metrics endpoint.

    Returns:
    --------
    WSGI app
        Prometheus metrics app
    """
    registry = get_metrics_registry()
    return make_wsgi_app(registry)


def get_metrics_text() -> str:
    """
    Get metrics in Prometheus text format.

    Returns:
    --------
    str
        Metrics in text format
    """
    registry = get_metrics_registry()
    return generate_latest(registry).decode('utf-8')


def start_metrics_server(
    port: int = 8000,
    host: str = '0.0.0.0'
) -> None:
    """
    Start standalone metrics server.

    Parameters:
    -----------
    port : int
        Port to listen on (default: 8000)
    host : str
        Host to bind to (default: 0.0.0.0)
    """
    try:
        from wsgiref.simple_server import make_server

        app = create_metrics_app()
        server = make_server(host, port, app)

        logger.info(f"Metrics server starting on {host}:{port}")
        print(f"Metrics available at http://{host}:{port}/metrics")

        server.serve_forever()

    except ImportError:
        logger.error("wsgiref not available, cannot start metrics server")
        raise
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        raise


if __name__ == '__main__':
    """Run metrics server standalone."""
    import sys

    # Parse command line arguments
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    # Start server
    try:
        start_metrics_server(port=port)
    except KeyboardInterrupt:
        print("\nShutting down metrics server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
