@echo off
SET VENV_DIR=.venv

REM Check if .venv exists
IF NOT EXIST %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM Activate the virtual environment
CALL %VENV_DIR%\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install specific packages
echo Installing required packages...
pip install uv

REM Check for NVIDIA GPU
FOR /F "delims=" %%i IN ('nvidia-smi 2^>^&1') DO (
    SET GPU_CHECK=%%i
)
IF NOT ERRORLEVEL 1 (
    echo NVIDIA GPU detected, installing GPU dependencies...
    uv pip install xformers torch torchvision --index-url https://download.pytorch.org/whl/cu126
) ELSE (
    echo No NVIDIA GPU detected, installing CPU dependencies...
    uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

uv pip install numpy>=1.24.3

REM Install additional requirements
IF EXIST requirements.txt (
    echo Installing additional requirements...
    uv pip install -r requirements.txt
) ELSE (
    echo requirements.txt not found, skipping...
)

REM Check for enhance-prompt argument
echo Checking for enhance-prompt argument...
echo %* | findstr /i /c:"--enhance-prompt" >nul
IF %ERRORLEVEL% EQU 0 (
    echo Installing ollama with winget...
    winget install --id ollama.ollama
    ollama pull deepseek-r1
)

REM Launch the script
echo Launching LightDiffusion...
python .\modules\user\pipeline.py %*

REM Deactivate the virtual environment
deactivate
