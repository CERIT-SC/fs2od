#!/bin/bash

# store start time of container
export START_TIME=`date -Is | sed 's/+/\n/g' | head -n 1`

# run processing
python3 run-dirs-check.py

# waiting
python3 waiting.py
