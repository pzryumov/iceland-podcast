#!/usr/bin/env bash
# Convert podcast WAV files into podcast-ready MP3s.
#
# Usage:
#   ./convert_to_mp3.sh [INPUT_DIR] [OUTPUT_DIR]
# Defaults:
#   INPUT_DIR  = ../daily-podcasts/wav   (put your .wav files here)
#   OUTPUT_DIR = ./audio
#
# Output MP3s keep the same base filename as the source .wav, which must match
# the transcript names, e.g.  day-01-pod-1-land-of-fire-and-ice.wav
#                          -> day-01-pod-1-land-of-fire-and-ice.mp3
#
# Settings: mono, 96 kbps (good for two-voice speech; drop to 64k for smaller
# files), with EBU R128 loudness normalization so every episode plays at a
# consistent volume in the car. Requires ffmpeg (brew install ffmpeg).
set -euo pipefail

INPUT_DIR="${1:-../daily-podcasts/wav}"
OUTPUT_DIR="${2:-./audio}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg not found. Install it with:  brew install ffmpeg" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

shopt -s nullglob
wavs=("$INPUT_DIR"/*.wav)
if [ ${#wavs[@]} -eq 0 ]; then
  echo "No .wav files found in: $INPUT_DIR" >&2
  exit 1
fi

for w in "${wavs[@]}"; do
  base="$(basename "${w%.wav}")"
  out="$OUTPUT_DIR/$base.mp3"
  echo ">> $base"
  ffmpeg -hide_banner -loglevel error -y -i "$w" \
    -ac 1 \
    -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
    -c:a libmp3lame -b:a 96k \
    "$out"
done

echo "Done. MP3s written to: $OUTPUT_DIR"
