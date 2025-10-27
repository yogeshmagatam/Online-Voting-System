Installing face_recognition on Windows

The `face_recognition` package depends on `dlib`, which is hard to build on Windows (requires CMake and MSVC). Use prebuilt binaries instead of building from source.

Quick start (recommended on Windows)

1) Run the helper script (from repo root or backend folder):

```powershell
./backend/install_face_deps.ps1
```

This installs `dlib-bin` (prebuilt), `Pillow`, `face_recognition_models`, and `face_recognition` without pulling `dlib` from source.

Manual options

1) Pre-built wheel
   - Find a pre-built `dlib` wheel matching your Python and architecture.
   - Install it and then install face_recognition:

```powershell
pip install path\to\dlib‑X.Y.Z‑cp3X‑cp3X‑win_amd64.whl
pip install face_recognition
```

2) Conda (often easiest)

```powershell
conda create -n faceenv python=3.11 -y; conda activate faceenv
conda install -c conda-forge dlib face_recognition
```

3) Build from source (advanced)

```powershell
pip install cmake
pip install dlib
pip install face_recognition
```

Verify

```powershell
python -c "import face_recognition, dlib; print('ok')"
```

Notes
- The base `requirements.txt` purposely omits `face_recognition` to avoid building `dlib`. Use the script above for Windows.
- If you cannot install these packages, the app will still run, but face verification endpoints will not work.
