#!/bin/bash

echo "exec cam copy"

ffmpeg_command="ffmpeg -f v4l2 -i /dev/video0 -codec copy -f v4l2 /dev/video4"

$ffmpeg_command &

sleep 5

echo "exec venv"

source venv/bin/activate

while ! nmcli dev wifi | grep "COPEL 03"; do
    sleep 1
done

python main.py
