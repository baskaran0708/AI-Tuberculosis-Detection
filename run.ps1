param(
	[switch]$Full,
	[string]$ModelPath,
	[string]$HostName = "127.0.0.1",
	[int]$Port = 8000
)

$ErrorActionPreference = "Stop"

Write-Host "=== AI TB Detect - Launcher ===" -ForegroundColor Cyan

# Ensure we're in script directory
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Bypass execution policy for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force | Out-Null

# Function to check if port is available
function Test-Port {
	param([int]$PortNum)
	try {
		$connection = New-Object System.Net.Sockets.TcpClient($HostName, $PortNum)
		$connection.Close()
		return $false
	} catch {
		return $true
	}
}

# Check port availability and find alternative if needed
if (-not (Test-Port -PortNum $Port)) {
	Write-Host "Port $Port is in use. Trying alternative ports..." -ForegroundColor Yellow
	$found = $false
	for ($p = $Port + 1; $p -le $Port + 10; $p++) {
		if (Test-Port -PortNum $p) {
			$Port = $p
			$found = $true
			Write-Host "Using port $Port instead" -ForegroundColor Green
			break
		}
	}
	if (-not $found) {
		Write-Host "Could not find an available port. Please close other applications using ports $Port-$($Port+10)" -ForegroundColor Red
		exit 1
	}
}

# Handle locked venv - try to remove and recreate
if ((Test-Path .venv) -and (-not (Test-Path (Join-Path .venv "Scripts\python.exe")))) {
	Write-Host "Removing corrupted virtual environment..." -ForegroundColor Yellow
	Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
}

# Create venv if missing
if (-not (Test-Path .venv)) {
	Write-Host "Creating virtual environment..." -ForegroundColor Yellow
	python -m venv .venv
	if ($LASTEXITCODE -ne 0) {
		Write-Host "Failed to create venv. Make sure Python is installed." -ForegroundColor Red
		exit 1
	}
}

$venvPython = Join-Path (Resolve-Path .venv).Path "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
	Write-Host "Virtual environment python not found. Recreating..." -ForegroundColor Yellow
	Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
	python -m venv .venv
	$venvPython = Join-Path (Resolve-Path .venv).Path "Scripts\python.exe"
}

# Upgrade pip (safe and quick)
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip --quiet | Out-Null

# Install deps
if ($Full) {
	Write-Host "Installing full dependencies (with TensorFlow)..." -ForegroundColor Yellow
	& $venvPython -m pip install -r requirements-full.txt
} else {
	Write-Host "Installing app dependencies (no TensorFlow)..." -ForegroundColor Yellow
	& $venvPython -m pip install -r requirements-app.txt
}

if ($LASTEXITCODE -ne 0) {
	Write-Host "Failed to install dependencies." -ForegroundColor Red
	exit 1
}

# Optional: set MODEL_PATH for this process
if ($ModelPath) {
	if (Test-Path $ModelPath) {
		$env:MODEL_PATH = (Resolve-Path $ModelPath).Path
		Write-Host "Using MODEL_PATH=$($env:MODEL_PATH)" -ForegroundColor Green
	} else {
		Write-Host "Warning: Model path not found: $ModelPath" -ForegroundColor Yellow
	}
}

# Run server
$url = "http://${HostName}:${Port}"
Write-Host "Starting server on $url ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
& $venvPython -m uvicorn main:app --host $HostName --port $Port --reload
