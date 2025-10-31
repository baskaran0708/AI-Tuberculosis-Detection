# AI Tuberculosis Detection (Futuristic Medical Imaging Web App)

A FastAPI-powered web application for AI-assisted tuberculosis (TB) screening. Upload chest X‑ray JPG/PNG images or DICOM (.dcm) files and get an instant prediction with a modern, medical UI.

## Features

- Futuristic, medical-themed UI with glassmorphism and gradients
- Upload support: JPG/PNG and DICOM (.dcm)
- Lazy model loading (.keras) with environment override
- Multi‑input model support (e.g., 3-input ensembles)
- Client-side preview, drag‑and‑drop, and a radial confidence gauge
- One‑click Windows launch scripts (`start.bat`, `run.ps1`)

## Tech Stack

- Backend: FastAPI, Uvicorn
- ML Runtime: TensorFlow / Keras (.keras model)
- Imaging: Pillow, pydicom, NumPy
- Frontend: Jinja2 templates + Tailwind (CDN)

## Project Structure

- `main.py` – FastAPI app, routes, predict API
- `services/model_loader.py` – Lazy, thread‑safe model loader; multi‑input detection
- `services/preprocess.py` – Preprocessing for JPG/PNG and DICOM; rescale=1/255 to match training
- `templates/` – Landing and Detect pages
- `static/js/detect.js` – Upload, preview, API call, confidence gauge
- `models/` – Put your `.keras` model here (auto‑detected)
- `run.ps1`, `start.bat` – One‑click launchers for Windows

## Requirements

- Windows 10/11 (tested) with PowerShell
- Python 3.10+

Dependencies: see `requirements-app.txt` (UI only) and `requirements-full.txt` (adds TensorFlow)

## Quick Start (Windows)

- Double‑click `start.bat` to run the UI quickly (no TensorFlow = no predictions yet)
- Or open PowerShell in the project folder and run:

```powershell
# Allow script for this terminal session if blocked
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Quick run (UI only)
./run.ps1
# Open http://127.0.0.1:8000 and go to /detect
```

### Enable Predictions (TensorFlow)

```powershell
# With your model path (recommended)
./run.ps1 -Full -ModelPath "C:\Users\YOURNAME\path\to\tb_best_model.keras"

# Or place your model in the repo at models\model.keras and run
./run.ps1 -Full
```

The server will print the URL (e.g., `http://127.0.0.1:8000`).

## Model Placement

- Recommended: keep your trained model outside the repo and pass the path at runtime:
```powershell
./run.ps1 -Full -ModelPath "D:\models\tb_best_model.keras"
```
- Alternative: copy `.keras` into `models/` (first `.keras` file is auto‑detected).
- You can also set an env var for ad‑hoc runs:
```powershell
$env:MODEL_PATH = "D:\Ai_Model_Detect_Tuberculosis\tb_best_model.keras"
```

## API

- `POST /api/predict`
  - Form: `file` (binary) — JPG/PNG image or DICOM `.dcm`
  - Response:
```json
{
  "label": "Tuberculosis" | "Normal",
  "confidence": 0.87,
  "raw_output": 0.87,
  "input": { "type": "image" | "dicom", "filename": "...", "shape": [H, W, C], "preprocessing": "rescale_1_255" }
}
```

Notes:
- Preprocessing strictly matches training with `rescale=1/255.0`.
- Multi‑input models (e.g., 3 inputs) are supported — the same image is copied across inputs for inference.

## Troubleshooting

- Script blocked by policy:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
- Port already in use: `./run.ps1 -Port 8010` (auto‑fallback tries nearby ports)
- venv locked/corrupted: close terminals → `Remove-Item -Recurse -Force .venv` → rerun
- Slow TensorFlow install: `pip install --no-cache-dir -r requirements-full.txt`
- Model not found: ensure `.keras` file exists at the printed path or pass `-ModelPath`.
- Predictions look wrong: verify your model was trained with rescale=1/255 and matches channels‑last `(H, W, C)`; replace the model when ready.

## Development

Install dependencies and run manually:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-full.txt  # or requirements-app.txt for UI only
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Screens

- Landing: modern, medical-themed hero with CT/X‑ray imagery
- Detect: upload card, large preview, prediction result with radial confidence gauge

## License

MIT (update as needed).

## Acknowledgements

- Built with FastAPI, Tailwind, TensorFlow, Pillow, and pydicom.
