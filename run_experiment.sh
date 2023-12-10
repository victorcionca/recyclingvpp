#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <arg1> <arg2> <arg3> <arg4>"
    exit 1
fi

# Change directory to /home/pi/recyclingvpp/
cd /home/pi/recyclingvpp/ || exit 1

# Activate the virtual environment
source venv/bin/activate || exit 1

# Change directory to /home/pi/recyclingvpp/experiment_manager/
cd experiment_manager || exit 1

# Run the Python script with the specified arguments
python3 main.py "$1" "$2" "$3" "$4"