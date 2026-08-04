#!/bin/bash
set -euo pipefail

echo "packaide-irregular-stock-worker: Starting RunPod handler"
python3 -u /rp_handler.py
