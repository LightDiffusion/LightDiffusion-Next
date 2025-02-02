#!/bin/bash

VENV_DIR=.venv
# for WSL2 Ubuntu install
# sudo apt install software-properties-common
# sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.10 python3.10-venv python3.10-full python3-pip

# Check if .venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3.10 -m venv $VENV_DIR
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

pip3 install --index-url https://download.pytorch.org/whl/cu121 \
    'torch==2.2.2' torchvision 'xformers>=0.0.22' 'triton>=2.1.0' \
    'stable_fast-1.0.5+torch222cu121-cp310-cp310-manylinux2014_x86_64.whl'

# Install tkinter
echo "Installing tkinter..."
sudo apt-get install python3.10-tk

# Install additional requirements
if [ -f requirements.txt ]; then
    echo "Installing additional requirements..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found, skipping..."
fi

# Launch the script
echo "Launching LightDiffusion..."
# python3.10 ./modules/user/GUI.py
python3.10 LightDiffusion.py

# Deactivate the virtual environment
deactivate
