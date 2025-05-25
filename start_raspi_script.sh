#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate the virtual environment
source "$SCRIPT_DIR/myenv/bin/activate"

python "$SCRIPT_DIR/start_scripts/start_gazebo_sitl.py" -

