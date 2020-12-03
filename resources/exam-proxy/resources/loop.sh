#!/bin/sh


if [ "$VULNHOST" = "" ]; then
    echo "VULNHOST NOT SET"
    exit 1
fi
if [ "$VULNPORT" = "" ]; then
    echo VULNPORT NOT SET
    exit 2
fi

socat -d -d TCP-LISTEN:4000,fork EXEC:"exam-proxy --output /log/challenge.log -- nc -N $VULNHOST $VULNPORT" 2>&1 > /log/socat.log
