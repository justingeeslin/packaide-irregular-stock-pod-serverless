#!/bin/bash
set -euo pipefail

echo "packaide-irregular-stock-worker: Starting RunPod handler"
echo "packaide-irregular-stock-worker: Python $(python3 --version)"
python3 - <<'PY'
import platform

import packaide
import packaide_irregular_stock
import runpod

print(f"packaide-irregular-stock-worker: platform {platform.platform()}", flush=True)
print("packaide-irregular-stock-worker: imports OK", flush=True)
PY

python3 -u /rp_handler.py
