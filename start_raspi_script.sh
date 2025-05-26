#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate the virtual environment
source "$SCRIPT_DIR/myenv/bin/activate"
cd start_scripts
python "start_webserver_raspi.py"
cd ..