"""
ML Model Persistence and Version Management
============================================

Handles:
1. Model training and persistence
2. Version tracking and metadata
3. Model loading and caching
4. Calibration and performance monitoring
"""

import joblib
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Model training metadata."""
    model_id: str
    model_type: str  # "IsolationForest"
    version: str
    training_date: str
    dataset_hash: str
    training_samples: int
    contamination: float
    performance_metrics: Dict[str, float]
    calibration_data: Dict[str, float]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary."""
        return cls(**data)


class MLModelManager:
    """Manages ML model lifecycle."""

    MODEL_DIR = Path("models/anomaly_detection")

    def __init__(self):
        """Initialize model manager."""
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self._model_cache = {}

    def train_and_save_model(
        self,
        model,
        training_data,
        contamination: float,
        model_type: str = "IsolationForest"
    ) -> str:
        """
        Train model and save with metadata.

        Parameters:
        -----------
        model : Any
            Trained model or model package
        training_data : pd.DataFrame
            Training data used
        contamination : float
            Contamination parameter used
        model_type : str
            Type of model

        Returns:
        --------
        str : Model ID
        """
        # Generate dataset hash for reproducibility
        try:
            import pandas as pd
            if isinstance(training_data, pd.DataFrame):
                dataset_str = training_data.to_json()
            else:
                dataset_str = str(training_data)
            dataset_hash = hashlib.md5(dataset_str.encode()).hexdigest()[:12]
        except Exception as e:
            logger.warning(f"Could not generate dataset hash: {e}")
            dataset_hash = "unknown"

        # Generate model ID
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_id = f"{model_type}_{version}_{dataset_hash}"

        # Calculate performance metrics
        try:
            import pandas as pd
            import numpy as np

            if isinstance(training_data, pd.DataFrame):
                # Extract actual model if it's a package
                if isinstance(model, dict) and 'model' in model:
                    actual_model = model['model']
                else:
                    actual_model = model

                predictions = actual_model.predict(training_data)
                anomaly_rate = (predictions == -1).sum() / len(predictions)
            else:
                anomaly_rate = contamination  # Use expected rate
        except Exception as e:
            logger.warning(f"Could not calculate performance metrics: {e}")
            anomaly_rate = contamination

        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            version=version,
            training_date=datetime.now().isoformat(),
            dataset_hash=dataset_hash,
            training_samples=len(training_data) if hasattr(training_data, '__len__') else 0,
            contamination=contamination,
            performance_metrics={
                "training_anomaly_rate": float(anomaly_rate),
                "expected_contamination": contamination
            },
            calibration_data={}
        )

        # Save model
        model_path = self.MODEL_DIR / f"{model_id}.joblib"
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")

        # Save metadata
        metadata_path = self.MODEL_DIR / f"{model_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        logger.info(f"Metadata saved to {metadata_path}")

        # Update latest symlink
        latest_path = self.MODEL_DIR / f"latest_{model_type}.txt"
        with open(latest_path, 'w') as f:
            f.write(model_id)
        logger.info(f"Updated latest model pointer: {model_id}")

        return model_id

    def load_model(
        self,
        model_id: Optional[str] = None,
        model_type: str = "IsolationForest"
    ) -> Tuple[Any, ModelMetadata]:
        """
        Load model from disk.

        Parameters:
        -----------
        model_id : str, optional
            Specific model ID to load. If None, loads latest.
        model_type : str
            Model type to load

        Returns:
        --------
        Tuple[model, ModelMetadata]
        """
        # Use cache if available
        cache_key = model_id or f"latest_{model_type}"
        if cache_key in self._model_cache:
            logger.info(f"Loading model from cache: {cache_key}")
            return self._model_cache[cache_key]

        # Load latest if no ID specified
        if model_id is None:
            latest_path = self.MODEL_DIR / f"latest_{model_type}.txt"
            if latest_path.exists():
                with open(latest_path, 'r') as f:
                    model_id = f.read().strip()
                logger.info(f"Loading latest model: {model_id}")
            else:
                raise FileNotFoundError(
                    f"No trained {model_type} model found. "
                    f"Train a model first using train_and_save_model()."
                )

        # Load model and metadata
        model_path = self.MODEL_DIR / f"{model_id}.joblib"
        metadata_path = self.MODEL_DIR / f"{model_id}.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model = joblib.load(model_path)
        logger.info(f"Model loaded from {model_path}")

        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = ModelMetadata.from_dict(json.load(f))
        else:
            # Create minimal metadata if not found
            logger.warning(f"Metadata not found for {model_id}, creating minimal metadata")
            metadata = ModelMetadata(
                model_id=model_id,
                model_type=model_type,
                version="unknown",
                training_date=datetime.now().isoformat(),
                dataset_hash="unknown",
                training_samples=0,
                contamination=0.1,
                performance_metrics={},
                calibration_data={}
            )

        # Cache
        self._model_cache[cache_key] = (model, metadata)
        self._model_cache[model_id] = (model, metadata)

        return model, metadata

    def list_models(self) -> List[ModelMetadata]:
        """
        List all available models.

        Returns:
        --------
        List[ModelMetadata] : List of model metadata, sorted by date (newest first)
        """
        models = []
        for metadata_file in self.MODEL_DIR.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = ModelMetadata.from_dict(json.load(f))
                    models.append(metadata)
            except Exception as e:
                logger.warning(f"Could not load metadata from {metadata_file}: {e}")

        return sorted(models, key=lambda m: m.training_date, reverse=True)

    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model and its metadata.

        Parameters:
        -----------
        model_id : str
            Model ID to delete

        Returns:
        --------
        bool : True if successful
        """
        model_path = self.MODEL_DIR / f"{model_id}.joblib"
        metadata_path = self.MODEL_DIR / f"{model_id}.json"

        deleted = False

        if model_path.exists():
            model_path.unlink()
            logger.info(f"Deleted model: {model_path}")
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            logger.info(f"Deleted metadata: {metadata_path}")
            deleted = True

        # Remove from cache
        if model_id in self._model_cache:
            del self._model_cache[model_id]

        return deleted

    def update_calibration(
        self,
        model_id: str,
        calibration_data: Dict[str, float]
    ) -> None:
        """
        Update calibration data for a model.

        Parameters:
        -----------
        model_id : str
            Model ID to update
        calibration_data : Dict[str, float]
            Calibration data to add
        """
        metadata_path = self.MODEL_DIR / f"{model_id}.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found for model: {model_id}")

        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)

        # Update calibration data
        metadata_dict['calibration_data'].update(calibration_data)

        with open(metadata_path, 'w') as f:
            json.dump(metadata_dict, f, indent=2)

        logger.info(f"Updated calibration for model: {model_id}")

        # Invalidate cache
        if model_id in self._model_cache:
            del self._model_cache[model_id]

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        """
        Get metadata for a specific model.

        Parameters:
        -----------
        model_id : str
            Model ID

        Returns:
        --------
        ModelMetadata or None
        """
        metadata_path = self.MODEL_DIR / f"{model_id}.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, 'r') as f:
            return ModelMetadata.from_dict(json.load(f))

    def clear_cache(self) -> None:
        """Clear the model cache."""
        self._model_cache.clear()
        logger.info("Model cache cleared")


# Singleton instance
_model_manager_instance = None


def get_model_manager() -> MLModelManager:
    """Get singleton model manager instance."""
    global _model_manager_instance
    if _model_manager_instance is None:
        _model_manager_instance = MLModelManager()
    return _model_manager_instance
