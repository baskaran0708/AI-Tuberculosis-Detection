# GitHub Troubleshooting Guide

## Common Issues and Solutions

### 1. Push Error: "remote contains work you don't have"

**Problem:** `! [rejected] main -> main (fetch first)`

**Solution:**
```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 2. Files Not Showing on GitHub

**Check if files are tracked:**
```powershell
git ls-files
```

**If missing, add them:**
```powershell
git add .
git commit -m "Add missing files"
git push
```

### 3. Large Model Files (.keras) - Avoid Pushing

**Problem:** GitHub has 100MB file limit. Models should NOT be in the repo.

**Solution:** Already handled by `.gitignore`, but verify:
```powershell
# Check if .keras files are being tracked (should return nothing)
git ls-files | Select-String "\.keras"
```

**If a model is tracked, remove it:**
```powershell
git rm --cached models/*.keras
git commit -m "Remove model files from tracking"
git push
```

### 4. Authentication Error

**Problem:** `fatal: Authentication failed`

**Solution - Use Personal Access Token:**

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when pushing:
```powershell
git push -u origin main
# Username: your-github-username
# Password: paste-your-token-here
```

**Or use SSH instead:**
```powershell
# Change remote to SSH
git remote set-url origin git@github.com:baskaran0708/AI-Tuberculosis-Detection.git
```

### 5. Branch Protection / Force Push Needed

**Problem:** Branch is protected or history conflict

**NEVER force push to main!** Instead:
```powershell
git pull --rebase origin main
git push
```

### 6. Check Current Status

**Always check before pushing:**
```powershell
git status
git log --oneline -5
git remote -v
```

### 7. Files You Should NOT Commit

✅ **Should be in repo:**
- All `.py` files
- `templates/`, `static/`
- `requirements*.txt`
- `README.md`, `.gitignore`
- `run.ps1`, `start.bat`

❌ **Should NOT be in repo (handled by .gitignore):**
- `.venv/` (virtual environment)
- `models/*.keras` (large model files)
- `__pycache__/`
- `.env` files
- `logs/`, `saved_models/`

### 8. Verify Your Repo on GitHub

Visit: https://github.com/baskaran0708/AI-Tuberculosis-Detection

Should see:
- ✅ README.md (with project description)
- ✅ All Python files
- ✅ Templates and static files
- ✅ Requirements files
- ❌ NO `.venv` folder
- ❌ NO `.keras` model files

### 9. Quick Fix Commands

**Reset everything and start fresh:**
```powershell
git init
git add .
git commit -m "Initial commit: AI TB Detection web app"
git remote add origin https://github.com/YOUR-USER/REPO-NAME.git

```git push -u origin main
git status
git remote -v
git push -u origin main
git pull origin main --allow-unrelated-histories
git push -u origin main