# Quick Start - Copy & Paste These Commands

## Method 1: Double-click (Easiest)

1. **Double-click `start.bat`** in the project folder
2. Wait for it to start (first time may take 1-2 minutes)
3. Open browser to the URL shown (usually `http://127.0.0.1:8000`)

---

## Method 2: PowerShell Commands (If double-click doesn't work)

**Open PowerShell in the project folder** (Right-click folder → "Open in Terminal" or "Open PowerShell window here")

**Then copy-paste these commands ONE AT A TIME:**

### Step 1: Allow script execution
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Step 2A: Quick start (UI only, no predictions)
```powershell
.\run.ps1
```
Then open: http://127.0.0.1:8000

### Step 2B: Full start (with predictions - includes TensorFlow)
```powershell
.\run.ps1 -Full -ModelPath "C:\Users\baska\Downloads\Phone Link\tb_best_model.keras"
```

---

## If You See Errors:

### "Port 8000 is in use"
The script will automatically try port 8001, 8002, etc. Just use the URL it shows.

### "Permission denied .venv"
Close ALL PowerShell windows, then run:
```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\run.ps1
```

### "Python not found"
Install Python from: https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation.

---

## After It Starts:

- Landing page: http://127.0.0.1:8000 (or whatever port it shows)
- Detection page: http://127.0.0.1:8000/detect

Press **Ctrl+C** in the terminal to stop the server.

