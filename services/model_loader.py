import os
import threading
from pathlib import Path
from typing import Optional, List

_model_instance = None
_model_lock = threading.Lock()
_model_input_shape_cache = None


def _resolve_model_path() -> Path:
	# 1) Environment override
	env_path = os.getenv("MODEL_PATH")
	if env_path:
		p = Path(env_path)
		if p.exists():
			return p
	# 2) Default path
	models_dir = Path(__file__).resolve().parent.parent / "models"
	default_path = models_dir / "model.keras"
	if default_path.exists():
		return default_path
	# 3) Auto-detect first .keras in models folder
	candidates: List[Path] = sorted(models_dir.glob("*.keras"))
	if candidates:
		return candidates[0]
	# 4) Nothing found
	return default_path


def get_model():
	"""Lazy-load and cache the Keras model.
	Returns the loaded model instance. TensorFlow is imported only when needed.
	"""
	global _model_instance, _model_input_shape_cache
	if _model_instance is not None:
		return _model_instance
	with _model_lock:
		if _model_instance is None:
			try:
				import tensorflow as tf  # Lazy import
			except Exception as import_err:
				raise RuntimeError(
					"TensorFlow is required for predictions but is not installed. Install with 'pip install tensorflow==2.16.2' or use requirements-full.txt."
				) from import_err
			model_path = _resolve_model_path()
			if not model_path.exists():
				raise FileNotFoundError(f"Model file not found at {model_path}. Place your .keras model in models/ or set MODEL_PATH.")
			_model_instance = tf.keras.models.load_model(str(model_path))
			# Cache input shape (batch, H, W, C) or similar
			# Handle multiple inputs - get the first input shape
			shape = _model_instance.input_shape
			if isinstance(shape, list):
				# Multiple inputs - use first one's shape
				shape = shape[0] if shape else None
			if shape is None:
				# Try getting from input layer
				if hasattr(_model_instance, 'input') and _model_instance.input is not None:
					if isinstance(_model_instance.input, list):
						shape = _model_instance.input[0].shape if _model_instance.input else None
					else:
						shape = _model_instance.input.shape
			_model_input_shape_cache = shape
	return _model_instance


def get_model_input_count():
	"""Get the number of inputs the model expects."""
	model = get_model()
	if isinstance(model.input_shape, list):
		return len(model.input_shape)
	if hasattr(model, 'input') and model.input is not None:
		if isinstance(model.input, list):
			return len(model.input)
	return 1


def get_model_input_shape():
	# Returns tuple like (None, H, W, C)
	global _model_input_shape_cache
	if _model_input_shape_cache is None:
		_ = get_model()
	return _model_input_shape_cache
