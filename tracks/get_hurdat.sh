#!/bin/bash

# URL for the HURDAT2 storm data
DATA_URL="https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2024-040425.txt"
DATA_FILE="hurdat2-bt.txt"
TRACK_OUTPUT="storm_tracks.txt"

# download the data if not present
if [ ! -f "$DATA_FILE" ]; then
    echo "Downloading storm data from $DATA_URL..."
    curl -s -o "$DATA_FILE" "$DATA_URL"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download the data file"
        exit 1
    fi
    echo "Download complete."
fi

# prompt user for the STORM_ID
read -p "Enter the STORM_ID (e.g. AL031968): " STORM_ID

if [ -z "$STORM_ID" ]; then
    echo "Error: No STORM_ID entered."
    exit 1
fi

# find the storm header line number
START_LINE=$(grep -n "^$STORM_ID," "$DATA_FILE" | cut -d: -f1)
if [ -z "$START_LINE" ]; then
    echo "Storm ID $STORM_ID not found."
    exit 1
fi

# get the number of data lines for this storm and extract the storm's track
NUM_POINTS=$(sed -n "${START_LINE}p" "$DATA_FILE" | awk -F, '{print $3}' | tr -d ' ')

END_LINE=$((START_LINE + NUM_POINTS))
sed -n "${START_LINE},${END_LINE}p" "$DATA_FILE" > "$TRACK_OUTPUT"

echo "Track data for storm $STORM_ID saved to $TRACK_OUTPUT"