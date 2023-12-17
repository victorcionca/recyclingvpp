#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <arg1>"
    exit 1
fi

# Define the directory to be transferred
source_directory="$1"

# Define the common destination directory on the devices
destination_directory="/home/pi/recyclingvpp/"

# Define the list of devices
devices=("raspberrypi1.local" "raspberrypi2.local" "raspberrypi3.local" "raspberrypi4.local")

# Define the common username and password
username="pi"
password="123"

# Iterate over the devices and perform the scp command
for device in "${devices[@]}"; do
    echo "Copying to ${device}..."
    scp -r -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -P 22 \
        "${source_directory}" "${username}@${device}:${destination_directory}"
    if [ $? -eq 0 ]; then
        echo "Copy to ${device} successful."
    else
        echo "Error copying to ${device}."
    fi
done