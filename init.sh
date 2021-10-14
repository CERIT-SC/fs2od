#!/bin/sh

# store start time of container
export START_TIME=`date -Is | sed 's/+/\n/g' | head -n 1`

if $RUN_PERIODICALLY; then
    # run processing
    python3 run-dirs-check.py

    # waiting
    python3 waiting.py
else
    # for manual and debug purposes
    sleep 1d
fi
