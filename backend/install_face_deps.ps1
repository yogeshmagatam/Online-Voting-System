# Install face_recognition dependencies on Windows
# This script installs prebuilt dlib and face_recognition packages

Write-Host "Installing face_recognition dependencies..." -ForegroundColor Green
Write-Host "This will use prebuilt wheels from a trusted repository." -ForegroundColor Cyan

# Get Python version
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$pythonVersionShort = python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')"
$pythonVersionMajorMinor = [float]$pythonVersion
Write-Host "`nDetected Python version: $pythonVersion" -ForegroundColor Cyan

# Check if Python version is supported
if ($pythonVersionMajorMinor -gt 3.12) {
    Write-Host "`nWARNING: Python $pythonVersion detected!" -ForegroundColor Red
    Write-Host "Prebuilt dlib wheels are only available for Python 3.8-3.12" -ForegroundColor Yellow
    Write-Host "`nRECOMMENDED SOLUTION:" -ForegroundColor Cyan
    Write-Host "1. Create a new virtual environment with Python 3.11:" -ForegroundColor White
    Write-Host "   py -3.11 -m venv .venv311" -ForegroundColor Gray
    Write-Host "   .\.venv311\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "   pip install -r backend\requirements.txt" -ForegroundColor Gray
    Write-Host "   .\backend\install_face_deps.ps1" -ForegroundColor Gray
    Write-Host "`n2. OR install Miniconda and use conda:" -ForegroundColor White
    Write-Host "   Download from: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Gray
    Write-Host "   After installation, restart PowerShell and run:" -ForegroundColor Gray
    Write-Host "   conda create -n faceenv python=3.11 -y" -ForegroundColor Gray
    Write-Host "   conda activate faceenv" -ForegroundColor Gray
    Write-Host "   conda install -c conda-forge dlib face_recognition" -ForegroundColor Gray
    exit 1
}

# Install dependencies
Write-Host "`nInstalling numpy..." -ForegroundColor Yellow
pip install numpy

Write-Host "`nInstalling Pillow..." -ForegroundColor Yellow
pip install Pillow

# Install cmake (needed by dlib)
Write-Host "`nInstalling cmake..." -ForegroundColor Yellow
pip install cmake

# Try to install prebuilt dlib 
Write-Host "`nInstalling dlib (prebuilt)..." -ForegroundColor Yellow
Write-Host "Trying prebuilt wheels from GitHub..." -ForegroundColor Cyan

# Try from z-mahmud22's repository (has cp311 wheel)
$dlibWheelUrl = "https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.1-cp311-cp311-win_amd64.whl"
Write-Host "Downloading from: $dlibWheelUrl" -ForegroundColor Cyan
pip install $dlibWheelUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nFailed. Trying alternative source..." -ForegroundColor Yellow
    # Try sachadee's repository
    pip install "https://github.com/sachadee/Dlib/raw/main/dlib-19.22.99-cp311-cp311-win_amd64.whl"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nFailed. Trying to build from source..." -ForegroundColor Yellow
        # Install Visual C++ Build Tools dependencies
        pip install wheel
        # Try building from source (will only work if Visual Studio/Build Tools installed)
        pip install dlib
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`nCould not install dlib." -ForegroundColor Red
            Write-Host "`nPLEASE CHOOSE ONE OF THESE OPTIONS:" -ForegroundColor Yellow
            Write-Host "`nOption 1: Install Miniconda (Easiest)" -ForegroundColor Cyan
            Write-Host "  1. Download from: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor White
            Write-Host "  2. Install and restart PowerShell" -ForegroundColor White
            Write-Host "  3. Run: conda create -n faceenv python=3.11 -y" -ForegroundColor White
            Write-Host "  4. Run: conda activate faceenv" -ForegroundColor White
            Write-Host "  5. Run: pip install -r backend\requirements.txt" -ForegroundColor White
            Write-Host "  6. Run: conda install -c conda-forge dlib face_recognition" -ForegroundColor White
            Write-Host "`nOption 2: Skip face recognition (app will work without it)" -ForegroundColor Cyan
            Write-Host "  The app will run but face verification features won't work" -ForegroundColor White
            exit 1
        }
    }
}


# Install face_recognition_models
Write-Host "`nInstalling face_recognition_models..." -ForegroundColor Yellow
pip install face_recognition_models

# Install face_recognition (without dependencies since we already have dlib)
Write-Host "`nInstalling face_recognition..." -ForegroundColor Yellow
pip install --no-deps face_recognition
pip install Click

# Verify installation
Write-Host "`nVerifying installation..." -ForegroundColor Yellow
python -c "import face_recognition, dlib; print('Face recognition successfully installed!')"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nInstallation completed successfully!" -ForegroundColor Green
    Write-Host "You can now use face_recognition in your application." -ForegroundColor Cyan
} else {
    Write-Host "`nInstallation verification failed." -ForegroundColor Red
    Write-Host "Please use conda instead (see INSTALL_FACE_RECOGNITION.md)" -ForegroundColor Yellow
}
