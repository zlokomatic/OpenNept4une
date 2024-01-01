#!/bin/bash

sudo apt update
sudo apt install python3.11-venv -y

# Navigate to the script directory
cd /home/mks/OpenNept4une/display

# Create a Python virtual environment in the current directory
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required Python packages
pip install pyserial moonrakerpy nextion

# Deactivate the virtual environment
deactivate
