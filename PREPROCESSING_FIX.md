# Preprocessing Fix for Model Predictions

## Problem
Predictions were incorrect because preprocessing didn't match the training pipeline.

## Root Cause
The training code uses `ImageDataGenerator` with `rescale=1/255.0`, which:
- Takes images in uint8 format [0, 255]
- Divides by 255.0 to normalize to [0.0, 1.0] float32

Our original preprocessing was using **min-max normalization**, which produces different values and breaks predictions.

## Solution

### 1. Fixed Normalization Method
Changed from min-max normalization to **rescale normalization** (divide by 255.0):
```python
# OLD (wrong):
arr = (arr - min_val) / (max_val - min_val)

# NEW (correct):
arr = arr / 255.0  # Match training's rescale=1/255.0
```

### 2. Updated Preprocessing Pipeline
Now matches training exactly:
1. Load image as RGB
2. Resize to model input size (from `model.input_shape`)
3. Convert to uint8 numpy array [0, 255]
4. Convert to float32
5. **Divide by 255.0** to get [0.0, 1.0] range
6. Add batch dimension: (1, H, W, 3)

### 3. Three-Input Model Handling
Training uses 3 inputs (ensemble model). For inference:
- Create 3 identical copies of the preprocessed image
- Pass as list: `[x, x, x]` to `model.predict()`

## Testing
After this fix:
1. Upload a training image that you know should be classified correctly
2. Prediction should now match expected behavior
3. Check the raw output value in the response to verify normalization range is [0, 1]

## Key Changes
- `services/preprocess.py`: Changed `_normalize_array()` to use rescale (divide by 255.0)
- `main.py`: Improved three-input handling with proper array copies

The preprocessing now matches your training pipeline exactly!

