from io import BytesIO
from typing import Dict, Tuple

import numpy as np
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageFile
import pydicom

from services.model_loader import get_model_input_shape

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/pjpeg", "image/x-png"}
SUPPORTED_DICOM_EXT = {".dcm", ".dicom"}

# Allow loading slightly truncated images from some sources
ImageFile.LOAD_TRUNCATED_IMAGES = True


def _infer_target_shape() -> Tuple[int, int, int]:
	# Model input shape is typically (None, H, W, C)
	shape = get_model_input_shape()
	if len(shape) != 4:
		raise HTTPException(status_code=400, detail=f"Unsupported model input shape: {shape}")
	_, h, w, c = shape
	if c is None:
		c = 3
	return int(h), int(w), int(c)


def _to_rgb(image: Image.Image, channels: int) -> Image.Image:
	if channels == 1:
		return image.convert("L")
	# Convert any mode (L, LA, P, RGBA, CMYK) to RGB
	return image.convert("RGB")


def _normalize_array(arr: np.ndarray, use_rescale: bool = True) -> np.ndarray:
	"""
	Normalize array to [0, 1] range.
	If use_rescale=True: divide by 255.0 (matches training's rescale=1/255.0)
	If use_rescale=False: min-max normalization (for DICOM that may have different ranges)
	"""
	arr = arr.astype("float32")
	if use_rescale:
		# Match training: rescale=1/255.0 from ImageDataGenerator
		# Assumes input is uint8 [0, 255]
		arr = arr / 255.0
		arr = np.clip(arr, 0.0, 1.0)
	else:
		# Min-max normalization for DICOM or unusual ranges
		min_val = float(arr.min()) if arr.size else 0.0
		max_val = float(arr.max()) if arr.size else 1.0
		if max_val > min_val:
			arr = (arr - min_val) / (max_val - min_val)
		else:
			arr = np.zeros_like(arr, dtype="float32")
	return arr


def _preprocess_pil(img: Image.Image, target_h: int, target_w: int, channels: int, use_rescale: bool = True) -> np.ndarray:
	"""
	Preprocess PIL image to match training pipeline.
	Matches ImageDataGenerator with rescale=1/255.0
	"""
	# Convert to RGB (PIL images are usually RGB when opened)
	img = _to_rgb(img, channels)
	# Resize to target size (match training target_size)
	img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
	# Convert to numpy array - should be uint8 [0, 255]
	arr = np.array(img, dtype=np.uint8)
	# Normalize using rescale (divide by 255.0) to match training
	arr = _normalize_array(arr, use_rescale=use_rescale)
	
	# Handle channel mismatches
	if channels == 1 and arr.ndim == 3:
		# Convert RGB to single channel (take first channel)
		arr = arr[..., 0:1]
	elif channels == 3 and arr.ndim == 2:
		# Convert grayscale to RGB by stacking
		arr = np.stack([arr, arr, arr], axis=-1)
	
	# Ensure shape is (H, W, C) before adding batch dimension
	if arr.ndim == 2:
		arr = np.expand_dims(arr, axis=-1)
	
	# Add batch dimension: (1, H, W, C)
	arr = np.expand_dims(arr, axis=0)
	return arr


def _read_dicom(bytes_data: bytes) -> Image.Image:
	"""
	Read DICOM file and convert to PIL Image.
	Handles various DICOM pixel value ranges.
	"""
	# Some DICOM files require force=True if missing meta
	ds = pydicom.dcmread(BytesIO(bytes_data), force=True)
	# Extract pixel data; handle multi-frame by selecting middle slice
	pixels = ds.pixel_array
	
	# Handle multi-frame DICOM
	if pixels.ndim == 3:
		shape = pixels.shape
		if shape[0] > 3:  # (frames, H, W)
			idx = shape[0] // 2
			pixels = pixels[idx]
		elif shape[-1] > 3:  # (H, W, frames)
			idx = shape[-1] // 2
			pixels = pixels[..., idx]
	
	# Normalize DICOM to 0-255 range for PIL
	# DICOM can have various bit depths and value ranges
	pixels_float = pixels.astype("float32")
	min_val = float(pixels_float.min())
	max_val = float(pixels_float.max())
	
	if max_val > min_val:
		# Normalize to 0-255 range
		pixels8 = ((pixels_float - min_val) / (max_val - min_val) * 255.0).clip(0, 255).astype("uint8")
	else:
		pixels8 = np.zeros_like(pixels, dtype="uint8")
	
	return Image.fromarray(pixels8)


def _read_image(bytes_data: bytes) -> Image.Image:
	img = Image.open(BytesIO(bytes_data))
	# Ensure actual load to catch early errors
	img.load()
	return img


async def prepare_input_from_upload(file: UploadFile, model) -> Tuple[np.ndarray, Dict]:
	"""
	Prepare input from uploaded file to match training preprocessing.
	Training uses ImageDataGenerator with rescale=1/255.0, so we divide by 255.0.
	Returns preprocessed array ready for model prediction.
	"""
	filename = (file.filename or "").lower()
	content_type = (file.content_type or "").lower()
	data = await file.read()

	target_h, target_w, channels = _infer_target_shape()

	try:
		if content_type in SUPPORTED_IMAGE_TYPES or filename.endswith((".jpg", ".jpeg", ".png")):
			# Standard image: use rescale (divide by 255.0) to match training
			img = _read_image(data)
			arr = _preprocess_pil(img, target_h, target_w, channels, use_rescale=True)
			meta = {
				"type": "image", 
				"filename": file.filename, 
				"shape": [target_h, target_w, channels],
				"preprocessing": "rescale_1_255"
			}
			return arr, meta
		elif filename.endswith(tuple(SUPPORTED_DICOM_EXT)) or content_type in {"application/dicom", "application/dicom+json", "application/dicom+octet-stream", "application/octet-stream"}:
			# DICOM: convert to PIL first, then apply rescale
			img = _read_dicom(data)
			# DICOM is already normalized to 0-255 uint8 in _read_dicom, so use rescale
			arr = _preprocess_pil(img, target_h, target_w, channels, use_rescale=True)
			meta = {
				"type": "dicom", 
				"filename": file.filename, 
				"shape": [target_h, target_w, channels],
				"preprocessing": "rescale_1_255"
			}
			return arr, meta
		else:
			raise HTTPException(status_code=400, detail="Unsupported file type. Upload JPG, PNG, or DICOM (.dcm)")
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Failed to process file: {e}")
