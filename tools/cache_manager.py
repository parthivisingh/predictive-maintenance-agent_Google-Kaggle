"""
Caching Layer for Performance Optimization
===========================================

Caches:
- Historical sensor data (per unit)
- Pre-trained ML models
- Database query results
- Similarity search results
"""

from functools import lru_cache
import hashlib
import json
from typing import Any, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for all tools."""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Initialize cache manager.

        Parameters:
        -----------
        ttl_seconds : int
            Time-to-live for cached entries (default: 1 hour)
        max_size : int
            Maximum number of cached entries (default: 1000)
        """
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache = {}
        self._timestamps = {}
        self._access_counts = {}

    def _generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate cache key from parameters.

        Parameters:
        -----------
        prefix : str
            Cache key prefix
        **kwargs
            Parameters to include in key

        Returns:
        --------
        str
            Cache key
        """
        # Sort kwargs to ensure consistent keys
        key_data = json.dumps(kwargs, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"{prefix}:{key_hash}"

    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """
        Get from cache if not expired.

        Parameters:
        -----------
        prefix : str
            Cache key prefix
        **kwargs
            Parameters to match

        Returns:
        --------
        Any or None
            Cached value if found and not expired, None otherwise
        """
        key = self._generate_key(prefix, **kwargs)

        if key in self._cache:
            # Check TTL
            timestamp = self._timestamps[key]
            age = (datetime.now() - timestamp).total_seconds()

            if age < self.ttl:
                # Update access count
                self._access_counts[key] = self._access_counts.get(key, 0) + 1

                logger.debug(f"Cache hit: {key} (age: {age:.1f}s)")
                return self._cache[key]
            else:
                # Expired, remove
                self._remove_key(key)
                logger.debug(f"Cache expired: {key} (age: {age:.1f}s)")

        logger.debug(f"Cache miss: {key}")
        return None

    def set(self, prefix: str, value: Any, **kwargs) -> None:
        """
        Set cache entry.

        Parameters:
        -----------
        prefix : str
            Cache key prefix
        value : Any
            Value to cache
        **kwargs
            Parameters to include in key
        """
        # Evict old entries if at max size
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        key = self._generate_key(prefix, **kwargs)
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        self._access_counts[key] = 0

        logger.debug(f"Cache set: {key}")

    def _remove_key(self, key: str) -> None:
        """Remove a key from all cache structures."""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
        if key in self._access_counts:
            del self._access_counts[key]

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find entry with lowest access count and oldest timestamp
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._access_counts.get(k, 0), self._timestamps.get(k, datetime.min))
        )

        logger.debug(f"Cache eviction: {lru_key}")
        self._remove_key(lru_key)

    def clear(self, prefix: Optional[str] = None) -> None:
        """
        Clear cache (optionally by prefix).

        Parameters:
        -----------
        prefix : str, optional
            Clear only keys with this prefix (clears all if None)
        """
        if prefix is None:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            self._access_counts.clear()
            logger.info(f"Cache cleared: {count} entries")
        else:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                self._remove_key(key)
            logger.info(f"Cache cleared for prefix '{prefix}': {len(keys_to_remove)} entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
        --------
        Dict
            Cache statistics
        """
        total_entries = len(self._cache)
        total_accesses = sum(self._access_counts.values())

        # Calculate average age
        if self._timestamps:
            now = datetime.now()
            ages = [(now - ts).total_seconds() for ts in self._timestamps.values()]
            avg_age = sum(ages) / len(ages)
            max_age = max(ages)
        else:
            avg_age = 0
            max_age = 0

        return {
            'total_entries': total_entries,
            'max_size': self.max_size,
            'utilization': total_entries / self.max_size if self.max_size > 0 else 0,
            'total_accesses': total_accesses,
            'avg_age_seconds': round(avg_age, 2),
            'max_age_seconds': round(max_age, 2),
            'ttl_seconds': self.ttl
        }

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
        --------
        int
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, ts in self._timestamps.items()
            if (now - ts).total_seconds() >= self.ttl
        ]

        for key in expired_keys:
            self._remove_key(key)

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)


# Global cache instance
_cache_instance = None


def get_cache() -> CacheManager:
    """
    Get singleton cache instance.

    Returns:
    --------
    CacheManager
        Global cache manager
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(ttl_seconds=3600)
    return _cache_instance


# ============================================================================
# Specialized Cache Functions
# ============================================================================

def load_historical_data_cached(
    unit_id: int,
    lookback_cycles: int = 100,
    dataset_path: str = "data/cmapss_processed.csv"
) -> pd.DataFrame:
    """
    Load historical sensor data with caching.

    Parameters:
    -----------
    unit_id : int
        Equipment unit ID
    lookback_cycles : int
        Number of cycles to look back
    dataset_path : str
        Path to dataset

    Returns:
    --------
    pd.DataFrame
        Historical sensor data
    """
    cache = get_cache()

    # Try cache first
    cached_data = cache.get(
        "historical_data",
        unit_id=unit_id,
        lookback_cycles=lookback_cycles,
        dataset_path=dataset_path
    )

    if cached_data is not None:
        logger.debug(f"Historical data cache hit for unit {unit_id}")
        from tools.metrics import record_cache_hit
        record_cache_hit("historical_data")
        return cached_data

    # Load from disk
    logger.debug(f"Historical data cache miss for unit {unit_id}")
    from tools.metrics import record_cache_miss
    record_cache_miss("historical_data")

    try:
        df = pd.read_csv(dataset_path)
        unit_data = df[df['unit_id'] == unit_id].copy()

        if len(unit_data) == 0:
            logger.warning(f"No data found for unit {unit_id}")
            return pd.DataFrame()

        unit_data = unit_data.sort_values('time_cycle', ascending=False)
        unit_data = unit_data.head(lookback_cycles)

        sensor_cols = [col for col in unit_data.columns if col.startswith('sensor_')]
        result = unit_data[sensor_cols]

        # Cache result
        cache.set(
            "historical_data",
            result,
            unit_id=unit_id,
            lookback_cycles=lookback_cycles,
            dataset_path=dataset_path
        )

        return result

    except Exception as e:
        logger.error(f"Could not load historical data: {e}")
        return pd.DataFrame()


def cache_similarity_results(
    sensor_values: Dict[str, float],
    results: list,
    top_n: int,
    threshold: float
) -> None:
    """
    Cache similarity search results.

    Parameters:
    -----------
    sensor_values : Dict[str, float]
        Sensor values used for search
    results : list
        Search results
    top_n : int
        Number of results requested
    threshold : float
        Similarity threshold used
    """
    cache = get_cache()
    cache.set(
        "similarity_search",
        results,
        sensor_values=sensor_values,
        top_n=top_n,
        threshold=threshold
    )


def get_cached_similarity_results(
    sensor_values: Dict[str, float],
    top_n: int,
    threshold: float
) -> Optional[list]:
    """
    Get cached similarity search results.

    Parameters:
    -----------
    sensor_values : Dict[str, float]
        Sensor values for search
    top_n : int
        Number of results
    threshold : float
        Similarity threshold

    Returns:
    --------
    list or None
        Cached results if found
    """
    cache = get_cache()
    result = cache.get(
        "similarity_search",
        sensor_values=sensor_values,
        top_n=top_n,
        threshold=threshold
    )

    if result is not None:
        from tools.metrics import record_cache_hit
        record_cache_hit("similarity_search")
    else:
        from tools.metrics import record_cache_miss
        record_cache_miss("similarity_search")

    return result
