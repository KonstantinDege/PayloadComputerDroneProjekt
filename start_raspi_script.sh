#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
./activate_myenv.sh

python "$SCRIPT_DIR/start_scripts/start_gazebo_sitl.py" -