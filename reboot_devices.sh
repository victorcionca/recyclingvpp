#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <device1> <device2> <device3> <device4>"
    exit 1
fi

# Array of device hostnames or IP addresses
devices=("$@")

# SSH username
username="pi"

# Loop through devices and reboot each one
for device in "${devices[@]}"; do
    echo "Rebooting ${device}..."
    ssh "${username}@${device}" 'sudo reboot'
done