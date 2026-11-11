#!/bin/sh
# usage: make.sh OUT.mp4   (run from the atlas work folder)
python3 tools/render_atlas.py parts /mnt/project-files/bennu/EP012/voice/narration.wav minbar_top.json - | ffmpeg -v error -y -i bg.mp4 -f rawvideo -pix_fmt rgba -s 1920x1080 -r 30 -i - -ss 300.4 -t 12.0 -i /mnt/project-files/bennu/EP012/v2/EP012_Bennu_final_v2_1080p30.mp4 -filter_complex "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]" -map "[v]" -map 2:a -t 12.0 -c:v libx264 -crf 17 -preset medium -c:a aac -b:a 192k -movflags +faststart "$1"
