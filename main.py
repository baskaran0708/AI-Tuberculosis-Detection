from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

from services.model_loader import get_model
from services.preprocess import prepare_input_from_upload

app = FastAPI(title="AI Tuberculosis Detection")

# Static and templates
base_dir = Path(__file__).parent
static_dir = base_dir / "static"
templates_dir = base_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
	return templates.TemplateResponse("index.html", {"request": request})


@app.get("/detect", response_class=HTMLResponse)
async def detect_page(request: Request):
	return templates.TemplateResponse("detect.html", {"request": request})


@app.post("/api/predict")
async def predict(file: UploadFile = File(...)):
	try:
		from services.model_loader import get_model, get_model_input_count
		import numpy as np
		model = get_model()
		x, meta = await prepare_input_from_upload(file, model)
		
		# Handle models with multiple inputs (e.g., 3 identical inputs for ensemble)
		# Training uses 3 inputs with same image (potentially augmented differently)
		# For inference, we use the same preprocessed image 3 times
		input_count = get_model_input_count()
		if input_count > 1:
			# Create identical copies for each input (matching training's multi-input structure)
			# Use copy() to ensure they're separate arrays
			inputs = [np.copy(x) for _ in range(input_count)]
			pred = model.predict(inputs, verbose=0)
		else:
			pred = model.predict(x, verbose=0)
		
		# Binary classification: output is probability of TB
		# Model output shape is typically (1, 1) for sigmoid or (1,) for single output
		pred_flat = pred.flatten()
		prob = float(pred_flat[0])
		
		# Clip probability to [0, 1] range
		prob = max(0.0, min(1.0, prob))
		
		label = "Tuberculosis" if prob >= 0.5 else "Normal"
		
		return JSONResponse({
			"label": label,
			"confidence": prob,
			"raw_output": float(pred_flat[0]),
			"input": meta
		})
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		error_detail = f"{str(e)}\n{traceback.format_exc()}"
		raise HTTPException(status_code=500, detail=error_detail)


if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
